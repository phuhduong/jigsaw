"""Deterministic core examples; no model or supplier calls."""

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from checks import refresh_checks, run_checks
from fakes import example, legacy_support_example
from models import (
    REVIEW_AREAS,
    Assumption,
    DesignRun,
    Endpoint,
    Finding,
    Interface,
    PowerLoad,
    PriceBreak,
    Quantity,
    Rail,
    RegulatorCheck,
    Review,
    SignalCheck,
)
from run_store import (
    RunStore,
    bom_rows,
    design_context,
    export_csv,
    export_json,
    product_context,
)


class CheckTests(unittest.TestCase):
    def test_invalid_numeric_records_are_not_component_conflicts(self):
        run = example()
        run.rails[0].voltage_min.value = 4
        run.rails[0].available_current.value = -1
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        findings = {finding.id: finding for finding in run.findings}
        self.assertEqual(findings["code:voltage:supply:U1"].status, "unknown")
        self.assertEqual(findings["code:current:supply"].status, "unknown")

    def test_repair_findings_report_the_actual_acquisition_and_selection_failure(self):
        run = example()
        run.components[0].document_ids = []
        run.components[0].document_errors = ["Document server returned HTTP 403"]
        run.components[1].product = None
        run.components[1].selection_error = "No compatible candidate for 1uF; candidate capacitance was 0.1uF"
        findings = {finding.id: finding for finding in run_checks(run)}
        self.assertIn("HTTP 403", findings["code:source:U1"].explanation)
        self.assertIn("replace the part", findings["code:source:U1"].remedy)
        self.assertIn("0.1uF", findings["code:selection:U2"].explanation)
        self.assertIn("search_query", findings["code:selection:U2"].remedy)
        self.assertEqual(findings["code:selection:U2"].status, "fail")
        refresh_checks(run)
        self.assertEqual(run.compatibility, "issues_found")

    def test_only_current_explicit_functional_or_electrical_failures_block_review(self):
        run = example()
        power = next(f for f in run.findings if f.area == "power")
        power.status = "unknown"
        next(f for f in run.findings if f.area == "evidence").status = "fail"
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        power.status = "fail"
        refresh_checks(run)
        self.assertEqual(run.compatibility, "issues_found")
        power.kind = "guidance"
        run.findings.append(power.model_copy(update={"id": "stale", "kind": "check", "revision": 0}))
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")

    def test_interface_can_use_its_current_source_backed_review_without_duplicate_refs(self):
        run = example()
        run.interfaces[0].evidence_ids = []
        review = next(f for f in run.findings if f.area == "signals")
        review.subject_ids.append("bus")

        def interface_check():
            return next(f for f in run_checks(run) if f.id == "code:interface:bus")

        self.assertEqual(interface_check().status, "pass")
        self.assertEqual(interface_check().evidence_ids, ["spec"])
        review.revision = 0
        self.assertEqual(interface_check().status, "unknown")
        review.revision = run.revision
        run.interfaces[0].evidence_ids = ["invalid"]
        self.assertEqual(interface_check().status, "unknown")

    def test_i2c_needs_each_direction_and_names_wrong_source_owner(self):
        run = example()
        run.signal_checks = run.signal_checks[:1]
        finding = next(f for f in run_checks(run) if f.id == "code:interface_directions:bus")
        self.assertEqual(finding.status, "unknown")
        self.assertIn("U2 to U1", finding.explanation)
        sensor = run.evidence[0].model_copy(update={"id": "sensor_low", "component_ids": ["U2"]})
        run.evidence.append(sensor)
        run.signal_checks[0].output_low_max.evidence_ids = [sensor.id]
        finding = next(f for f in run_checks(run) if f.id == "code:signal:U1_to_U2")
        self.assertEqual(finding.status, "unknown")
        self.assertIn("U1 output_low_max", finding.explanation)
        self.assertIn("sensor_low belongs to U2", finding.explanation)

    def test_protocol_review_cannot_bypass_numeric_checks(self):
        run = example()
        next(f for f in run.findings if f.area == "signals").subject_ids.append("bus")
        run.signal_checks = run.signal_checks[:1]
        finding = next(f for f in run_checks(run) if f.id == "code:interface_directions:bus")
        self.assertEqual(finding.status, "unknown")
        run.signal_checks[0].output_low_max.value = 1.2
        refresh_checks(run)
        failures = {f.id for f in run.findings if f.status == "fail"}
        self.assertIn("code:signal:U1_to_U2", failures)
        self.assertEqual(run.compatibility, "issues_found")

    def test_one_component_capability_needs_its_current_source_backed_review(self):
        for endpoint_count in (1, 2):
            with self.subTest(endpoint_count=endpoint_count):
                run = example()
                run.interfaces.append(
                    Interface(
                        id="radio",
                        protocol="Bluetooth",
                        configuration="Built-in BLE capability",
                        endpoints=[Endpoint(component_id="U1") for _ in range(endpoint_count)],
                        evidence_ids=["spec"],
                    )
                )
                finding = next(f for f in run_checks(run) if f.id == "code:interface:radio")
                self.assertEqual(finding.status, "unknown")
                next(f for f in run.findings if f.area == "signals").subject_ids.append("radio")
                finding = next(f for f in run_checks(run) if f.id == "code:interface:radio")
                self.assertEqual(finding.status, "pass")
                self.assertIn("not an inter-part", finding.explanation)
                run.interfaces[-1].protocol = "I2C"
                finding = next(f for f in run_checks(run) if f.id == "code:interface:radio")
                self.assertEqual(finding.status, "unknown")

    def test_current_only_passive_load_keeps_current_and_explicit_voltage_checks(self):
        run = example()
        run.components[1].kind = "passive"
        load = run.rails[0].loads[1]
        load.voltage_min = load.voltage_max = None
        review = next(f for f in run.findings if f.area == "power")
        review.subject_ids.append("supply")
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        for problem in ("missing_review", "active_load", "missing_rail_bound"):
            with self.subTest(problem=problem):
                rejected = run.model_copy(deep=True)
                if problem == "missing_review":
                    rejected.findings = [f for f in rejected.findings if f.method != "model_review"]
                elif problem == "active_load":
                    rejected.components[1].kind = "active"
                else:
                    rejected.rails[0].voltage_min = None
                finding = next(f for f in run_checks(rejected) if f.id == "code:voltage:supply:U2")
                self.assertEqual(finding.status, "unknown")
        load.current.value = 200
        finding = next(f for f in run_checks(run) if f.id == "code:current:supply")
        self.assertEqual(finding.status, "fail")
        load.voltage_min = run.rails[0].loads[0].voltage_min.model_copy()
        load.voltage_max = Quantity(value=3.0, unit="V", basis="max", evidence_ids=["spec"])
        finding = next(f for f in run_checks(run) if f.id == "code:voltage:supply:U2")
        self.assertEqual(finding.status, "fail")

    def test_passive_load_drive_needs_review_and_preserves_supplied_limits(self):
        run = example()
        run.components[1].kind = "passive"
        signal = run.signal_checks[0]
        signal.input_high_min = signal.input_low_max = None

        def signal_status(candidate):
            return next(f.status for f in run_checks(candidate) if f.id == "code:signal:U1_to_U2")

        self.assertEqual(signal_status(run), "pass")
        for problem in ("missing_review", "stale_review", "invalid_driver", "active_receiver", "missing_load_source"):
            with self.subTest(problem=problem):
                rejected = run.model_copy(deep=True)
                review = next(f for f in rejected.findings if f.area == "signals")
                if problem == "missing_review":
                    review.subject_ids = ["U1"]
                elif problem == "stale_review":
                    review.revision = 0
                elif problem == "invalid_driver":
                    rejected.signal_checks[0].output_low_max.evidence_ids = ["missing"]
                elif problem == "active_receiver":
                    rejected.components[1].kind = "active"
                else:
                    rejected.evidence[0].component_ids = ["U1"]
                self.assertEqual(signal_status(rejected), "unknown")
        run.evidence[0].component_ids = ["U1"]
        run.components[1].product.parameters = [{"name": "Current - Test", "value": "20mA"}]
        self.assertEqual(signal_status(run), "pass")
        run.evidence[0].component_ids = ["U1", "U2"]
        signal.input_high_min = Quantity(value=3.4, unit="V", basis="min", evidence_ids=["spec"])
        signal.input_low_max = Quantity(value=0.9, unit="V", basis="max", evidence_ids=["spec"])
        self.assertEqual(signal_status(run), "fail")

    def test_partial_review_passes_without_area_coverage_but_absent_review_has_no_verdict(self):
        for findings in ([], [f for f in example().findings if f.area != "support"]):
            with self.subTest(findings=len(findings)):
                run = example()
                run.findings = Review(findings=findings).findings
                refresh_checks(run)
                self.assertEqual(run.compatibility, "checked" if findings else None)
                self.assertEqual([f for f in run.findings if f.method == "model_review"], findings)
                self.assertTrue(any(f.id == "code:review_coverage" and f.status == "unknown" for f in run.findings))

    def test_commodity_catalog_review_does_not_replace_active_evidence(self):
        run = legacy_support_example()
        capacitor = run.components[-1]
        capacitor.product.parameters = [{"name": "Capacitance", "value": "4.7 uF"}]
        self.assertFalse(any(f.id == "code:catalog_source:C1" for f in run_checks(run)))
        run.findings.append(
            Finding(
                id="catalog",
                revision=run.revision,
                area="evidence",
                status="pass",
                subject_ids=["C1"],
                explanation="Supplier Capacitance field meets the 4.7 uF requirement.",
            )
        )
        for kind in ("passive", "connector"):
            capacitor.kind = kind
            refresh_checks(run)
            self.assertEqual(run.compatibility, "checked")
            self.assertTrue(any(f.id == "code:catalog_source:C1" and f.status == "pass" for f in run.findings))
        capacitor.kind = "active"
        self.assertTrue(any(f.id == "code:source:C1" and f.status == "unknown" for f in run_checks(run)))

    def test_open_drain_high_uses_pullup_rail_and_rejects_unknown_rail(self):
        run = example()
        run.evidence[0].fact += "; VIH 2.3 V, VIL 0.9 V, open-drain VOL 0.4 V."
        run.signal_checks = [
            SignalCheck(
                id="sda",
                source_component_id="U1",
                receiver_component_id="U2",
                description="Open-drain SDA",
                pullup_rail_id="supply",
                input_high_min=Quantity(value=2.3, unit="V", basis="min", evidence_ids=["spec"]),
                input_low_max=Quantity(value=0.9, unit="V", basis="max", evidence_ids=["spec"]),
                output_low_max=Quantity(value=0.4, unit="V", basis="max", evidence_ids=["spec"]),
            )
        ]
        for rail_id, voltage, expected in (
            ("supply", 3.3, "pass"),
            ("missing", 3.3, "unknown"),
            ("supply", 1.8, "fail"),
        ):
            run.signal_checks[0].pullup_rail_id = rail_id
            run.rails[0].voltage_min.value = voltage
            finding = next(f for f in run_checks(run) if f.id == "code:signal:sda")
            self.assertEqual(finding.status, expected)

    def test_legacy_support_records_remain_readable_without_new_completeness_checks(self):
        run = legacy_support_example()
        run.components = run.components[:2]
        need = run.support_needs[0]
        need.update(status="unresolved", component_ids=[])
        run = DesignRun.model_validate(run.model_dump())
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.support_needs[0]["status"], "unresolved")
        self.assertTrue(run.source_support_needs)
        self.assertFalse(any(f.method == "code" and f.area == "support" for f in run.findings))

    def test_bom_without_pin_mapping_passes_but_voltage_conflict_fails(self):
        run = example()
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        run.rails[0].loads[1].voltage_max.value = 3.0
        refresh_checks(run)
        self.assertEqual(run.compatibility, "issues_found")
        self.assertTrue(any(f.status == "fail" and "voltage:" in f.id for f in run.findings))

    def test_missing_or_absolute_limit_stays_unknown_without_failing_review(self):
        for change in ("absolute", "uncited", "previous_variant"):
            with self.subTest(change=change):
                run = example()
                operand = run.rails[0].loads[0].voltage_max
                if change == "absolute":
                    operand.basis = "absolute_maximum"
                elif change == "uncited":
                    operand.evidence_ids = []
                else:
                    run.components[0].document_ids = ["replacement_document"]
                refresh_checks(run)
                self.assertEqual(run.compatibility, "checked")
                self.assertTrue(any(f.id == "code:voltage:supply:U1" and f.status == "unknown" for f in run.findings))

    def test_address_collision_fails_until_addresses_are_distinct(self):
        run = example()
        run.interfaces[0].endpoints[1].address = "68"
        refresh_checks(run)
        self.assertEqual(run.compatibility, "issues_found")
        run.interfaces[0].endpoints[1].address = "0x45"
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")

    def test_empty_and_stale_reviews_cannot_pass(self):
        run = DesignRun(original_request="A device", review_completed=True, lifecycle="finished")
        refresh_checks(run)
        self.assertIsNone(run.compatibility)
        self.assertEqual(run.sourcing, "unknown")
        run = example()
        run.revision += 1
        refresh_checks(run)
        self.assertIsNone(run.compatibility)

    def test_external_programmer_assumption_gap_is_nonblocking(self):
        run = example()
        run.interfaces.append(
            Interface(
                id="program",
                protocol="UART",
                configuration="Board programming pads connect to a 3.3 V UART tool",
                evidence_ids=["spec"],
                endpoints=[
                    Endpoint(component_id="U1"),
                    Endpoint(component_id="external", assumption_id="programmer"),
                ],
            )
        )
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertTrue(any(f.id == "code:interface:program" and f.status == "unknown" for f in run.findings))
        run.assumptions.append(
            Assumption(id="programmer", description="External 3.3 V USB/UART programmer attached to board pads")
        )
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")


class StoreTests(unittest.TestCase):
    def test_malformed_supplier_links_leave_a_usable_report_with_unknown_sourcing(self):
        run = example()
        for component in run.components:
            component.product.product_url = "https://[invalid"
            component.product.datasheet_url = "https://[invalid"
            component.product.offers[0].url = "https://[invalid"
        refresh_checks(run)
        row = json.loads(export_json(run))["bom"][0]
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.sourcing, "unknown")
        self.assertEqual(row["availability"], "unknown")
        self.assertIsNone(row["purchase_url"])
        self.assertIsNone(row["datasheet_url"])

    def test_legacy_fields_are_adapted_when_loading_without_regrading(self):
        legacy = legacy_support_example().model_dump()
        legacy["compatibility"] = "incomplete"
        legacy["components"][0]["requirement_ids"] = ["req"]
        legacy["rails"][0]["source_pin"] = "3V3"
        legacy["rails"][0]["loads"][0]["pin"] = "VDD"
        legacy["interfaces"][0]["electrical_basis"] = "manufacturer_guidance"
        legacy["interfaces"][0]["endpoints"][0]["pins"] = ["SDA", "SCL"]
        legacy["regulator_checks"] = [{
            "component_id": "U1", "kind": "linear", "input_rail_id": "supply", "output_rail_id": "supply",
            "dissipation_limit": {"value": 10, "unit": "W"},
        }]
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(directory)
            (Path(directory) / f"{legacy['id']}.json").write_text(json.dumps(legacy), encoding="utf-8")
            saved = store.load(legacy["id"])
        self.assertTrue(saved.review_completed)
        self.assertEqual(saved.support_needs, legacy["support_needs"])
        self.assertEqual(saved.source_support_needs, legacy["source_support_needs"])
        self.assertIsNone(saved.compatibility)
        exported = json.loads(export_json(saved))
        for record, field in (
            (exported["components"][0], "requirement_ids"),
            (exported["rails"][0], "source_pin"),
            (exported["rails"][0]["loads"][0], "pin"),
            (exported["interfaces"][0], "electrical_basis"),
            (exported["interfaces"][0]["endpoints"][0], "pins"),
            (exported["regulator_checks"][0], "dissipation_limit"),
        ):
            self.assertNotIn(field, record)
        self.assertIsNone(exported["compatibility"])
        self.assertIsNone(exported["bom"][0]["review_status"])
        self.assertEqual(next(csv.DictReader(io.StringIO(export_csv(saved))))["review_status"], "")

    def test_candidate_offer_context_rounds_purchase_quantity_and_exposes_packaging(self):
        run = example()
        run.components = run.components[:1]
        run.options.board_quantity = 6
        product = run.components[0].product
        offer = product.offers[0]
        offer.moq, offer.order_multiple, offer.packaging = 10, 4, "Cut Tape (CT)"
        offer.price_breaks.append(PriceBreak(quantity=10, unit_price=1))
        context = product_context(product, quantity=6)["offers"][0]
        row = bom_rows(run)[0]
        self.assertEqual((context["order_quantity"], context["unit_price"], context["extended_price"]), (12, 1, 12))
        self.assertEqual(context["extended_price"], row["extended_price"])
        self.assertEqual(context["order_quantity"], row["order_quantity"])
        self.assertEqual(context["packaging"], "Cut Tape (CT)")

    def test_ordinary_packaging_precedes_custom_reeling_with_unquoted_fee(self):
        run = example()
        run.components = run.components[:1]
        product = run.components[0].product
        offer = product.offers[0]
        cut = offer.model_copy(
            update={
                "sku": "CT",
                "packaging": "Cut Tape (CT)",
                "price_breaks": [PriceBreak(quantity=1, unit_price=0.11)],
            }
        )
        custom = offer.model_copy(
            update={"sku": "DKR", "packaging": "Digi-Reel®", "price_breaks": [PriceBreak(quantity=1, unit_price=0.10)]}
        )
        product.offers = [custom, cut]
        row = bom_rows(run)[0]
        self.assertEqual((row["supplier_sku"], row["extended_price"]), ("CT", 0.11))
        self.assertNotIn("setup fee", row["ordering_note"])
        product.offers = [custom]
        row = bom_rows(run)[0]
        self.assertEqual((row["supplier_sku"], row["availability"]), ("DKR", "available"))
        self.assertIn("exclude any custom-reeling/setup fee", row["ordering_note"])
        product.offers.append(cut.model_copy(update={"sku": "TR", "packaging": "Tape & Reel (TR)"}))
        self.assertEqual(bom_rows(run)[0]["supplier_sku"], "TR")

    def test_reasoning_context_keeps_actionable_gaps_without_repeating_passes(self):
        run = example()
        issue = Finding(
            id="missing",
            revision=run.revision,
            area="power",
            status="unknown",
            subject_ids=["U1"],
            explanation="Operating current needs a source",
        )
        run.findings.append(issue)
        context = design_context(run)
        self.assertEqual([finding["id"] for finding in context["findings"]], ["missing"])
        self.assertEqual(context["evidence"], run.model_dump()["evidence"])
        self.assertEqual(len(run.findings), len(REVIEW_AREAS) + 1)
        self.assertNotIn("offers", context["components"][0]["product"])
        self.assertTrue(run.components[0].product.offers)
        self.assertTrue(run.components[0].product.retrieved_at)

    def test_model_context_uses_actual_purchasing_quantities(self):
        run = example()
        self.assertEqual(design_context(run)["purchasing_bom"][0]["extended_price"], 4)
        run.options.board_quantity = 10
        context = design_context(run)
        self.assertEqual(context["purchasing_options"]["board_quantity"], 10)
        self.assertEqual(context["purchasing_bom"][0]["extended_price"], 40)
        for component in run.components:
            component.product.offers[0].order_multiple = 100
        row = design_context(run)["purchasing_bom"][0]
        self.assertEqual((row["required_quantity"], row["order_quantity"], row["extended_price"]), (20, 100, 200))
        self.assertEqual(row["extended_price"], bom_rows(run)[0]["extended_price"])

    def test_bom_quantities_prices_unknowns_and_csv(self):
        run = example()
        run.options.board_quantity = 3
        for component in run.components:
            component.product.manufacturer = "=Example"
            offer = component.product.offers[0]
            offer.moq = 10
            offer.order_multiple = 4
            offer.price_breaks.append(PriceBreak(quantity=10, unit_price=1))
        refresh_checks(run)
        row = bom_rows(run)[0]
        self.assertEqual(
            (row["installed_quantity"], row["required_quantity"], row["order_quantity"], row["extended_price"]),
            (2, 6, 12, 12),
        )
        self.assertEqual(run.sourcing, "available")
        exported = list(csv.DictReader(io.StringIO(export_csv(run))))
        self.assertEqual(exported[0]["manufacturer"], "'=Example")
        report = json.loads(export_json(run))
        self.assertEqual(report["id"], run.id)
        self.assertEqual(report["bom"], bom_rows(run))
        self.assertEqual(int(exported[0]["order_quantity"]), report["bom"][0]["order_quantity"])
        for component in run.components:
            component.product.offers[0].price_breaks = []
        refresh_checks(run)
        self.assertIsNone(bom_rows(run)[0]["extended_price"])
        self.assertEqual(run.sourcing, "unknown")

    def test_save_load_restart_and_invalid_id(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(directory)
            run = example()
            run.lifecycle = "running"
            store.save(run)
            self.assertEqual(store.load(run.id).original_request, "Two sensors")
            self.assertEqual(store.interrupt_unfinished(), 1)
            self.assertEqual(store.load(run.id).lifecycle, "interrupted")
            self.assertIsNone(store.load(run.id).compatibility)
            with self.assertRaises(ValueError):
                store.load("../outside")


class ThermalCheckTests(unittest.TestCase):
    def make_run(self):
        run = example()
        run.assumptions.append(Assumption(id="workload", description="100 mA sustained output with 400 mA short peaks"))
        run.assumptions.append(Assumption(id="thermal", description="70 degC ambient and 100 degC junction target"))
        run.evidence[0].fact = (
            "Fixture regulator supplies 3.3 V at 300 mA; load peak is 400 mA; typical package theta_JA is 100 degC/W."
        )

        def q(value, unit="V"):
            return Quantity(value=value, unit=unit, basis="max", evidence_ids=["spec"])

        run.rails = [
            Rail(
                id="input",
                source_component_id="external",
                description="Fixture 5 V input",
                voltage_min=Quantity(value=5, unit="V", basis="estimate", assumption_id="supply"),
                voltage_max=Quantity(value=5, unit="V", basis="estimate", assumption_id="supply"),
                available_current=Quantity(value=1, unit="A", basis="estimate", assumption_id="supply"),
                loads=[PowerLoad(component_id="U1", voltage_min=q(2.5), voltage_max=q(6), current=q(0.4, "A"))],
            ),
            Rail(
                id="output",
                source_component_id="U1",
                description="Fixture regulator output",
                voltage_min=q(3.3),
                voltage_max=q(3.3),
                available_current=q(0.3, "A"),
                loads=[PowerLoad(component_id="U2", voltage_min=q(2.7), voltage_max=q(3.6), current=q(0.4, "A"))],
            ),
        ]
        run.regulator_checks = [
            RegulatorCheck(
                component_id="U1",
                kind="linear",
                input_rail_id="input",
                output_rail_id="output",
                dropout=q(0.2),
                ambient_max=Quantity(value=70, unit="degC", basis="estimate", assumption_id="thermal"),
                junction_target=Quantity(value=100, unit="degC", basis="estimate", assumption_id="thermal"),
                theta_ja=Quantity(value=100, unit="degC/W", basis="typical", evidence_ids=["spec"]),
            )
        ]
        return run

    def test_thermal_allowance_is_calculated_from_temperature_and_package(self):
        run = self.make_run()
        regulator = run.regulator_checks[0]
        regulator.ambient_max.value, regulator.junction_target.value, regulator.theta_ja.value = 55, 125, 125
        run.rails[0].voltage_max.value = 5.4
        finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
        self.assertEqual(finding.status, "fail")
        self.assertIn("dissipation 0.84 W", finding.explanation)
        self.assertIn("(125 - 55) / 125 = 0.56 W", finding.explanation)

    def test_thermal_operands_need_package_evidence_and_valid_headroom(self):
        run = self.make_run()
        regulator = run.regulator_checks[0]
        regulator.theta_ja.evidence_ids, regulator.theta_ja.assumption_id = [], "thermal"

        def thermal_status():
            return next(f.status for f in run_checks(run) if f.id == "code:dissipation:U1")

        self.assertEqual(thermal_status(), "unknown")
        regulator.theta_ja.evidence_ids, regulator.theta_ja.value = ["spec"], 0
        self.assertEqual(thermal_status(), "unknown")
        regulator.theta_ja = None
        self.assertEqual(thermal_status(), "unknown")
        regulator.ambient_max = regulator.junction_target = None
        self.assertEqual(thermal_status(), "unknown")

    def test_average_thermal_load_does_not_reduce_peak_capacity_check(self):
        run = self.make_run()
        findings = {f.id: f for f in run_checks(run)}
        self.assertEqual(findings["code:dissipation:U1"].status, "fail")
        self.assertIn("peak load", findings["code:dissipation:U1"].explanation)
        run.regulator_checks[0].average_output_current = Quantity(
            value=100, unit="mA", basis="estimate", assumption_id="workload"
        )
        findings = {f.id: f for f in run_checks(run)}
        self.assertEqual(findings["code:dissipation:U1"].status, "pass")
        self.assertIn("average output current 0.1 A", findings["code:dissipation:U1"].explanation)
        self.assertEqual(findings["code:current:output"].status, "fail")

    def test_average_thermal_load_needs_valid_basis_and_peak_bounds(self):
        for value, unit, assumption, expected in (
            (-0.1, "A", "workload", "unknown"),
            (0.5, "A", "workload", "unknown"),
            (0.1, "A", None, "unknown"),
            (0.1, "W", "workload", "unknown"),
        ):
            with self.subTest(value=value, unit=unit, assumption=assumption):
                run = self.make_run()
                run.regulator_checks[0].average_output_current = Quantity(
                    value=value, unit=unit, basis="estimate", assumption_id=assumption
                )
                finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
                self.assertEqual(finding.status, expected)
        run = self.make_run()
        run.evidence.append(run.evidence[0].model_copy(update={"id": "reg_only", "component_ids": ["U1"]}))
        run.regulator_checks[0].average_output_current = Quantity(
            value=0.1, unit="A", basis="typical", evidence_ids=["reg_only"]
        )
        finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
        self.assertEqual(finding.status, "unknown")


if __name__ == "__main__":
    unittest.main()
