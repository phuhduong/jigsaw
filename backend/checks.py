"""Small, explicit pre-layout checks. Source interpretation remains model-assisted."""
from __future__ import annotations

from collections import Counter

from models import DesignRun, Evidence, Finding, Quantity, REVIEW_AREAS

_UNITS = {"V": ("V", 1), "mV": ("V", .001), "A": ("A", 1),
          "mA": ("A", .001), "uA": ("A", .000001), "µA": ("A", .000001),
          "W": ("W", 1), "mW": ("W", .001),
          "degC": ("degC", 1), "°C": ("degC", 1), "C": ("degC", 1),
          "degC/W": ("degC/W", 1), "°C/W": ("degC/W", 1), "C/W": ("degC/W", 1), "K/W": ("degC/W", 1)}


def _finding(run, key, area, status, subjects, explanation, quantities=(), evidence_ids=()):
    refs = list(evidence_ids)
    for quantity in quantities:
        if quantity:
            refs.extend(quantity.evidence_ids)
    return Finding(id=f"code:{key}", revision=run.revision, area=area, method="code",
                   status=status, subject_ids=list(subjects), explanation=explanation,
                   evidence_ids=list(dict.fromkeys(refs)))


def _valid_evidence(run: DesignRun) -> dict[str, Evidence]:
    documents = {doc.get("document_id"): doc for doc in run.documents}
    components = {c.id: c for c in run.components if c.product}
    valid = {}
    for item in run.evidence:
        doc = documents.get(item.document_id)
        if (doc and isinstance(doc.get("page_count"), int)
                and item.page <= doc["page_count"] and item.quote.strip() and item.fact.strip()
                and item.component_ids and set(item.component_ids) <= components.keys()
                and all(components[key].kind == "passive" or item.document_id in components[key].document_ids
                        for key in item.component_ids)):
            valid[item.id] = item
    return valid


def _number(quantity: Quantity | None, unit: str, run: DesignRun,
            evidence: dict[str, Evidence], owners=(), allow_assumption=True, *, allow_typical=False):
    if quantity is None or quantity.basis == "absolute_maximum":
        return None
    conversion = _UNITS.get(quantity.unit)
    if not conversion or conversion[0] != unit:
        return None
    if any(ref not in evidence for ref in quantity.evidence_ids):
        return None
    documented = bool(quantity.evidence_ids)
    if documented and owners:
        documented = any(set(owners) & set(evidence[ref].component_ids)
                         for ref in quantity.evidence_ids)
    assumed = allow_assumption and quantity.assumption_id in {a.id for a in run.assumptions}
    if not documented and not assumed:
        return None
    if not allow_assumption and (quantity.basis == "estimate" or quantity.basis == "typical" and not allow_typical):
        return None
    return quantity.value * conversion[1]


def _missing_operands(quantities, values, labels, evidence):
    """Explain the specific unusable operand without asking the model to guess it."""
    problems = []
    for quantity, value, label in zip(quantities, values, labels):
        if value is not None:
            continue
        details = "missing"
        if quantity is not None:
            refs = [f"{key} belongs to {','.join(evidence[key].component_ids)}" if key in evidence
                    else f"{key} is not valid evidence" for key in quantity.evidence_ids]
            details = f"{quantity.value:g} {quantity.unit}, basis={quantity.basis}; " + ("; ".join(refs) or "no source citation")
            if quantity.assumption_id:
                details += f"; assumption_id={quantity.assumption_id}"
        problems.append(f"{label}: {details}")
    return "; ".join(problems) + (
        ". Correct the operand/reference using existing facts first. Derived device limits need citations "
        "to their underlying source relationship (for example, regulator output maximum and dropout), "
        "not only an assumption ID. Do not reread merely because the calculated literal is not printed; "
        "reread only when a necessary underlying source fact is absent or wrong.")


def run_checks(run: DesignRun) -> list[Finding]:
    """Recompute code results for this complete revision; never mutate model findings."""
    results = [error.model_copy(update={"revision": run.revision}) for error in run.evidence_errors]
    selected = {c.id for c in run.components if c.product and c.product.mpn.strip()
                and c.product.manufacturer.strip()}
    evidence = _valid_evidence(run)
    current_review = [f for f in run.findings if f.revision == run.revision
                      and f.method == "model_review" and f.kind == "check"]
    subjects = ({c.id for c in run.components} | {r.id for r in run.requirements}
                | {r.id for r in run.rails} | {i.id for i in run.interfaces}
                | {s.id for s in run.support_needs} | {s.id for s in run.source_support_needs}
                | {a.id for a in run.assumptions}
                | {s.id for s in run.signal_checks} | {"external"})

    def add(key, area, status, ids, message, quantities=(), refs=()):
        results.append(_finding(run, key, area, status, ids, message, quantities, refs))

    for name in ("components", "requirements", "assumptions", "rails", "interfaces",
                 "source_support_needs", "support_needs", "evidence"):
        duplicates = [key for key, count in Counter(x.id for x in getattr(run, name)).items()
                      if count > 1]
        if duplicates:
            add(f"duplicate:{name}", "evidence", "fail", duplicates, f"Duplicate {name} IDs.")
    if not run.requirements or not run.components:
        add("empty_design", "requirements", "unknown", [], "A device needs requirements and component selections.")
    for component in run.components:
        catalog_reviewed = (component.kind in {"connector", "passive"} and component.product
                            and (component.product.product_url or "").startswith(("https://", "http://"))
                            and any(str(parameter.get("name") or "").strip() and str(parameter.get("value") or "").strip()
                                    for parameter in component.product.parameters)
                            and any(finding.area == "evidence" and finding.status == "pass"
                                    and component.id in finding.subject_ids and finding.explanation.strip()
                                    for finding in current_review))
        if component.id not in selected:
            add(f"selection:{component.id}", "requirements", "unknown", [component.id],
                "No exact manufacturer part is selected.")
        elif catalog_reviewed:
            add(f"catalog_source:{component.id}", "evidence", "pass", [component.id],
                "Commodity specifications use labeled supplier data with an explicit current evidence review, not a manufacturer-document claim. Required support is checked separately.")
        elif component.kind != "passive" and not any(
                component.id in e.component_ids and e.document_id in component.document_ids for e in evidence.values()):
            add(f"source:{component.id}", "evidence", "unknown", [component.id],
                "Active parts/modules need manufacturer evidence; a connector may instead have an explicit current review of its labeled supplier specifications.")
        elif not any(component.id in e.component_ids for e in evidence.values()) and not any(
                component.id in need.component_ids and need.evidence_ids
                and all(ref in evidence for ref in need.evidence_ids) for need in run.support_needs):
            add(f"source:{component.id}", "evidence", "unknown", [component.id],
                "No valid component or support-circuit evidence is recorded.")
    for item in run.evidence:
        if item.id not in evidence:
            add(f"evidence:{item.id}", "evidence", "unknown", item.component_ids,
                "Evidence needs an existing source/page, selected component, quotation or figure label, and fact.")
    for finding in current_review:
        if (not finding.explanation.strip() or any(ref not in evidence for ref in finding.evidence_ids)
                or any(ref not in subjects for ref in finding.subject_ids)):
            add(f"finding:{finding.id}", "evidence", "unknown", [],
                "A model finding has an invalid explanation, subject, or evidence reference.")
    for requirement in run.requirements:
        mapped = bool(requirement.component_ids) and set(requirement.component_ids) <= selected
        reviewed = any(requirement.id in finding.subject_ids and finding.area == "requirements"
                       and finding.status != "not_applicable" for finding in current_review)
        add(f"requirement:{requirement.id}", "requirements", "pass" if mapped and reviewed else "unknown",
            [requirement.id], "Requirement maps to selected parts and a current review check."
            if mapped and reviewed else "Requirement needs selected parts and a current, applicable review check.")
    missing_areas = set(REVIEW_AREAS) - {finding.area for finding in current_review}
    if missing_areas or not run.review_completed:
        add("review_coverage", "evidence", "unknown", [],
            "Whole-design review is unfinished or missing areas: " + ", ".join(sorted(missing_areas)))
    if current_review and all(f.status == "not_applicable" for f in current_review):
        add("vacuous_review", "requirements", "unknown", [], "An all-not-applicable review does not check a device.")

    fulfillment = {need.id: need for need in run.support_needs}
    for source in run.source_support_needs:
        refs_valid = bool(source.evidence_ids) and all(
            ref in evidence and evidence[ref].document_id == source.document_id for ref in source.evidence_ids)
        owners = {key for ref in source.evidence_ids if ref in evidence for key in evidence[ref].component_ids}
        valid = (refs_valid and bool(source.parent_ids) and set(source.parent_ids) <= selected & owners
                 and bool(source.purpose.strip()))
        need = fulfillment.get(source.id)
        linked = (need is not None and set(source.parent_ids) <= set(need.parent_ids)
                  and set(source.evidence_ids) <= set(need.evidence_ids)
                  and all(ref in evidence for ref in need.evidence_ids))
        satisfied = (linked and need.status == "satisfied" and bool(need.component_ids)
                     and set(need.component_ids) <= selected and bool(need.purpose.strip())
                     and need.necessity in ({"required"} if source.necessity == "required" else {"required", "recommended"}))
        declined = (linked and source.necessity == "recommended" and need.status == "not_applicable"
                    and bool(need.explanation.strip()) and any(
                        f.area == "support" and source.id in f.subject_ids and f.status in {"pass", "not_applicable"}
                        for f in current_review))
        resolved = satisfied or declined
        if not valid:
            problem = "The source obligation has invalid evidence or parent references; reread the affected source."
        elif not linked:
            problem = "Return a same-ID support entry preserving its parents and source references."
        elif need.status == "satisfied" and not need.component_ids:
            problem = "It is marked satisfied but has no purchased component IDs; add the missing placements."
        elif need.status == "included":
            problem = "This source describes EXTERNAL support; included/internal is not its fulfillment. Select the separate parts or correct the source interpretation with evidence."
        else:
            problem = "Required support needs selected placements. A recommendation can be declined only with a concrete source/configuration rationale and a current support-review finding."
        add(f"source_support:{source.id}", "support" if valid else "evidence", "pass" if valid and resolved else "unknown",
            [source.id, *source.parent_ids], "Manufacturer support is accounted for with valid source references and an explicit disposition."
            if valid and resolved else f"{source.purpose}: {source.connection_requirement}. {problem}",
            refs=source.evidence_ids)

    for need in run.support_needs:
        if need.necessity != "required":
            continue
        refs_valid = bool(need.evidence_ids) and all(ref in evidence for ref in need.evidence_ids)
        parents_valid = bool(need.parent_ids) and set(need.parent_ids) <= subjects
        if need.status == "satisfied":
            resolved = bool(need.component_ids) and set(need.component_ids) <= selected and bool(need.purpose.strip())
        else:
            resolved = need.status in {"included", "not_applicable"} and bool(need.explanation.strip())
        add(f"support:{need.id}", "support", "pass" if resolved and refs_valid and parents_valid else "unknown",
            [need.id], "Required support is accounted for with source references."
            if resolved and refs_valid and parents_valid else "Required support or its source/functional purpose remains unresolved.",
            refs=need.evidence_ids)

    powered = {load.component_id for rail in run.rails for load in rail.loads}
    for component in run.components:
        if component.id in selected and component.kind in {"active", "module"} and component.id not in powered:
            add(f"power_assignment:{component.id}", "power", "unknown", [component.id], "No intended supply is recorded.")
    for rail in run.rails:
        source_ok = rail.source_component_id == "external" or rail.source_component_id in selected
        if not source_ok or not rail.loads:
            add(f"rail:{rail.id}", "power", "unknown", [rail.id], "Supply needs a selected/declared source and intended loads.")
        low = _number(rail.voltage_min, "V", run, evidence, [rail.source_component_id])
        high = _number(rail.voltage_max, "V", run, evidence, [rail.source_component_id])
        for load in rail.loads:
            minimum = _number(load.voltage_min, "V", run, evidence, [load.component_id], False)
            maximum = _number(load.voltage_max, "V", run, evidence, [load.component_id], False)
            operands = (rail.voltage_min, rail.voltage_max, load.voltage_min, load.voltage_max)
            if None in (low, high, minimum, maximum) or load.component_id not in selected or not source_ok:
                status, message = "unknown", "Supply compatibility needs selected source/load components and cited operating voltage limits."
                if None in (low, high, minimum, maximum):
                    message += " " + _missing_operands(operands, (low, high, minimum, maximum),
                        (f"{rail.source_component_id} source voltage_min", f"{rail.source_component_id} source voltage_max",
                         f"{load.component_id} operating voltage_min", f"{load.component_id} operating voltage_max"), evidence)
            else:
                valid = low <= high and minimum <= maximum and minimum <= low and high <= maximum
                status = "pass" if valid else "fail"
                message = f"Source {low:g}–{high:g} V must fit {minimum:g}–{maximum:g} V operating range."
            add(f"voltage:{rail.id}:{load.component_id}", "power", status, [rail.id, load.component_id], message, operands)
        currents = [_number(load.current, "A", run, evidence, [load.component_id]) for load in rail.loads]
        available = _number(rail.available_current, "A", run, evidence, [rail.source_component_id])
        if not source_ok or not currents or available is None or any(value is None or value < 0 for value in currents):
            status, message = "unknown", "Current budget needs an explicit source capability and cited or assumed load currents."
            if available is None or any(value is None for value in currents):
                message += " " + _missing_operands([rail.available_current] + [load.current for load in rail.loads],
                    [available, *currents], [f"{rail.source_component_id} available_current"] +
                    [f"{load.component_id} load current" for load in rail.loads], evidence)
                if any(load.component_id == output.source_component_id for load in rail.loads for output in run.rails):
                    message += " Converter input current is a derived budget: declare an assumption including downstream loads and converter losses/own current, not a downstream device's rating relabeled as the converter's."
        else:
            total = sum(currents)
            status = "pass" if 0 <= total <= available else "fail"
            message = f"Recorded load {total:g} A versus source capability {available:g} A; applicable to the stated operating assumptions."
        add(f"current:{rail.id}", "power", status, [rail.id], message,
            [rail.available_current] + [load.current for load in rail.loads])

    assumptions = {assumption.id for assumption in run.assumptions if assumption.description.strip()}
    for interface in run.interfaces:
        refs = interface.evidence_ids
        if not refs:
            refs = list(dict.fromkeys(ref for finding in current_review
                if finding.area == "signals" and finding.status == "pass"
                and interface.id in finding.subject_ids and finding.evidence_ids
                and all(key in evidence for key in finding.evidence_ids)
                for ref in finding.evidence_ids))
        valid = (len(interface.endpoints) >= 2 and bool(interface.protocol.strip()) and bool(interface.configuration.strip())
                 and any(endpoint.component_id in selected for endpoint in interface.endpoints)
                 and bool(refs) and all(ref in evidence for ref in refs))
        addresses = {}
        for endpoint in interface.endpoints:
            external = endpoint.component_id == "external" and endpoint.assumption_id in assumptions
            valid = valid and (endpoint.component_id in selected or external)
            if interface.protocol.strip().casefold() in {"i2c", "i²c"} and endpoint.address is not None:
                try:
                    address = int(endpoint.address, 16 if endpoint.address.lower().startswith("0x") else 10)
                    if address in addresses:
                        add(f"address:{interface.id}:{endpoint.component_id}", "signals", "fail", [interface.id, endpoint.component_id],
                            f"I2C address {endpoint.address} conflicts with {addresses[address]}.")
                    addresses[address] = endpoint.component_id
                except ValueError:
                    valid = False
        add(f"interface:{interface.id}", "signals", "pass" if valid else "unknown", [interface.id],
            "Interacting components and protocol assumptions are recorded; electrical compatibility is reviewed separately."
            if valid else "Interface needs selected components, any declared external-tool assumption, protocol, operating configuration, and valid evidence (recorded here or in a current source-backed signals review naming this interface).", refs=refs)
        participants = {endpoint.component_id for endpoint in interface.endpoints}
        if (interface.protocol.strip().casefold() in {"i2c", "i²c"} and len(participants) == 2
                and participants <= selected):
            first, second = sorted(participants)
            directions = {(signal.source_component_id, signal.receiver_component_id) for signal in run.signal_checks}
            missing = {(first, second), (second, first)} - directions
            add(f"interface_directions:{interface.id}", "signals", "unknown" if missing else "pass",
                [interface.id, first, second],
                "Missing I2C electrical assessment direction(s): " + ", ".join(f"{a} to {b}" for a, b in sorted(missing))
                + ". One assessment per driving direction is sufficient; no pin or per-wire plan is required."
                if missing else "Both I2C driving directions are represented; their operands are checked separately.")
    rails = {rail.id: rail for rail in run.rails}
    for signal in run.signal_checks:
        high, high_owner = signal.output_high_min, signal.source_component_id
        if signal.pullup_rail_id is not None:
            pullup = rails.get(signal.pullup_rail_id)
            high = pullup.voltage_min if pullup and (pullup.source_component_id in selected or pullup.source_component_id == "external") else None
            high_owner = pullup.source_component_id if pullup else "missing"
        quantities = (high, signal.input_high_min, signal.output_low_max, signal.input_low_max)
        owners = (high_owner, signal.receiver_component_id, signal.source_component_id, signal.receiver_component_id)
        values = [_number(q, "V", run, evidence, [owner], index == 0 and signal.pullup_rail_id is not None)
                  for index, (q, owner) in enumerate(zip(quantities, owners))]
        if None in values or not {signal.source_component_id, signal.receiver_component_id} <= selected:
            status, message = "unknown", "Signal thresholds need cited driver/receiver limits and, when used, a valid documented or assumed pull-up rail."
            if None in values:
                message += " " + _missing_operands(quantities, values,
                    (f"{high_owner} output/pull-up high minimum", f"{signal.receiver_component_id} input_high_min",
                     f"{signal.source_component_id} output_low_max", f"{signal.receiver_component_id} input_low_max"), evidence)
        else:
            status = "pass" if values[0] >= values[1] and values[2] <= values[3] else "fail"
            high_label = "Pull-up rail minimum" if signal.pullup_rail_id is not None else "VOH"
            message = f"{high_label} {values[0]:g} ≥ VIH {values[1]:g}; VOL {values[2]:g} ≤ VIL {values[3]:g} V."
            if signal.pullup_rail_id is not None:
                message += " Static thresholds only; actual pullups, leakage and rise time require source-assisted review."
        add(f"signal:{signal.id}", "signals", status,
            [signal.id, signal.source_component_id, signal.receiver_component_id], message, quantities)
    for regulator in run.regulator_checks:
        if regulator.kind != "linear":
            continue
        source, output = rails.get(regulator.input_rail_id), rails.get(regulator.output_rail_id)
        if (not source or not output or regulator.component_id not in selected
                or output.source_component_id != regulator.component_id
                or not any(load.component_id == regulator.component_id for load in source.loads)):
            add(f"regulator:{regulator.component_id}", "power", "unknown", [regulator.component_id], "Regulator references unresolved parts/rails.")
            continue
        vin_min = _number(source.voltage_min, "V", run, evidence, [source.source_component_id])
        vin_max = _number(source.voltage_max, "V", run, evidence, [source.source_component_id])
        vout_min = _number(output.voltage_min, "V", run, evidence, [output.source_component_id])
        vout_max = _number(output.voltage_max, "V", run, evidence, [output.source_component_id])
        dropout = _number(regulator.dropout, "V", run, evidence, [regulator.component_id])
        status = "unknown" if None in (vin_min, vout_max, dropout) else "pass" if vin_min >= vout_max + dropout else "fail"
        add(f"headroom:{regulator.component_id}", "power", status, [regulator.component_id],
            "Linear-regulator input minimum must cover output maximum plus documented/assumed dropout.",
            (source.voltage_min, output.voltage_max, regulator.dropout))
        currents = [_number(load.current, "A", run, evidence, [load.component_id]) for load in output.loads]
        thermal_quantities = (regulator.ambient_max, regulator.junction_target, regulator.theta_ja)
        ambient = _number(regulator.ambient_max, "degC", run, evidence)
        target = _number(regulator.junction_target, "degC", run, evidence)
        theta = _number(regulator.theta_ja, "degC/W", run, evidence, [regulator.component_id], False, allow_typical=True)
        average = _number(regulator.average_output_current, "A", run, evidence,
                          [load.component_id for load in output.loads])
        if None in (ambient, target, theta):
            status, message = "unknown", "Thermal screening needs ambient, junction target, and source-owned package theta_JA. " + _missing_operands(
                thermal_quantities, (ambient, target, theta), ("ambient_max", "junction_target", "theta_ja"), evidence)
        elif theta <= 0 or target <= ambient:
            status, message = "fail", "Thermal resistance must be positive and the junction target must exceed maximum ambient."
        elif None in (vin_max, vout_min) or not currents or any(c is None or c < 0 for c in currents):
            status, message = "unknown", "Dissipation needs valid source/output rail bounds and peak load currents."
        elif regulator.average_output_current is not None and average is None:
            status, message = "unknown", _missing_operands([regulator.average_output_current], [average],
                [f"{regulator.component_id} average_output_current"], evidence)
        else:
            peak = sum(currents)
            thermal_current = peak if average is None else average
            if not 0 <= thermal_current <= peak:
                status, message = "fail", f"Average output current {thermal_current:g} A must be between zero and the recorded peak load {peak:g} A."
            else:
                limit = (target - ambient) / theta
                watts = (vin_max - vout_min) * thermal_current
                status = "pass" if 0 <= watts <= limit else "fail"
                basis = (f"recorded average output current {average:g} A (peak budget {peak:g} A)" if average is not None
                         else f"peak load {peak:g} A as a conservative sustained estimate")
                message = f"Approximate linear-regulator dissipation {watts:g} W versus allowance ({target:g} - {ambient:g}) / {theta:g} = {limit:g} W, using {basis}; not measured junction temperature."
        add(f"dissipation:{regulator.component_id}", "power", status, [regulator.component_id], message,
            [source.voltage_max, output.voltage_min, *thermal_quantities, regulator.average_output_current]
            + [load.current for load in output.loads])
    return results


def update_outcomes(run: DesignRun) -> None:
    """Derive badges after the caller has installed this revision's code results."""
    current = [finding for finding in run.findings if finding.revision == run.revision and finding.kind == "check"]
    if any(finding.status == "fail" for finding in current):
        run.compatibility = "issues_found"
    elif (not run.review_completed or not run.components or not run.requirements
          or run.lifecycle in {"interrupted", "error", "needs_input"}
          or not any(f.method == "code" for f in current)
          or any(f.status == "unknown" for f in current)
          or set(REVIEW_AREAS) - {f.area for f in current if f.method == "model_review"}
          or not any(f.method == "model_review" and f.status == "pass" for f in current)):
        run.compatibility = "incomplete"
    else:
        run.compatibility = "checked"
    from run_store import bom_rows
    rows = bom_rows(run)
    available = sum(row["availability"] == "available" for row in rows)
    run.sourcing = ("available" if rows and available == len(rows) and all(
                        c.product and c.product.mpn.strip() and c.product.manufacturer.strip() for c in run.components)
                    else "partial" if available else "unknown")
