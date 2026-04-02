"""
Pydantic data models for the 3-agent pipeline.
These define the contracts between agents.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# Canonical mapping from component_id -> hierarchy level
HIERARCHY_MAP = {
    "mcu": 0,
    "power": 1,
    "sensor": 1,
    "memory": 2,
    "antenna": 2,
    "connector": 3,
    "other": 3,
}


class ComponentConstraint(BaseModel):
    """Single component requirement extracted by Agent 1."""

    component_id: Literal["mcu", "power", "sensor", "memory", "antenna", "connector", "other"] = Field(description="Component category")
    component_name: str = Field(description="Human-readable name, e.g. 'Microcontroller', 'Power Management'")
    hierarchy_level: int = Field(description="Dependency order: 0=MCU, 1=Power/Sensor, 2=Memory/Antenna, 3=Passive/Connector")
    description: str = Field(description="What the user needs from this component")
    voltage: str | None = Field(default=None, description="Operating voltage requirement, e.g. '3.3V'")
    interfaces: list[str] = Field(default_factory=list, description="Required interfaces, e.g. ['I2C', 'SPI']")
    package: str | None = Field(default=None, description="Package type preference, e.g. 'QFN', 'SOT-23'")
    notes: str | None = Field(default=None, description="Any additional specs: current rating, frequency, temperature range, etc.")
    search_query: str = Field(description="Suggested DigiKey search string for this component")

    @field_validator("hierarchy_level", mode="before")
    @classmethod
    def clamp_hierarchy(cls, v: Any, info) -> int:
        """Force hierarchy_level to the canonical value based on component_id."""
        data = info.data
        if "component_id" in data and data["component_id"] in HIERARCHY_MAP:
            return HIERARCHY_MAP[data["component_id"]]
        if isinstance(v, int):
            return max(0, min(3, v))
        return 3


class ParsedRequirements(BaseModel):
    """Output of Agent 1: structured requirements for all components."""

    project_summary: str = Field(description="Brief summary of what the user is building")
    components: list[ComponentConstraint] = Field(description="Required components sorted by hierarchy_level ascending")
    board_voltage: str | None = Field(default=None, description="Overall board voltage, e.g. '3.3V', '5V'")
    notes: str | None = Field(default=None, description="Any project-level context or constraints")


class ComponentPick(BaseModel):
    """Agent 2's selection of the best component from search results."""

    chosen_index: int = Field(description="Index of the best matching component in the results list (0-based). Set to -1 if NONE of the results are suitable (e.g., all are dev boards instead of bare ICs).")
    reasoning: str = Field(description="Why this component best matches the constraint, or why all results were rejected")


class RetrievedComponent(BaseModel):
    """A single retrieved and selected component from DigiKey."""

    component_id: str
    component_name: str
    hierarchy_level: int
    part_data: dict[str, Any] = Field(description="Raw DigiKey result: mpn, manufacturer, description, price, etc.")
    search_query_used: str


class RetrievalResult(BaseModel):
    """Output of Agent 2: all retrieved components."""

    components: list[RetrievedComponent] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list, description="component_ids where search returned no usable results")


class ValidationVerdict(BaseModel):
    """Agent 3's verdict for a single component."""

    component_id: str = Field(description="The component_id being validated")
    status: Literal["approved", "rejected"] = Field(description="Whether the component meets the original constraints")
    reasoning: str = Field(description="Explanation including any unverifiable constraints flagged as such")
    retry_query: str | None = Field(default=None, description="Suggested better search query if rejected")


class ValidationResult(BaseModel):
    """Output of Agent 3: collected verdicts."""

    verdicts: list[ValidationVerdict] = Field(default_factory=list)
    retry_component_ids: list[str] = Field(default_factory=list, description="component_ids that need re-search; empty means all approved")


class RefinementPlan(BaseModel):
    """LLM output: what to change based on the user's modification request."""

    components_to_replace: list[ComponentConstraint] = Field(default_factory=list, description="Components to re-search with updated constraints")
    components_to_add: list[ComponentConstraint] = Field(default_factory=list, description="New components to add")
    components_to_remove: list[str] = Field(default_factory=list, description="component_ids to remove from the design")
    reasoning: str = Field(description="Brief explanation of what changes are being made and why")
