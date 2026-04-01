"""
Agent 2: Component Retriever
Deterministic search via DigiKey + LLM pick of best result per constraint.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

from models import (
    ComponentConstraint,
    ComponentPick,
    RetrievedComponent,
)
from tools import search_components

PICK_SYSTEM_PROMPT = """\
You are an expert at selecting electronic components for custom PCB designs.

Given a component requirement and a list of search results from DigiKey, pick the single best match.

Consider:
- Voltage compatibility with the requirement
- Interface support (I2C, SPI, UART, etc.)
- Package match if specified
- General fitness for the described use case
- Price (prefer lower cost when specs are comparable)

Selection priority (pick the highest-priority option available):
1. Bare ICs / discrete components — ideal for custom PCB designs
2. Modules (e.g., ESP32 module) — acceptable when no bare IC is available
3. Development boards / eval kits — acceptable ONLY if nothing else matches the required capabilities (e.g., WiFi, Bluetooth)

IMPORTANT: The component MUST match the required capabilities. A bare IC that lacks required features (e.g., a basic 8-bit PIC when WiFi is needed) is WORSE than a module or dev board that has them. Always prioritize capability match over form factor.

Set chosen_index to -1 ONLY if the results are completely unrelated to the requirement (wrong component category entirely).

Return the index (0-based) of the best result, or -1 if none are suitable, and explain why."""


@traceable(name="Agent2_RetrieveComponent")
def _retrieve_one(
    constraint: ComponentConstraint,
    llm: ChatGoogleGenerativeAI,
) -> RetrievedComponent | None:
    """Search DigiKey for one constraint and use LLM to pick the best result."""
    specs = {}
    if constraint.voltage:
        specs["voltage"] = constraint.voltage
    if constraint.interfaces:
        specs["interface"] = constraint.interfaces[0]
    if constraint.package:
        specs["package"] = constraint.package

    logger = logging.getLogger(__name__)

    # Try queries in order: specific search query, then simplified fallback
    queries_to_try = [
        (constraint.search_query, specs if specs else None),
        (constraint.component_name, None),
    ]

    last_results = None
    last_query = None

    for query, query_specs in queries_to_try:
        logger.info(
            "Searching for %s: query=%r, specs=%r",
            constraint.component_name, query, query_specs,
        )
        results = search_components(query, query_specs)
        logger.info(
            "Search returned %d results for %s",
            len(results) if results else 0, constraint.component_name,
        )

        if not results or (len(results) == 1 and results[0].get("mpn") == "ERROR"):
            logger.warning("No usable results for %s with query=%r, trying next", constraint.component_name, query)
            continue

        # LLM picks — may reject all results (returns None)
        chosen_index = _llm_pick(constraint, results, llm, logger)
        if chosen_index is not None:
            return RetrievedComponent(
                component_id=constraint.component_id,
                component_name=constraint.component_name,
                hierarchy_level=constraint.hierarchy_level,
                part_data=results[chosen_index],
                search_query_used=query,
            )

        # Remember last valid results in case all queries get rejected
        last_results = results
        last_query = query

    # If LLM rejected all results from every query, fall back to first result
    # from the last successful search. Something is better than nothing.
    if last_results:
        logger.warning("LLM rejected all results for %s, falling back to first result", constraint.component_name)
        return RetrievedComponent(
            component_id=constraint.component_id,
            component_name=constraint.component_name,
            hierarchy_level=constraint.hierarchy_level,
            part_data=last_results[0],
            search_query_used=last_query or constraint.search_query,
        )

    logger.warning("All search attempts failed for %s", constraint.component_name)
    return None


def _llm_pick(
    constraint: ComponentConstraint,
    results: list[dict],
    llm: ChatGoogleGenerativeAI,
    logger: logging.Logger,
) -> int | None:
    """Use LLM to pick the best result. Returns index or None if all rejected."""
    try:
        structured_llm = llm.with_structured_output(ComponentPick, method="json_schema")
        prompt = ChatPromptTemplate.from_messages([
            ("system", PICK_SYSTEM_PROMPT),
            ("human", "Requirement:\n{requirement}\n\nSearch results:\n{results}"),
        ])
        chain = prompt | structured_llm

        requirement_text = (
            f"{constraint.component_name}: {constraint.description}"
            f"\nVoltage: {constraint.voltage or 'not specified'}"
            f"\nInterfaces: {', '.join(constraint.interfaces) if constraint.interfaces else 'not specified'}"
            f"\nPackage: {constraint.package or 'not specified'}"
        )
        if constraint.notes:
            requirement_text += f"\nNotes: {constraint.notes}"

        results_text = "\n".join(
            f"[{i}] {r.get('mpn', 'N/A')} by {r.get('manufacturer', 'N/A')} — "
            f"{r.get('description', 'N/A')} | ${r.get('price', 'N/A')} | "
            f"voltage: {r.get('voltage', 'N/A')} | package: {r.get('package', 'N/A')} | "
            f"interfaces: {r.get('interfaces', 'N/A')}"
            for i, r in enumerate(results)
        )

        pick = chain.invoke({
            "requirement": requirement_text,
            "results": results_text,
        })

        if pick.chosen_index == -1:
            logger.info("LLM rejected all %d results for %s: %s", len(results), constraint.component_name, pick.reasoning)
            return None
        if 0 <= pick.chosen_index < len(results):
            return pick.chosen_index
    except Exception:
        pass

    # Fallback: pick first result. Agent 3 is the quality gate.
    return 0
