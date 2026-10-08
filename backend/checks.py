"""Small, explicit pre-layout checks. Source interpretation remains model-assisted."""

from __future__ import annotations

from collections import Counter

from models import REVIEW_AREAS, DesignRun, Evidence, Finding, Quantity
from numeric import bind_quantities, convert_value
from run_store import bom_rows


def _finding(run, key, area, status, subjects, explanation, quantities=(), evidence_ids=(), remedy=""):
    refs = list(evidence_ids)
    for quantity in quantities:
        if quantity:
            refs.extend(quantity.evidence_ids)
    return Finding(
        id=f"code:{key}",
        revision=run.revision,
        area=area,
        method="code",
        status=status,
        subject_ids=list(subjects),
        explanation=explanation,
        remedy=remedy,
        evidence_ids=list(dict.fromkeys(refs)),
    )


def _collect_valid_evidence(run: DesignRun) -> dict[str, Evidence]:
    documents = {doc.get("document_id"): doc for doc in run.documents}
    components = {c.id: c for c in run.components if c.product}
    valid = {}
    for item in run.evidence:
        doc = documents.get(item.document_id)
        if (
            doc
            and isinstance(doc.get("page_count"), int)
            and item.page <= doc["page_count"]
            and item.quote.strip()
            and item.fact.strip()
            and item.component_ids
            and set(item.component_ids) <= components.keys()
            and all(
                components[key].kind == "passive" or item.document_id in components[key].document_ids
                for key in item.component_ids
            )
        ):
            valid[item.id] = item
    return valid


def _read_number(
    quantity: Quantity | None,
    unit: str,
    run: DesignRun,
    evidence: dict[str, Evidence],
    owners=(),
    allow_assumption=True,
    *,
    allow_typical=False,
):
    if quantity is None or quantity.binding_error or quantity.basis == "absolute_maximum":
        return None
    if any(ref not in evidence for ref in quantity.evidence_ids):
        return None
    documented = bool(quantity.evidence_ids)
    if documented and owners:
        documented = any(set(owners) & set(evidence[ref].component_ids) for ref in quantity.evidence_ids)
    if run.numeric_binding_version and quantity.calculation == "linear_input":
        # The resolver checks the converter, downstream loads and own-current provenance.
        documented = True
    assumed = allow_assumption and quantity.assumption_id in {a.id for a in run.assumptions}
    if not documented and not assumed:
        return None
    if not allow_assumption:
        if quantity.basis == "estimate":
            return None
        if quantity.basis == "typical" and not allow_typical:
            return None
    try:
        return convert_value(quantity.value, quantity.unit, unit)
    except ValueError:
        return None


def _describe_missing_operands(quantities, values, labels, evidence):
    """Explain the specific unusable operand without asking the model to guess it."""
    problems = []
    for quantity, value, label in zip(quantities, values, labels):
        if value is not None:
            continue
        details = "missing"
        if quantity is not None:
            refs = [
                f"{key} belongs to {','.join(evidence[key].component_ids)}"
                if key in evidence
                else f"{key} is not valid evidence"
                for key in quantity.evidence_ids
            ]
            details = f"{quantity.value:g} {quantity.unit}, basis={quantity.basis}; " + (
                "; ".join(refs) or "no source citation"
            )
            if quantity.assumption_id:
                details += f"; assumption_id={quantity.assumption_id}"
            if quantity.binding_error:
                details += f"; {quantity.binding_error}"
        problems.append(f"{label}: {details}")
    return "; ".join(problems)


def _has_catalog_review(component, current_review):
    return bool(
        component.kind in {"connector", "passive"}
        and component.product
        and (component.product.product_url or "").startswith(("https://", "http://"))
        and any(
            str(parameter.get("name") or "").strip() and str(parameter.get("value") or "").strip()
            for parameter in component.product.parameters
        )
        and any(
            finding.area == "evidence"
            and finding.status == "pass"
            and component.id in finding.subject_ids
            and finding.explanation.strip()
            for finding in current_review
        )
    )


def _has_passive_load_review(component, area, subjects, evidence, current_review, source_ids=()):
    """Require review of the actual passive arrangement, not invented digital/supply limits."""
    for finding in current_review:
        if (
            finding.area != area
            or finding.status != "pass"
            or not set(subjects) <= set(finding.subject_ids)
            or not finding.explanation.strip()
            or any(ref not in evidence for ref in finding.evidence_ids)
        ):
            continue
        owners = {owner for ref in finding.evidence_ids for owner in evidence[ref].component_ids}
        if set(source_ids) <= owners and (component.id in owners or _has_catalog_review(component, current_review)):
            return True
    return False


def _check_evidence_and_selections(run, selected, evidence, current_review, subjects):
    """Check identities, source references, and model-finding integrity."""
    for name in (
        "components",
        "requirements",
        "assumptions",
        "rails",
        "interfaces",
        "evidence",
    ):
        duplicates = [key for key, count in Counter(x.id for x in getattr(run, name)).items() if count > 1]
        if duplicates:
            yield _finding(run, f"duplicate:{name}", "evidence", "fail", duplicates, f"Duplicate {name} IDs.")
    if not run.requirements or not run.components:
        yield _finding(
            run, "empty_design", "requirements", "unknown", [], "A device needs requirements and component selections."
        )
    for component in run.components:
        catalog_reviewed = _has_catalog_review(component, current_review)
        if component.id not in selected:
            yield _finding(
                run,
                f"selection:{component.id}",
                "requirements",
                "fail",
                [component.id],
                "No exact manufacturer part is selected. " + (component.selection_error or ""),
                remedy=(
                    "Use a different suitable exact MPN in search_query or change the failed search terms. "
                    "Changing only name while repeating search_query/broad_query repeats the failed selection."
                ),
            )
        elif catalog_reviewed:
            yield _finding(
                run,
                f"catalog_source:{component.id}",
                "evidence",
                "pass",
                [component.id],
                "Commodity specifications use labeled supplier data with an explicit current evidence review, not a manufacturer-document claim.",
            )
        elif component.kind != "passive" and not any(
            component.id in e.component_ids and e.document_id in component.document_ids for e in evidence.values()
        ):
            yield _finding(
                run,
                f"source:{component.id}",
                "evidence",
                "unknown",
                [component.id],
                "Active parts/modules need manufacturer evidence; a connector may instead have an explicit current review of its labeled supplier specifications. "
                + ("Acquisition errors: " + "; ".join(dict.fromkeys(component.document_errors)) + ". " if component.document_errors else "")
                + ("Selected catalog description (not manufacturer evidence): " + component.product.description if component.product else ""),
                remedy=(
                    "No source was acquired for this part. Rereading the same failed URL does not establish ratings. "
                    "Supply a different accessible source URL through a part update, or replace the part. "
                    "The replacement must meet the recorded downstream peak current, voltage and thermal needs."
                    if component.document_errors and not component.document_ids
                    else "Read an applicable source for this exact part; do not claim an inaccessible or mismatched document was verified."
                ),
            )
        elif not any(component.id in e.component_ids for e in evidence.values()):
            yield _finding(
                run,
                f"source:{component.id}",
                "evidence",
                "unknown",
                [component.id],
                "No valid component evidence or reviewed catalog specifications are recorded.",
            )
    for item in run.evidence:
        if item.id not in evidence:
            yield _finding(
                run,
                f"evidence:{item.id}",
                "evidence",
                "unknown",
                item.component_ids,
                "Evidence needs an existing source/page, selected component, quotation or figure label, and fact.",
            )
    for finding in current_review:
        if (
            not finding.explanation.strip()
            or any(ref not in evidence for ref in finding.evidence_ids)
            or any(ref not in subjects for ref in finding.subject_ids)
        ):
            yield _finding(
                run,
                f"finding:{finding.id}",
                "evidence",
                "unknown",
                [],
                "A model finding has an invalid explanation, subject, or evidence reference.",
            )


def _check_requirements(run, selected, current_review):
    """Record requirement mappings and review coverage without blocking on gaps."""
    for requirement in run.requirements:
        mapped = bool(requirement.component_ids) and set(requirement.component_ids) <= selected
        reviewed = any(
            requirement.id in finding.subject_ids
            and finding.area == "requirements"
            and finding.status != "not_applicable"
            for finding in current_review
        )
        yield _finding(
            run,
            f"requirement:{requirement.id}",
            "requirements",
            "pass" if mapped and reviewed else "unknown",
            [requirement.id],
            "Requirement maps to selected parts and a current review check."
            if mapped and reviewed
            else "Requirement needs selected parts and a current, applicable review check.",
        )
    missing_areas = set(REVIEW_AREAS) - {finding.area for finding in current_review}
    if missing_areas or not run.review_completed:
        yield _finding(
            run,
            "review_coverage",
            "evidence",
            "unknown",
            [],
            "Whole-design review is unfinished or missing areas: " + ", ".join(sorted(missing_areas)),
        )
    if current_review and all(f.status == "not_applicable" for f in current_review):
        yield _finding(
            run,
            "vacuous_review",
            "requirements",
            "unknown",
            [],
            "An all-not-applicable review does not check a device.",
        )


def _check_power(run, selected, evidence, current_review):
    """Check supply assignments, operating ranges, and peak current budgets."""
    components = {component.id: component for component in run.components if component.id in selected}
    powered = {load.component_id for rail in run.rails for load in rail.loads}
    for component in run.components:
        if component.id in selected and component.kind in {"active", "module"} and component.id not in powered:
            yield _finding(
                run,
                f"power_assignment:{component.id}",
                "power",
                "unknown",
                [component.id],
                "No intended supply is recorded.",
            )
    for rail in run.rails:
        source_ok = rail.source_component_id == "external" or rail.source_component_id in selected
        if not source_ok or not rail.loads:
            yield _finding(
                run,
                f"rail:{rail.id}",
                "power",
                "unknown",
                [rail.id],
                "Supply needs a selected/declared source and intended loads.",
            )
        low = _read_number(rail.voltage_min, "V", run, evidence, [rail.source_component_id])
        high = _read_number(rail.voltage_max, "V", run, evidence, [rail.source_component_id])
        for load in rail.loads:
            component = components.get(load.component_id)
            if component and component.kind == "passive" and load.voltage_min is None and load.voltage_max is None:
                reviewed = _has_passive_load_review(
                    component, "power", [rail.id, component.id], evidence, current_review
                )
                valid = source_ok and None not in (low, high) and low <= high and reviewed
                yield _finding(
                    run,
                    f"voltage:{rail.id}:{load.component_id}",
                    "power",
                    "pass" if valid else "unknown",
                    [rail.id, load.component_id],
                    "Current-only passive load has a reviewed rating/current-limiting arrangement on this rail; its current remains in the total budget."
                    if valid
                    else "A current-only passive load needs valid rail bounds and a current power review naming its rail and component, supported by its applicable source or reviewed catalog ratings. Do not invent IC operating-voltage limits for it.",
                    (rail.voltage_min, rail.voltage_max),
                )
                continue
            minimum = _read_number(load.voltage_min, "V", run, evidence, [load.component_id], False)
            maximum = _read_number(load.voltage_max, "V", run, evidence, [load.component_id], False)
            operands = (rail.voltage_min, rail.voltage_max, load.voltage_min, load.voltage_max)
            if None in (low, high, minimum, maximum) or load.component_id not in selected or not source_ok:
                status, message = (
                    "unknown",
                    "Supply compatibility needs selected source/load components and cited operating voltage limits.",
                )
                if None in (low, high, minimum, maximum):
                    message += " " + _describe_missing_operands(
                        operands,
                        (low, high, minimum, maximum),
                        (
                            f"{rail.source_component_id} source voltage_min",
                            f"{rail.source_component_id} source voltage_max",
                            f"{load.component_id} operating voltage_min",
                            f"{load.component_id} operating voltage_max",
                        ),
                        evidence,
                    )
            elif low > high or minimum > maximum:
                status, message = "unknown", "Recorded voltage minimum exceeds its maximum; the range cannot be checked."
            else:
                valid = minimum <= low and high <= maximum
                status = "pass" if valid else "fail"
                message = f"Source {low:g}–{high:g} V must fit {minimum:g}–{maximum:g} V operating range."
            yield _finding(
                run,
                f"voltage:{rail.id}:{load.component_id}",
                "power",
                status,
                [rail.id, load.component_id],
                message,
                operands,
            )
        currents = [_read_number(load.current, "A", run, evidence, [load.component_id]) for load in rail.loads]
        available = _read_number(rail.available_current, "A", run, evidence, [rail.source_component_id])
        if (
            not source_ok
            or not currents
            or available is None
            or available < 0
            or any(value is None or value < 0 for value in currents)
        ):
            status, message = (
                "unknown",
                "Current budget needs an explicit source capability and cited or assumed load currents.",
            )
            if available is None or any(value is None for value in currents):
                message += " " + _describe_missing_operands(
                    [rail.available_current] + [load.current for load in rail.loads],
                    [available, *currents],
                    [f"{rail.source_component_id} available_current"]
                    + [f"{load.component_id} load current" for load in rail.loads],
                    evidence,
                )
                if any(load.component_id == output.source_component_id for load in rail.loads for output in run.rails):
                    message += " Converter input current is a derived budget: declare an assumption including downstream loads and converter losses/own current, not a downstream device's rating relabeled as the converter's."
        else:
            total = sum(currents)
            status = "pass" if total <= available else "fail"
            message = f"Recorded load {total:g} A versus source capability {available:g} A; applicable to the stated operating assumptions."
        yield _finding(
            run,
            f"current:{rail.id}",
            "power",
            status,
            [rail.id],
            message,
            [rail.available_current] + [load.current for load in rail.loads],
        )


def _check_interfaces(run, selected, evidence, current_review):
    """Check interface declarations, address conflicts, and logic thresholds."""
    assumptions = {assumption.id for assumption in run.assumptions if assumption.description.strip()}
    components = {component.id: component for component in run.components if component.id in selected}
    for interface in run.interfaces:
        is_i2c = interface.protocol.strip().casefold() in {"i2c", "i²c"}
        participants = {endpoint.component_id for endpoint in interface.endpoints}
        reviews = [
            finding
            for finding in current_review
            if finding.area == "signals"
            and finding.status == "pass"
            and interface.id in finding.subject_ids
            and finding.explanation.strip()
            and finding.evidence_ids
            and all(key in evidence for key in finding.evidence_ids)
        ]
        refs = interface.evidence_ids or list(
            dict.fromkeys(ref for finding in reviews for ref in finding.evidence_ids)
        )
        owners = {owner for ref in refs if ref in evidence for owner in evidence[ref].component_ids}
        reviewed = any(
            participants <= {owner for ref in finding.evidence_ids for owner in evidence[ref].component_ids}
            for finding in reviews
        )
        valid = (
            bool(interface.protocol.strip())
            and bool(interface.configuration.strip())
            and bool(participants & selected)
            and bool(refs)
            and all(ref in evidence for ref in refs)
        )
        addresses = {}
        for endpoint in interface.endpoints:
            external = endpoint.component_id == "external" and endpoint.assumption_id in assumptions
            valid = valid and (endpoint.component_id in selected or external)
            if is_i2c and endpoint.address is not None:
                try:
                    address = int(endpoint.address, 16 if endpoint.address.lower().startswith("0x") else 10)
                    if address in addresses and addresses[address] != endpoint.component_id:
                        yield _finding(
                            run,
                            f"address:{interface.id}:{endpoint.component_id}",
                            "signals",
                            "fail",
                            [interface.id, endpoint.component_id],
                            f"I2C address {endpoint.address} conflicts with {addresses[address]}.",
                        )
                    addresses[address] = endpoint.component_id
                except ValueError:
                    valid = False
        if not is_i2c and len(participants) == 1 and participants <= selected:
            valid = valid and participants <= owners and reviewed
            message = (
                "A source-backed current review establishes this component capability, not an inter-part electrical connection."
                if valid
                else "A single-component capability needs its own source evidence and a current source-backed signals pass naming this interface; a missing material interface participant must be restored."
            )
        else:
            valid = valid and len(participants) >= 2
            message = (
                "Interacting components and protocol assumptions are recorded; electrical compatibility is reviewed separately."
                if valid
                else "Interface needs selected components, any declared external-tool assumption, protocol, operating configuration, and valid evidence (recorded here or in a current source-backed signals review naming this interface)."
            )
        yield _finding(
            run,
            f"interface:{interface.id}",
            "signals",
            "pass" if valid else "unknown",
            [interface.id],
            message,
            evidence_ids=refs,
        )
        if is_i2c and len(participants) == 2 and participants <= selected:
            first, second = sorted(participants)
            directions = {(signal.source_component_id, signal.receiver_component_id) for signal in run.signal_checks}
            missing = {(first, second), (second, first)} - directions
            yield _finding(
                run,
                f"interface_directions:{interface.id}",
                "signals",
                "unknown" if missing else "pass",
                [interface.id, first, second],
                "Missing I2C electrical assessment direction(s): "
                + ", ".join(f"{a} to {b}" for a, b in sorted(missing))
                + ". One assessment per driving direction is sufficient; no pin or per-wire plan is required."
                if missing
                else "Both I2C driving directions are represented; their operands are checked separately.",
            )
    rails = {rail.id: rail for rail in run.rails}
    for signal in run.signal_checks:
        high, high_owner = signal.output_high_min, signal.source_component_id
        if signal.pullup_rail_id is not None:
            pullup = rails.get(signal.pullup_rail_id)
            if pullup and (pullup.source_component_id in selected or pullup.source_component_id == "external"):
                high = pullup.voltage_min
            else:
                high = None
            high_owner = pullup.source_component_id if pullup else "missing"
        quantities = (high, signal.input_high_min, signal.output_low_max, signal.input_low_max)
        owners = (high_owner, signal.receiver_component_id, signal.source_component_id, signal.receiver_component_id)
        values = [
            _read_number(q, "V", run, evidence, [owner], index == 0 and signal.pullup_rail_id is not None)
            for index, (q, owner) in enumerate(zip(quantities, owners))
        ]
        source, receiver = components.get(signal.source_component_id), components.get(signal.receiver_component_id)
        if (
            source
            and source.kind in {"active", "module"}
            and receiver
            and receiver.kind == "passive"
            and signal.input_high_min is None
            and signal.input_low_max is None
        ):
            driver_valid = (
                (
                    signal.output_high_min is None
                    or _read_number(signal.output_high_min, "V", run, evidence, [source.id], False) is not None
                )
                and (signal.output_low_max is None or values[2] is not None)
                and (signal.pullup_rail_id is None or values[0] is not None)
            )
            reviewed = _has_passive_load_review(
                receiver, "signals", [source.id, receiver.id], evidence, current_review, [source.id]
            )
            status = "pass" if driver_valid and reviewed else "unknown"
            message = (
                "Passive load drive is supported by a current source-backed review of the driver and load arrangement; the load has no digital input thresholds."
                if status == "pass"
                else "Passive load drive needs valid supplied driver limits and a current signals review naming driver and load, with driver evidence and applicable load evidence or reviewed catalog ratings. Review current limiting, ratings, and driver capacity; do not invent passive VIH/VIL thresholds."
            )
        elif None in values or not {signal.source_component_id, signal.receiver_component_id} <= selected:
            status, message = (
                "unknown",
                "Signal thresholds need cited driver/receiver limits and, when used, a valid documented or assumed pull-up rail.",
            )
            if None in values:
                message += " " + _describe_missing_operands(
                    quantities,
                    values,
                    (
                        f"{high_owner} output/pull-up high minimum",
                        f"{signal.receiver_component_id} input_high_min",
                        f"{signal.source_component_id} output_low_max",
                        f"{signal.receiver_component_id} input_low_max",
                    ),
                    evidence,
                )
        else:
            status = "pass" if values[0] >= values[1] and values[2] <= values[3] else "fail"
            high_label = "Pull-up rail minimum" if signal.pullup_rail_id is not None else "VOH"
            message = f"{high_label} {values[0]:g} ≥ VIH {values[1]:g}; VOL {values[2]:g} ≤ VIL {values[3]:g} V."
            if signal.pullup_rail_id is not None:
                message += (
                    " Static thresholds only; actual pullups, leakage and rise time require source-assisted review."
                )
        yield _finding(
            run,
            f"signal:{signal.id}",
            "signals",
            status,
            [signal.id, signal.source_component_id, signal.receiver_component_id],
            message,
            quantities,
        )


def _check_regulators(run, selected, evidence):
    """Check linear-regulator headroom and source-backed thermal screening."""
    rails = {rail.id: rail for rail in run.rails}
    for regulator in run.regulator_checks:
        if regulator.kind != "linear":
            continue
        source, output = rails.get(regulator.input_rail_id), rails.get(regulator.output_rail_id)
        if (
            not source
            or not output
            or regulator.component_id not in selected
            or output.source_component_id != regulator.component_id
            or not any(load.component_id == regulator.component_id for load in source.loads)
        ):
            yield _finding(
                run,
                f"regulator:{regulator.component_id}",
                "power",
                "unknown",
                [regulator.component_id],
                "Regulator references unresolved parts/rails.",
            )
            continue
        vin_min = _read_number(source.voltage_min, "V", run, evidence, [source.source_component_id])
        vin_max = _read_number(source.voltage_max, "V", run, evidence, [source.source_component_id])
        vout_min = _read_number(output.voltage_min, "V", run, evidence, [output.source_component_id])
        vout_max = _read_number(output.voltage_max, "V", run, evidence, [output.source_component_id])
        dropout = _read_number(regulator.dropout, "V", run, evidence, [regulator.component_id])
        if None in (vin_min, vout_max, dropout):
            status = "unknown"
        else:
            status = "pass" if vin_min >= vout_max + dropout else "fail"
        yield _finding(
            run,
            f"headroom:{regulator.component_id}",
            "power",
            status,
            [regulator.component_id],
            "Linear-regulator input minimum must cover output maximum plus documented/assumed dropout.",
            (source.voltage_min, output.voltage_max, regulator.dropout),
        )
        currents = [_read_number(load.current, "A", run, evidence, [load.component_id]) for load in output.loads]
        thermal_quantities = (regulator.ambient_max, regulator.junction_target, regulator.theta_ja)
        ambient = _read_number(regulator.ambient_max, "degC", run, evidence)
        target = _read_number(regulator.junction_target, "degC", run, evidence)
        theta = _read_number(
            regulator.theta_ja, "degC/W", run, evidence, [regulator.component_id], False, allow_typical=True
        )
        average = _read_number(
            regulator.average_output_current, "A", run, evidence, [load.component_id for load in output.loads]
        )
        own_current = (
            _read_number(regulator.quiescent_current, "A", run, evidence, [regulator.component_id])
            if run.numeric_binding_version or regulator.quiescent_current is not None
            else 0
        )
        if None in (ambient, target, theta):
            status, message = (
                "unknown",
                "Thermal screening needs ambient, junction target, and source-owned package theta_JA. "
                + _describe_missing_operands(
                    thermal_quantities,
                    (ambient, target, theta),
                    ("ambient_max", "junction_target", "theta_ja"),
                    evidence,
                ),
            )
        elif theta <= 0:
            status, message = "unknown", "Recorded thermal resistance must be positive to calculate dissipation."
        elif target <= ambient:
            status, message = (
                "fail",
                "The junction target must exceed maximum ambient for usable thermal headroom.",
            )
        elif None in (vin_max, vout_min) or not currents or any(c is None or c < 0 for c in currents):
            status, message = "unknown", "Dissipation needs valid source/output rail bounds and peak load currents."
        elif regulator.average_output_current is not None and average is None:
            status, message = (
                "unknown",
                _describe_missing_operands(
                    [regulator.average_output_current],
                    [average],
                    [f"{regulator.component_id} average_output_current"],
                    evidence,
                ),
            )
        elif own_current is None or own_current < 0:
            status, message = "unknown", "Linear-regulator heat needs a sourced or conservatively assumed own/ground current."
        else:
            peak = sum(currents)
            thermal_current = peak if average is None else average
            if not 0 <= thermal_current <= peak:
                status, message = (
                    "unknown",
                    f"Average output current {thermal_current:g} A must be between zero and the recorded peak load {peak:g} A.",
                )
            else:
                limit = (target - ambient) / theta
                watts = (vin_max - vout_min) * thermal_current + vin_max * own_current
                status = "pass" if 0 <= watts <= limit else "fail"
                basis = (
                    f"recorded average output current {average:g} A (peak budget {peak:g} A)"
                    if average is not None
                    else f"peak load {peak:g} A as a conservative sustained estimate"
                )
                message = f"Approximate linear-regulator dissipation {watts:g} W versus allowance ({target:g} - {ambient:g}) / {theta:g} = {limit:g} W, using {basis} plus {own_current:g} A own current; not measured junction temperature."
        yield _finding(
            run,
            f"dissipation:{regulator.component_id}",
            "power",
            status,
            [regulator.component_id],
            message,
            [source.voltage_max, output.voltage_min, *thermal_quantities, regulator.average_output_current, regulator.quiescent_current]
            + [load.current for load in output.loads],
        )


def run_checks(run: DesignRun) -> list[Finding]:
    """Recompute code results for this complete revision; never mutate model findings."""
    results = [error.model_copy(update={"revision": run.revision}) for error in run.evidence_errors]
    selected = {c.id for c in run.components if c.product and c.product.mpn.strip() and c.product.manufacturer.strip()}
    evidence = _collect_valid_evidence(run)
    bind_quantities(run, evidence)
    current_review = [
        f for f in run.findings if f.revision == run.revision and f.method == "model_review" and f.kind == "check"
    ]
    subjects = (
        {c.id for c in run.components}
        | {r.id for r in run.requirements}
        | {r.id for r in run.rails}
        | {i.id for i in run.interfaces}
        | {s.get("id") for s in [*run.support_needs, *run.source_support_needs]}
        | {a.id for a in run.assumptions}
        | {s.id for s in run.signal_checks}
        | {"external"}
    )

    results.extend(_check_evidence_and_selections(run, selected, evidence, current_review, subjects))
    results.extend(_check_requirements(run, selected, current_review))
    results.extend(_check_power(run, selected, evidence, current_review))
    results.extend(_check_interfaces(run, selected, evidence, current_review))
    results.extend(_check_regulators(run, selected, evidence))
    return results


def refresh_checks(run: DesignRun) -> None:
    """Replace derived checks and badges, preserving the model's review findings."""
    run.findings = [finding for finding in run.findings if finding.method == "model_review"] + run_checks(run)
    update_outcomes(run)


def update_outcomes(run: DesignRun) -> None:
    """Derive badges after the caller has installed this revision's code results."""
    current = [finding for finding in run.findings if finding.revision == run.revision and finding.kind == "check"]
    if any(finding.blocks_review for finding in current):
        run.compatibility = "issues_found"
    elif (
        not run.review_completed
        or not run.components
        or not run.requirements
        or run.lifecycle in {"interrupted", "error", "needs_input"}
        or not any(f.method == "model_review" for f in current)
    ):
        run.compatibility = None
    else:
        run.compatibility = "checked"
    rows = bom_rows(run)
    available = sum(row["availability"] == "available" for row in rows)
    if (
        rows
        and available == len(rows)
        and all(c.product and c.product.mpn.strip() and c.product.manufacturer.strip() for c in run.components)
    ):
        run.sourcing = "available"
    elif available:
        run.sourcing = "partial"
    else:
        run.sourcing = "unknown"
