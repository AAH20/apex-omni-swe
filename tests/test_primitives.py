"""
Unit tests for APEX_OMNI_SWE core primitives and CodeGraph contracts.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import unittest
from apex_omni_swe.core.primitives import (
    ASTSymbol,
    CodeGraph,
    EdgeKind,
    IssueSpec,
    MutationKind,
    NerveStatus,
    PatchCandidate,
    SkillIntentType,
    VerificationReport,
)


class TestCorePrimitives(unittest.TestCase):
    def test_ast_symbol_creation(self):
        sym = ASTSymbol(
            symbol_id="mod::foo",
            symbol_name="foo",
            file_path="pkg/mod.py",
            line_start=10,
            line_end=20,
            kind="function",
            source_code="def foo(): return 42",
            prize=15.0,
            token_cost=30,
        )
        self.assertEqual(sym.symbol_id, "mod::foo")
        self.assertEqual(sym.symbol_name, "foo")
        self.assertEqual(sym.prize, 15.0)
        d = sym.to_dict()
        self.assertEqual(d["kind"], "function")
        self.assertEqual(d["line_start"], 10)

    def test_code_graph_nodes_and_edges(self):
        graph = CodeGraph()
        sym1 = ASTSymbol(
            symbol_id="a",
            symbol_name="func_a",
            file_path="a.py",
            line_start=1,
            line_end=5,
            kind="function",
            source_code="def func_a(): pass",
            prize=10.0,
        )
        sym2 = ASTSymbol(
            symbol_id="b",
            symbol_name="func_b",
            file_path="b.py",
            line_start=1,
            line_end=5,
            kind="function",
            source_code="def func_b(): pass",
            prize=5.0,
        )
        graph.add_symbol(sym1)
        graph.add_symbol(sym2)
        graph.add_edge("a", "b", EdgeKind.CALLS, cost=1.5)

        self.assertEqual(graph.node_count(), 2)
        self.assertEqual(graph.edge_count(), 1)
        neighbors = graph.get_neighbors("a")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0][0], "b")
        self.assertEqual(neighbors[0][1], EdgeKind.CALLS)
        self.assertEqual(neighbors[0][2], 1.5)

    def test_issue_spec_contract(self):
        issue = IssueSpec(
            issue_id="ISSUE-101",
            repo_name="org/repo",
            problem_statement="Calculation produces off-by-one result",
            fail_to_pass_tests=["test_f2p"],
            pass_to_pass_tests=["test_p2p"],
            target_files=["calc.py"],
        )
        self.assertEqual(issue.issue_id, "ISSUE-101")
        d = issue.to_dict()
        self.assertIn("fail_to_pass_tests", d)
        self.assertEqual(d["repo_name"], "org/repo")

    def test_patch_candidate_and_verification_report(self):
        patch = PatchCandidate(
            patch_id="p-001",
            file_path="calc.py",
            mutation_kind=MutationKind.OPERATOR_INVERSION,
            original_code="return a < b",
            mutated_code="return a <= b",
            unified_diff="--- a\n+++ b\n@@ -1 +1 @@\n-return a < b\n+return a <= b\n",
            strategy_tag="ast_operator_inversion",
        )
        self.assertEqual(patch.patch_id, "p-001")
        self.assertEqual(patch.mutation_kind, MutationKind.OPERATOR_INVERSION)

        report = VerificationReport(
            patch_id="p-001",
            is_resolved=True,
            fail_to_pass_passed=1,
            fail_to_pass_total=1,
            pass_to_pass_passed=5,
            pass_to_pass_total=5,
            syntax_valid=True,
            regression_detected=False,
            execution_latency_ms=12.4,
        )
        self.assertTrue(report.is_resolved)
        self.assertFalse(report.regression_detected)
        self.assertEqual(report.to_dict()["fail_to_pass_passed"], "1/1")


if __name__ == "__main__":
    unittest.main()
