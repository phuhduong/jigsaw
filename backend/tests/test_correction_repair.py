"""Correction routing with local records, not electrical acceptance fixtures."""

import unittest
from types import SimpleNamespace

from fakes import SourcePages, configuration_for, drain, gateway_for, workflow_example
from llm import Budget
from models import (
    Assumption,
    ComponentSpec,
    Correction,
    Evidence,
    EvidencePacket,
    OperatingConfiguration,
    PageSelection,
    Pick,
    Picks,
    PowerLoad,
    Quantity,
    ReadingPlan,
    RegulatorCheck,
    SourceNumber,
)
from pipeline import Workflow


def incompatible_supply():
    run = workflow_example()
    run.assumptions[0].description = "External USB 5 V, 100 mA supply"
    run.assumptions.append(Assumption(id="thermal", description="25 C ambient and 100 C junction target"))
    run.documents[0]["url"] = run.components[0].product.product_url
    run.rails[0].voltage_min.value = 4.75
    run.rails[0].voltage_max.value = 5.25
    run.evidence[0].numbers[0].value = 3
    run.evidence[0].quote = run.evidence[0].fact = "Operating supply 3.0 to 3.6 V"
    for load in run.rails[0].loads:
        load.voltage_min.value = 3
    run.requirements[0].component_ids = []
    return run


class RegulatorSource(SourcePages):
    def fetch(self, url, **kwargs):
        return {"document_id": "regulator", "url": url, "page_count": 1, "media_type": "text/html"}


class CorrectionRepairTests(unittest.TestCase):
    def test_mapping_repair_cannot_clear_incompatible_module_supply(self):
        run = incompatible_supply()
        workflow = Workflow(SourcePages(), object(), gateway_for(run))
        workflow._apply_correction(
            run,
            Correction(reason="Repair mapping", requirement_components={"req:one": ["U1", "U2"]}),
        )
        drain(workflow._review_bom(run, Budget(run), []))
        self.assertEqual(run.compatibility, "issues_found")
        self.assertTrue(any(f.id == "code:voltage:supply:U1" and f.status == "fail" for f in run.findings))

    def test_adding_regulator_selects_reads_and_reviews_the_repaired_bom(self):
        run = incompatible_supply()
        original_requirements = [(r.clause, r.description) for r in run.requirements]
        product = run.components[0].product.model_copy(
            update={"mpn": "LDO-1", "datasheet_url": "https://example.com/regulator"}
        ).model_dump()
        supplier = SimpleNamespace(search=lambda *a, **k: [product], get_product=lambda *a, **k: product)

        def configure(payload, blocks):
            proposal = configuration_for(run)
            observation = next(e for e in run.evidence if e.component_ids == ["U3"])

            def rating(role, basis=None):
                number = next(n for n in observation.numbers if n.role == role and (basis is None or n.basis == basis))
                return Quantity(source_ids=[number.id])

            output = proposal.rails[0]
            source = output.model_copy(deep=True)
            source.id, source.description = "usb", "External USB supply"
            source.loads = [
                PowerLoad(
                    component_id="U3",
                    voltage_min=rating("operating_voltage", "min"),
                    voltage_max=rating("operating_voltage", "max"),
                    current=Quantity(calculation="linear_input"),
                )
            ]
            output.source_component_id = "U3"
            output.voltage_min = rating("output_voltage", "min")
            output.voltage_max = rating("output_voltage", "max")
            output.available_current = rating("output_current")
            proposal.rails = [source, output]
            proposal.regulator_checks = [
                RegulatorCheck(
                    component_id="U3",
                    kind="linear",
                    input_rail_id="usb",
                    output_rail_id="supply",
                    dropout=rating("dropout"),
                    theta_ja=rating("theta_ja"),
                    quiescent_current=rating("quiescent_current"),
                    ambient_max=Quantity(value=25, unit="degC", basis="estimate", assumption_id="thermal"),
                    junction_target=Quantity(value=100, unit="degC", basis="estimate", assumption_id="thermal"),
                )
            ]
            return proposal

        gateway = gateway_for(
            run,
            {
                Picks: Picks(picks=[Pick(component_id="U3", chosen_index=0, reason="Local compatible regulator")]),
                ReadingPlan: ReadingPlan(
                    selections=[PageSelection(document_id="regulator", pages=[1], reason="Regulator ratings")]
                ),
                EvidencePacket: EvidencePacket(
                    applicability={"U3": {"applies": True, "reason": "Exact fixture regulator"}},
                    evidence=[
                        Evidence(
                            id="regulator-spec",
                            component_ids=["U3"],
                            document_id="regulator",
                            page=1,
                            kind="text",
                            quote="Input 3.5 to 6 V; output 3.3 V",
                            fact=(
                                "Input 3.5 to 6 V; output 3.3 V at up to 100 mA. "
                                "Dropout 0.2 V; theta_JA 100 degC/W; quiescent current 1 mA."
                            ),
                            numbers=[
                                SourceNumber(id=f"n{index}", role=role, value=value, unit=unit, basis=basis)
                                for index, (role, value, unit, basis) in enumerate(
                                    [
                                        ("operating_voltage", 3.5, "V", "min"),
                                        ("operating_voltage", 6, "V", "max"),
                                        ("output_voltage", 3.3, "V", "min"),
                                        ("output_voltage", 3.3, "V", "max"),
                                        ("output_current", 100, "mA", "min"),
                                        ("dropout", 0.2, "V", "max"),
                                        ("theta_ja", 100, "degC/W", "typical"),
                                        ("quiescent_current", 1, "mA", "max"),
                                    ]
                                )
                            ],
                        )
                    ],
                ),
                OperatingConfiguration: configure,
            },
        )
        workflow, budget = Workflow(RegulatorSource(), supplier, gateway), Budget(run)
        repair = Correction(
            reason="Add required power conversion",
            add_components=[
                ComponentSpec(
                    id="U3", name="Regulator", kind="active", purpose="5 V to 3.3 V", search_query="LDO-1"
                )
            ],
            requirement_components={"req:one": ["U1", "U2", "U3"]},
            configuration_instructions="Use the new regulator between USB and the modules.",
        )
        workflow._apply_correction(run, repair)
        drain(workflow._select_components(run, budget))
        pages = drain(workflow._complete_correction(run, budget, repair, []))
        drain(workflow._review_bom(run, budget, pages))
        self.assertEqual(run.compatibility, "checked")
        self.assertEqual(run.components[-1].product.mpn, "LDO-1")
        self.assertEqual(run.components[-1].document_ids, ["regulator"])
        self.assertEqual([(r.clause, r.description) for r in run.requirements], original_requirements)
