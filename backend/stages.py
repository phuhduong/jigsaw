"""Structured model stages; the workflow owns execution and saved state."""

import re
from decimal import Decimal

from models import Picks, Plan, Review
from prompts import PLAN, REVIEW, SELECT
from run_store import design_context, product_context

_CAPACITANCE = re.compile(r"(?<![\w.])([0-9]+(?:\.[0-9]+)?)\s*([munpµμ]?)\s*[Ff]\b")
_SCALE = {
    "": "1",
    "m": "0.001",
    "u": "0.000001",
    "µ": "0.000001",
    "μ": "0.000001",
    "n": "0.000000001",
    "p": "0.000000000001",
}


def find_capacitance_mismatch(component, product):
    """Reject explicit nominal-value contradictions, not infer a capacitor's fitness."""
    if component.kind != "passive":
        return None
    query = component.search_query
    requested = list(_CAPACITANCE.finditer(query))
    # Ranges/alternatives and MPN-only hints remain the source-assisted review's job.
    if len(requested) != 1 or re.search(
        r"[<>≤≥~–]|\d\s*-\s*\d|\b(?:minimum|maximum|at least|at most|up to|to|or)\b", query, re.I
    ):
        return None
    fields = [
        str(item.get("value", "")).strip()
        for item in product.get("parameters") or []
        if str(item.get("name", "")).lower() == "capacitance"
    ]
    if len(fields) != 1 or not (actual := _CAPACITANCE.fullmatch(fields[0])):
        return None
    desired = requested[0]

    def farads(match):
        return Decimal(match[1]) * Decimal(_SCALE[match[2]])

    if farads(desired) != farads(actual):
        return f"Catalog capacitance {fields[0]} does not match requested nominal {desired[0]}"
    return None


def plan_requirements(gateway, budget, run):
    plan = yield from gateway.call(
        budget,
        "plan",
        Plan,
        PLAN,
        {
            "original_request": run.original_request,
            "modification": run.modification,
            "previous_design": design_context(run) if run.parent_run_id else None,
            "purchasing": run.options.model_dump(),
        },
        max_output=2800,
    )
    # Requirement subjects must not collide with physical resistor IDs such as R1.
    identifiers = {item.id: item.id if item.id.startswith("req:") else f"req:{item.id}" for item in plan.requirements}
    for requirement in plan.requirements:
        requirement.id = identifiers[requirement.id]
    for question in plan.pending_questions:
        question.requirement_id = identifiers.get(question.requirement_id, question.requirement_id)
    return plan


def select_candidates(gateway, budget, run, candidates):
    groups = {}
    for component_id, products in candidates.items():
        identity = tuple((p["manufacturer"], p["mpn"]) for p in products)
        if identity not in groups:
            groups[identity] = {
                "component_ids": [],
                "candidates": [product_context(p, run.options.board_quantity) for p in products],
            }
        groups[identity]["component_ids"].append(component_id)
    return (
        yield from gateway.call(
            budget,
            "select",
            Picks,
            SELECT,
            {
                "design": design_context(run),
                "candidate_groups": list(groups.values()),
                "instruction": "Return a Pick for EVERY component_id in every group; indices are relative to that group's candidates.",
                "options": run.options,
            },
            max_output=2200,
        )
    )


def review_bom(gateway, budget, run, blocks, pdf_pages, inventory=None, prior_requirements=None):
    return (
        yield from gateway.call(
            budget,
            "review",
            Review,
            REVIEW,
            {
                "original_request": run.original_request,
                "prior_requirements": prior_requirements or [],
                "latest_modification": run.modification,
                "design": design_context(run),
                "source_inventory": inventory or [],
            },
            blocks,
            max_output=4200,
            pdf_pages=pdf_pages,
        )
    )
