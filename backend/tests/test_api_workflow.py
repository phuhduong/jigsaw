"""Small application/state checks using local workflows and supplier/model fakes."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

# Importing the serving module creates its default app; keep that runtime data isolated.
with tempfile.TemporaryDirectory() as import_directory, patch.dict(os.environ, {"DATA_DIR": import_directory}):
    from app import create_app

from llm import Budget, BudgetExceeded
from agents.requirements_parser import parse_requirements
from models import CircuitProposal, ComponentSpec, Correction, DesignProposal, EvidencePacket, Finding, PageSelection, Pick, Picks, Plan, PriceBreak, Quantity, Question, ReadingPlan, Requirement, Review, REVIEW_AREAS, now
from pipeline import Workflow, compact_inventory
from run_store import RunStore
from test_checks_store import evaluate, example, supported_example


def events(response):
    return [json.loads(item[6:]) for item in response.get_data(as_text=True).split("\n\n") if item.startswith("data: ")]


class LocalWorkflow:
    def __init__(self):
        self.inputs = []
        self.fail = False

    def execute(self, run):
        self.inputs.append(run.model_copy(deep=True))
        if self.fail:
            raise RuntimeError("Local workflow failure")
        fixture = example()
        if not run.parent_run_id:
            for field in ("requirements", "assumptions", "components", "documents", "evidence", "rails", "interfaces", "signal_checks"):
                setattr(run, field, getattr(fixture, field))
        run.findings = fixture.findings
        for finding in run.findings:
            finding.revision = run.revision
        run.review_completed, run.lifecycle = True, "finished"
        run.terminal_reason = "Local fixture complete"
        evaluate(run)
        yield {"type": "complete"}


class SourcePages:
    def pages(self, *args, **kwargs):
        return [{"type": "text", "text": "Local source fixture"}]

    def inventory(self, identifier):
        return {"document_id": identifier, "url": "https://example.com/source", "title": "Fixture",
                "page_count": 1, "pages": [], "links": []}


class LocalEvidenceWorkflow(Workflow):
    def _engineer(self, *args):
        yield {"type": "progress"}
        return [PageSelection(document_id="doc", pages=[1], reason="Local evidence")]


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store, self.workflow = RunStore(self.directory.name), LocalWorkflow()
        self.app = create_app(self.store, self.workflow)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_completed_run_and_exports_match_saved_snapshot(self):
        response = self.client.post("/api/component-analysis", json={"query": "Two sensors"}, buffered=True)
        terminal = events(response)[-1]
        run_id = terminal["run_id"]
        self.assertEqual((terminal["type"], terminal["snapshot"]["compatibility"]), ("complete", "checked"))
        saved = self.store.load(run_id)
        self.assertEqual(saved.lifecycle, "finished")
        report = self.client.get(f"/api/runs/{run_id}/export?format=json").get_json()
        self.assertEqual(report["id"], run_id)
        self.assertEqual(report["bom"], terminal["snapshot"]["bom"])
        self.assertIn("SENSOR-1", self.client.get(f"/api/runs/{run_id}/export?format=csv").get_data(as_text=True))
        self.assertEqual(self.client.get(f"/api/runs/{run_id}").get_json()["bom"][0]["installed_quantity"], 2)

    def test_failure_releases_admission_and_cannot_claim_checked(self):
        self.workflow.fail = True
        with self.assertLogs("app", level="ERROR"):
            response = self.client.post("/api/component-analysis", json={"query": "Two sensors"}, buffered=True)
        terminal = events(response)[-1]
        self.assertEqual((terminal["type"], terminal["snapshot"]["compatibility"]), ("error", "incomplete"))
        self.assertEqual(self.store.load(terminal["run_id"]).lifecycle, "error")
        self.workflow.fail = False
        self.assertEqual(events(self.client.post("/api/component-analysis", json={"query": "Retry"}, buffered=True))[-1]["type"], "complete")

    def test_refinement_uses_complete_saved_state_and_valid_questions(self):
        base = example()
        base.prompt_version = "older"
        base.options.board_quantity = 3
        self.store.save(base)
        response = self.client.post("/api/refine", json={"base_run_id": base.id, "modification": "Lower the cost"}, buffered=True)
        incoming = self.workflow.inputs[-1]
        self.assertEqual((incoming.parent_run_id, incoming.revision), (base.id, base.revision + 1))
        self.assertEqual(incoming.prompt_version, example().prompt_version)
        self.assertEqual((len(incoming.components), len(incoming.rails), len(incoming.evidence), incoming.options.board_quantity), (2, 1, 1, 3))
        self.assertFalse(incoming.review_completed)
        self.assertEqual(events(response)[-1]["type"], "complete")
        base.pending_questions = [Question(id="q", requirement_id="req", question="What range?")]
        self.store.save(base)
        self.assertEqual(self.client.post("/api/refine", json={"base_run_id": base.id, "answers": {"wrong": "Indoor"}}).status_code, 400)
        base.lifecycle = "running"
        self.store.save(base)
        self.assertEqual(self.client.post("/api/refine", json={"base_run_id": base.id, "modification": "Change it"}).status_code, 409)

    def test_closing_old_response_does_not_release_new_run(self):
        old = self.client.post("/api/component-analysis", json={"query": "First"}, buffered=False)
        for chunk in old.response:
            message = json.loads(chunk.decode().strip()[6:])
            if message["type"] == "complete":
                break
        old.close()
        self.assertEqual(self.store.load(message["run_id"]).lifecycle, "finished")
        current = self.client.post("/api/component-analysis", json={"query": "Second"}, buffered=False)
        old.close()
        self.assertEqual(self.client.post("/api/component-analysis", json={"query": "Third"}).status_code, 409)
        current.close()
        self.assertFalse(self.client.get("/health").get_json()["busy"])


class WorkflowTests(unittest.TestCase):
    def test_correction_repairs_requirement_mapping_without_rewriting_requirement(self):
        run = example()
        requirement = run.requirements[0]
        requirement.component_ids = []
        before = requirement.model_dump(exclude={"component_ids"})
        workflow = Workflow(object(), object(), object())
        self.assertTrue(workflow._correct(run, Correction(reason="Restore affected components",
            requirement_components={"req": ["U1", "U2"]})))
        self.assertEqual(requirement.component_ids, ["U1", "U2"])
        self.assertEqual(requirement.model_dump(exclude={"component_ids"}), before)
        self.assertEqual((run.revision, run.review_completed), (2, False))
        for mapping in ({"missing_requirement": ["U1"]}, {"req": ["missing_component"]}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                workflow._correct(run, Correction(reason="Invalid reference", requirement_components=mapping))
        self.assertEqual(requirement.component_ids, ["U1", "U2"])
        with self.assertRaises(ValueError):
            workflow._correct(run, Correction(reason="Invalid source owner", reread_component_ids=["missing"]))
        self.assertTrue(workflow._correct(run, Correction(reason="Read missing fact", reread_component_ids=["U1"])))

    def test_signal_gap_can_reread_one_existing_source_before_assembly(self):
        run = example()
        run.lifecycle, run.requirements[0].id, run.limits.correction_rounds = "running", "req:one", 1
        run.documents, run.evidence = [], []
        for component, identifier, ref in zip(run.components, ("doc", "other"), ("D1E1", "other-spec")):
            component.document_ids = [identifier]
            component.product.datasheet_url = f"https://example.com/{identifier}"
            run.documents.append({"document_id": identifier, "url": component.product.datasheet_url,
                "page_count": 1, "media_type": "text/html", "pages_read": [1], "pages_interpreted": [1]})
            run.evidence.append(example().evidence[0].model_copy(update={"id": ref,
                "document_id": identifier, "component_ids": [component.id]}))
            load = next(load for load in run.rails[0].loads if load.component_id == component.id)
            for quantity in (load.voltage_min, load.voltage_max, load.current):
                quantity.evidence_ids = [ref]
            for signal in run.signal_checks:
                if signal.source_component_id == component.id:
                    signal.output_low_max.evidence_ids = [ref]
                if signal.receiver_component_id == component.id:
                    signal.input_high_min.evidence_ids = signal.input_low_max.evidence_ids = [ref]
        run.interfaces[0].evidence_ids = [e.id for e in run.evidence]
        run.signal_checks[0].output_low_max = None
        untouched = run.evidence[1].model_dump()
        stages, reading_scopes, review_sources = [], [], []

        class Documents(SourcePages):
            def pages(self, identifier, pages, **kwargs):
                return [{"type": "text", "text": identifier}]

            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                stages.append(stage)
                yield {"type": "progress"}
                if stage == "plan":
                    return Plan(summary="Local fixture", requirements=run.requirements, assumptions=run.assumptions,
                        components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components],
                        configuration_notes=[])
                if stage == "review":
                    review_sources.append({block["text"] for block in args[0]})
                    return Review(findings=[Finding(id=area, area=area, status="pass",
                        subject_ids=["req:one"] if area == "requirements" else ["U1", "U2"],
                        evidence_ids=[e.id for e in run.evidence], explanation="Local fixture review") for area in REVIEW_AREAS])
                if stage == "correct":
                    return Correction(reason="Missing MCU VOL", reread_component_ids=["U1"],
                        configuration_instructions="Reread doc page 1 for the missing MCU VOL, despite its prior interpretation.")
                if stage == "choose evidence pages":
                    reading_scopes.append([d["document_id"] for d in payload["documents"]])
                    return ReadingPlan(selections=[PageSelection(document_id="doc", pages=[1], reason="Missing MCU VOL")])
                if stage == "interpret U1":
                    fact = payload["previous_observations"][0].model_copy(update={"id": "output", "fact": "VOL maximum 0.4 V"})
                    return EvidencePacket(applicability={"U1": "Exact local fixture"},
                        evidence=[*payload["previous_observations"], fact])
                if stage == "complete BOM and compatibility":
                    signals = [run.signal_checks[0].model_copy(update={"output_low_max":
                        Quantity(value=.4, unit="V", basis="max", evidence_ids=["D1E2"])})] + run.signal_checks[1:]
                    return CircuitProposal(additional_components=[], support_needs=[], rails=run.rails,
                        interfaces=run.interfaces, signal_checks=signals, assumptions=run.assumptions, configuration_notes=[])
                raise AssertionError(stage)

        class SeededWorkflow(Workflow):
            def _engineer(self, run, budget, instructions="", source_component_ids=None):
                if source_component_ids is not None:
                    return (yield from super()._engineer(run, budget, instructions, source_component_ids))
                yield {"type": "progress"}
                return [PageSelection(document_id=key, pages=[1], reason="Previously interpreted source") for key in ("doc", "other")]

        list(SeededWorkflow(Documents(), object(), Gateway()).execute(run))
        self.assertEqual((run.compatibility, run.usage.correction_rounds), ("checked", 1))
        self.assertEqual(reading_scopes, [["doc"]])
        self.assertEqual([stage for stage in stages if stage.startswith("interpret")], ["interpret U1"])
        self.assertLess(stages.index("interpret U1"), stages.index("complete BOM and compatibility"))
        self.assertLess(stages.index("review"), stages.index("correct"))
        self.assertEqual(stages[-1], "review")
        self.assertEqual(next(e.model_dump() for e in run.evidence if e.id == "other-spec"), untouched)
        self.assertEqual(review_sources, [{"doc", "other"}, {"doc", "other"}])

    def test_numeric_gap_is_reviewed_but_cannot_be_overridden_by_model_pass(self):
        run = example()
        run.lifecycle, run.review_completed, run.findings = "running", False, []
        run.requirements[0].id = "req:one"
        run.documents[0]["media_type"] = "text/html"
        run.signal_checks[0].output_low_max = None
        run.limits.correction_rounds = 0
        stages = []

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                stages.append(stage)
                yield {"type": "progress"}
                if stage == "plan":
                    return Plan(summary="Local fixture", requirements=run.requirements, assumptions=run.assumptions,
                        components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components],
                        configuration_notes=[])
                if stage == "review":
                    return Review(findings=[Finding(id=area, area=area, status="pass",
                        subject_ids=["req:one"] if area == "requirements" else ["U1", "U2"],
                        evidence_ids=["spec"], explanation="Local fixture review") for area in REVIEW_AREAS])
                raise AssertionError(stage)

        list(LocalEvidenceWorkflow(SourcePages(), object(), Gateway()).execute(run))
        self.assertEqual(stages, ["plan", "review"])
        self.assertEqual((run.lifecycle, run.compatibility, run.review_completed), ("finished", "incomplete", True))
        self.assertIn("Correction allowance reached", run.terminal_reason)

    def test_mapping_only_correction_reviews_without_rebuilding_design(self):
        run = example()
        run.lifecycle, run.requirements[0].id = "running", "req:one"
        run.requirements[0].component_ids = []
        run.documents[0].update(media_type="text/html", pages_interpreted=[1])
        design_fields = {"components", "rails", "interfaces", "signal_checks", "evidence"}
        before = run.model_dump(include=design_fields)
        stages = []

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                stages.append(stage)
                yield {"type": "progress"}
                if stage == "plan":
                    return Plan(summary="Local fixture", requirements=run.requirements, assumptions=run.assumptions,
                        components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components],
                        configuration_notes=[])
                if stage == "review":
                    return Review(findings=[Finding(id=area, area=area, status="pass",
                        subject_ids=["req:one"] if area == "requirements" else ["U1", "U2"],
                        evidence_ids=["spec"], explanation="Local fixture review") for area in REVIEW_AREAS])
                if stage == "correct":
                    return Correction(reason="Restore requirement mapping", requirement_components={"req:one": ["U1", "U2"]})
                raise AssertionError("Mapping repair must not rebuild the design: " + stage)

        list(LocalEvidenceWorkflow(SourcePages(), object(), Gateway()).execute(run))
        self.assertEqual(stages, ["plan", "review", "correct", "review"])
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.model_dump(include=design_fields), before)

    def test_direct_configuration_preserves_sources_and_skips_assembly(self):
        run = supported_example()
        run.lifecycle, run.requirements[0].id, run.limits.correction_rounds = "running", "req:one", 1
        run.requirements[0].component_ids = []
        run.documents[0].update(media_type="text/html", pages_interpreted=[1])
        run.rails[0].loads[0].current = None
        run.evidence_errors = [Finding(id="unused", method="code", kind="guidance", area="evidence",
            status="unknown", subject_ids=["U1"], document_id="doc", explanation="Unused optional observation")]
        preserved = {"components", "evidence", "source_support_needs", "support_needs", "evidence_errors"}
        before, stages = run.model_dump(include=preserved), []

        class Documents(SourcePages):
            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                stages.append(stage)
                yield {"type": "progress"}
                if stage == "plan":
                    return Plan(summary="Local fixture", requirements=run.requirements, assumptions=run.assumptions,
                        components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components],
                        configuration_notes=[])
                if stage == "review":
                    return Review(findings=[Finding(id=area, area=area, status="pass",
                        subject_ids=["req:one"] if area == "requirements" else ["U1", "U2", "C1"],
                        evidence_ids=["spec"], explanation="Local fixture review") for area in REVIEW_AREAS])
                if stage == "correct":
                    configuration = CircuitProposal(**run.model_dump(include=set(CircuitProposal.model_fields)), additional_components=[])
                    configuration.rails[0].loads[0].current = Quantity(value=10, unit="mA", basis="estimate", assumption_id="supply")
                    return Correction(reason="Repair current and mapping", configuration=configuration,
                        requirement_components={"req:one": ["U1", "U2"]})
                raise AssertionError("Direct configuration must not call assembly: " + stage)

        list(LocalEvidenceWorkflow(Documents(), object(), Gateway()).execute(run))
        self.assertEqual(stages, ["plan", "review", "correct", "review"])
        self.assertEqual((run.compatibility, run.review_completed, run.revision), ("checked", True, 2))
        self.assertEqual(run.model_dump(include=preserved), before)
        self.assertEqual(run.requirements[0].component_ids, ["U1", "U2"])

    def test_direct_configuration_rejects_conflicting_modes(self):
        run = example()
        configuration = CircuitProposal(**run.model_dump(include=set(CircuitProposal.model_fields)), additional_components=[])
        part = ComponentSpec(**run.components[0].model_dump(include=set(ComponentSpec.model_fields)))
        for change in ({"add_components": [part]}, {"replace_components": [part]},
                       {"remove_component_ids": ["U1"]}, {"reread_component_ids": ["U1"]},
                       {"configuration": configuration.model_copy(update={"additional_components": [part]})}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                Correction(**{"reason": "Conflicting modes", "configuration": configuration, **change})
        run.components[0].product = None
        with self.assertRaises(ValueError):
            Workflow(object(), object(), object())._correct(run, Correction(reason="Unselected part", configuration=configuration))
        self.assertEqual(run.revision, 1)

    def test_numeric_repair_does_not_reread_an_unchanged_catalog_reviewed_connector(self):
        run = example()
        run.lifecycle, run.requirements[0].id = "running", "req:one"
        run.documents[0].update(media_type="text/html", pages_interpreted=[1])
        run.components.append(run.components[0].model_copy(update={"id": "J1", "kind": "connector", "document_ids": [],
            "product": run.components[0].product.model_copy(update={"parameters": [{"name": "Current Rating", "value": "1 A"}]})}))
        run.rails[0].loads[0].current = None
        stages, engineering_calls = [], []

        class Documents(SourcePages):
            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                stages.append(stage)
                yield {"type": "progress"}
                if stage == "plan":
                    return Plan(summary="Local fixture", requirements=run.requirements, assumptions=run.assumptions,
                        components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components],
                        configuration_notes=[])
                if stage == "review":
                    return Review(findings=[Finding(id=area, area=area, status="pass",
                        subject_ids=["req:one"] if area == "requirements" else [c.id for c in run.components],
                        evidence_ids=["spec"], explanation="Local fixture; catalog current rating supports J1") for area in REVIEW_AREAS])
                if stage == "correct":
                    return Correction(reason="Restore current estimate", configuration_instructions="Use the existing 10mA load estimate.")
                if stage == "complete BOM and compatibility":
                    rails = [rail.model_copy(deep=True) for rail in run.rails]
                    rails[0].loads[0].current = Quantity(value=10, unit="mA", basis="estimate", assumption_id="supply")
                    return CircuitProposal(additional_components=[], support_needs=[], rails=rails,
                        interfaces=run.interfaces, signal_checks=run.signal_checks, assumptions=run.assumptions, configuration_notes=[])
                raise AssertionError(stage)

        class SeededWorkflow(LocalEvidenceWorkflow):
            def _engineer(self, *args, **kwargs):
                engineering_calls.append(True)
                return (yield from super()._engineer(*args, **kwargs))

        list(SeededWorkflow(Documents(), object(), Gateway()).execute(run))
        self.assertEqual(stages, ["plan", "review", "correct", "complete BOM and compatibility", "review"])
        self.assertEqual(len(engineering_calls), 1)
        self.assertEqual(run.compatibility, "checked")

    def test_refinement_instructions_reach_source_page_selection(self):
        run = example()
        run.modification = "Read the controller current table before updating the load estimate."
        payloads = []

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, **kwargs):
                payloads.append(payload)
                yield {"type": "progress"}
                return ReadingPlan(selections=[])

        list(Workflow(SourcePages(), object(), Gateway())._read_plan(run, Budget(run)))
        self.assertEqual(payloads[0]["latest_modification"], run.modification)

    def test_explicit_passive_source_request_is_not_silently_skipped(self):
        run = supported_example()
        run.components, run.documents = [run.components[-1]], []
        component = run.components[0]
        component.product.datasheet_url = "https://example.com/capacitor.pdf"
        class Documents:
            def fetch(self, url, **kwargs):
                return {"document_id": "capacitor", "url": url, "page_count": 1, "media_type": "application/pdf"}
        workflow = Workflow(Documents(), object(), object())
        list(workflow._fetch_documents(run, Budget(run)))
        self.assertEqual(component.document_ids, [])
        list(workflow._fetch_documents(run, Budget(run), {component.id}))
        self.assertEqual(component.document_ids, ["capacitor"])
        self.assertEqual(run.documents[0]["url"], component.product.datasheet_url)

    def test_discarded_unused_observation_does_not_block_but_cannot_support_a_claim(self):
        class Documents:
            def quote_matches(self, document_id, page, quote):
                return quote != "Unsupported optional observation"

        run = example()
        run.documents[0]["pages_read"] = [1]
        unused = run.evidence[0].model_copy(update={"id": "unused", "quote": "Unsupported optional observation"})
        workflow = Workflow(Documents(), object(), object())
        run.evidence, run.evidence_errors = workflow._verify_evidence(run, [*run.evidence, unused], {"U1", "U2"})
        evaluate(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.evidence_errors[0].kind, "guidance")
        run.rails[0].loads[0].voltage_max.evidence_ids = ["unused"]
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")
        self.assertTrue(any(f.area == "power" and f.status == "unknown" for f in run.findings))

    def test_requirement_namespace_does_not_change_physical_placements(self):
        plan = Plan(summary="Resistor fixture", assumptions=[], configuration_notes=[],
            requirements=[Requirement(id=key, clause="Fixture", description="Fixture", component_ids=["R1"])
                          for key in ("R1", "req:retained")],
            components=[ComponentSpec(id="R1", name="Resistor", kind="passive", purpose="Bias", search_query="10k",
                                      requirement_ids=["R1", "req:retained"])],
            pending_questions=[Question(id="question", requirement_id="R1", question="What value?")])

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return plan

        run, parsed = example(), []
        def parse():
            parsed.append((yield from parse_requirements(Gateway(), Budget(run), run)))
        list(parse())
        result = parsed[0]
        self.assertEqual([r.id for r in result.requirements], ["req:R1", "req:retained"])
        self.assertEqual(result.components[0].requirement_ids, ["req:R1", "req:retained"])
        self.assertEqual(result.pending_questions[0].requirement_id, "req:R1")
        self.assertEqual((result.components[0].id, result.requirements[0].component_ids), ("R1", ["R1"]))

    def test_new_support_source_does_not_reread_unchanged_documents(self):
        run = example()
        run.documents[0]["media_type"] = "text/html"
        scopes, source_reads, assemblies, selections = [], [], [], []

        class Documents(SourcePages):
            def pages(self, document_id, pages, **kwargs):
                source_reads.append(document_id)
                return super().pages(document_id, pages)

            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                yield {"type": "progress"}
                if stage == "choose evidence pages":
                    scopes.append([d["document_id"] for d in payload["documents"]])
                    return ReadingPlan(selections=[PageSelection(document_id=key, pages=[1], reason="Required support") for key in scopes[-1]])
                owners = [c["id"] for c in payload["components"]]
                document_id = "switch" if "SW1" in owners else "doc"
                fact = example().evidence[0].model_copy(update={"component_ids": owners, "document_id": document_id})
                return EvidencePacket(applicability={key: "Exact fixture part" for key in owners}, evidence=[fact])

        class AddingSupport(Workflow):
            def _fetch_documents(self, run, budget, requested_component_ids=()):
                yield {"type": "progress"}
                if len(run.components) == 3:
                    run.components[-1].document_ids = ["switch"]
                    run.documents.append({"document_id": "switch", "page_count": 1, "media_type": "text/html"})

            def _assemble(self, run, budget, instructions=""):
                assemblies.append((len(run.components), {e.document_id for e in run.evidence}))
                if len(run.components) == 2:
                    run.components.append(run.components[0].model_copy(update={"id": "SW1", "kind": "connector", "document_ids": []}))
                yield {"type": "progress"}

        workflow = AddingSupport(Documents(), object(), Gateway())
        def engineer():
            selections.extend((yield from workflow._engineer(run, Budget(run))))
        list(engineer())
        self.assertEqual(scopes, [["doc"], ["switch"]])
        self.assertEqual(source_reads, ["doc", "switch"])
        self.assertEqual(assemblies, [(2, {"doc"}), (3, {"doc", "switch"})])
        self.assertEqual({s.document_id for s in selections}, {"doc", "switch"})
        self.assertFalse(run.review_completed)

    def test_bounded_navigation_preserves_late_toc_chapters(self):
        inventory = SourcePages().inventory("doc")
        inventory.update(page_count=20, pages=[{"page_number": page, "text_status": "available",
                         "text": "Register description " + "bit field details " * 24} for page in range(1, 21)])
        inventory["pages"][7]["text"] = "Table of Contents\n1 Overview " + "." * 900 + " 1\n19 Electrical characteristics ... 19"
        navigation = compact_inventory(inventory, max_chars=2000)
        toc = next(page for page in navigation["pages"] if page["page"] == 8)
        self.assertIn("19 Electrical characteristics", toc["sections"])
        self.assertGreater(navigation["omitted_page_cards"], 0)
        self.assertIn("original physical page", navigation["navigation_note"])
        self.assertLess(len(json.dumps(navigation, ensure_ascii=False)), 2100)

    def test_module_reading_includes_external_support_heading_within_page_cap(self):
        run = example()
        run.documents[0]["page_count"] = 40

        class Documents(SourcePages):
            def inventory(self, identifier):
                return {**super().inventory(identifier), "page_count": 40, "pages": [
                    {"page_number": page, "text_status": "available", "text": text}
                    for page, text in ((2, "Contents\n9 Peripheral Schematics ... 39"),
                                      (37, "8 Module Schematics\nInternal module circuit"),
                                      (39, "9\nPeripheralSchematics\nExternal support circuit"))]}

        class Gateway:
            pages = [37]
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return ReadingPlan(selections=[PageSelection(document_id="doc", pages=self.pages, reason="Model choice")])

        gateway = Gateway()
        workflow = Workflow(Documents(), object(), gateway)
        selected = []
        def read():
            selected.extend((yield from workflow._read_plan(run, Budget(run))))
        list(read())
        self.assertEqual(selected[0].pages, [37, 39])
        self.assertIn("external support", selected[0].reason)
        gateway.pages = list(range(1, 25))
        with self.assertRaises(BudgetExceeded):
            list(read())

    def test_source_support_remapping_survives_omitted_circuit_fulfillment(self):
        run = supported_example()
        run.documents[0]["media_type"] = "text/html"
        packet = EvidencePacket(applicability={key: "Exact fixture sensor family" for key in ("U1", "U2")},
            evidence=[run.evidence[0].model_copy(update={"id": "raw_fact"})],
            source_support_needs=[run.source_support_needs[0].model_copy(update={"id": "raw_need", "evidence_ids": ["raw_fact"]})])

        class Documents(SourcePages):
            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return packet

        workflow = Workflow(Documents(), object(), Gateway())
        list(workflow._interpret(run, Budget(run), [PageSelection(document_id="doc", pages=[1], reason="Support circuit")], ""))
        source = run.source_support_needs[0]
        self.assertEqual((source.id, source.document_id, source.evidence_ids), ("D1S1", "doc", ["D1E1"]))
        self.assertEqual(run.evidence[0].id, "D1E1")
        proposal = DesignProposal(evidence=run.evidence, additional_components=[], support_needs=[], rails=run.rails,
                                  interfaces=run.interfaces, assumptions=run.assumptions, configuration_notes=[])
        workflow._apply_design(run, proposal)
        self.assertEqual([(n.id, n.status) for n in run.support_needs], [("D1S1", "unresolved")])
        evaluate(run)
        self.assertTrue(any(f.id == "code:source_support:D1S1" and f.status == "unknown" for f in run.findings))
        replacement = ComponentSpec(**run.components[0].model_dump(include=set(ComponentSpec.model_fields)))
        replacement.search_query = "SENSOR-2 from the same family document"
        workflow._correct(run, Correction(reason="Another variant", replace_components=[replacement]))
        self.assertEqual(run.source_support_needs, [])
        self.assertEqual(run.evidence[0].component_ids, ["U2"])

    def test_reading_plan_merges_shared_sources_and_completes_short_documents(self):
        run = example()
        run.documents[0]["page_count"] = 3

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return ReadingPlan(selections=[PageSelection(document_id="doc", pages=pages, reason="Needed facts")
                                               for pages in ([1], [1, 2])])

        selections = []
        def read():
            selections.extend((yield from Workflow(SourcePages(), object(), Gateway())._read_plan(run, Budget(run))))
        list(read())
        self.assertEqual([(s.document_id, s.pages) for s in selections], [("doc", [1, 2, 3])])

    def test_reinterpreting_one_source_preserves_other_owners_and_gaps(self):
        run = example()
        run.components[0].document_ids = ["replacement"]
        run.documents[0]["media_type"] = "text/html"
        run.documents.append({"document_id": "replacement", "page_count": 1, "media_type": "text/html"})
        run.evidence.append(run.evidence[0].model_copy(update={"id": "obsolete", "component_ids": ["U1"]}))
        run.evidence_errors = [Finding(id=f"gap:{doc}", document_id=doc, area="evidence", method="code", status="unknown",
                                      subject_ids=owners, explanation="Unresolved source fact")
                               for doc, owners in (("doc", ["U1", "U2"]), ("replacement", ["U1"]))]

        class Documents(SourcePages):
            def quote_matches(self, *args):
                return True

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                yield {"type": "progress"}
                owner = payload["components"][0]["id"]
                document_id = "replacement" if owner == "U1" else "doc"
                previous = payload["previous_observations"]
                observation = (previous[0] if previous else example().evidence[0]).model_copy(
                    update={"component_ids": [owner], "document_id": document_id})
                applicability = {} if getattr(self, "reject", False) else {owner: "Exact fixture sensor variant"}
                return EvidencePacket(applicability=applicability, evidence=[observation])

        workflow = Workflow(Documents(), object(), Gateway())
        list(workflow._interpret(run, Budget(run), [PageSelection(document_id="replacement", pages=[1], reason="New part")], ""))
        self.assertEqual({e.id: e.component_ids for e in run.evidence}, {"spec": ["U2"], "D2E1": ["U1"]})
        self.assertEqual([(e.document_id, e.subject_ids) for e in run.evidence_errors], [("doc", ["U2"])])
        list(workflow._interpret(run, Budget(run), [PageSelection(document_id="doc", pages=[1], reason="Resolve remaining gap")], ""))
        self.assertEqual(run.evidence_errors, [])
        self.assertEqual({e.id for e in run.evidence}, {"D1E1", "D2E1"})
        workflow.gateway.reject = True
        list(workflow._interpret(run, Budget(run), [PageSelection(document_id="doc", pages=[1], reason="Check variant applicability")], ""))
        self.assertEqual({e.id for e in run.evidence}, {"D2E1"})
        self.assertTrue(any(e.status == "unknown" and e.document_id == "doc" for e in run.evidence_errors))

    def test_refreshed_prices_reach_planner_and_cost_review(self):
        run = example()
        run.parent_run_id, run.lifecycle = "a" * 32, "running"
        for component in run.components:
            component.product.retrieved_at = "2000-01-01T00:00:00+00:00"
        run.original_request = "Two sensors for at most 5 USD"
        run.requirements.append(Requirement(id="budget", clause="at most 5 USD", description="Cost limit", component_ids=["U1", "U2"]))
        run.documents[0]["media_type"] = "text/html"
        plan = Plan(summary=run.original_request, requirements=run.requirements, assumptions=run.assumptions,
                    components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components], configuration_notes=[])
        seen_cost = {}

        class Supplier:
            def get_product(self, *args, **kwargs):
                product = example().components[0].product
                product.retrieved_at = now()
                product.offers[0].price_breaks = [PriceBreak(quantity=1, unit_price=10)]
                return product.model_dump()

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                yield {"type": "progress"}
                if stage in {"plan", "review"}:
                    design = payload["previous_design"] if stage == "plan" else payload["design"]
                    seen_cost[stage] = sum(row["extended_price"] for row in design["purchasing_bom"])
                if stage == "plan":
                    return plan
                if stage == "review":
                    finding = Finding(id="cost", area="requirements", status="pass" if seen_cost[stage] <= 5 else "fail",
                                      subject_ids=["req:budget"], explanation="Cost versus requested limit")
                    findings = example().findings
                    findings[0].subject_ids = ["req:req"]
                    return Review(findings=findings + [finding])
                return Correction(reason="Cannot meet the stated budget with these offers")

        list(LocalEvidenceWorkflow(SourcePages(), Supplier(), Gateway()).execute(run))
        self.assertEqual(seen_cost, {"plan": 20, "review": 20}, run.terminal_reason)
        self.assertEqual((run.lifecycle, run.compatibility), ("finished", "issues_found"))

    def test_review_catches_requirement_lost_by_refinement_planner(self):
        run = example()
        run.parent_run_id, run.modification, run.lifecycle = "a" * 32, "Lower the cost", "running"
        run.requirements.append(Requirement(id="display", clause="Add a display", description="Earlier refinement requested a display", component_ids=["U1"]))
        for component in run.components:
            component.product.retrieved_at = now()
        run.documents[0]["media_type"] = "text/html"
        plan = Plan(summary="Cheaper sensors", requirements=example().requirements, assumptions=run.assumptions,
                    components=[ComponentSpec(**c.model_dump(include=set(ComponentSpec.model_fields))) for c in run.components], configuration_notes=[])

        class Gateway:
            def call(self, budget, stage, schema, instructions, payload, *args, **kwargs):
                yield {"type": "progress"}
                if stage == "plan":
                    return plan
                if stage == "review":
                    findings = example().findings
                    findings[0].subject_ids = ["req:req"]
                    prior = {r["id"] for r in payload["prior_requirements"]}
                    current = {r["id"] for r in payload["design"]["requirements"]}
                    if "display" in prior - current:
                        findings.append(Finding(id="omitted", revision=run.revision, area="requirements", status="fail",
                                                subject_ids=["U1"], explanation="Earlier display requirement was dropped"))
                    return Review(findings=findings)
                return Correction(reason="Cannot silently remove a requirement")

        list(LocalEvidenceWorkflow(SourcePages(), supplier=object(), gateway=Gateway()).execute(run))
        self.assertEqual((run.lifecycle, run.compatibility), ("finished", "issues_found"))
        self.assertTrue(any(f.id == "omitted" for f in run.findings))

    def test_rejected_candidate_is_not_selected_and_other_parts_survive(self):
        class Supplier:
            def search(self, *args, **kwargs):
                return [{"manufacturer": "Wrong", "mpn": "WRONG-1"}]

            def get_product(self, *args, **kwargs):
                raise AssertionError("A rejected candidate must not be looked up")

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return Picks(picks=[Pick(component_id="U1", chosen_index=-1, reason="Wrong function")])

        run = example()
        run.components[0].product = None
        workflow = Workflow(object(), Supplier(), Gateway())
        list(workflow._select(run, Budget(run)))
        self.assertIsNone(run.components[0].product)
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")
        self.assertEqual(run.components[0].selection_error, "Wrong function")

    def test_selected_catalog_identity_replaces_plan_name_and_source_hints(self):
        run = example()
        chosen = run.components[0].product.model_copy(update={"mpn": "ALTERNATE-1", "datasheet_url": "https://example.com/alternate.pdf"})
        run.components[0].product = None
        run.components[0].name = "Original proposed part"
        run.components[0].document_urls = ["https://example.com/original.pdf"]
        run.components[0].document_ids = []

        class Supplier:
            def search(self, *args, **kwargs):
                return [chosen.model_dump()]

            def get_product(self, *args, **kwargs):
                return chosen.model_dump()

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return Picks(picks=[Pick(component_id="U1", chosen_index=0, reason="Suitable actual catalog candidate")])

        list(Workflow(object(), Supplier(), Gateway())._select(run, Budget(run)))
        self.assertEqual((run.components[0].name, run.components[0].product.mpn), ("ALTERNATE-1", "ALTERNATE-1"))
        self.assertEqual(run.components[0].document_urls, [])
        self.assertEqual(run.components[0].product.datasheet_url, "https://example.com/alternate.pdf")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_undocumented_active_candidate_uses_broad_query_alternative(self):
        run = example()
        undocumented = run.components[0].product.model_copy(update={"mpn": "NO-DOC", "offers": []})
        documented = undocumented.model_copy(update={"mpn": "WITH-DOC", "datasheet_url": "https://example.com/source.pdf"})
        run.components[0].product = None
        run.components[0].broad_query = "Documented sensor alternative"

        class Supplier:
            def search(self, query, **kwargs):
                return [(documented if query == "Documented sensor alternative" else undocumented).model_dump()]

            def get_product(self, identifier, **kwargs):
                return {"NO-DOC": undocumented, "WITH-DOC": documented}[identifier].model_dump()

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return Picks(picks=[Pick(component_id="U1", chosen_index=0, reason="Candidate fit")])

        list(Workflow(object(), Supplier(), Gateway())._select(run, Budget(run)))
        self.assertEqual(run.components[0].product.mpn, "WITH-DOC")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_invalid_source_and_targeted_correction_preserve_whole_design(self):
        class Documents:
            def quote_matches(self, *args):
                return False

        workflow = Workflow(Documents(), supplier=object(), gateway=object())
        run = example()
        run.documents[0]["pages_read"] = [1]
        proposal = DesignProposal(evidence=run.evidence, additional_components=[], support_needs=[], rails=run.rails,
                                  interfaces=run.interfaces, assumptions=run.assumptions, configuration_notes=[])
        workflow._apply_design(run, proposal)
        self.assertEqual(run.evidence, [])
        replacement = ComponentSpec(**run.components[0].model_dump(include=set(ComponentSpec.model_fields)))
        replacement.search_query = "REPLACEMENT-1"
        self.assertTrue(workflow._correct(run, Correction(reason="Replace selected sensor", replace_components=[replacement])))
        self.assertIsNone(run.components[0].product)
        self.assertEqual((run.components[1].product.mpn, len(run.rails), run.requirements[0].component_ids), ("SENSOR-1", 1, ["U1", "U2"]))
        self.assertEqual((run.compatibility, run.review_completed, run.revision), ("incomplete", False, 2))


if __name__ == "__main__":
    unittest.main()
