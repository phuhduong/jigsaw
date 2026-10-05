"""Opt-in live smoke run against an already running backend; consumes provider quota."""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

DEFAULT_QUERY = "Make me a temperature and humidity sensor with WiFi and Bluetooth powered by USB-C for consumer use."


def concise(value):
    return " ".join(str(value).split())[:500]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Device request; defaults to the public sensor example")
    parser.add_argument("--url", default="http://127.0.0.1:3001", help="Backend base URL")
    parser.add_argument("--base-run-id", help="Saved run to refine; requires --modification")
    parser.add_argument("--modification", help="Requested change; requires --base-run-id")
    parser.add_argument(
        "--record", type=Path, help="Save all SSE JSON events to a new JSONL file; never overwrite an existing file"
    )
    args = parser.parse_args()
    if (args.base_run_id is None) != (args.modification is None):
        parser.error("--base-run-id and --modification must be provided together")
    if args.base_run_id is not None:
        if not args.base_run_id.strip() or not args.modification.strip():
            parser.error("--base-run-id and --modification must not be blank")
        path, payload = "/api/refine", {"base_run_id": args.base_run_id, "modification": args.modification}
    elif not args.query.strip():
        parser.error("--query must not be blank")
    else:
        path, payload = "/api/component-analysis", {"query": args.query}

    run_id, sequence, terminal = None, 0, None
    started = time.monotonic()
    recording = None
    try:
        if args.record is not None:
            args.record.parent.mkdir(parents=True, exist_ok=True)
            recording = args.record.open("x", encoding="utf-8")
            print(f"Recording SSE events: {args.record}", flush=True)
        print("Starting live smoke run (uses model/supplier quota).", flush=True)
        with requests.post(
            f"{args.url.rstrip('/')}{path}",
            json=payload,
            stream=True,
            timeout=(10, 60),
        ) as response:
            if not response.ok:
                print(f"Start failed: HTTP {response.status_code}", file=sys.stderr)
                return 1
            response.encoding = "utf-8"
            for line in response.iter_lines(decode_unicode=True):
                if time.monotonic() - started > 600:
                    print("Stopped after the 10-minute client allowance.", file=sys.stderr)
                    return 1
                # The backend emits one JSON data line per SSE event.
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:].strip())
                if recording is not None:
                    recording.write(line[5:].strip() + "\n")
                    recording.flush()
                if not event.get("run_id") or not isinstance(event.get("sequence"), int):
                    raise ValueError("Invalid run event")
                if run_id and event["run_id"] != run_id:
                    continue
                if event["sequence"] <= sequence:
                    continue
                if run_id is None:
                    run_id = event["run_id"]
                    print(f"Run: {run_id}", flush=True)
                sequence = event["sequence"]
                if event["type"] == "progress":
                    print(
                        f"[{sequence}] {concise(event.get('stage', 'progress'))}: {concise(event.get('message', ''))}",
                        flush=True,
                    )
                if event["type"] in {"complete", "error"}:
                    terminal = event
            # Drain through EOF so normal completion closes the request cleanly.
    except (requests.RequestException, ValueError, KeyError, TypeError):
        print("Stream failed or returned invalid data; inspect the saved run if an ID was printed.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not create or write the recording file; existing files are never overwritten.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Stopped; the backend may finish its current operation before noticing disconnect.", file=sys.stderr)
        return 130
    finally:
        if recording is not None:
            recording.close()

    if terminal is None or not isinstance(terminal.get("snapshot"), dict):
        print("No terminal snapshot received; this is an interrupted run, not success.", file=sys.stderr)
        return 1
    snapshot = terminal["snapshot"]
    print(
        "Outcome: "
        + ", ".join(f"{key}={snapshot.get(key, 'unknown')}" for key in ("lifecycle", "compatibility", "sourcing"))
    )
    print("Reason: " + concise(snapshot.get("terminal_reason", "")))
    usage = snapshot.get("usage", {})
    print(
        "Usage: "
        + ", ".join(
            f"{key}={usage.get(key, 'unknown')}"
            for key in (
                "model_calls",
                "input_tokens",
                "output_tokens",
                "supplier_calls",
                "documents",
                "pdf_pages",
                "correction_rounds",
                "elapsed_seconds",
            )
        )
    )
    unresolved = [
        finding
        for finding in snapshot.get("findings", [])
        if finding.get("revision") == snapshot.get("revision")
        and finding.get("kind") == "check"
        and finding.get("status") in {"fail", "unknown"}
    ]
    failures = [f for f in unresolved if f.get("status") == "fail" and f.get("area") != "evidence"]
    print(f"Blocking functional/electrical failures: {len(failures)}")
    print(f"Nonblocking review details: {len(unresolved) - len(failures)} (retained in the saved report)")
    for finding in failures:
        print(f"- {finding['status']} [{concise(finding.get('id', ''))}]: {concise(finding.get('explanation', ''))}")
    return 0 if terminal["type"] == "complete" and snapshot.get("compatibility") == "checked" else 1


if __name__ == "__main__":
    sys.exit(main())
