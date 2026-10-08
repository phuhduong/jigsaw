"""Saved design and structured stage responses. One instance per physical placement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PurchasingOptions(Record):
    board_quantity: int = Field(default=1, ge=1, le=10000, strict=True)
    region: str = Field(default="US", pattern=r"^[A-Z]{2}$")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class Requirement(Record):
    id: str
    clause: str
    description: str
    component_ids: list[str] = Field(default_factory=list)


class Assumption(Record):
    id: str
    description: str


class Question(Record):
    id: str
    requirement_id: str
    question: str
    guidance: str = ""


class PriceBreak(Record):
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class Offer(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    sku: str
    url: str | None = None
    currency: str | None = None
    region: str | None = None
    stock: int | None = Field(default=None, ge=0)
    moq: int | None = Field(default=None, ge=1)
    order_multiple: int | None = Field(default=None, ge=1)
    packaging: str | None = None
    standard_package: int | None = None
    price_breaks: list[PriceBreak] = Field(default_factory=list)
    retrieved_at: str


class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    manufacturer: str
    mpn: str
    package: str | None = None
    description: str = ""
    datasheet_url: str | None = None
    product_url: str | None = None
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    offers: list[Offer] = Field(default_factory=list)
    retrieved_at: str


class ComponentSpec(Record):
    id: str = Field(description="Unique placement ID, e.g. U1, U2, C1; never just a category")
    name: str
    kind: Literal["active", "module", "passive", "connector"] = Field(
        description=(
            "BOM source-policy category. active: powered ICs, drivers and amplifiers; module: purchased "
            "assemblies; passive: resistors, capacitors, dry-contact switches and bare current-limited "
            "indicator LEDs; connector: connectors. Smart LEDs and LED driver ICs are active, not passive."
        )
    )
    purpose: str
    search_query: str = Field(description="Prefer a known exact MPN, otherwise short capability/value query")
    broad_query: str = ""
    support_for: list[str] = Field(default_factory=list)
    document_urls: list[str] = Field(
        default_factory=list, description="Manufacturer guide URL hints; fetched before use"
    )


class Component(ComponentSpec):
    product: Product | None = None
    selection_reason: str = ""
    selection_error: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    document_errors: list[str] = Field(default_factory=list)


NumberBasis = Literal["min", "max", "typical", "nominal", "estimate", "absolute_maximum"]


class SourceNumber(Record):
    """A source interpretation, never a second set of configuration-authored ratings."""

    id: str
    role: Literal[
        "operating_voltage", "output_voltage", "output_tolerance", "input_current", "average_current",
        "supply_current_required", "output_current", "input_high", "input_low",
        "output_high", "output_low", "dropout", "theta_ja", "quiescent_current",
    ] = Field(description="input_current is the mode's peak/design demand. Use average_current only when the source explicitly distinguishes average consumption from peak demand; typical basis alone does not imply average.")
    value: float
    unit: str
    basis: NumberBasis
    supply_factor: float = Field(
        default=0,
        description="For a source formula value + supply_factor * VDD, in volts; e.g. 0.7*VDD uses value=0, factor=0.7. Otherwise zero. Do not substitute nominal VDD.",
    )
    conditions: str = Field(default="", description="Exact applicable mode, package, test/load and board/copper conditions")


class Evidence(Record):
    id: str
    component_ids: list[str]
    document_id: str
    page: int = Field(ge=1, description="Original physical page; HTML page 1")
    kind: Literal["text", "figure"] = Field(
        description="text: verbatim narrative or supplied HTML text. figure: ALL visual PDF tables, charts, diagrams and schematics."
    )
    quote: str = Field(
        description=(
            "For text, a short exact source excerpt (at most 12 words). For figure, the visible table/figure "
            "title or label. Never reconstruct a multi-column row or rewrite wording/units as a quotation."
        )
    )
    fact: str
    conditions: str = ""
    numbers: list[SourceNumber] = Field(
        default_factory=list,
        description="Source-owned numbers needed for power/logic/thermal checks. Separate roles and bounds; ordinary supporting-circuit details remain evidence facts and configuration notes.",
    )


class Quantity(Record):
    value: float = Field(default=0, description="Only authoritative for a declared design assumption, conservative current margin or outward output-voltage margin. Source-bound values are computed by code.")
    unit: str = Field(default="", description="Assumed value's unit. Code materializes sourced values and units.")
    basis: SkipJsonSchema[NumberBasis] = "estimate"
    source_ids: list[str] = Field(default_factory=list, description="SourceNumber IDs, not Evidence IDs. Device ratings must bind the applicable source numbers.")
    calculation: SkipJsonSchema[Literal["direct", "output_min", "output_max", "input_min", "linear_input"]] = "direct"
    binding_error: SkipJsonSchema[str] = ""
    source_conditions: SkipJsonSchema[list[str]] = Field(default_factory=list)
    # Computed by binding and retained in diagnostic reports.
    evidence_ids: SkipJsonSchema[list[str]] = Field(default_factory=list)
    assumption_id: str | None = Field(
        default=None,
        description=(
            "ID of a declared supply/load/thermal design assumption, never a substitute for documented device "
            "operating limits"
        ),
    )


class PowerLoad(Record):
    """A powered device or a passive branch included in the rail's current budget."""

    component_id: str
    voltage_min: Quantity | None = Field(
        default=None,
        description=(
            "Receiving component_id's recommended minimum input voltage, not the proposed rail voltage. A "
            "linear-regulator input requirement may be derived from cited output MAX plus documented "
            "headroom/dropout, while preserving any separate VIN minimum/UVLO restriction. Cite the "
            "underlying source observations even if the calculated value is not printed literally; an "
            "assumption alone is insufficient."
        ),
    )
    voltage_max: Quantity | None = Field(
        default=None,
        description=(
            "Receiving component_id's documented recommended operating MAXIMUM supply voltage. Cite that "
            "receiver's source, never copy the proposed rail's delivered voltage."
        ),
    )
    current: Quantity | None = Field(
        default=None,
        description=(
            "Peak/design load on this supply. For a converter input, derive downstream demand plus losses/own "
            "current in a declared assumption; do not relabel a downstream device rating as the converter's."
        ),
    )


class Rail(Record):
    id: str
    source_component_id: str = Field(description="Selected component ID, or external for an explicitly assumed supply")
    description: str
    voltage_min: Quantity | None = Field(
        default=None,
        description=(
            "Source's lowest delivered voltage under the intended input/load conditions, including relevant "
            "output tolerance and load/line regulation; not the receiver's operating minimum."
        ),
    )
    voltage_max: Quantity | None = Field(
        default=None,
        description=(
            "Source's highest delivered voltage under the intended input/load conditions, including relevant "
            "output tolerance and load/line regulation; not the receiver's operating maximum."
        ),
    )
    available_current: Quantity | None = None
    loads: list[PowerLoad] = Field(
        default_factory=list,
        description=(
            "Powered devices and current-budget loads. A passive branch may leave both operating-voltage "
            "bounds null; review must name this rail and load and verify its ratings/current-limiting arrangement."
        ),
    )
    evidence_ids: list[str] = Field(default_factory=list)


class Endpoint(Record):
    component_id: str
    address: str | None = None
    assumption_id: str | None = Field(
        default=None, description="For component_id='external', the declared off-board tool/interface assumption"
    )


class Interface(Record):
    id: str
    protocol: str
    endpoints: list[Endpoint]
    configuration: str = Field(
        description="Protocol roles, rate and operating assumptions relevant to BOM compatibility; no pin mapping"
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Source observations supporting the shared protocol/resources. A current source-backed signals "
            "review naming this interface can also establish this; numeric signal limits are checked "
            "separately."
        ),
    )


class SignalCheck(Record):
    id: str
    source_component_id: str
    receiver_component_id: str
    description: str
    pullup_rail_id: str | None = Field(
        default=None,
        description=(
            "For an open-drain line, derive its static high level from this recorded pull-up rail; leave "
            "output_high_min null. State a feasible pull-up/rate/loading assumption, not purchased resistor placements."
        ),
    )
    output_high_min: Quantity | None = None
    input_high_min: Quantity | None = None
    output_low_max: Quantity | None = None
    input_low_max: Quantity | None = None


class RegulatorCheck(Record):
    component_id: str
    kind: Literal["linear", "switching"]
    input_rail_id: str
    output_rail_id: str
    dropout: Quantity | None = None
    quiescent_current: Quantity | None = Field(
        default=None,
        description="Regulator's own supply/ground current. Bind its source number or disclose a conservative estimate. Code includes it in linear input current and heat.",
    )
    ambient_max: Quantity | None = Field(
        default=None,
        description=(
            "Maximum ambient temperature in degC for this operating configuration; declare the environmental "
            "assumption."
        ),
    )
    junction_target: Quantity | None = Field(
        default=None,
        description=(
            "Conservative design junction-temperature target in degC, below the device limit; declare the "
            "design assumption, not an invented device rating."
        ),
    )
    theta_ja: Quantity | None = Field(
        default=None,
        description=(
            "Selected package's documented junction-to-ambient thermal resistance in degC/W; cite its source "
            "and state applicable board/copper conditions. Documented typical values are estimates, not "
            "certified board performance."
        ),
    )
    average_output_current: Quantity | None = Field(
        default=None,
        description=(
            "Optional total sustained/average output load for thermal screening only, supported by applicable "
            "current evidence or an explicit workload/duty-cycle assumption. Must not exceed the recorded "
            "peak output-load sum. Leave null to use peak loads conservatively; never reduce rail peak loads "
            "to obtain a thermal pass."
        ),
    )


Area = Literal["requirements", "power", "signals", "support", "evidence"]
REVIEW_AREAS = ("requirements", "power", "signals", "support", "evidence")


class Finding(Record):
    id: str
    revision: int = 0
    area: Area
    method: Literal["code", "model_review"] = "model_review"
    kind: Literal["check", "guidance"] = "check"
    status: Literal["pass", "fail", "unknown", "not_applicable"]
    subject_ids: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    document_id: str | None = None
    explanation: str
    remedy: str = ""

    @property
    def blocks_review(self) -> bool:
        """Only explicit functional/electrical failures determine the verdict."""
        return self.kind == "check" and self.status == "fail" and self.area != "evidence"


class Usage(Record):
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    supplier_calls: int = 0
    documents: int = 0
    pdf_pages: int = 0
    correction_rounds: int = 0
    elapsed_seconds: float = 0


class Limits(Record):
    seconds: int = 480
    model_calls: int = 30
    input_tokens: int = 400000
    output_tokens: int = 64000
    supplier_calls: int = 60
    documents: int = 20
    pdf_pages: int = 120
    functional_blocks: int = 8
    bom_rows: int = 40
    correction_rounds: int = 2


class DesignRun(Record):
    schema_version: int = 1
    # Old snapshots remain readable. Every executed workflow enables current bindings.
    numeric_binding_version: int = 0
    id: str = Field(default_factory=lambda: uuid4().hex)
    parent_run_id: str | None = None
    revision: int = 1
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    lifecycle: Literal["running", "needs_input", "finished", "interrupted", "error"] = "running"
    compatibility: Literal["checked", "issues_found"] | None = None
    sourcing: Literal["available", "partial", "unknown"] = "unknown"
    stage: str = "started"
    terminal_reason: str = ""
    model: str = ""
    model_configuration: dict[str, str] = Field(default_factory=dict)
    prompt_version: str = "41"
    original_request: str
    modification: str | None = None
    options: PurchasingOptions = Field(default_factory=PurchasingOptions)
    summary: str = ""
    requirements: list[Requirement] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    # Retain historical inventories verbatim; current workflows do not generate them.
    source_support_needs: SkipJsonSchema[list[dict[str, Any]]] = Field(default_factory=list)
    support_needs: SkipJsonSchema[list[dict[str, Any]]] = Field(default_factory=list)
    rails: list[Rail] = Field(default_factory=list)
    interfaces: list[Interface] = Field(default_factory=list)
    signal_checks: list[SignalCheck] = Field(default_factory=list)
    regulator_checks: list[RegulatorCheck] = Field(default_factory=list)
    configuration_notes: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    evidence_errors: list[Finding] = Field(default_factory=list)
    review_completed: bool = False
    pending_questions: list[Question] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    limits: Limits = Field(default_factory=Limits)

    def invalidate_review(self) -> None:
        """Any design change needs a fresh whole-BOM review."""
        self.review_completed = False
        self.findings = []
        self.compatibility = None

    def invalidate_configuration(self) -> None:
        """Rebuild operating records after changing parts or source-number identities."""
        self.rails = []
        self.interfaces = []
        self.signal_checks = []
        self.regulator_checks = []
        self.configuration_notes = []
        self.invalidate_review()


class Plan(Record):
    summary: str
    requirements: list[Requirement]
    assumptions: list[Assumption]
    components: list[ComponentSpec]
    configuration_notes: list[str]
    pending_questions: list[Question] = Field(default_factory=list)


class Pick(Record):
    component_id: str
    chosen_index: int = Field(ge=-1)
    reason: str


class Picks(Record):
    picks: list[Pick]


class PageSelection(Record):
    document_id: str
    pages: list[int]
    reason: str


class DocumentRequest(Record):
    component_id: str
    url: str
    reason: str


class ReadingPlan(Record):
    selections: list[PageSelection]
    document_requests: list[DocumentRequest] = Field(default_factory=list)


class SourceApplicability(Record):
    applies: bool
    reason: str


class EvidencePacket(Record):
    applicability: dict[str, SourceApplicability] = Field(
        description="For each selected component ID, state whether this source applies and explain the exact manufacturer/variant or general circuit guidance match. Use applies=false for a mismatched or unestablished source; its facts cannot establish that component's compatibility."
    )
    evidence: list[Evidence]
    missing_facts: list[str] = Field(
        default_factory=list,
        description="Concrete needed facts not established by these pages, not hypothetical future concerns",
    )


class OperatingConfiguration(Record):
    """Engineering update: models cannot write product identities or supplier offers."""

    additional_components: list[ComponentSpec] = Field(
        description="Missing functional components such as power conversion or level translation, not ordinary supporting resistors/capacitors unless explicitly requested."
    )
    rails: list[Rail]
    interfaces: list[Interface] = Field(
        description=(
            "Material communication between purchased components or explicitly requested external "
            "connections. Built-in radio capability and ordinary off-board programming belong in "
            "requirement evidence/configuration notes, not extra board interfaces."
        )
    )
    signal_checks: list[SignalCheck] = Field(
        default_factory=list,
        description=(
            "One assessment per necessary digital driving direction/electrical class, not per wire. "
            "Do not invent active-driver thresholds for a dry-contact switch or an LED. Review their "
            "contact/pull-up or current-limiting/rating compatibility using source/catalog evidence."
        ),
    )
    regulator_checks: list[RegulatorCheck] = Field(default_factory=list)
    assumptions: list[Assumption]
    configuration_notes: list[str]


class Review(Record):
    findings: list[Finding]
    additional_pages: list[PageSelection] = Field(default_factory=list)
    document_requests: list[DocumentRequest] = Field(default_factory=list)


class Correction(Record):
    reason: str
    replace_components: list[ComponentSpec] = Field(default_factory=list)
    add_components: list[ComponentSpec] = Field(default_factory=list)
    remove_component_ids: list[str] = Field(default_factory=list)
    requirement_components: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Repair component-ID mappings for existing requirements only; preserve requirement text",
    )
    reread_component_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Components whose source needs a missing or corrected fact, even on already-read pages; state the "
            "needed fact in configuration_instructions"
        ),
    )
    configuration: OperatingConfiguration | None = Field(
        default=None,
        description=(
            "Complete replacement compatibility record using unchanged selected parts and current evidence; "
            "no additional_components, part changes or source rereads"
        ),
    )
    configuration_instructions: str = ""

    @model_validator(mode="after")
    def assert_direct_configuration_mode(self):
        if self.configuration is not None and (
            self.replace_components
            or self.add_components
            or self.remove_component_ids
            or self.reread_component_ids
            or self.configuration.additional_components
        ):
            raise ValueError(
                "Direct configuration cannot include part changes, source rereads, or additional components"
            )
        return self


class AnalysisRequest(Record):
    query: str = Field(min_length=1, max_length=10000)
    options: PurchasingOptions = Field(default_factory=PurchasingOptions)


class RefinementRequest(Record):
    base_run_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    modification: str | None = Field(default=None, min_length=1, max_length=10000)
    answers: dict[str, str] | None = None

    @model_validator(mode="after")
    def assert_one_instruction(self):
        if (self.modification is None) == (self.answers is None):
            raise ValueError("Provide exactly one of modification or answers")
        if self.answers is not None and (not self.answers or any(not a.strip() for a in self.answers.values())):
            raise ValueError("Answers must be nonempty")
        return self
