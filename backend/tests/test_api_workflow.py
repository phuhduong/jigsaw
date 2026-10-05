"""Small application/state checks using local workflows and supplier/model fakes."""

import json
import tempfile
import unittest
from types import SimpleNamespace

from app import create_app
from checks import refresh_checks
from documents import DocumentError
from fakes import (
    Gateway,
    SeededWorkflow,
    SourcePages,
    component_spec,
    configuration_for,
    drain,
    example,
    gateway_for,
    plan_for,
    replacement_packet,
    replacement_source_example,
    review_for,
    split_source_example,
    legacy_support_example,
    workflow_example,
)
from llm import Budget
from models import (
    ComponentSpec,
    Correction,
    DocumentRequest,
    EvidencePacket,
    Finding,
    OperatingConfiguration,
    PageSelection,
    Pick,
    Picks,
    Plan,
    PriceBreak,
    Quantity,
    Question,
    ReadingPlan,
    Requirement,
    Review,
    SourceNumber,
    now,
)
from pipeline import Workflow, compact_inventory
from prompts import USB_C_GUIDE_URL
from run_store import RunStore, design_context
from stages import plan_requirements


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
            for field in (
                "requirements",
                "assumptions",
                "components",
                "documents",
                "evidence",
                "rails",
                "interfaces",
                "signal_checks",
            ):
                setattr(run, field, getattr(fixture, field))
        run.findings = fixture.findings
        for finding in run.findings:
            finding.revision = run.revision
        run.review_completed, run.lifecycle = True, "finished"
        run.terminal_reason = "Local fixture complete"
        refresh_checks(run)
        yield {"type": "complete"}


class AddingFunctionalComponentWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configurations = []

    def _fetch_documents(self, run, budget, requested_component_ids=()):
        yield {"type": "progress"}
        if len(run.components) == 3:
            run.components[-1].document_ids = ["switch"]
            run.documents.append({"document_id": "switch", "page_count": 1, "media_type": "text/html"})

    def _configure_bom(self, run, budget, instructions=""):
        self.configurations.append((len(run.components), {e.document_id for e in run.evidence}))
        if len(run.components) == 2:
            run.components.append(
                run.components[0].model_copy(update={"id": "SW1", "kind": "connector", "document_ids": []})
            )
        yield {"type": "progress"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store, self.workflow = RunStore(self.directory.name), LocalWorkflow()
        self.app = create_app(self.store, self.workflow)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_refinement_rejects_an_unsupported_saved_base(self):
        base = example()
        base.schema_version = 99
        self.store.save(base)
        response = self.client.post("/api/refine", json={"base_run_id": base.id, "modification": "Lower the cost"})
        self.assertEqual(response.status_code, 404)

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
        self.assertEqual((terminal["type"], terminal["snapshot"]["compatibility"]), ("error", None))
        self.assertEqual(self.store.load(terminal["run_id"]).lifecycle, "error")
        self.assertEqual(self.client.get(f"/api/runs/{terminal['run_id']}").get_json(), terminal["snapshot"])
        self.workflow.fail = False
        self.assertEqual(
            events(self.client.post("/api/component-analysis", json={"query": "Retry"}, buffered=True))[-1]["type"],
            "complete",
        )

    def test_refinement_uses_complete_saved_state_and_valid_questions(self):
        base = example()
        base.prompt_version = "older"
        base.options.board_quantity = 3
        self.store.save(base)
        response = self.client.post(
            "/api/refine", json={"base_run_id": base.id, "modification": "Lower the cost"}, buffered=True
        )
        incoming = self.workflow.inputs[-1]
        self.assertEqual((incoming.parent_run_id, incoming.revision), (base.id, base.revision + 1))
        self.assertEqual(incoming.prompt_version, example().prompt_version)
        self.assertEqual(
            (len(incoming.components), len(incoming.rails), len(incoming.evidence), incoming.options.board_quantity),
            (2, 1, 1, 3),
        )
        self.assertFalse(incoming.review_completed)
        self.assertEqual(events(response)[-1]["type"], "complete")
        base.pending_questions = [Question(id="q", requirement_id="req", question="What range?")]
        self.store.save(base)
        self.assertEqual(
            self.client.post("/api/refine", json={"base_run_id": base.id, "answers": {"wrong": "Indoor"}}).status_code,
            400,
        )
        base.lifecycle = "running"
        self.store.save(base)
        self.assertEqual(
            self.client.post("/api/refine", json={"base_run_id": base.id, "modification": "Change it"}).status_code, 409
        )

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
    def test_legacy_support_is_readable_but_not_used_by_new_execution_or_model_schemas(self):
        legacy = legacy_support_example()
        legacy.documents[0].update(media_type="text/html", pages_interpreted=[1])
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(directory)
            store.save(legacy)
            original = store.load(legacy.id).model_dump()
            run = store.load(legacy.id)
            for field in ("source_support_needs", "support_needs"):
                self.assertTrue(original[field])
                self.assertNotIn(field, design_context(run))
                for schema in (EvidencePacket, OperatingConfiguration):
                    self.assertNotIn(field, schema.model_json_schema()["properties"])
            run.lifecycle = "running"
            list(SeededWorkflow(SourcePages(), object(), gateway_for(run)).execute(run))
            self.assertEqual((run.lifecycle, run.compatibility), ("finished", "checked"))
            self.assertEqual((run.source_support_needs, run.support_needs), ([], []))
            self.assertEqual(store.load(legacy.id).model_dump(), original)

    def test_correction_repairs_requirement_mapping_without_rewriting_requirement(self):
        run = example()
        requirement = run.requirements[0]
        requirement.component_ids = []
        before = requirement.model_dump(exclude={"component_ids"})
        workflow = Workflow(object(), object(), object())
        self.assertTrue(
            workflow._apply_correction(
                run, Correction(reason="Restore affected components", requirement_components={"req": ["U1", "U2"]})
            )
        )
        self.assertEqual(requirement.component_ids, ["U1", "U2"])
        self.assertEqual(requirement.model_dump(exclude={"component_ids"}), before)
        self.assertEqual((run.revision, run.review_completed), (2, False))
        for mapping in ({"missing_requirement": ["U1"]}, {"req": ["missing_component"]}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                workflow._apply_correction(run, Correction(reason="Invalid reference", requirement_components=mapping))
        self.assertEqual(requirement.component_ids, ["U1", "U2"])
        with self.assertRaises(ValueError):
            workflow._apply_correction(run, Correction(reason="Invalid source owner", reread_component_ids=["missing"]))
        self.assertTrue(
            workflow._apply_correction(run, Correction(reason="Read missing fact", reread_component_ids=["U1"]))
        )

    def test_signal_conflict_can_reread_one_existing_source_before_configuration(self):
        run = split_source_example()
        run.limits.correction_rounds = 1
        next(n for n in run.evidence[0].numbers if n.role == "output_low").value = 1.2
        untouched = run.evidence[1].model_dump()

        def extract(payload, blocks):
            fact = payload["previous_observations"][0].model_copy(
                update={
                    "id": "output",
                    "fact": "VOL maximum 0.4 V",
                    "numbers": [SourceNumber(id="vol", role="output_low", value=0.4, unit="V", basis="max")],
                }
            )
            return EvidencePacket(
                applicability={"U1": {"applies": True, "reason": "Exact local fixture"}},
                evidence=[*payload["previous_observations"], fact],
            )

        def configure(payload, blocks):
            configuration = configuration_for(run)
            source = next(e for e in run.evidence if e.fact == "VOL maximum 0.4 V")
            configuration.signal_checks[0].output_low_max = Quantity(
                source_ids=[source.numbers[0].id]
            )
            return configuration

        gateway = gateway_for(
            run,
            {
                Correction: Correction(
                    reason="MCU VOL exceeds the receiving logic-low limit",
                    reread_component_ids=["U1"],
                    configuration_instructions="Reread the already-interpreted source for MCU VOL.",
                ),
                ReadingPlan: ReadingPlan(
                    selections=[PageSelection(document_id="doc", pages=[1], reason="Missing VOL")]
                ),
                EvidencePacket: extract,
                OperatingConfiguration: configure,
            },
        )
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual((run.compatibility, run.usage.correction_rounds), ("checked", 1))
        self.assertEqual(
            [[d["document_id"] for d in c["payload"]["documents"]] for c in gateway.calls_for(ReadingPlan)], [["doc"]]
        )
        self.assertEqual(len(gateway.calls_for(EvidencePacket)), 1)
        self.assertEqual(next(e.model_dump() for e in run.evidence if e.id == "other-spec"), untouched)
        self.assertEqual([{b["text"] for b in c["blocks"]} for c in gateway.calls_for(Review)], [{"doc", "other"}] * 2)

    def test_numeric_gap_remains_recorded_without_correction_or_failed_review(self):
        run = workflow_example()
        run.signal_checks[0].output_low_max = None
        gateway = gateway_for(run)
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual(len(gateway.calls_for(Review)), 1)
        self.assertEqual((run.lifecycle, run.compatibility, run.review_completed), ("finished", "checked", True))
        self.assertEqual(run.usage.correction_rounds, 0)
        self.assertEqual(gateway.calls_for(Correction), [])
        self.assertTrue(any(f.id == "code:signal:U1_to_U2" and f.status == "unknown" for f in run.findings))

    def test_review_verdict_does_not_require_more_requested_pages(self):
        run = workflow_example()
        review = review_for(run)
        review.additional_pages = [PageSelection(document_id="doc", pages=[1], reason="More detail")]
        gateway = gateway_for(run, {Review: review})
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual((run.compatibility, run.review_completed), ("checked", True))
        self.assertEqual(len(gateway.calls_for(Review)), 2)
        self.assertEqual(gateway.calls_for(Correction), [])

    def test_available_catalog_is_reviewed_when_source_documents_are_missing(self):
        run = workflow_example()
        run.documents, run.evidence = [], []
        for component in run.components:
            component.document_ids = []
        gateway = gateway_for(run)
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual((run.lifecycle, run.compatibility), ("finished", "checked"))
        self.assertEqual(len(gateway.calls_for(Review)), 1)
        self.assertTrue(any(f.area == "evidence" and f.status == "unknown" for f in run.findings))

    def test_mapping_gap_does_not_trigger_correction_or_rebuild(self):
        run = workflow_example()
        run.requirements[0].component_ids = []
        design_fields = {"components", "rails", "interfaces", "signal_checks", "evidence"}
        before = run.model_dump(include=design_fields)
        gateway = gateway_for(run)
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual(len(gateway.calls_for(Review)), 1)
        self.assertEqual(gateway.calls_for(Correction), [])
        self.assertEqual(gateway.calls_for(OperatingConfiguration), [])
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.model_dump(include=design_fields), before)

    def test_empty_requirement_mapping_remains_unresolved_without_crashing(self):
        run = example()
        workflow = Workflow(object(), object(), object())
        workflow._apply_correction(run, Correction(reason="Unresolved mapping", requirement_components={"req": []}))
        refresh_checks(run)
        self.assertIsNone(run.compatibility)
        self.assertEqual(run.requirements[0].component_ids, [])
        self.assertTrue(any(f.id == "code:requirement:req" and f.status == "unknown" for f in run.findings))
        with self.assertRaises(ValueError):
            workflow._apply_correction(
                run, Correction(reason="Unknown placement", requirement_components={"req": ["missing"]})
            )

    def test_direct_correction_preserves_sources_without_another_configuration_call(self):
        run = workflow_example()
        run.limits.correction_rounds = 1
        run.requirements[0].component_ids = []
        run.rails[0].loads[0].current = Quantity(
            value=200, unit="mA", basis="estimate", assumption_id="supply", source_ids=["specN3"]
        )
        run.evidence_errors = [
            Finding(
                id="unused",
                method="code",
                kind="guidance",
                area="evidence",
                status="unknown",
                subject_ids=["U1"],
                document_id="doc",
                explanation="Unused optional observation",
            )
        ]
        preserved = {"components", "evidence", "evidence_errors"}
        before = run.model_dump(include=preserved)
        configuration = configuration_for(run)
        configuration.rails[0].loads[0].current = Quantity(
            value=10, unit="mA", basis="estimate", assumption_id="supply", source_ids=["specN3"]
        )
        gateway = gateway_for(
            run,
            {
                Correction: Correction(
                    reason="Repair current and mapping",
                    configuration=configuration,
                    requirement_components={"req:one": ["U1", "U2"]},
                )
            },
        )
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual(gateway.calls_for(OperatingConfiguration), [])
        self.assertEqual(len(gateway.calls_for(Review)), 2)
        self.assertEqual((run.compatibility, run.review_completed, run.revision), ("checked", True, 2))
        self.assertEqual(run.model_dump(include=preserved), before)
        self.assertEqual(run.requirements[0].component_ids, ["U1", "U2"])

    def test_direct_configuration_rejects_conflicting_modes(self):
        run = example()
        configuration = configuration_for(run)
        part = component_spec(run.components[0])
        for change in (
            {"add_components": [part]},
            {"replace_components": [part]},
            {"remove_component_ids": ["U1"]},
            {"reread_component_ids": ["U1"]},
            {"configuration": configuration.model_copy(update={"additional_components": [part]})},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                Correction(**{"reason": "Conflicting modes", "configuration": configuration, **change})
        run.components[0].product = None
        with self.assertRaises(ValueError):
            Workflow(object(), object(), object())._apply_correction(
                run, Correction(reason="Unselected part", configuration=configuration)
            )
        self.assertEqual(run.revision, 1)

    def test_unselected_part_requires_part_repair_in_requested_response(self):
        run = workflow_example()
        run.components[0].product = None
        gateway = gateway_for(run, {Correction: Correction(reason="Await a suitable selection")})
        supplier = SimpleNamespace(search=lambda *args, **kwargs: [])
        workflow = SeededWorkflow(SourcePages(), supplier, gateway)
        list(workflow.execute(run))
        response_type = gateway.calls_for(Correction)[0]["schema"]
        with self.assertRaises(ValueError):
            response_type.model_validate(
                {"reason": "Skip selection", "configuration": configuration_for(run).model_dump()}
            )
        replacement = component_spec(run.components[0])
        replacement.search_query = "Documented replacement sensor"
        repair = response_type.model_validate(
            {"reason": "Find a replacement", "replace_components": [replacement.model_dump()]}
        )
        self.assertTrue(workflow._apply_correction(run, repair))
        self.assertEqual(run.components[0].search_query, "Documented replacement sensor")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_numeric_repair_does_not_reread_sources_for_unrelated_evidence_gaps(self):
        run = workflow_example()
        run.components.append(
            run.components[0].model_copy(
                update={
                    "id": "J1",
                    "kind": "connector",
                    "document_ids": [],
                    "product": run.components[0].product.model_copy(
                        update={"parameters": [{"name": "Current Rating", "value": "1 A"}]}
                    ),
                }
            )
        )
        run.rails[0].loads[0].current = Quantity(
            value=200, unit="mA", basis="estimate", assumption_id="supply", source_ids=["specN3"]
        )
        configuration = configuration_for(run)
        configuration.rails[0].loads[0].current = Quantity(
            value=10, unit="mA", basis="estimate", assumption_id="supply", source_ids=["specN3"]
        )
        review = review_for(run)
        next(f for f in review.findings if f.area == "evidence").status = "unknown"
        gateway = gateway_for(
            run,
            {
                Review: review,
                Correction: Correction(
                    reason="Restore current estimate", configuration_instructions="Use the existing 10mA load estimate."
                ),
                OperatingConfiguration: configuration,
            },
        )
        workflow = SeededWorkflow(SourcePages(), object(), gateway)
        list(workflow.execute(run))
        self.assertEqual(workflow.completion_calls, 1)
        self.assertEqual(len(gateway.calls_for(OperatingConfiguration)), 1)
        self.assertEqual(len(gateway.calls_for(Review)), 2)
        self.assertEqual(run.compatibility, "checked")

    def test_review_numeric_citations_resolve_to_evidence_without_discarding_invalid_refs(self):
        run = workflow_example()
        evidence = run.evidence[0]
        review = review_for(run)
        finding = review.findings[0]
        finding.evidence_ids = [evidence.numbers[0].id, evidence.id, "unknown"]
        workflow = Workflow(SourcePages(), object(), Gateway({Review: review}))
        drain(workflow._review_bom(run, Budget(run), []))
        installed = next(f for f in run.findings if f.id == finding.id)
        self.assertEqual(installed.evidence_ids, [evidence.id, "unknown"])
        self.assertTrue(any(f.id == f"code:finding:{finding.id}" and f.status == "unknown" for f in run.findings))

    def test_refinement_instructions_reach_source_page_selection(self):
        run = example()
        run.modification = "Read the controller current table before updating the load estimate."
        gateway = Gateway({ReadingPlan: ReadingPlan(selections=[])})
        drain(Workflow(SourcePages(), object(), gateway)._plan_source_reads(run, Budget(run)))
        self.assertEqual(gateway.calls[0]["payload"]["latest_modification"], run.modification)

    def test_explicit_passive_source_request_is_not_silently_skipped(self):
        run = legacy_support_example()
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

    def test_catalog_usb_c_connector_receives_shared_support_guide_once(self):
        run = example()
        run.components, run.documents = [run.components[0]], []
        connector = run.components[0]
        connector.kind, connector.document_ids = "connector", []
        connector.product.datasheet_url = "https://example.com/connector.pdf"
        connector.product.parameters = [{"name": "Connector Type", "value": "USB-C (USB TYPE-C)"}]
        fetched = []

        class Documents:
            def fetch(self, url, **kwargs):
                fetched.append(url)
                return {"document_id": url, "url": url, "page_count": 1, "media_type": "text/html"}

        workflow = Workflow(Documents(), object(), object())
        list(workflow._fetch_documents(run, Budget(run)))
        list(workflow._fetch_documents(run, Budget(run)))
        self.assertEqual(fetched, [connector.product.datasheet_url, USB_C_GUIDE_URL])
        self.assertIn(USB_C_GUIDE_URL, connector.document_ids)
        run.documents, connector.document_ids = [], []
        fetched.clear()
        connector.product.parameters[0]["value"] = "USB-A"
        list(workflow._fetch_documents(run, Budget(run)))
        self.assertEqual(fetched, [connector.product.datasheet_url])
        run.documents, connector.document_ids = [], []
        fetched.clear()
        connector.product.parameters[0]["value"] = "USB-C"
        connector.product.datasheet_url = None
        connector.product.product_url = "https://example.com/connector"
        list(workflow._fetch_documents(run, Budget(run)))
        self.assertEqual(fetched, [connector.product.product_url, USB_C_GUIDE_URL])

    def test_discarded_unused_observation_does_not_block_but_cannot_support_a_claim(self):
        class Documents:
            def quote_matches(self, document_id, page, quote):
                return quote != "Unsupported optional observation"

        run = example()
        run.documents[0]["pages_read"] = [1]
        unused = run.evidence[0].model_copy(update={"id": "unused", "quote": "Unsupported optional observation"})
        workflow = Workflow(Documents(), object(), object())
        run.evidence, run.evidence_errors = workflow._filter_evidence(run, [*run.evidence, unused], {"U1", "U2"})
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.evidence_errors[0].kind, "guidance")
        run.rails[0].loads[0].voltage_max.evidence_ids = ["unused"]
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertTrue(any(f.area == "power" and f.status == "unknown" for f in run.findings))

    def test_requirement_namespace_does_not_change_physical_placements(self):
        plan = Plan(
            summary="Resistor fixture",
            assumptions=[],
            configuration_notes=[],
            requirements=[
                Requirement(id=key, clause="Fixture", description="Fixture", component_ids=["R1"])
                for key in ("R1", "req:retained")
            ],
            components=[ComponentSpec(id="R1", name="Resistor", kind="passive", purpose="Bias", search_query="10k")],
            pending_questions=[Question(id="question", requirement_id="R1", question="What value?")],
        )
        run = example()
        result = drain(plan_requirements(Gateway({Plan: plan}), Budget(run), run))
        self.assertEqual([r.id for r in result.requirements], ["req:R1", "req:retained"])
        self.assertEqual(result.pending_questions[0].requirement_id, "req:R1")
        self.assertEqual((result.components[0].id, result.requirements[0].component_ids), ("R1", ["R1"]))

    def test_new_functional_component_source_does_not_reread_unchanged_documents(self):
        run = workflow_example()

        def choose(payload, blocks):
            return ReadingPlan(
                selections=[
                    PageSelection(document_id=d["document_id"], pages=[1], reason="Functional component ratings")
                    for d in payload["documents"]
                ]
            )

        def extract(payload, blocks):
            owners = [c["id"] for c in payload["components"]]
            document_id = "switch" if "SW1" in owners else "doc"
            fact = example().evidence[0].model_copy(update={"component_ids": owners, "document_id": document_id})
            return EvidencePacket(
                applicability={key: {"applies": True, "reason": "Exact fixture part"} for key in owners},
                evidence=[fact],
            )

        gateway = Gateway({ReadingPlan: choose, EvidencePacket: extract})
        workflow = AddingFunctionalComponentWorkflow(SourcePages(), object(), gateway)
        selections = drain(workflow._source_and_configure(run, Budget(run)))
        self.assertEqual(
            [[d["document_id"] for d in c["payload"]["documents"]] for c in gateway.calls_for(ReadingPlan)],
            [["doc"], ["switch"]],
        )
        self.assertEqual(
            [{b["text"] for b in c["blocks"]} for c in gateway.calls_for(EvidencePacket)], [{"doc"}, {"switch"}]
        )
        self.assertEqual(workflow.configurations, [(2, {"doc"}), (3, {"doc", "switch"})])
        self.assertEqual({s.document_id for s in selections}, {"doc", "switch"})
        self.assertFalse(run.review_completed)

    def test_missing_source_can_discover_an_alternate_before_extraction(self):
        alternate = "https://example.com/alternate"

        class Documents(SourcePages):
            def fetch(self, url, **kwargs):
                if url != alternate:
                    raise DocumentError("Document server returned HTTP 403")
                return {"document_id": "alternate", "url": url, "page_count": 1, "media_type": "text/html"}

        for retained_source, kind in ((False, "module"), (True, "module"), (True, "passive")):
            with self.subTest(retained_source=retained_source, kind=kind):
                run = split_source_example()
                run.components[0].kind = kind
                run.components[0].document_ids = []
                run.documents, run.evidence = run.documents[1:], run.evidence[1:]
                if not retained_source:
                    run.components[1].document_ids = []
                    run.documents, run.evidence = [], []

                def choose(payload, blocks):
                    if not payload["documents"]:
                        return ReadingPlan(
                            selections=[],
                            document_requests=[DocumentRequest(component_id="U1", url=alternate, reason="Alternate source")],
                        )
                    return ReadingPlan(
                        selections=[PageSelection(document_id="alternate", pages=[1], reason="Recovered source")]
                    )

                fact = example().evidence[0].model_copy(
                    deep=True, update={"component_ids": ["U1"], "document_id": "alternate"}
                )
                gateway = Gateway(
                    {
                        ReadingPlan: choose,
                        EvidencePacket: EvidencePacket(
                            applicability={"U1": {"applies": True, "reason": "Exact selected fixture part"}},
                            evidence=[fact],
                        ),
                        OperatingConfiguration: lambda payload, blocks: configuration_for(run),
                    }
                )
                workflow = Workflow(Documents(), object(), gateway)
                pages = drain(
                    workflow._source_and_configure(run, Budget(run), source_component_ids={"U1"} if retained_source else None)
                )
                self.assertIn("alternate", {p.document_id for p in pages})
                self.assertEqual(run.components[0].document_ids, ["alternate"])
                self.assertTrue(any(e.document_id == "alternate" and e.component_ids == ["U1"] for e in run.evidence))
                self.assertIn("https://example.com/doc", run.components[0].document_errors[0])
                if retained_source:
                    self.assertTrue(any(e.id == "other-spec" for e in run.evidence))

    def test_bounded_navigation_preserves_late_toc_chapters(self):
        inventory = SourcePages().inventory("doc")
        inventory.update(
            page_count=20,
            pages=[
                {
                    "page_number": page,
                    "text_status": "available",
                    "text": "Register description " + "bit field details " * 24,
                }
                for page in range(1, 21)
            ],
        )
        inventory["pages"][7]["text"] = (
            "Table of Contents\n1 Overview " + "." * 900 + " 1\n19 Electrical characteristics ... 19"
        )
        navigation = compact_inventory(inventory, max_chars=2000)
        toc = next(page for page in navigation["pages"] if page["page"] == 8)
        self.assertIn("19 Electrical characteristics", toc["sections"])
        self.assertGreater(navigation["omitted_page_cards"], 0)
        self.assertIn("original physical page", navigation["navigation_note"])
        self.assertLess(len(json.dumps(navigation, ensure_ascii=False)), 2100)

    def test_navigation_exposes_support_prose_below_page_headers(self):
        inventory = SourcePages().inventory("doc")
        inventory["pages"] = [
            {
                "page_number": 1,
                "text_status": "available",
                "text": "Manufacturer header\nRevision date\nElectrical table continued\n"
                "10. Functional Description\nThe regulator requires an output capacitor for stability.",
            }
        ]
        navigation = compact_inventory(inventory, max_chars=1000)
        preview = navigation["pages"][0]["sections"]
        self.assertIn("Functional Description", preview)
        self.assertIn("requires an output capacitor", preview)
        self.assertLess(len(json.dumps(navigation, ensure_ascii=False)), 1100)

    def test_reading_plan_merges_shared_sources_and_completes_short_documents(self):
        run = example()
        run.documents[0]["page_count"] = 3
        gateway = Gateway(
            {
                ReadingPlan: ReadingPlan(
                    selections=[
                        PageSelection(document_id="doc", pages=pages, reason="Needed facts") for pages in ([1], [1, 2])
                    ]
                )
            }
        )
        selections = drain(Workflow(SourcePages(), object(), gateway)._plan_source_reads(run, Budget(run)))
        self.assertEqual([(s.document_id, s.pages) for s in selections], [("doc", [1, 2, 3])])

    def test_extraction_assigns_source_identity_without_model_transcription(self):
        run = workflow_example()
        raw = {
            "applicability": {
                key: {"applies": True, "reason": "Exact fixture source"} for key in ("U1", "U2")
            },
            "evidence": [item.model_dump(exclude={"document_id"}) for item in run.evidence],
        }

        def extract(payload, blocks):
            response_type = gateway.calls_for(EvidencePacket)[-1]["schema"]
            return response_type.model_validate(raw)

        gateway = Gateway({EvidencePacket: extract})
        workflow = Workflow(SourcePages(), object(), gateway)
        selection = PageSelection(document_id="doc", pages=[1], reason="Source facts")
        drain(workflow._extract_evidence(run, Budget(run), [selection], ""))
        self.assertEqual({item.document_id for item in run.evidence}, {"doc"})
        self.assertEqual(run.model_dump()["evidence"][0]["document_id"], "doc")
        raw["evidence"][0]["document_id"] = "another-source"
        with self.assertRaises(ValueError):
            gateway.calls_for(EvidencePacket)[-1]["schema"].model_validate(raw)

    def test_negative_source_applicability_discards_facts_only_for_that_owner(self):
        run = workflow_example()
        fact = run.evidence[0]
        packet = EvidencePacket(
            applicability={
                "U1": {"applies": False, "reason": "This datasheet describes a different component."},
                "U2": {"applies": True, "reason": "Exact fixture variant."},
            },
            evidence=[
                fact.model_copy(update={"id": "wrong", "component_ids": ["U1"]}),
                fact.model_copy(update={"id": "valid", "component_ids": ["U2"]}),
            ],
        )
        workflow = Workflow(SourcePages(), object(), Gateway({EvidencePacket: packet}))
        selection = PageSelection(document_id="doc", pages=[1], reason="Source facts")
        drain(workflow._extract_evidence(run, Budget(run), [selection], ""))
        self.assertEqual([(e.id, e.component_ids) for e in run.evidence], [("D1E2", ["U2"])])
        self.assertEqual(run.documents[0]["applicability"]["U1"], packet.applicability["U1"].reason)
        self.assertTrue(any(f.id == "code:source:U1" and f.status == "unknown" for f in run.findings))

    def test_reinterpreting_one_source_preserves_other_owners_and_gaps(self):
        run = replacement_source_example()
        gateway = Gateway({EvidencePacket: replacement_packet})
        workflow = Workflow(SourcePages(), object(), gateway)

        def extract(document_id):
            drain(
                workflow._extract_evidence(
                    run,
                    Budget(run),
                    [PageSelection(document_id=document_id, pages=[1], reason="Resolve source gap")],
                    "",
                )
            )

        extract("replacement")
        self.assertEqual({e.document_id: e.component_ids for e in run.evidence}, {"doc": ["U2"], "replacement": ["U1"]})
        self.assertEqual([(e.document_id, e.subject_ids) for e in run.evidence_errors], [("doc", ["U2"])])
        preserved = next(e.model_dump() for e in run.evidence if e.document_id == "replacement")
        extract("doc")
        self.assertEqual(run.evidence_errors, [])
        self.assertEqual({e.document_id for e in run.evidence}, {"doc", "replacement"})
        gateway.responses[EvidencePacket] = lambda p, b: replacement_packet(p, b).model_copy(
            update={"applicability": {}}
        )
        extract("doc")
        self.assertEqual([e.model_dump() for e in run.evidence], [preserved])
        self.assertTrue(any(e.status == "unknown" and e.document_id == "doc" for e in run.evidence_errors))

    def test_refreshed_prices_reach_planner_and_cost_review(self):
        run = workflow_example()
        run.parent_run_id = "a" * 32
        run.original_request = "Two sensors for at most 5 USD"
        run.requirements.append(
            Requirement(id="budget", clause="at most 5 USD", description="Cost limit", component_ids=["U1", "U2"])
        )
        for component in run.components:
            component.product.retrieved_at = "2000-01-01T00:00:00+00:00"

        class Supplier:
            def get_product(self, *args, **kwargs):
                product = example().components[0].product
                product.retrieved_at = now()
                product.offers[0].price_breaks = [PriceBreak(quantity=1, unit_price=10)]
                return product.model_dump()

        def review(payload, blocks):
            cost = sum(row["extended_price"] for row in payload["design"]["purchasing_bom"])
            result = review_for(run)
            result.findings.append(
                Finding(
                    id="cost",
                    area="requirements",
                    status="pass" if cost <= 5 else "fail",
                    subject_ids=["req:budget"],
                    explanation="Cost versus requested limit",
                )
            )
            return result

        gateway = gateway_for(run, {Review: review, Correction: Correction(reason="Cannot meet the budget")})
        list(SeededWorkflow(SourcePages(), Supplier(), gateway).execute(run))
        for schema, field in ((Plan, "previous_design"), (Review, "design")):
            rows = gateway.calls_for(schema)[0]["payload"][field]["purchasing_bom"]
            self.assertEqual(sum(row["extended_price"] for row in rows), 20)
        self.assertEqual((run.lifecycle, run.compatibility), ("finished", "issues_found"))

    def test_review_catches_requirement_lost_by_refinement_planner(self):
        run = workflow_example()
        run.parent_run_id, run.modification = "a" * 32, "Lower the cost"
        plan = plan_for(run)
        run.requirements.append(
            Requirement(
                id="display",
                clause="Add a display",
                description="Earlier refinement requested a display",
                component_ids=["U1"],
            )
        )
        for component in run.components:
            component.product.retrieved_at = now()

        def review(payload, blocks):
            result = review_for(run)
            prior = {r["id"] for r in payload["prior_requirements"]}
            current = {r["id"] for r in payload["design"]["requirements"]}
            if "display" in prior - current:
                result.findings.append(
                    Finding(
                        id="omitted",
                        area="requirements",
                        status="fail",
                        subject_ids=["U1"],
                        explanation="Earlier display requirement was dropped",
                    )
                )
            return result

        gateway = gateway_for(
            run, {Plan: plan, Review: review, Correction: Correction(reason="Cannot silently remove a requirement")}
        )
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
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
        list(workflow._select_components(run, Budget(run)))
        self.assertIsNone(run.components[0].product)
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")
        self.assertEqual(run.components[0].selection_error, "Wrong function")

    def test_selected_identity_preserves_correction_source_leads_without_inheriting_evidence(self):
        run = example()
        chosen = run.components[0].product.model_copy(
            update={"mpn": "ALTERNATE-1", "datasheet_url": "https://example.com/alternate.pdf"}
        )
        replacement = component_spec(run.components[0])
        replacement.name = "Original proposed part"
        replacement.document_urls = ["https://example.com/original.pdf"]

        class Supplier:
            def search(self, *args, **kwargs):
                return [chosen.model_dump()]

            def get_product(self, *args, **kwargs):
                return chosen.model_dump()

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return Picks(
                    picks=[Pick(component_id="U1", chosen_index=0, reason="Suitable actual catalog candidate")]
                )

        workflow = Workflow(object(), Supplier(), Gateway())
        workflow._apply_correction(run, Correction(reason="Documented replacement", replace_components=[replacement]))
        list(workflow._select_components(run, Budget(run)))
        self.assertEqual((run.components[0].name, run.components[0].product.mpn), ("ALTERNATE-1", "ALTERNATE-1"))
        self.assertEqual(run.components[0].document_urls, ["https://example.com/original.pdf"])
        self.assertEqual(run.components[0].document_ids, [])
        self.assertEqual(run.evidence[0].component_ids, ["U2"])
        self.assertEqual(run.components[0].product.datasheet_url, "https://example.com/alternate.pdf")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_missing_datasheet_link_does_not_reject_a_selected_active_part(self):
        run = example()
        undocumented = run.components[0].product.model_copy(update={"mpn": "NO-DOC", "offers": []})
        run.components[0].product = None

        class Supplier:
            def search(self, query, **kwargs):
                return [undocumented.model_dump()]

            def get_product(self, identifier, **kwargs):
                return undocumented.model_dump()

        class Gateway:
            def call(self, *args, **kwargs):
                yield {"type": "progress"}
                return Picks(picks=[Pick(component_id="U1", chosen_index=0, reason="Candidate fit")])

        list(Workflow(object(), Supplier(), Gateway())._select_components(run, Budget(run)))
        self.assertEqual(run.components[0].product.mpn, "NO-DOC")
        self.assertIsNone(run.components[0].selection_error)
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_invalid_source_and_targeted_correction_preserve_whole_design(self):
        class Documents(SourcePages):
            def quote_matches(self, *args):
                return False

        workflow = Workflow(Documents(), supplier=object(), gateway=object())
        run = example()
        run.documents[0]["pages_read"] = [1]
        run.evidence, run.evidence_errors = workflow._filter_evidence(run, run.evidence, {"U1", "U2"})
        self.assertEqual(run.evidence, [])
        replacement = component_spec(run.components[0])
        replacement.search_query = "REPLACEMENT-1"
        self.assertTrue(
            workflow._apply_correction(
                run, Correction(reason="Replace selected sensor", replace_components=[replacement])
            )
        )
        self.assertIsNone(run.components[0].product)
        self.assertEqual(
            (run.components[1].product.mpn, len(run.rails), run.requirements[0].component_ids),
            ("SENSOR-1", 1, ["U1", "U2"]),
        )
        self.assertEqual((run.compatibility, run.review_completed, run.revision), (None, False, 2))


if __name__ == "__main__":
    unittest.main()
