"""Local/private single-process API. Progress streams; consistent snapshots are saved."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from threading import Lock

from checks import update_outcomes
from documents import DocumentStore
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS
from models import AnalysisRequest, DesignRun, RefinementRequest, Usage
from pipeline import Workflow
from pydantic import ValidationError
from run_store import RunStore, export_csv, export_json, run_snapshot

logger = logging.getLogger(__name__)


def create_app(store=None, workflow=None):
    load_dotenv(Path(__file__).with_name(".env"))
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 65536
    CORS(app, origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")])
    data_home = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    data = Path(os.getenv("DATA_DIR") or data_home / "jigsaw").expanduser()
    store = store or RunStore(data / "runs")
    workflow = workflow or Workflow(DocumentStore(data / "documents"))
    store.interrupt_unfinished()
    admission = Lock()
    app.extensions.update(run_store=store, workflow=workflow, admission=admission)

    def start(run):
        if not admission.acquire(blocking=False):
            return jsonify(error="Another design run is active; retry when it finishes"), 409
        released = False

        def release():
            nonlocal released
            if not released:
                released = True
                admission.release()

        def stop_run(lifecycle, reason):
            run.lifecycle, run.terminal_reason = lifecycle, reason
            run.review_completed = False
            update_outcomes(run)

        try:
            store.save(run)
        except Exception:
            release()
            logger.exception("Could not save initial run")
            return jsonify(error="Could not save the initial run"), 500

        def generate():
            sequence = 0
            iterator = None
            terminal_sent = False

            def event(kind, **fields):
                nonlocal sequence
                sequence += 1
                return "data: " + json.dumps({"type": kind, "run_id": run.id, "sequence": sequence, **fields}) + "\n\n"

            try:
                yield event("started", snapshot=run_snapshot(run))
                iterator = workflow.execute(run)
                for item in iterator:
                    kind = item["type"]
                    fields = {k: v for k, v in item.items() if k != "type"}
                    if kind in {"snapshot", "complete", "error"}:
                        store.save(run)
                        fields["snapshot"] = run_snapshot(run)
                    if kind in {"complete", "error"}:
                        terminal_sent = True
                    yield event(kind, **fields)
                if not terminal_sent:
                    store.save(run)
                    terminal_sent = True
                    yield event(
                        "error" if run.lifecycle == "error" else "complete",
                        message=run.terminal_reason,
                        snapshot=run_snapshot(run),
                    )
            except GeneratorExit:
                if iterator is not None:
                    iterator.close()
                if not terminal_sent:
                    stop_run("interrupted", "Client disconnected; no automatic background continuation")
                raise
            except Exception:
                logger.exception("Run could not finish or persist")
                stop_run("error", "Run failed while executing or saving; retrieve the last saved snapshot")
                try:
                    store.save(run)
                except Exception:
                    logger.exception("Failed to save terminal error")
                terminal_sent = True
                yield event("error", message=run.terminal_reason, snapshot=run_snapshot(run))
            finally:
                try:
                    if iterator is not None:
                        iterator.close()
                    if not terminal_sent and run.lifecycle in {"interrupted", "error"}:
                        store.save(run)
                except Exception:
                    logger.exception("Final snapshot unavailable")
                finally:
                    release()

        response = Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Run-Id": run.id,
            },
        )

        # Also release when a response is closed without starting its generator.
        def closed():
            if not released:
                stop_run("interrupted", "Response closed before completion")
                try:
                    store.save(run)
                finally:
                    release()

        response.call_on_close(closed)
        return response

    @app.errorhandler(ValidationError)
    def invalid(error):
        return jsonify(
            error="Invalid request",
            details=[
                {"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]}
                for e in error.errors(include_input=False)
            ],
        ), 400

    @app.post("/api/component-analysis")
    def analyze():
        body = AnalysisRequest.model_validate(request.get_json(silent=True) or {})
        if not body.query.strip():
            return jsonify(error="Query must not be blank"), 400
        return start(DesignRun(original_request=body.query.strip(), options=body.options))

    @app.post("/api/refine")
    def refine():
        body = RefinementRequest.model_validate(request.get_json(silent=True) or {})
        try:
            base = store.load(body.base_run_id)
        except (FileNotFoundError, ValueError):
            return jsonify(error="Base run not found"), 404
        if base.lifecycle == "running":
            return jsonify(error="The base run is still running"), 409
        modification = body.modification
        if body.answers is not None:
            questions = {q.id: q for q in base.pending_questions}
            if set(body.answers) != set(questions):
                return jsonify(error="Answers must match all pending question IDs on the base run"), 400
            modification = "\n".join(
                f"{questions[key].question}\nAnswer: {value}" for key, value in body.answers.items()
            )
        if not modification or not modification.strip():
            return jsonify(error="Modification must not be blank"), 400
        run = base.model_copy(deep=True)
        fresh = DesignRun(original_request=base.original_request)
        run.id, run.created_at, run.updated_at = fresh.id, fresh.created_at, fresh.updated_at
        run.prompt_version = fresh.prompt_version
        run.parent_run_id, run.modification = base.id, modification
        run.revision += 1
        run.lifecycle, run.stage = "running", "started"
        run.invalidate_review()
        run.terminal_reason = ""
        run.pending_questions, run.usage = [], Usage()
        return start(run)

    @app.get("/api/runs/<run_id>")
    def get_run(run_id):
        try:
            return jsonify(run_snapshot(store.load(run_id)))
        except (FileNotFoundError, ValueError):
            return jsonify(error="Run not found"), 404

    @app.get("/api/runs/<run_id>/export")
    def export_run(run_id):
        try:
            run = store.load(run_id)
        except (FileNotFoundError, ValueError):
            return jsonify(error="Run not found"), 404
        format_ = request.args.get("format", "csv")
        if format_ not in {"csv", "json"}:
            return jsonify(error="Export format must be csv or json"), 400
        content = export_csv(run) if format_ == "csv" else export_json(run)
        return Response(
            content,
            mimetype="text/csv" if format_ == "csv" else "application/json",
            headers={"Content-Disposition": f'attachment; filename="jigsaw-{run.id}-r{run.revision}.{format_}"'},
        )

    @app.get("/health")
    def health():
        return jsonify(status="healthy", busy=admission.locked())

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(
        host="127.0.0.1", port=int(os.getenv("PORT", "3001")), threaded=True, debug=False, use_reloader=False
    )
