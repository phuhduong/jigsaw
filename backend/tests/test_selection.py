"""Catalog nominal-value checks with local candidates, never a supplier network."""
import unittest

from agents.component_retriever import capacitance_mismatch
from llm import Budget
from models import Component, DesignRun, Pick, Picks
from pipeline import Workflow


class SelectionTests(unittest.TestCase):
    def test_capacitance_equivalence_mismatch_and_uninterpreted_queries(self):
        component = Component(id="C1", name="Bypass", kind="passive", purpose="Bypass", search_query="100nF 16V capacitor")
        product = {"parameters": [{"name": "Capacitance", "value": "0.1 µF"}]}
        self.assertIsNone(capacitance_mismatch(component, product))
        component.search_query = "1uF 0603 16V ceramic capacitor"
        self.assertIn("0.1 µF", capacitance_mismatch(component, product))
        for query in ("CAP-1", "1-4.7uF", "at least 0.01uF", "1uF or 0.1uF"):
            component.search_query = query
            self.assertIsNone(capacitance_mismatch(component, product))
        component.search_query = "1uF capacitor"
        self.assertIsNone(capacitance_mismatch(component, {}))
        self.assertIsNone(capacitance_mismatch(component, {"parameters": [{"name": "Capacitance", "value": "1–10 µF"}]}))

    def test_search_and_detail_mismatches_use_existing_broad_search(self):
        wrong = dict(manufacturer="Example", mpn="CAP-1", retrieved_at="2026-09-14T00:00:00Z",
                     parameters=[{"name": "Capacitance", "value": "0.1 µF"}])
        right = {**wrong, "mpn": "CAP-2", "parameters": [{"name": "Capacitance", "value": "1 µF"}]}
        for mismatch_in in ("search", "details"):
            with self.subTest(mismatch_in=mismatch_in):
                class Supplier:
                    def search(self, query, **kwargs):
                        return [right if query == "1uF capacitor" else
                                wrong if mismatch_in == "search" else {**right, "mpn": "CAP-1"}]

                    def get_product(self, identifier, **kwargs):
                        return right if identifier == "CAP-2" else wrong

                class Gateway:
                    def call(self, *args, **kwargs):
                        yield {"type": "progress"}
                        return Picks(picks=[Pick(component_id="C1", chosen_index=0, reason="Candidate fit")])

                run = DesignRun(original_request="Bypass capacitor", components=[Component(
                    id="C1", name="Bypass", kind="passive", purpose="Bypass", search_query="1uF 16V capacitor",
                    broad_query="1uF capacitor")])
                list(Workflow(object(), Supplier(), Gateway())._select(run, Budget(run)))
                self.assertEqual(run.components[0].product.mpn, "CAP-2")
                self.assertIsNone(run.components[0].selection_error)
