"""
Agent 3: Validation Agent
Validates every retrieved component against the original constraints.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

from models import (
    ComponentConstraint,
    ParsedRequirements,
    RetrievalResult,
    RetrievedComponent,
    ValidationResult,
    ValidationVerdict,
)

VALIDATION_SYSTEM_PROMPT = """\
You are an expert electrical engineer validating a component selection for a PCB design.

Given:
- The original requirement for a component
- The selected part from DigiKey

Validate whether this part meets the requirement. Check:
1. Voltage compatibility — does the part's operating voltage match or fall within the required range?
2. Interface support — does the part support the required interfaces (I2C, SPI, UART, etc.)?
3. Package match — if a package was specified, does the part match?
4. General fitness — does the part's description match the intended use?

Important rules:
- If the DigiKey data is MISSING a field (e.g., no voltage listed), mark it as "unverifiable" in your reasoning. Do NOT guess or assume — just note what couldn't be confirmed. You may still approve the part if everything else checks out.
- If the part clearly does NOT meet a stated requirement, reject it and suggest a better search query.
- Be practical: minor mismatches (e.g., slightly different package variant) are acceptable if the part is functionally correct."""

CROSS_CHECK_SYSTEM_PROMPT = """\
You are an expert electrical engineer doing a final cross-component compatibility check for a PCB design.

Given all approved components for a project, check for:
1. Voltage conflicts — are all components compatible with the board voltage?
2. Interface bus conflicts — any I2C address collisions or SPI bus contention?
3. Power budget — can the power supply handle the total current draw?

Only flag genuine compatibility issues. If you cannot verify something due to missing data, note it as unverifiable rather than rejecting."""


@traceable(name="Agent3_ValidateComponent")
def _validate_one(
    constraint: ComponentConstraint,
    retrieved: RetrievedComponent,
    board_voltage: str | None,
    llm: ChatGoogleGenerativeAI,
) -> ValidationVerdict:
    """Validate a single component against its constraint."""
    structured_llm = llm.with_structured_output(ValidationVerdict, method="json_schema")

    prompt = ChatPromptTemplate.from_messages([
        ("system", VALIDATION_SYSTEM_PROMPT),
        ("human", (
            "Component requirement:\n{requirement}\n\n"
            "Board voltage: {board_voltage}\n\n"
            "Selected part:\n{part}"
        )),
    ])

    chain = prompt | structured_llm

    requirement_text = (
        f"component_id: {constraint.component_id}\n"
        f"Name: {constraint.component_name}\n"
        f"Description: {constraint.description}\n"
        f"Voltage: {constraint.voltage or 'not specified'}\n"
        f"Interfaces: {', '.join(constraint.interfaces) if constraint.interfaces else 'not specified'}\n"
        f"Package: {constraint.package or 'not specified'}"
    )
    if constraint.notes:
        requirement_text += f"\nNotes: {constraint.notes}"

    part_data = retrieved.part_data
    part_text = (
        f"MPN: {part_data.get('mpn', 'N/A')}\n"
        f"Manufacturer: {part_data.get('manufacturer', 'N/A')}\n"
        f"Description: {part_data.get('description', 'N/A')}\n"
        f"Price: ${part_data.get('price', 'N/A')}\n"
        f"Voltage: {part_data.get('voltage', 'NOT PROVIDED')}\n"
        f"Package: {part_data.get('package', 'NOT PROVIDED')}\n"
        f"Interfaces: {part_data.get('interfaces', 'NOT PROVIDED')}"
    )

    return chain.invoke({
        "requirement": requirement_text,
        "board_voltage": board_voltage or "not specified",
        "part": part_text,
    })


@traceable(name="Agent3_ValidationAgent")
def validate_components(
    requirements: ParsedRequirements,
    retrieval: RetrievalResult,
    llm: ChatGoogleGenerativeAI,
) -> ValidationResult:
    """Validate all retrieved components against original constraints."""
    constraint_map = {c.component_id: c for c in requirements.components}

    verdicts: list[ValidationVerdict] = []
    retry_ids: list[str] = []

    for retrieved in retrieval.components:
        constraint = constraint_map.get(retrieved.component_id)
        if not constraint:
            continue

        verdict = _validate_one(constraint, retrieved, requirements.board_voltage, llm)
        # Ensure component_id is set correctly (LLM might alter it)
        verdict.component_id = retrieved.component_id
        verdicts.append(verdict)

        if verdict.status == "rejected":
            retry_ids.append(retrieved.component_id)

    return ValidationResult(verdicts=verdicts, retry_component_ids=retry_ids)
