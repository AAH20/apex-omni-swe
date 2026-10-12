"""
Unit tests for APEX_OMNI_SWE GraphRAG topological solvers.
Evaluates PCST Primal-Dual, Causal Tracer, and Submodular Compactor.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import unittest
from apex_omni_swe.core.primitives import ASTSymbol, CodeGraph, EdgeKind
from apex_omni_swe.graphrag.pcst_solver import PCSTPrimalDualSolver
from apex_omni_swe.graphrag.causal_tracer import CausalPathTracer
from apex_omni_swe.graphrag.submodular_compactor import SubmodularContextCompactor


class TestGraphRAGSolvers(unittest.TestCase):
    def setUp(self):
        self.graph = CodeGraph()
        # Create a 4-node pipeline: A -(1)-> B -(1)-> C -(1)-> D
        # A has prize 10, D has prize 20, B & C have prize 0
        symbols = [
            ASTSymbol("A", "func_a", "a.py", 1, 10, "function", "def func_a(): pass", prize=10.0, token_cost=100),
            ASTSymbol("B", "func_b", "b.py", 1, 10, "function", "def func_b(): pass", prize=0.0, token_cost=150),
            ASTSymbol("C", "func_c", "c.py", 1, 10, "function", "def func_c(): pass", prize=0.0, token_cost=200),
            ASTSymbol("D", "func_d", "d.py", 1, 10, "function", "def func_d(): pass", prize=20.0, token_cost=100),
        ]
        for s in symbols:
            self.graph.add_symbol(s)

        self.graph.add_edge("A", "B", EdgeKind.CALLS, cost=1.0)
        self.graph.add_edge("B", "C", EdgeKind.CALLS, cost=1.0)
        self.graph.add_edge("C", "D", EdgeKind.CALLS, cost=1.0)

    def test_pcst_solver(self):
        solver = PCSTPrimalDualSolver()
        result = solver.solve(self.graph)
        self.assertGreater(len(result.selected_nodes), 0)
        self.assertIn("D", result.selected_nodes)
        self.assertGreater(result.total_prize_collected, 0.0)
        self.assertGreater(result.latency_us, 0.0)

    def test_causal_tracer_feasible(self):
        tracer = CausalPathTracer(max_weight_bound=1000.0)
        res = tracer.trace(self.graph, "A", "D")
        self.assertTrue(res.is_feasible)
        self.assertEqual(res.path, ["A", "B", "C", "D"])
        self.assertAlmostEqual(res.total_cost, 3.0)
        self.assertEqual(res.total_weight, 550.0)

    def test_causal_tracer_budget_exceeded(self):
        # Strict weight budget of 300 (A=100, B=150 is 250, adding C=200 exceeds 300)
        tracer = CausalPathTracer(max_weight_bound=300.0)
        res = tracer.trace(self.graph, "A", "D")
        self.assertFalse(res.is_feasible)

    def test_submodular_compactor(self):
        compactor = SubmodularContextCompactor(default_budget=350)
        candidates = {"A", "B", "C", "D"}
        res = compactor.compact(candidates, self.graph, token_budget=350)
        self.assertLessEqual(res.total_tokens, 350)
        self.assertGreater(len(res.selected_symbols), 0)
        self.assertGreater(res.coverage_score, 0.0)
        self.assertAlmostEqual(res.approximation_ratio, 0.6321, places=2)


if __name__ == "__main__":
    unittest.main()
