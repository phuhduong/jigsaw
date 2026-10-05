"""Bounded catalog selection and value checks using local candidates."""

import unittest

from fakes import Gateway, component_spec, configuration_for
from llm import Budget
from models import Component, Correction, DesignRun, OperatingConfiguration, Pick, Picks
from pipeline import Workflow
from stages import find_capacitance_mismatch


class SelectionTests(unittest.TestCase):
    def test_configuration_selects_only_new_parts_and_correction_can_retry_old_parts(self):
        old = Component(
            id="R1", name="Old", kind="passive", purpose="Pull-up", search_query="old", selection_error="No fit"
        )
        new = Component(
            id="R2", name="New", kind="passive", purpose="Pull-up", search_query="new", broad_query="new broad"
        )
        run = DesignRun(original_request="Two explicitly requested resistors", components=[old])
        proposal = configuration_for(run)
        proposal.additional_components = [component_spec(old), component_spec(new)]
        product = dict(manufacturer="Example", mpn="RES-1", retrieved_at="2026-09-14T00:00:00Z")
        queries = []

        class Supplier:
            def search(self, query, **kwargs):
                queries.append(query)
                return [product] if query in {"new broad", "repaired"} else []

            def get_product(self, identifier, **kwargs):
                return product

        gateway = Gateway(
            {
                OperatingConfiguration: proposal,
                Picks: lambda payload, blocks: Picks(
                    picks=[
                        Pick(component_id=key, chosen_index=0, reason="Local candidate")
                        for group in payload["candidate_groups"]
                        for key in group["component_ids"]
                    ]
                ),
            }
        )
        workflow = Workflow(object(), Supplier(), gateway)
        budget = Budget(run)
        list(workflow._configure_bom(run, budget))
        self.assertEqual(queries, ["new", "new broad"])
        self.assertIsNone(run.components[0].product)
        self.assertEqual(run.components[1].product.mpn, "RES-1")

        replacement = component_spec(old).model_copy(update={"search_query": "repaired"})
        workflow._apply_correction(run, Correction(reason="Different query", replace_components=[replacement]))
        list(workflow._select_components(run, budget))
        self.assertEqual(queries, ["new", "new broad", "repaired"])
        self.assertEqual(run.components[0].product.mpn, "RES-1")

    def test_capacitance_equivalence_mismatch_and_uninterpreted_queries(self):
        component = Component(
            id="C1", name="Bypass", kind="passive", purpose="Bypass", search_query="100nF 16V capacitor"
        )
        product = {"parameters": [{"name": "Capacitance", "value": "0.1 µF"}]}
        self.assertIsNone(find_capacitance_mismatch(component, product))
        component.search_query = "1uF 0603 16V ceramic capacitor"
        self.assertIn("0.1 µF", find_capacitance_mismatch(component, product))
        for query in ("CAP-1", "1-4.7uF", "at least 0.01uF", "1uF or 0.1uF"):
            component.search_query = query
            self.assertIsNone(find_capacitance_mismatch(component, product))
        component.search_query = "1uF capacitor"
        self.assertIsNone(find_capacitance_mismatch(component, {}))
        self.assertIsNone(
            find_capacitance_mismatch(component, {"parameters": [{"name": "Capacitance", "value": "1–10 µF"}]})
        )

    def test_search_and_detail_mismatches_use_existing_broad_search(self):
        wrong = dict(
            manufacturer="Example",
            mpn="CAP-1",
            retrieved_at="2026-09-14T00:00:00Z",
            parameters=[{"name": "Capacitance", "value": "0.1 µF"}],
        )
        right = {**wrong, "mpn": "CAP-2", "parameters": [{"name": "Capacitance", "value": "1 µF"}]}
        for mismatch_in in ("search", "details"):
            with self.subTest(mismatch_in=mismatch_in):

                class Supplier:
                    def search(self, query, **kwargs):
                        return [
                            right
                            if query == "1uF capacitor"
                            else wrong
                            if mismatch_in == "search"
                            else {**right, "mpn": "CAP-1"}
                        ]

                    def get_product(self, identifier, **kwargs):
                        return right if identifier == "CAP-2" else wrong

                class Gateway:
                    def call(self, *args, **kwargs):
                        yield {"type": "progress"}
                        return Picks(picks=[Pick(component_id="C1", chosen_index=0, reason="Candidate fit")])

                run = DesignRun(
                    original_request="Bypass capacitor",
                    components=[
                        Component(
                            id="C1",
                            name="Bypass",
                            kind="passive",
                            purpose="Bypass",
                            search_query="1uF 16V capacitor",
                            broad_query="1uF capacitor",
                        )
                    ],
                )
                list(Workflow(object(), Supplier(), Gateway())._select_components(run, Budget(run)))
                self.assertEqual(run.components[0].product.mpn, "CAP-2")
                self.assertIsNone(run.components[0].selection_error)
