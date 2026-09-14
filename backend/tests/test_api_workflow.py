"""Small application/state checks using local workflows and supplier/model fakes."""

import json
import tempfile
import unittest
from types import SimpleNamespace

from app import create_app
from checks import refresh_checks as evaluate
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
    supported_example,
    workflow_example,
)
from llm import Budget, BudgetExceeded
from models import (
    CircuitProposal,
    ComponentSpec,
    Correction,
    EvidencePacket,
    Finding,
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
    now,
)
from pipeline import Workflow, compact_inventory
from run_store import RunStore
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
        evaluate(run)
        yield {"type": "complete"}


class AddingSupportWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assemblies = []

    def _fetch_documents(self, run, budget, requested_component_ids=()):
        yield {"type": "progress"}
        if len(run.components) == 3:
            run.components[-1].document_ids = ["switch"]
            run.documents.append({"document_id": "switch", "page_count": 1, "media_type": "text/html"})

    def _assemble_bom(self, run, budget, instructions=""):
        self.assemblies.append((len(run.components), {e.document_id for e in run.evidence}))
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

    def test_signal_gap_can_reread_one_existing_source_before_assembly(self):
        run = split_source_example()
        run.limits.correction_rounds = 1
        run.signal_checks[0].output_low_max = None
        untouched = run.evidence[1].model_dump()

        def extract(payload, blocks):
            fact = payload["previous_observations"][0].model_copy(update={"id": "output", "fact": "VOL maximum 0.4 V"})
            return EvidencePacket(
                applicability={"U1": "Exact local fixture"}, evidence=[*payload["previous_observations"], fact]
            )

        def assemble(payload, blocks):
            configuration = configuration_for(run)
            reference = next(e.id for e in run.evidence if e.fact == "VOL maximum 0.4 V")
            configuration.signal_checks[0].output_low_max = Quantity(
                value=0.4, unit="V", basis="max", evidence_ids=[reference]
            )
            return configuration

        gateway = gateway_for(
            run,
            {
                Correction: Correction(
                    reason="Missing MCU VOL",
                    reread_component_ids=["U1"],
                    configuration_instructions="Reread the already-interpreted source for MCU VOL.",
                ),
                ReadingPlan: ReadingPlan(
                    selections=[PageSelection(document_id="doc", pages=[1], reason="Missing VOL")]
                ),
                EvidencePacket: extract,
                CircuitProposal: assemble,
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

    def test_numeric_gap_is_reviewed_but_cannot_be_overridden_by_model_pass(self):
        run = workflow_example()
        run.signal_checks[0].output_low_max = None
        run.limits.correction_rounds = 0
        gateway = gateway_for(run)
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual(len(gateway.calls_for(Review)), 1)
        self.assertEqual((run.lifecycle, run.compatibility, run.review_completed), ("finished", "incomplete", True))
        self.assertIn("Correction allowance reached", run.terminal_reason)

    def test_mapping_only_correction_reviews_without_rebuilding_design(self):
        run = workflow_example()
        run.requirements[0].component_ids = []
        design_fields = {"components", "rails", "interfaces", "signal_checks", "evidence"}
        before = run.model_dump(include=design_fields)
        gateway = gateway_for(
            run,
            {
                Correction: Correction(
                    reason="Restore requirement mapping", requirement_components={"req:one": ["U1", "U2"]}
                )
            },
        )
        list(SeededWorkflow(SourcePages(), object(), gateway).execute(run))
        self.assertEqual(len(gateway.calls_for(Review)), 2)
        self.assertEqual(gateway.calls_for(CircuitProposal), [])
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.model_dump(include=design_fields), before)

    def test_direct_configuration_preserves_sources_and_skips_assembly(self):
        run = workflow_example(support=True)
        run.limits.correction_rounds = 1
        run.requirements[0].component_ids = []
        run.rails[0].loads[0].current = None
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
        preserved = {"components", "evidence", "source_support_needs", "support_needs", "evidence_errors"}
        before = run.model_dump(include=preserved)
        configuration = configuration_for(run)
        configuration.rails[0].loads[0].current = Quantity(
            value=10, unit="mA", basis="estimate", assumption_id="supply"
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
        self.assertEqual(gateway.calls_for(CircuitProposal), [])
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

    def test_numeric_repair_does_not_reread_an_unchanged_catalog_reviewed_connector(self):
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
        run.rails[0].loads[0].current = None
        configuration = configuration_for(run)
        configuration.rails[0].loads[0].current = Quantity(
            value=10, unit="mA", basis="estimate", assumption_id="supply"
        )
        gateway = gateway_for(
            run,
            {
                Correction: Correction(
                    reason="Restore current estimate", configuration_instructions="Use the existing 10mA load estimate."
                ),
                CircuitProposal: configuration,
            },
        )
        workflow = SeededWorkflow(SourcePages(), object(), gateway)
        list(workflow.execute(run))
        self.assertEqual(workflow.completion_calls, 1)
        self.assertEqual(len(gateway.calls_for(CircuitProposal)), 1)
        self.assertEqual(len(gateway.calls_for(Review)), 2)
        self.assertEqual(run.compatibility, "checked")

    def test_refinement_instructions_reach_source_page_selection(self):
        run = example()
        run.modification = "Read the controller current table before updating the load estimate."
        gateway = Gateway({ReadingPlan: ReadingPlan(selections=[])})
        drain(Workflow(SourcePages(), object(), gateway)._plan_source_reads(run, Budget(run)))
        self.assertEqual(gateway.calls[0]["payload"]["latest_modification"], run.modification)

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

    def test_new_support_source_does_not_reread_unchanged_documents(self):
        run = workflow_example()

        def choose(payload, blocks):
            return ReadingPlan(
                selections=[
                    PageSelection(document_id=d["document_id"], pages=[1], reason="Required support")
                    for d in payload["documents"]
                ]
            )

        def extract(payload, blocks):
            owners = [c["id"] for c in payload["components"]]
            document_id = "switch" if "SW1" in owners else "doc"
            fact = example().evidence[0].model_copy(update={"component_ids": owners, "document_id": document_id})
            return EvidencePacket(applicability={key: "Exact fixture part" for key in owners}, evidence=[fact])

        gateway = Gateway({ReadingPlan: choose, EvidencePacket: extract})
        workflow = AddingSupportWorkflow(SourcePages(), object(), gateway)
        selections = drain(workflow._complete_bom(run, Budget(run)))
        self.assertEqual(
            [[d["document_id"] for d in c["payload"]["documents"]] for c in gateway.calls_for(ReadingPlan)],
            [["doc"], ["switch"]],
        )
        self.assertEqual(
            [{b["text"] for b in c["blocks"]} for c in gateway.calls_for(EvidencePacket)], [{"doc"}, {"switch"}]
        )
        self.assertEqual(workflow.assemblies, [(2, {"doc"}), (3, {"doc", "switch"})])
        self.assertEqual({s.document_id for s in selections}, {"doc", "switch"})
        self.assertFalse(run.review_completed)

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

    def test_module_reading_includes_external_support_heading_within_page_cap(self):
        run = example()
        run.documents[0]["page_count"] = 40

        class Documents(SourcePages):
            def inventory(self, identifier):
                return {
                    **super().inventory(identifier),
                    "page_count": 40,
                    "pages": [
                        {"page_number": page, "text_status": "available", "text": text}
                        for page, text in (
                            (2, "Contents\n9 Peripheral Schematics ... 39"),
                            (37, "8 Module Schematics\nInternal module circuit"),
                            (39, "9\nPeripheralSchematics\nExternal support circuit"),
                        )
                    ],
                }

        selection = PageSelection(document_id="doc", pages=[37], reason="Model choice")
        gateway = Gateway({ReadingPlan: ReadingPlan(selections=[selection])})
        workflow = Workflow(Documents(), object(), gateway)
        selected = drain(workflow._plan_source_reads(run, Budget(run)))
        self.assertEqual(selected[0].pages, [37, 39])
        self.assertIn("external support", selected[0].reason)
        selection.pages = list(range(1, 25))
        with self.assertRaises(BudgetExceeded):
            drain(workflow._plan_source_reads(run, Budget(run)))

    def test_source_support_remapping_survives_omitted_circuit_fulfillment(self):
        run = workflow_example(support=True)
        packet = EvidencePacket(
            applicability={key: "Exact fixture sensor family" for key in ("U1", "U2")},
            evidence=[run.evidence[0].model_copy(update={"id": "raw_fact"})],
            source_support_needs=[
                run.source_support_needs[0].model_copy(update={"id": "raw_need", "evidence_ids": ["raw_fact"]})
            ],
        )
        workflow = Workflow(SourcePages(), object(), Gateway({EvidencePacket: packet}))
        drain(
            workflow._extract_evidence(
                run, Budget(run), [PageSelection(document_id="doc", pages=[1], reason="Support circuit")], ""
            )
        )
        source = run.source_support_needs[0]
        self.assertEqual((source.document_id, source.evidence_ids), ("doc", [run.evidence[0].id]))
        proposal = configuration_for(run)
        proposal.support_needs = []
        workflow._apply_configuration(run, proposal)
        self.assertEqual([(n.id, n.status) for n in run.support_needs], [(source.id, "unresolved")])
        evaluate(run)
        self.assertTrue(any(f.id == f"code:source_support:{source.id}" and f.status == "unknown" for f in run.findings))
        replacement = component_spec(run.components[0])
        replacement.search_query = "SENSOR-2 from the same family document"
        workflow._apply_correction(run, Correction(reason="Another variant", replace_components=[replacement]))
        self.assertEqual(run.source_support_needs, [])
        self.assertEqual(run.evidence[0].component_ids, ["U2"])

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
        run = workflow_example(support=True)
        raw = {
            "applicability": {"U1": "Exact fixture source", "U2": "Exact fixture source"},
            "evidence": [item.model_dump(exclude={"document_id"}) for item in run.evidence],
            "source_support_needs": [item.model_dump(exclude={"document_id"}) for item in run.source_support_needs],
        }

        def extract(payload, blocks):
            response_type = gateway.calls_for(EvidencePacket)[-1]["schema"]
            return response_type.model_validate(raw)

        gateway = Gateway({EvidencePacket: extract})
        workflow = Workflow(SourcePages(), object(), gateway)
        selection = PageSelection(document_id="doc", pages=[1], reason="Source facts")
        drain(workflow._extract_evidence(run, Budget(run), [selection], ""))
        self.assertEqual({item.document_id for item in run.evidence + run.source_support_needs}, {"doc"})
        self.assertEqual(run.model_dump()["evidence"][0]["document_id"], "doc")
        raw["evidence"][0]["document_id"] = "another-source"
        with self.assertRaises(ValueError):
            gateway.calls_for(EvidencePacket)[-1]["schema"].model_validate(raw)

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

    def test_selected_catalog_identity_replaces_plan_name_and_source_hints(self):
        run = example()
        chosen = run.components[0].product.model_copy(
            update={"mpn": "ALTERNATE-1", "datasheet_url": "https://example.com/alternate.pdf"}
        )
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
                return Picks(
                    picks=[Pick(component_id="U1", chosen_index=0, reason="Suitable actual catalog candidate")]
                )

        list(Workflow(object(), Supplier(), Gateway())._select_components(run, Budget(run)))
        self.assertEqual((run.components[0].name, run.components[0].product.mpn), ("ALTERNATE-1", "ALTERNATE-1"))
        self.assertEqual(run.components[0].document_urls, [])
        self.assertEqual(run.components[0].product.datasheet_url, "https://example.com/alternate.pdf")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_undocumented_active_candidate_uses_broad_query_alternative(self):
        run = example()
        undocumented = run.components[0].product.model_copy(update={"mpn": "NO-DOC", "offers": []})
        documented = undocumented.model_copy(
            update={"mpn": "WITH-DOC", "datasheet_url": "https://example.com/source.pdf"}
        )
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

        list(Workflow(object(), Supplier(), Gateway())._select_components(run, Budget(run)))
        self.assertEqual(run.components[0].product.mpn, "WITH-DOC")
        self.assertEqual(run.components[1].product.mpn, "SENSOR-1")

    def test_invalid_source_and_targeted_correction_preserve_whole_design(self):
        class Documents(SourcePages):
            def quote_matches(self, *args):
                return False

        workflow = Workflow(Documents(), supplier=object(), gateway=object())
        run = example()
        run.documents[0]["pages_read"] = [1]
        run.evidence, run.evidence_errors = workflow._verify_evidence(run, run.evidence, {"U1", "U2"})
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
        self.assertEqual((run.compatibility, run.review_completed, run.revision), ("incomplete", False, 2))


if __name__ == "__main__":
    unittest.main()
