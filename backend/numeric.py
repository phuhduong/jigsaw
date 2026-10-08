"""Bind the existing compatibility operands to source-owned numbers."""

from __future__ import annotations

from collections import Counter
from math import isclose

from models import DesignRun, Evidence

_UNITS = {
    "V": ("V", 1), "mV": ("V", .001),
    "A": ("A", 1), "mA": ("A", .001), "uA": ("A", .000001), "µA": ("A", .000001), "μA": ("A", .000001),
    "degC": ("degC", 1), "°C": ("degC", 1), "C": ("degC", 1),
    "degC/W": ("degC/W", 1), "°C/W": ("degC/W", 1), "C/W": ("degC/W", 1), "K/W": ("degC/W", 1),
    "%": ("%", 1),
}


def convert_value(value: float, unit: str, expected: str) -> float:
    """Normalize compatible units, rejecting unsupported or mismatched dimensions."""
    conversion = _UNITS.get(unit)
    if conversion is None or conversion[0] != expected:
        raise ValueError(f"Expected {expected}, not {unit!r}.")
    return value * conversion[1]


def bind_quantities(run: DesignRun, evidence: dict[str, Evidence]) -> None:
    """Materialize numbers without allowing assembly to rewrite their source values."""
    if not run.numeric_binding_version:
        return
    source_entries = [(number.id, item, number) for item in evidence.values() for number in item.numbers]
    duplicates = {key for key, count in Counter(key for key, _, _ in source_entries).items() if count > 1}
    sources = {key: (item, number) for key, item, number in source_entries if key not in duplicates}
    components = {component.id: component for component in run.components}
    rails = {rail.id: rail for rail in run.rails}
    regulators = {item.component_id: item for item in run.regulator_checks}
    assumptions = {item.id for item in run.assumptions}
    resolved, resolving = set(), set()

    def source_records(source_ids, owner, roles):
        owners = {owner} if isinstance(owner, str) else set(owner)
        result = []
        for key in source_ids:
            if key not in sources:
                raise ValueError(f"Source number {key!r} is missing, duplicated or invalid; use a current source number ID.")
            item, number = sources[key]
            if not owners.intersection(item.component_ids) or number.role not in roles:
                raise ValueError(f"{key} is {number.role} for {', '.join(item.component_ids)}, not {sorted(roles)} for {', '.join(sorted(owners))}.")
            if number.basis in {"absolute_maximum", "estimate"}:
                raise ValueError(f"{key} has basis {number.basis}, not a documented operating specification.")
            result.append((item, number))
        return result

    def set_bound_value(quantity, value, unit, basis, entries=(), operands=(), context=()):
        quantity.value, quantity.unit, quantity.basis = value, unit, basis
        quantity.evidence_ids = list(dict.fromkeys(
            [item.id for item, _ in entries] + [item.id for item in context]
            + [key for operand in operands for key in operand.evidence_ids]
        ))
        quantity.source_conditions = list(dict.fromkeys(
            [condition for item, number in entries for condition in (item.conditions, number.conditions) if condition]
            + [item.conditions for item in context if item.conditions]
            + [condition for operand in operands for condition in operand.source_conditions]
        ))

    def require_bound_quantity(quantity):
        if quantity is None:
            raise ValueError("A required dependent quantity is missing.")
        if quantity.binding_error:
            raise ValueError(f"Dependent quantity is unresolved: {quantity.binding_error}")
        return quantity

    def bind_once(quantity, calculate):
        if quantity is None or id(quantity) in resolved:
            return quantity
        if id(quantity) in resolving:
            raise ValueError("Supply/current dependency is circular; correct the rail assignments.")
        resolving.add(id(quantity))
        quantity.binding_error = ""
        quantity.source_conditions = []
        try:
            calculate()
        except ValueError as error:
            quantity.binding_error = str(error)
        finally:
            resolving.remove(id(quantity))
            resolved.add(id(quantity))
        return quantity

    def source_value(entry, owner, unit, corner):
        _, number = entry
        value = convert_value(number.value, number.unit, unit)
        dependencies = []
        if number.supply_factor:
            if unit != "V" or corner not in {"min", "max"}:
                raise ValueError("A VDD-scaled source number needs a voltage corner.")
            supplies = [rail for rail in run.rails if any(load.component_id == owner for load in rail.loads)]
            if len(supplies) != 1:
                raise ValueError(f"{owner} needs one unambiguous assigned supply for its VDD-scaled limit.")
            side = corner if number.supply_factor > 0 else ("max" if corner == "min" else "min")
            supply = require_bound_quantity(bind_voltage(supplies[0], side))
            value += number.supply_factor * supply.value
            dependencies.append(supply)
        return value, dependencies

    def bind_direct(quantity, owner, roles, unit, *, corner=None, bound=None, assume=False, margin=False):
        def calculate():
            quantity.calculation = "direct"
            entries = source_records(quantity.source_ids, owner, roles)
            if not entries:
                if roles == {"quiescent_current"} and any(
                    owner in item.component_ids and number.role == "quiescent_current"
                    and number.basis not in {"absolute_maximum", "estimate"}
                    and _UNITS.get(number.unit, (None,))[0] == "A"
                    for item, number in sources.values()
                ):
                    raise ValueError("Documented regulator own current is available; reference the applicable quiescent_current source instead of replacing it with an assumption.")
                if not assume or quantity.assumption_id not in assumptions:
                    raise ValueError(f"Reference one documented {sorted(roles)} source number for {owner}.")
                set_bound_value(quantity, convert_value(quantity.value, quantity.unit, unit), unit, quantity.basis)
                return
            if len(entries) != 1:
                raise ValueError("A direct quantity needs exactly one applicable source number.")
            number = entries[0][1]
            if bound and number.basis != bound:
                raise ValueError(f"This {bound} operand needs a documented {bound} bound, not {number.basis}.")
            value, dependencies = source_value(entries[0], owner, unit, corner)
            if value < 0 and (unit in {"A", "degC/W"} or number.role == "dropout"):
                raise ValueError(f"{number.role} cannot be negative.")
            basis = number.basis
            if margin and quantity.basis == "estimate" and quantity.assumption_id in assumptions:
                estimate = convert_value(quantity.value, quantity.unit, unit)
                if estimate < value:
                    raise ValueError(f"Estimated demand {estimate:g} {unit} is below its documented source demand {value:g} {unit}; retain the source demand or select a documented lower-power mode.")
                if number.role == "dropout" and number.basis == "typical" and estimate == value:
                    raise ValueError("Typical dropout requires an explicit conservative headroom margin, not relabeling the same typical value.")
                value, basis = estimate, "estimate"
            if number.role == "dropout" and basis == "typical":
                raise ValueError("Typical dropout alone does not guarantee headroom; use a documented bound or disclose a conservative estimated margin.")
            set_bound_value(quantity, value, unit, basis, entries, dependencies)
        return bind_once(quantity, calculate)

    def bind_supply_assumption(quantity, rail, roles, unit):
        component = components.get(rail.source_component_id)
        external = rail.source_component_id == "external"
        connector = bool(component and component.product and component.kind == "connector")
        if quantity is None or quantity.assumption_id not in assumptions or not (external or connector):
            return False

        def calculate():
            quantity.calculation = "direct"
            context = [evidence[key] for key in quantity.source_ids if key in evidence]
            numeric_ids = [key for key in quantity.source_ids if key not in evidence]
            entries = source_records(numeric_ids, components.keys(), roles)
            # Guide/connector ratings provide context, not the upstream supply contract.
            set_bound_value(quantity, convert_value(quantity.value, quantity.unit, unit), unit, "estimate", entries, context=context)
        bind_once(quantity, calculate)
        return True

    def bind_voltage(rail, side):
        quantity = getattr(rail, f"voltage_{side}")
        if quantity is None or bind_supply_assumption(
            quantity, rail, {"operating_voltage", "output_voltage", "output_tolerance"}, "V",
        ):
            return quantity

        def calculate():
            quantity.calculation = f"output_{side}"
            entries = source_records(quantity.source_ids, rail.source_component_id, {"output_voltage", "output_tolerance"})
            outputs = [entry for entry in entries if entry[1].role == "output_voltage"]
            tolerances = [entry for entry in entries if entry[1].role == "output_tolerance"]
            if len(outputs) != 1 or outputs[0][1].basis not in {side, "nominal"}:
                raise ValueError(f"Use one documented output {side} bound or nominal voltage plus tolerances.")
            if outputs[0][1].basis == "nominal" and not tolerances:
                raise ValueError("Nominal output voltage alone is not a guaranteed delivered interval; reference output tolerance.")
            nominal, dependencies = source_value(outputs[0], rail.source_component_id, "V", side)
            excursion = 0
            for _, tolerance in tolerances:
                signed_minimum = side == "min" and tolerance.basis == "min" and tolerance.value <= 0
                absolute_bound = tolerance.basis == "max" and tolerance.value >= 0
                if tolerance.supply_factor or not (signed_minimum or absolute_bound):
                    raise ValueError("Output tolerance needs a nonnegative maximum magnitude, or a signed negative minimum for the lower bound.")
                magnitude = abs(tolerance.value)
                excursion += abs(nominal) * magnitude / 100 if tolerance.unit == "%" else convert_value(magnitude, tolerance.unit, "V")
            value, basis = nominal + (-excursion if side == "min" else excursion), side
            if quantity.assumption_id is not None:
                if quantity.assumption_id not in assumptions:
                    raise ValueError("A widened output window needs a declared design assumption.")
                estimate = convert_value(quantity.value, quantity.unit, "V")
                if isclose(estimate, value, rel_tol=1e-12, abs_tol=1e-12):
                    estimate = value
                elif (side == "min" and estimate > value) or (side == "max" and estimate < value):
                    raise ValueError(f"Estimated output {side} {estimate:g} V narrows the source-derived bound {value:g} V; the design window may only widen it.")
                value, basis = estimate, "estimate"
            set_bound_value(quantity, value, "V", basis, entries, dependencies)
        return bind_once(quantity, calculate)

    def bind_input_min(rail, load):
        quantity = load.voltage_min
        regulator = regulators.get(load.component_id)
        if quantity is None or not regulator or regulator.kind != "linear" or regulator.input_rail_id != rail.id:
            return bind_direct(quantity, load.component_id, {"operating_voltage"}, "V", corner="min", bound="min")

        def calculate():
            quantity.calculation = "input_min"
            output = rails.get(regulator.output_rail_id)
            if not output or output.source_component_id != load.component_id:
                raise ValueError("Regulator output rail is missing or has the wrong source component.")
            entries = source_records(quantity.source_ids, load.component_id, {
                "operating_voltage", "output_voltage", "output_tolerance", "dropout",
            })
            # Output/headroom citations are redundant with the bound rail and dropout below.
            entries = [entry for entry in entries if entry[1].role == "operating_voltage"]
            if len(entries) > 1 or any(number.basis != "min" for _, number in entries):
                raise ValueError("input_min accepts at most one documented minimum operating-input bound.")
            if not entries:
                entries = [
                    (item, number) for item, number in sources.values()
                    if load.component_id in item.component_ids
                    and number.role == "operating_voltage" and number.basis == "min"
                ]
                if len(entries) > 1:
                    raise ValueError("Several operating-input minima are documented; reference the one applicable to this regulator configuration.")
            maximum = require_bound_quantity(bind_voltage(output, "max"))
            dropout = require_bound_quantity(bind_direct(regulator.dropout, load.component_id, {"dropout"}, "V", margin=True))
            minimum, dependencies = source_value(entries[0], load.component_id, "V", "min") if entries else (0, [])
            set_bound_value(quantity, max(minimum, maximum.value + dropout.value), "V", "min", entries, [maximum, dropout, *dependencies])
        return bind_once(quantity, calculate)

    def bind_current(rail, load):
        quantity = load.current
        component = components.get(load.component_id)
        regulator = regulators.get(load.component_id)
        if quantity is None or not regulator or regulator.kind != "linear" or regulator.input_rail_id != rail.id:
            assume = bool(component and component.kind == "passive") or bool(
                regulator and regulator.kind == "switching" and regulator.input_rail_id == rail.id
            )
            roles = {"input_current", "supply_current_required"}
            if not regulator and not any(output.source_component_id == load.component_id for output in run.rails):
                # Sensor datasheets also use Iq for total active supply current.
                # Its operating conditions still require review; converter Iq is not its input load.
                roles.add("quiescent_current")
            return bind_direct(quantity, load.component_id, roles, "A", assume=assume, margin=True)

        def calculate():
            quantity.calculation, quantity.source_ids = "linear_input", []
            output = rails.get(regulator.output_rail_id)
            if not output or output.source_component_id != load.component_id or not output.loads:
                raise ValueError("Linear-regulator input demand needs a populated output rail sourced by that regulator.")
            own = require_bound_quantity(bind_direct(regulator.quiescent_current, load.component_id, {"quiescent_current"}, "A", assume=True, margin=True))
            currents = [require_bound_quantity(bind_current(output, downstream)) for downstream in output.loads]
            if own.value < 0 or any(current.value < 0 for current in currents):
                raise ValueError("Regulator own current and downstream current demands must be nonnegative.")
            set_bound_value(quantity, own.value + sum(current.value for current in currents), "A", "estimate", operands=[own, *currents])
        return bind_once(quantity, calculate)

    for rail in run.rails:
        bind_voltage(rail, "min")
        bind_voltage(rail, "max")
        if not bind_supply_assumption(rail.available_current, rail, {"output_current", "supply_current_required"}, "A"):
            bind_direct(rail.available_current, rail.source_component_id, {"output_current"}, "A")
        for load in rail.loads:
            bind_input_min(rail, load)
            bind_direct(load.voltage_max, load.component_id, {"operating_voltage"}, "V", corner="max", bound="max")
            bind_current(rail, load)
    for signal in run.signal_checks:
        for field, owner, role, corner in (
            ("output_high_min", signal.source_component_id, "output_high", "min"),
            ("input_high_min", signal.receiver_component_id, "input_high", "max"),
            ("output_low_max", signal.source_component_id, "output_low", "max"),
            ("input_low_max", signal.receiver_component_id, "input_low", "min"),
        ):
            # The threshold's documented min/max label differs from the supply corner.
            bind_direct(getattr(signal, field), owner, {role}, "V", corner=corner, bound="min" if "high" in role else "max")
    for regulator in run.regulator_checks:
        bind_direct(regulator.dropout, regulator.component_id, {"dropout"}, "V", margin=True)
        bind_direct(regulator.theta_ja, regulator.component_id, {"theta_ja"}, "degC/W")
        bind_direct(regulator.quiescent_current, regulator.component_id, {"quiescent_current"}, "A", assume=True, margin=True)
        bind_direct(regulator.ambient_max, regulator.component_id, set(), "degC", assume=True)
        bind_direct(regulator.junction_target, regulator.component_id, set(), "degC", assume=True)
        output = rails.get(regulator.output_rail_id)
        owners = [load.component_id for load in output.loads] if output else []
        bind_direct(regulator.average_output_current, owners, {"average_current", "input_current"}, "A", assume=True, margin=True)
