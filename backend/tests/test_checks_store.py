"""Deterministic core examples; no model or supplier calls."""

import csv
import io
import json
import tempfile
import unittest

from checks import refresh_checks as evaluate
from checks import run_checks
from fakes import example, supported_example
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
    Review,
    SignalCheck,
    SupportNeed,
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

    def test_legacy_pin_data_is_readable_but_not_requested_or_reported(self):
        for model, data, field in (
            (PowerLoad, {"component_id": "U1", "pin": "VDD"}, "pin"),
            (
                Rail,
                {"id": "supply", "source_component_id": "external", "description": "Supply", "source_pin": "3V3"},
                "source_pin",
            ),
            (Endpoint, {"component_id": "U1", "pins": ["SDA", "SCL"]}, "pins"),
        ):
            with self.subTest(field=field):
                record = model.model_validate(data)
                self.assertEqual(getattr(record, field), data[field])
                self.assertNotIn(field, record.model_dump())
                self.assertNotIn(field, model.model_json_schema()["properties"])

    def test_partial_review_is_retained_but_cannot_pass_missing_coverage(self):
        for findings in ([], [f for f in example().findings if f.area != "support"]):
            with self.subTest(findings=len(findings)):
                run = example()
                run.findings = Review(findings=findings).findings
                evaluate(run)
                self.assertEqual(run.compatibility, "incomplete")
                self.assertEqual([f for f in run.findings if f.method == "model_review"], findings)
                self.assertTrue(any(f.id == "code:review_coverage" and f.status == "unknown" for f in run.findings))

    def test_commodity_catalog_review_does_not_replace_active_or_support_evidence(self):
        run = supported_example()
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
            evaluate(run)
            self.assertEqual(run.compatibility, "checked")
            self.assertTrue(any(f.id == "code:catalog_source:C1" and f.status == "pass" for f in run.findings))
        run.support_needs = []
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")
        self.assertTrue(any(f.id == "code:source_support:D1S1" and f.status == "unknown" for f in run.findings))
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

    def test_source_required_support_cannot_be_omitted_or_downgraded(self):
        run = supported_example()
        evaluate(run)
        self.assertEqual(run.compatibility, "checked")
        for change in ("omit", "optional", "included", "not_applicable"):
            with self.subTest(change=change):
                run = supported_example()
                if change == "omit":
                    run.support_needs = []
                elif change == "optional":
                    run.support_needs[0].necessity = "optional"
                else:
                    run.support_needs[0].status = change
                    run.support_needs[0].explanation = "Circuit claims no external component is needed"
                evaluate(run)
                self.assertEqual(run.compatibility, "incomplete")
                self.assertTrue(any(f.id == "code:source_support:D1S1" and f.status == "unknown" for f in run.findings))
        run = supported_example()
        run.support_needs[0].component_ids = []
        finding = next(f for f in run_checks(run) if f.id == "code:source_support:D1S1")
        self.assertEqual(finding.status, "unknown")
        self.assertIn(run.source_support_needs[0].purpose, finding.explanation)
        self.assertIn("no purchased component IDs", finding.explanation)

    def test_declining_recommended_support_requires_current_review(self):
        run = supported_example()
        run.source_support_needs[0].necessity = "recommended"
        run.components = run.components[:2]
        need = run.support_needs[0]
        need.necessity, need.status, need.component_ids = "recommended", "not_applicable", []
        need.explanation = (
            "The documented external supply already provides the recommended local bypass at these test terminals."
        )
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")
        run.findings.append(
            Finding(
                id="decline",
                revision=run.revision,
                area="support",
                status="pass",
                subject_ids=["D1S1"],
                evidence_ids=["spec"],
                explanation="Fixture review accepts the stated supply arrangement",
            )
        )
        evaluate(run)
        self.assertEqual(run.compatibility, "checked")

    def test_source_support_requires_current_owner_and_real_source_refs(self):
        for change in ("uncited", "wrong_owner"):
            with self.subTest(change=change):
                run = supported_example()
                if change == "uncited":
                    run.source_support_needs[0].evidence_ids = ["missing"]
                else:
                    run.source_support_needs[0].parent_ids = ["removed_part"]
                evaluate(run)
                self.assertEqual(run.compatibility, "incomplete")
                self.assertTrue(
                    any(
                        f.id == "code:source_support:D1S1" and f.status == "unknown" and f.area == "evidence"
                        for f in run.findings
                    )
                )

    def test_bom_without_pin_mapping_passes_but_voltage_conflict_fails(self):
        run = example()
        evaluate(run)
        self.assertEqual(run.compatibility, "checked")
        run.rails[0].loads[1].voltage_max.value = 3.0
        evaluate(run)
        self.assertEqual(run.compatibility, "issues_found")
        self.assertTrue(any(f.status == "fail" and "voltage:" in f.id for f in run.findings))

    def test_missing_or_absolute_limit_is_unknown_not_approved(self):
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
                evaluate(run)
                self.assertEqual(run.compatibility, "incomplete")

    def test_address_collision_and_required_support(self):
        run = example()
        run.interfaces[0].endpoints[1].address = "68"
        evaluate(run)
        self.assertEqual(run.compatibility, "issues_found")
        run.interfaces[0].endpoints[1].address = "0x45"
        run.support_needs = [
            SupportNeed(
                id="bypass",
                purpose="Bypass",
                parent_ids=["U1"],
                necessity="required",
                status="unresolved",
                connections="VDD to GND",
                evidence_ids=["spec"],
            )
        ]
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")

    def test_empty_and_stale_reviews_cannot_pass(self):
        run = DesignRun(original_request="A device", review_completed=True, lifecycle="finished")
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")
        self.assertEqual(run.sourcing, "unknown")
        run = example()
        run.revision += 1
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")

    def test_external_programmer_needs_explicit_assumption(self):
        run = example()
        run.interfaces.append(
            Interface(
                id="program",
                protocol="UART",
                configuration="Board programming pads connect to a 3.3 V UART tool",
                evidence_ids=["spec"],
                endpoints=[
                    Endpoint(component_id="U1", pins=["TX", "RX"]),
                    Endpoint(component_id="external", pins=["RX", "TX"], assumption_id="programmer"),
                ],
            )
        )
        evaluate(run)
        self.assertEqual(run.compatibility, "incomplete")
        run.assumptions.append(
            Assumption(id="programmer", description="External 3.3 V USB/UART programmer attached to board pads")
        )
        evaluate(run)
        self.assertEqual(run.compatibility, "checked")


class StoreTests(unittest.TestCase):
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
        evaluate(run)
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
        evaluate(run)
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
            with self.assertRaises(ValueError):
                store.load("../outside")


class ThermalCheckTests(unittest.TestCase):
    def fixture(self):
        from models import RegulatorCheck

        run = example()
        run.assumptions.append(Assumption(id="workload", description="100 mA sustained output with 400 mA short peaks"))
        run.assumptions.append(Assumption(id="thermal", description="70 degC ambient and 100 degC junction target"))
        run.evidence[
            0
        ].fact = (
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

    def test_thermal_allowance_is_calculated_not_taken_from_model_scalar(self):
        run = self.fixture()
        regulator = run.regulator_checks[0]
        regulator.ambient_max.value, regulator.junction_target.value, regulator.theta_ja.value = 55, 125, 125
        run.rails[0].voltage_max.value = 5.4
        regulator.dissipation_limit = Quantity(value=0.84, unit="W", basis="estimate", assumption_id="thermal")
        finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
        self.assertEqual(finding.status, "fail")
        self.assertIn("dissipation 0.84 W", finding.explanation)
        self.assertIn("(125 - 55) / 125 = 0.56 W", finding.explanation)
        self.assertNotIn("dissipation_limit", type(regulator).model_json_schema()["properties"])

    def test_thermal_operands_need_package_evidence_and_valid_headroom(self):
        run = self.fixture()
        regulator = run.regulator_checks[0]
        regulator.dissipation_limit = Quantity(value=10, unit="W", basis="estimate", assumption_id="thermal")
        regulator.theta_ja.evidence_ids, regulator.theta_ja.assumption_id = [], "thermal"

        def thermal_status():
            return next(f.status for f in run_checks(run) if f.id == "code:dissipation:U1")

        self.assertEqual(thermal_status(), "unknown")
        regulator.theta_ja.evidence_ids, regulator.theta_ja.value = ["spec"], 0
        self.assertEqual(thermal_status(), "fail")
        regulator.theta_ja = None
        self.assertEqual(thermal_status(), "unknown")
        regulator.ambient_max = regulator.junction_target = None
        self.assertEqual(thermal_status(), "unknown")

    def test_average_thermal_load_does_not_reduce_peak_capacity_check(self):
        run = self.fixture()
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
            (-0.1, "A", "workload", "fail"),
            (0.5, "A", "workload", "fail"),
            (0.1, "A", None, "unknown"),
            (0.1, "W", "workload", "unknown"),
        ):
            with self.subTest(value=value, unit=unit, assumption=assumption):
                run = self.fixture()
                run.regulator_checks[0].average_output_current = Quantity(
                    value=value, unit=unit, basis="estimate", assumption_id=assumption
                )
                finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
                self.assertEqual(finding.status, expected)
        run = self.fixture()
        run.evidence.append(run.evidence[0].model_copy(update={"id": "reg_only", "component_ids": ["U1"]}))
        run.regulator_checks[0].average_output_current = Quantity(
            value=0.1, unit="A", basis="typical", evidence_ids=["reg_only"]
        )
        finding = next(f for f in run_checks(run) if f.id == "code:dissipation:U1")
        self.assertEqual(finding.status, "unknown")


if __name__ == "__main__":
    unittest.main()
