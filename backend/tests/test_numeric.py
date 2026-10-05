"""Source binding and the small calculations that connect existing BOM checks."""

import unittest

from checks import refresh_checks
from fakes import example
from models import Assumption, PowerLoad, Quantity, Rail, RegulatorCheck, SourceNumber


def number(key, role, value, unit, basis, **kwargs):
    return SourceNumber(id=key, role=role, value=value, unit=unit, basis=basis, **kwargs)


def sourced(key, **kwargs):
    return Quantity(source_ids=[key], **kwargs)


def regulator_example():
    run = example()
    run.numeric_binding_version = 1
    run.evidence[0].component_ids.append("U3")
    run.evidence[0].numbers.extend([
        number("out", "output_voltage", 3.3, "V", "nominal"),
        number("tolerance", "output_tolerance", 2, "%", "max"),
        number("line", "output_tolerance", 10, "mV", "max"),
        number("capacity", "output_current", 1, "A", "max"),
        number("vin", "operating_voltage", 6, "V", "max"),
        number("drop", "dropout", 0.3, "V", "max"),
        number("thermal", "theta_ja", 125, "degC/W", "typical", conditions="SOT223 without heatsink"),
        number("own", "quiescent_current", 6, "mA", "max"),
    ])
    run.components.append(run.components[0].model_copy(update={"id": "U3", "kind": "active"}))
    output = run.rails[0]
    output.source_component_id = "U3"
    output.voltage_min = Quantity(calculation="output_min", source_ids=["out", "tolerance", "line"])
    output.voltage_max = Quantity(calculation="output_max", source_ids=["out", "tolerance", "line"])
    output.available_current = sourced("capacity")
    run.rails.insert(0, Rail(
        id="usb", source_component_id="external", description="USB supply",
        voltage_min=Quantity(value=4.75, unit="V", assumption_id="supply"),
        voltage_max=Quantity(value=5.25, unit="V", assumption_id="supply"),
        available_current=Quantity(value=0.5, unit="A", assumption_id="supply"),
        loads=[PowerLoad(component_id="U3", voltage_min=Quantity(calculation="input_min"),
                         voltage_max=sourced("vin"), current=Quantity(calculation="linear_input"))],
    ))
    run.regulator_checks = [RegulatorCheck(
        component_id="U3", kind="linear", input_rail_id="usb", output_rail_id="supply",
        dropout=sourced("drop"), quiescent_current=sourced("own"), theta_ja=sourced("thermal"),
        ambient_max=Quantity(value=50, unit="degC", assumption_id="supply"),
        junction_target=Quantity(value=110, unit="degC", assumption_id="supply"),
    )]
    return run


class NumericTests(unittest.TestCase):
    def test_voltage_reference_repair_uses_one_existing_owner_parameter_bound(self):
        run = example()
        run.numeric_binding_version = 1
        high = run.signal_checks[0].input_high_min = sourced("mistyped-id", value=9, unit="V")
        maximum = run.rails[0].loads[0].voltage_max = sourced("spec")
        refresh_checks(run)
        self.assertEqual((high.source_ids, high.value, high.binding_error), (["specN4"], 2.3, ""))
        self.assertEqual((maximum.source_ids, maximum.value, maximum.binding_error), (["specN2"], 3.6, ""))

    def test_voltage_reference_repair_does_not_choose_between_limits_or_replace_known_ids(self):
        run = example()
        run.numeric_binding_version = 1
        high = run.signal_checks[0].input_high_min = sourced("mistyped-id")
        run.evidence[0].numbers.append(number("other-high", "input_high", 2.5, "V", "min"))
        refresh_checks(run)
        self.assertTrue(high.binding_error)
        high.source_ids = ["specN3"]  # A real current fact is not a mistyped voltage reference.
        refresh_checks(run)
        self.assertTrue(high.binding_error)

    def test_active_sensor_supply_current_can_be_named_quiescent_current(self):
        run = regulator_example()
        run.evidence[0].numbers.append(number(
            "sensor-current", "quiescent_current", 3.7, "μA", "typical", conditions="Active full-scale measurement",
        ))
        load = run.rails[1].loads[0]
        load.current = sourced("sensor-current")
        refresh_checks(run)
        self.assertEqual(load.current.binding_error, "")
        self.assertAlmostEqual(load.current.value, .0000037)
        self.assertIn("Active full-scale measurement", load.current.source_conditions)
        self.assertAlmostEqual(run.rails[0].loads[0].current.value, .0160037)

    def test_converter_own_current_cannot_replace_switching_input_demand(self):
        run = regulator_example()
        run.regulator_checks[0].kind = "switching"
        current = run.rails[0].loads[0].current = sourced("own")
        refresh_checks(run)
        self.assertTrue(current.binding_error)
        run.regulator_checks = []
        refresh_checks(run)
        self.assertTrue(current.binding_error)

    def test_source_demand_cannot_be_rewritten_or_renamed_output_capacity(self):
        run = example()
        run.numeric_binding_version = 1
        run.evidence[0].numbers.append(number("peak", "input_current", 379, "mA", "max"))
        current = run.rails[0].loads[0].current = sourced("peak", value=250, unit="mA", basis="max")
        refresh_checks(run)
        self.assertAlmostEqual(current.value, .379)
        self.assertEqual(current.unit, "A")
        current.value, current.basis, current.assumption_id = .25, "estimate", "supply"
        refresh_checks(run)
        self.assertIn("below its documented source demand", current.binding_error)
        run.evidence[0].numbers.append(number("required", "supply_current_required", .5, "A", "min"))
        run.rails[0].source_component_id = "U1"
        run.rails[0].available_current = sourced("required")
        refresh_checks(run)
        self.assertIn("output_current", run.rails[0].available_current.binding_error)

    def test_supply_scaled_thresholds_use_opposite_worst_case_corners(self):
        run = example()
        run.numeric_binding_version = 1
        run.rails[0].voltage_min.value, run.rails[0].voltage_max.value = 3.2, 3.4
        run.evidence[0].numbers.extend([
            number("vih", "input_high", 0, "V", "min", supply_factor=.75),
            number("vil", "input_low", 0, "V", "max", supply_factor=.25),
            number("vol", "output_low", 0, "V", "max", supply_factor=.1),
        ])
        signal = run.signal_checks[0]
        signal.input_high_min, signal.input_low_max, signal.output_low_max = map(sourced, ("vih", "vil", "vol"))
        signal.input_high_min.calculation = "output_min"  # Historical authored labels cannot change the corner.
        refresh_checks(run)
        self.assertAlmostEqual(signal.input_high_min.value, 2.55)
        self.assertAlmostEqual(signal.input_low_max.value, .8)
        self.assertAlmostEqual(signal.output_low_max.value, .34)

    def test_output_headroom_current_and_heat_reuse_bound_operands(self):
        run = regulator_example()
        refresh_checks(run)
        source, output = run.rails
        self.assertAlmostEqual(output.voltage_min.value, 3.224)
        self.assertAlmostEqual(output.voltage_max.value, 3.376)
        self.assertAlmostEqual(source.loads[0].voltage_min.value, 3.676)
        self.assertAlmostEqual(source.loads[0].current.value, .026)
        thermal = next(f for f in run.findings if f.id == "code:dissipation:U3")
        self.assertIn("0.07202 W", thermal.explanation)
        self.assertIn("SOT223 without heatsink", run.regulator_checks[0].theta_ja.source_conditions)
        self.assertEqual(thermal.status, "pass")
        # Recomputing is stable; no repeated tolerance or current accumulation.
        before = run.model_dump()
        refresh_checks(run)
        self.assertEqual(run.model_dump(), before)

    def test_unbound_device_rating_remains_unknown_without_failing_review(self):
        run = example()
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        run.numeric_binding_version = 1
        run.rails[0].loads[0].voltage_max.source_ids = []
        refresh_checks(run)
        self.assertEqual(run.compatibility, "checked")
        self.assertIn("Reference one documented", run.rails[0].loads[0].voltage_max.binding_error)
        self.assertTrue(any(f.id == "code:voltage:supply:U1" and f.status == "unknown" for f in run.findings))

    def test_linear_input_cannot_bypass_downstream_demand_with_no_load_rating(self):
        run = regulator_example()
        run.evidence[0].numbers.append(number("no-load", "input_current", 6, "mA", "typical"))
        run.rails[0].available_current.value = .01
        run.rails[0].loads[0].current = sourced("no-load")
        refresh_checks(run)
        self.assertAlmostEqual(run.rails[0].loads[0].current.value, .026)
        self.assertEqual(next(f.status for f in run.findings if f.id == "code:current:usb"), "fail")

    def test_signed_lower_tolerance_is_resolved_without_changing_its_source(self):
        run = regulator_example()
        tolerance = next(n for n in run.evidence[0].numbers if n.id == "tolerance")
        tolerance.value, tolerance.basis = -2, "min"
        refresh_checks(run)
        self.assertAlmostEqual(run.rails[1].voltage_min.value, 3.224)
        self.assertEqual(run.rails[1].voltage_min.binding_error, "")
        self.assertEqual(tolerance.value, -2)
        self.assertTrue(run.rails[1].voltage_max.binding_error)

    def test_declared_output_window_widens_source_bounds_without_rewriting_ratings(self):
        run = regulator_example()
        run.assumptions.append(Assumption(id="window", description="Use 3.2–3.4 V to include load/line/temperature margin."))
        tolerance = next(n for n in run.evidence[0].numbers if n.id == "tolerance")
        tolerance.conditions = "Initial accuracy at light load"
        source_before = run.evidence[0].model_dump()
        output = run.rails[1]
        for quantity, value, unit in ((output.voltage_min, 3.2, "V"), (output.voltage_max, 3400, "mV")):
            quantity.value, quantity.unit, quantity.assumption_id = value, unit, "window"
        receiver_max = output.loads[0].voltage_max
        receiver_max.value, receiver_max.assumption_id = 9, "window"
        refresh_checks(run)
        self.assertEqual((output.voltage_min.value, output.voltage_max.value), (3.2, 3.4))
        self.assertEqual(output.voltage_min.basis, "estimate")
        self.assertIn("Initial accuracy at light load", output.voltage_min.source_conditions)
        self.assertEqual(receiver_max.value, 3.6)
        self.assertEqual(run.evidence[0].model_dump(), source_before)
        before = run.model_dump()
        refresh_checks(run)
        self.assertEqual(run.model_dump(), before)

    def test_output_window_cannot_narrow_or_replace_source_bounds(self):
        for side, changes in (
            ("min", {"value": 3.3}),
            ("max", {"value": 3.3}),
            ("min", {"assumption_id": "missing"}),
            ("min", {"unit": ""}),
            ("min", {"source_ids": []}),
            ("min", {"source_ids": ["out"]}),
        ):
            with self.subTest(side=side, changes=changes):
                run = regulator_example()
                quantity = getattr(run.rails[1], f"voltage_{side}")
                for key, value in {"value": 3.2, "unit": "V", "assumption_id": "supply", **changes}.items():
                    setattr(quantity, key, value)
                refresh_checks(run)
                self.assertTrue(quantity.binding_error)

    def test_regulator_own_current_cannot_discard_an_available_source(self):
        run = regulator_example()
        run.rails[0].available_current.value = .023
        own = run.regulator_checks[0].quiescent_current = Quantity(value=0, unit="A", assumption_id="supply")
        refresh_checks(run)
        self.assertIn("Documented regulator own current", own.binding_error)
        own.source_ids, own.assumption_id = ["own"], None
        refresh_checks(run)
        self.assertAlmostEqual(run.rails[0].loads[0].current.value, .026)
        self.assertEqual(next(f.status for f in run.findings if f.id == "code:current:usb"), "fail")
        run.evidence[0].numbers = [n for n in run.evidence[0].numbers if n.id != "own"]
        own.source_ids, own.assumption_id, own.value = [], "supply", .002
        refresh_checks(run)
        self.assertEqual(own.binding_error, "")
        self.assertAlmostEqual(run.rails[0].loads[0].current.value, .022)

    def test_declared_average_current_margin_is_not_reduced_to_its_source_value(self):
        run = regulator_example()
        average = run.regulator_checks[0].average_output_current = Quantity(
            value=15, unit="mA", source_ids=["specN3"], assumption_id="supply",
        )
        refresh_checks(run)
        self.assertEqual(average.binding_error, "")
        self.assertEqual(average.basis, "estimate")
        self.assertAlmostEqual(average.value, .015)
        refresh_checks(run)
        self.assertAlmostEqual(average.value, .015)

    def test_source_average_current_is_for_thermal_screening_not_peak_capacity(self):
        run = regulator_example()
        run.evidence[0].numbers.extend([
            number("radio-peak", "input_current", 379, "mA", "typical"),
            number("radio-average", "average_current", 239, "mA", "typical"),
        ])
        load = run.rails[1].loads[0]
        load.current = sourced("radio-average")
        average = run.regulator_checks[0].average_output_current = sourced("radio-average")
        refresh_checks(run)
        self.assertTrue(load.current.binding_error)
        self.assertEqual(average.binding_error, "")
        self.assertAlmostEqual(average.value, .239)
        load.current = sourced("radio-peak")
        refresh_checks(run)
        self.assertEqual(load.current.binding_error, "")
        self.assertAlmostEqual(load.current.value, .379)

    def test_supply_assumption_accepts_evidence_context_but_device_ratings_do_not(self):
        run = regulator_example()
        run.evidence[0].conditions = "Fixture power source context"
        supply = run.rails[0].available_current
        supply.source_ids = ["spec"]
        refresh_checks(run)
        self.assertEqual(supply.binding_error, "")
        self.assertEqual(supply.value, .5)
        self.assertEqual(supply.evidence_ids, ["spec"])
        self.assertIn("Fixture power source context", supply.source_conditions)
        current = run.rails[1].loads[0].current
        current.source_ids = ["spec"]
        refresh_checks(run)
        self.assertTrue(current.binding_error)

    def test_input_min_accepts_redundant_relationship_refs_without_losing_vin_limit(self):
        run = regulator_example()
        minimum = run.rails[0].loads[0].voltage_min
        refresh_checks(run)
        baseline = minimum.value
        minimum.source_ids = ["out", "tolerance", "drop"]
        refresh_checks(run)
        self.assertEqual(minimum.binding_error, "")
        self.assertEqual(minimum.value, baseline)
        next(n for n in run.evidence[0].numbers if n.id == "specN1").value = 4.2
        refresh_checks(run)
        self.assertEqual(minimum.value, 4.2)
        run.evidence.append(run.evidence[0].model_copy(update={
            "id": "other", "component_ids": ["U1"],
            "numbers": [number("other-output", "output_voltage", 3.3, "V", "nominal")],
        }))
        for reference in ("missing", "capacity", "other-output"):
            minimum.source_ids = [reference]
            refresh_checks(run)
            self.assertTrue(minimum.binding_error, reference)

    def test_assumed_usb_contract_retains_its_range_and_current_with_context_refs(self):
        run = regulator_example()
        run.components.append(run.components[0].model_copy(update={"id": "J1", "kind": "connector"}))
        run.evidence.append(run.evidence[0].model_copy(update={
            "id": "usb-guide", "component_ids": ["J1"], "numbers": [
                number("usb-nominal", "operating_voltage", 5, "V", "nominal", conditions="USB power context"),
                number("connector-current", "output_current", 3, "A", "max"),
            ],
        }))
        rail = run.rails[0]
        rail.voltage_min.source_ids = rail.voltage_max.source_ids = ["usb-nominal"]
        rail.available_current.source_ids = ["connector-current"]
        for owner in ("J1", "external"):
            rail.source_component_id = owner
            refresh_checks(run)
            self.assertEqual((rail.voltage_min.value, rail.voltage_max.value, rail.available_current.value), (4.75, 5.25, .5))
            self.assertEqual(rail.voltage_min.binding_error, "")
            self.assertIn("USB power context", rail.voltage_min.source_conditions)
        rail.source_component_id = "U3"
        refresh_checks(run)
        self.assertTrue(rail.voltage_min.binding_error)
        self.assertTrue(rail.available_current.binding_error)
        rail.source_component_id = "J1"
        rail.voltage_min.source_ids = ["specN1"]
        run.evidence[0].numbers.append(number("load-supply", "supply_current_required", .5, "A", "min"))
        rail.available_current.source_ids = ["load-supply"]
        refresh_checks(run)
        self.assertEqual(rail.voltage_min.binding_error, "")
        self.assertEqual(rail.available_current.binding_error, "")
        run.evidence.append(run.evidence[0].model_copy(update={
            "id": "off-bom", "component_ids": ["UNKNOWN"],
            "numbers": [number("off-bom-voltage", "output_voltage", 5, "V", "nominal")],
        }))
        for reference in ("missing", "off-bom-voltage", "connector-current"):
            rail.voltage_min.source_ids = [reference]
            refresh_checks(run)
            self.assertTrue(rail.voltage_min.binding_error)


if __name__ == "__main__":
    unittest.main()
