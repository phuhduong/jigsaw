"""
Pipeline orchestrator — wires the 3-agent pipeline and yields SSE events.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
from langsmith.run_trees import RunTree

from agents.requirements_parser import parse_requirements
from agents.component_retriever import _retrieve_one
from agents.validation_agent import validate_components
from langchain_core.prompts import ChatPromptTemplate
from models import (
    ParsedRequirements,
    RefinementPlan,
    RetrievalResult,
    RetrievedComponent,
)

load_dotenv()

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


def get_llm(temperature: float = 0) -> ChatGoogleGenerativeAI:
    """Create a ChatGoogleGenerativeAI instance from environment config."""
    return ChatGoogleGenerativeAI(
        model=os.getenv("MODEL", "gemini-3.1-flash-lite-preview"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=temperature,
    )


def stream_component_analysis(
    query: str,
    context: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Run the 3-agent pipeline and yield SSE-compatible event dicts.

    hierarchyLevel is set from the canonical HIERARCHY_MAP:
    0=MCU, 1=Power/Sensor, 2=Memory/Antenna, 3=Connector.
    """
    rt = RunTree(name="JigsawPipeline", inputs={"query": query, "context": context})

    try:
        llm = get_llm()

        # --- Agent 1: Parse Requirements ---
        try:
            requirements = parse_requirements(query, context, llm)
        except Exception as e:
            yield {"type": "error", "message": f"Failed to parse requirements: {e}"}
            rt.end(error=str(e))
            rt.post()
            return

        if not requirements.components:
            yield {
                "type": "error",
                "message": "Could not identify specific components from your description. Please provide more detail about what you're building.",
            }
            rt.end()
            rt.post()
            return

        # --- Agent 2: Retrieve Components (one at a time, yielding events) ---
        retrieved: list[RetrievedComponent] = []
        failures: list[str] = []

        for constraint in sorted(requirements.components, key=lambda c: c.hierarchy_level):
            yield {
                "type": "reasoning",
                "componentId": constraint.component_id,
                "componentName": constraint.component_name,
                "reasoning": f"Searching for {constraint.component_name}...",
                "hierarchyLevel": constraint.hierarchy_level,
            }

            try:
                component = _retrieve_one(constraint, llm)
            except Exception as e:
                component = None

            if component:
                retrieved.append(component)
                yield {
                    "type": "selection",
                    "componentId": component.component_id,
                    "componentName": component.component_name,
                    "partData": component.part_data,
                    "hierarchyLevel": component.hierarchy_level,
                }
            else:
                failures.append(constraint.component_id)
                yield {
                    "type": "reasoning",
                    "componentId": constraint.component_id,
                    "componentName": constraint.component_name,
                    "reasoning": f"No results found for {constraint.component_name}.",
                    "hierarchyLevel": constraint.hierarchy_level,
                }

        if not retrieved:
            yield {"type": "error", "message": "Could not find any components. Please try a different description."}
            rt.end(error="No components retrieved")
            rt.post()
            return

        retrieval = RetrievalResult(components=retrieved, failures=failures)

        # --- Agent 3: Validate + Retry Loop ---
        for attempt in range(MAX_RETRIES + 1):
            try:
                validation = validate_components(requirements, retrieval, llm)
            except Exception as e:
                yield {"type": "error", "message": f"Validation failed: {e}"}
                rt.end(error=str(e))
                rt.post()
                return

            if not validation.retry_component_ids or attempt == MAX_RETRIES:
                break

            # Re-search only rejected components
            retry_constraints = [
                c for c in requirements.components
                if c.component_id in validation.retry_component_ids
            ]
            retry_query_map = {
                v.component_id: v.retry_query
                for v in validation.verdicts
                if v.retry_query and v.status == "rejected"
            }
            for c in retry_constraints:
                if c.component_id in retry_query_map:
                    c.search_query = retry_query_map[c.component_id]

            # Re-run searches for failed components
            new_components: list[RetrievedComponent] = []
            for constraint in retry_constraints:
                try:
                    component = _retrieve_one(constraint, llm)
                except Exception:
                    component = None

                if component:
                    new_components.append(component)
                    yield {
                        "type": "selection",
                        "componentId": component.component_id,
                        "componentName": component.component_name,
                        "partData": component.part_data,
                        "hierarchyLevel": component.hierarchy_level,
                    }

            # Update retrieval for next validation pass
            component_map = {c.component_id: c for c in retrieval.components}
            for new_c in new_components:
                component_map[new_c.component_id] = new_c

            retrieval = RetrievalResult(
                components=[
                    component_map[cid]
                    for cid in validation.retry_component_ids
                    if cid in component_map
                ],
                failures=[
                    cid for cid in validation.retry_component_ids
                    if cid not in component_map
                ],
            )

        yield {"type": "complete", "message": "Component analysis complete."}
        rt.end(outputs={"status": "complete"})

    except Exception as e:
        yield {"type": "error", "message": str(e)}
        rt.end(error=str(e))

    rt.post()


REFINEMENT_PROMPT = """\
You are an expert electrical engineer. The user has an existing PCB component selection and wants to modify it.

Current components:
{current_components}

Project summary: {project_summary}

The user's modification request: {modification}

Determine what changes are needed. You can:
1. **Replace** existing components (provide updated ComponentConstraint with new search queries)
2. **Add** new components (provide new ComponentConstraint entries)
3. **Remove** components (list their component_ids)

Rules:
- Only change what the user asked for. Do not modify unrelated components.
- Use the same component_id values as the existing components when replacing.
- For new components, use standard IDs: mcu, power, sensor, memory, antenna, connector, other.
- Search queries should be SHORT and general (e.g., "3.3V buck converter", "SPI flash memory").
- Do NOT include passive components (capacitors, resistors, inductors, LEDs).
"""


def stream_refinement(
    modification: str,
    current_components: list[dict[str, Any]],
    project_summary: str,
) -> Generator[dict[str, Any], None, None]:
    """
    Process a refinement request: diff the modification against current selections,
    re-search only affected components, and yield SSE events.
    """
    rt = RunTree(name="JigsawRefinement", inputs={
        "modification": modification,
        "current_components": current_components,
        "project_summary": project_summary,
    })

    try:
        llm = get_llm()

        # Build current components text for the prompt
        components_text = "\n".join(
            f"- {c['component_id']}: {c['component_name']} "
            f"(MPN: {c.get('part_data', {}).get('mpn', 'N/A')}, "
            f"${c.get('part_data', {}).get('price', 'N/A')})"
            for c in current_components
        )

        # LLM decides what to change
        structured_llm = llm.with_structured_output(RefinementPlan, method="json_schema")
        prompt = ChatPromptTemplate.from_messages([
            ("system", REFINEMENT_PROMPT),
            ("human", "{modification}"),
        ])
        chain = prompt | structured_llm

        try:
            plan = chain.invoke({
                "current_components": components_text,
                "project_summary": project_summary,
                "modification": modification,
            })
        except Exception as e:
            yield {"type": "error", "message": f"Failed to plan refinement: {e}"}
            rt.end(error=str(e))
            rt.post()
            return

        logger.info("Refinement plan: replace=%d, add=%d, remove=%d",
                    len(plan.components_to_replace), len(plan.components_to_add), len(plan.components_to_remove))

        # Yield reasoning about the plan
        yield {
            "type": "reasoning",
            "componentId": "system",
            "componentName": "Refinement",
            "reasoning": plan.reasoning,
            "hierarchyLevel": 0,
        }

        # Handle removals
        for cid in plan.components_to_remove:
            yield {"type": "remove", "componentId": cid}

        # Search for replacements and additions
        all_constraints = plan.components_to_replace + plan.components_to_add
        retrieved: list[RetrievedComponent] = []

        for constraint in sorted(all_constraints, key=lambda c: c.hierarchy_level):
            yield {
                "type": "reasoning",
                "componentId": constraint.component_id,
                "componentName": constraint.component_name,
                "reasoning": f"Searching for {constraint.component_name}...",
                "hierarchyLevel": constraint.hierarchy_level,
            }

            try:
                component = _retrieve_one(constraint, llm)
            except Exception:
                component = None

            if component:
                retrieved.append(component)
                yield {
                    "type": "selection",
                    "componentId": component.component_id,
                    "componentName": component.component_name,
                    "partData": component.part_data,
                    "hierarchyLevel": component.hierarchy_level,
                }
            else:
                yield {
                    "type": "reasoning",
                    "componentId": constraint.component_id,
                    "componentName": constraint.component_name,
                    "reasoning": f"No results found for {constraint.component_name}.",
                    "hierarchyLevel": constraint.hierarchy_level,
                }

        # Validate new picks if any were found
        if retrieved:
            # Build minimal requirements for validation
            requirements = ParsedRequirements(
                project_summary=project_summary,
                components=all_constraints,
            )
            retrieval = RetrievalResult(components=retrieved)

            try:
                validate_components(requirements, retrieval, llm)
            except Exception:
                pass  # Validation failure is non-fatal for refinement

        yield {"type": "complete", "message": "Refinement complete."}
        rt.end(outputs={"status": "complete"})

    except Exception as e:
        yield {"type": "error", "message": str(e)}
        rt.end(error=str(e))

    rt.post()


@traceable(name="ChatResponse")
def get_chat_response(
    query: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Simple LLM chat response for /mcp/query and /mcp/continue routes."""
    llm = get_llm()

    messages = []
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    response = llm.invoke(messages)
    content = response.content
    # LangChain Gemini can return content as a list of blocks — flatten to string
    if isinstance(content, list):
        return " ".join(str(part) for part in content)
    return str(content)
