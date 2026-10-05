"""Fixed local records and responses for core tests, not engineering acceptance fixtures."""

from models import (
    REVIEW_AREAS,
    Assumption,
    Component,
    ComponentSpec,
    DesignRun,
    Endpoint,
    Evidence,
    EvidencePacket,
    Finding,
    Interface,
    Offer,
    OperatingConfiguration,
    PageSelection,
    Plan,
    PowerLoad,
    PriceBreak,
    Product,
    Quantity,
    Rail,
    Requirement,
    Review,
    SignalCheck,
    SourceNumber,
    SourceSupportNeed,
    SupportNeed,
)
from numeric import bind_quantities
from pipeline import Workflow


def example():
    product = Product(
        manufacturer="Example",
        mpn="SENSOR-1",
        package="MODULE",
        retrieved_at="2026-09-13T00:00:00Z",
        product_url="https://example.com/sensor",
        offers=[
            Offer(
                sku="SENSOR-CT",
                stock=100,
                currency="USD",
                region="US",
                moq=1,
                retrieved_at="2026-09-13T00:00:00Z",
                price_breaks=[PriceBreak(quantity=1, unit_price=2)],
            )
        ],
    )
    run = DesignRun(
        original_request="Two sensors",
        lifecycle="finished",
        review_completed=True,
        assumptions=[Assumption(id="supply", description="External 3.3 V supply")],
        requirements=[
            Requirement(id="req", clause="Two sensors", description="Two sensors", component_ids=["U1", "U2"])
        ],
    )
    run.components = [
        Component(
            id=key,
            name="Sensor",
            kind="module",
            purpose="Sensing",
            search_query="SENSOR-1",
            product=product.model_copy(deep=True),
            document_ids=["doc"],
        )
        for key in ("U1", "U2")
    ]
    run.documents = [{"document_id": "doc", "page_count": 1}]
    run.evidence = [
        Evidence(
            id="spec",
            component_ids=["U1", "U2"],
            document_id="doc",
            page=1,
            kind="text",
            quote="Operating supply 2.7 to 3.6 V",
            fact="Operating supply 2.7–3.6 V",
            numbers=[
                SourceNumber(id=f"specN{index}", role=role, value=value, unit=unit, basis=basis)
                for index, (role, value, unit, basis) in enumerate(
                    [
                        ("operating_voltage", 2.7, "V", "min"),
                        ("operating_voltage", 3.6, "V", "max"),
                        ("input_current", 10, "mA", "typical"),
                        ("input_high", 2.3, "V", "min"),
                        ("input_low", 0.9, "V", "max"),
                        ("output_low", 0.4, "V", "max"),
                    ],
                    1,
                )
            ],
        )
    ]

    def voltage(value, basis):
        number = {2.7: 1, 3.6: 2, 2.3: 4, 0.9: 5, 0.4: 6}[value]
        return Quantity(value=value, unit="V", basis=basis, evidence_ids=["spec"], source_ids=[f"specN{number}"])

    run.rails = [
        Rail(
            id="supply",
            source_component_id="external",
            description="External supply",
            voltage_min=Quantity(value=3.3, unit="V", basis="estimate", assumption_id="supply"),
            voltage_max=Quantity(value=3.3, unit="V", basis="estimate", assumption_id="supply"),
            available_current=Quantity(value=100, unit="mA", basis="estimate", assumption_id="supply"),
            loads=[
                PowerLoad(
                    component_id=key,
                    voltage_min=voltage(2.7, "min"),
                    voltage_max=voltage(3.6, "max"),
                    current=Quantity(
                        value=10, unit="mA", basis="typical", evidence_ids=["spec"], source_ids=["specN3"]
                    ),
                )
                for key in ("U1", "U2")
            ],
        )
    ]
    run.interfaces = [
        Interface(
            id="bus",
            protocol="I2C",
            configuration="100 kHz; distinct configured addresses",
            evidence_ids=["spec"],
            endpoints=[Endpoint(component_id="U1", address="0x44"), Endpoint(component_id="U2", address="0x45")],
        )
    ]
    run.signal_checks = [
        SignalCheck(
            id=f"{source}_to_{receiver}",
            source_component_id=source,
            receiver_component_id=receiver,
            description="Fixture open-drain electrical class",
            pullup_rail_id="supply",
            input_high_min=voltage(2.3, "min"),
            input_low_max=voltage(0.9, "max"),
            output_low_max=voltage(0.4, "max"),
        )
        for source, receiver in (("U1", "U2"), ("U2", "U1"))
    ]
    run.findings = [
        Finding(
            id=area,
            revision=1,
            area=area,
            status="pass",
            subject_ids=["req"] if area == "requirements" else ["U1", "U2"],
            evidence_ids=["spec"],
            explanation="Fixture review",
        )
        for area in REVIEW_AREAS
    ]
    return run


def legacy_support_example():
    """A saved circuit-completeness-era record, not the current workflow target."""
    run = example()
    run.evidence[0].quote += "; U1 requires a 4.7 uF bypass capacitor."
    run.evidence[0].fact += "; U1 requires a 4.7 uF bypass capacitor."
    run.components.append(
        Component(
            id="C1",
            name="Capacitor",
            kind="passive",
            purpose="U1 bypass",
            search_query="CAP-1",
            product=run.components[0].product.model_copy(update={"mpn": "CAP-1", "package": "0603"}),
        )
    )
    run.source_support_needs = [
        SourceSupportNeed(
            id="D1S1",
            purpose="U1 bypass",
            parent_ids=["U1"],
            necessity="required",
            connection_requirement="One 4.7 uF bypass capacitor for U1",
            evidence_ids=["spec"],
            document_id="doc",
        )
    ]
    run.support_needs = [
        SupportNeed(
            id="D1S1",
            purpose="U1 bypass",
            parent_ids=["U1"],
            necessity="required",
            status="satisfied",
            component_ids=["C1"],
            evidence_ids=["spec"],
        )
    ]
    return run


def component_spec(component):
    return ComponentSpec(**component.model_dump(include=set(ComponentSpec.model_fields)))


def plan_for(run):
    return Plan(
        summary="Local fixture",
        requirements=[r.model_copy(deep=True) for r in run.requirements],
        assumptions=run.assumptions,
        components=[component_spec(c) for c in run.components],
        configuration_notes=[],
    )


def review_for(run):
    return Review(
        findings=[
            Finding(
                id=area,
                area=area,
                status="pass",
                subject_ids=[r.id for r in run.requirements]
                if area == "requirements"
                else [c.id for c in run.components],
                evidence_ids=[e.id for e in run.evidence],
                explanation="Local fixture review",
            )
            for area in REVIEW_AREAS
        ]
    )


def configuration_for(run):
    return OperatingConfiguration(**run.model_dump(include=set(OperatingConfiguration.model_fields)), additional_components=[])


def workflow_example():
    run = example()
    run.lifecycle, run.requirements[0].id = "running", "req:one"
    run.documents[0].update(media_type="text/html", pages_interpreted=[1])
    run.numeric_binding_version = 1
    bind_quantities(run, {e.id: e for e in run.evidence})
    return run


def split_source_example():
    run = workflow_example()
    original = run.evidence[0]
    run.documents, run.evidence = [], []
    for component, identifier, ref in zip(run.components, ("doc", "other"), ("D1E1", "other-spec")):
        component.document_ids = [identifier]
        component.product.datasheet_url = f"https://example.com/{identifier}"
        run.documents.append(
            {
                "document_id": identifier,
                "url": component.product.datasheet_url,
                "page_count": 1,
                "media_type": "text/html",
                "pages_read": [1],
                "pages_interpreted": [1],
            }
        )
        observation = original.model_copy(
            deep=True, update={"id": ref, "document_id": identifier, "component_ids": [component.id]}
        )
        for number in observation.numbers:
            number.id = number.id.replace("spec", ref, 1)
        run.evidence.append(observation)
        load = next(load for load in run.rails[0].loads if load.component_id == component.id)
        for quantity in (load.voltage_min, load.voltage_max, load.current):
            quantity.evidence_ids = [ref]
            quantity.source_ids = [key.replace("spec", ref, 1) for key in quantity.source_ids]
        for signal in run.signal_checks:
            if signal.source_component_id == component.id:
                signal.output_low_max.evidence_ids = [ref]
                signal.output_low_max.source_ids = [f"{ref}N6"]
            if signal.receiver_component_id == component.id:
                signal.input_high_min.evidence_ids = signal.input_low_max.evidence_ids = [ref]
                signal.input_high_min.source_ids = [f"{ref}N4"]
                signal.input_low_max.source_ids = [f"{ref}N5"]
    run.interfaces[0].evidence_ids = [e.id for e in run.evidence]
    return run


def replacement_source_example():
    run = workflow_example()
    run.components[0].document_ids = ["replacement"]
    run.documents.append({"document_id": "replacement", "page_count": 1, "media_type": "text/html"})
    run.evidence.append(run.evidence[0].model_copy(update={"id": "obsolete", "component_ids": ["U1"]}))
    run.evidence_errors = [
        Finding(
            id=f"gap:{doc}",
            document_id=doc,
            area="evidence",
            method="code",
            status="unknown",
            subject_ids=owners,
            explanation="Unresolved source fact",
        )
        for doc, owners in (("doc", ["U1", "U2"]), ("replacement", ["U1"]))
    ]
    return run


def replacement_packet(payload, blocks):
    owner = payload["components"][0]["id"]
    previous = payload["previous_observations"]
    observation = (previous[0] if previous else example().evidence[0]).model_copy(
        deep=True,
        update={"component_ids": [owner], "document_id": "replacement" if owner == "U1" else "doc"}
    )
    return EvidencePacket(
        applicability={owner: {"applies": True, "reason": "Exact fixture sensor variant"}}, evidence=[observation]
    )


def drain(generator):
    """Consume progress events and return the generator's final result."""
    while True:
        try:
            next(generator)
        except StopIteration as result:
            return result.value


class Gateway:
    """One fixed response or callback per requested schema; unexpected calls fail."""

    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def call(self, budget, stage, schema, instructions, payload, blocks=None, **kwargs):
        self.calls.append({"schema": schema, "payload": payload, "blocks": blocks or []})
        yield {"type": "progress"}
        for accepted, response in self.responses.items():
            if issubclass(schema, accepted):
                return response(payload, blocks or []) if callable(response) else response.model_copy(deep=True)
        raise AssertionError(f"Unexpected model response requested: {schema.__name__}")

    def calls_for(self, schema):
        return [call for call in self.calls if issubclass(call["schema"], schema)]


def gateway_for(run, responses=None):
    return Gateway({Plan: lambda p, b: plan_for(run), Review: lambda p, b: review_for(run), **(responses or {})})


class SourcePages:
    def pages(self, identifier, pages, **kwargs):
        return [{"type": "text", "text": identifier}]

    def inventory(self, identifier):
        return {
            "document_id": identifier,
            "url": "https://example.com/source",
            "title": "Fixture",
            "page_count": 1,
            "pages": [],
            "links": [],
        }

    def quote_matches(self, *args):
        return True


class SeededWorkflow(Workflow):
    """Start with the supplied BOM, but exercise real explicitly requested rereads."""

    completion_calls = 0

    def _source_and_configure(self, run, budget, instructions="", source_component_ids=None):
        self.completion_calls += 1
        if source_component_ids is not None:
            return (yield from super()._source_and_configure(run, budget, instructions, source_component_ids))
        yield {"type": "progress"}
        return [PageSelection(document_id=d["document_id"], pages=[1], reason="Local evidence") for d in run.documents]
