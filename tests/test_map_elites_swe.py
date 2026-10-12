"""
Unit tests for APEX_OMNI_SWE MAP-Elites 4D Quality-Diversity Archive.
Evaluates niche coordinate mapping, elite replacement, and AST crossover.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import unittest
from apex_omni_swe.core.primitives import PatchCandidate, MutationKind, VerificationReport
from apex_omni_swe.evolution.map_elites_swe import MAPElitesSWEArchive
from apex_omni_swe.evolution.genetic_crossover import ASTSubtreeCrossover


class TestMAPElitesSWE(unittest.TestCase):
    def test_niche_computation_and_insertion(self):
        archive = MAPElitesSWEArchive()
        patch1 = PatchCandidate(
            patch_id="p1",
            file_path="math_ops.py",
            mutation_kind=MutationKind.OPERATOR_INVERSION,
            original_code="return a < b",
            mutated_code="return a <= b",
            unified_diff="+return a <= b",
            strategy_tag="op_inv",
            ast_edit_distance=2,
            token_cost=30,
        )
        report1 = VerificationReport(
            patch_id="p1",
            is_resolved=True,
            fail_to_pass_passed=2,
            fail_to_pass_total=2,
            pass_to_pass_passed=10,
            pass_to_pass_total=10,
            syntax_valid=True,
            regression_detected=False,
            execution_latency_ms=5.0,
        )

        became_elite = archive.consider_candidate(patch1, report1, localization_precision=2)
        self.assertTrue(became_elite)
        self.assertEqual(archive.cell_count(), 1)
        self.assertGreater(archive.coverage_ratio(), 0.0)

        best = archive.best_elite()
        self.assertIsNotNone(best)
        self.assertEqual(best.patch.patch_id, "p1")

    def test_ast_subtree_crossover(self):
        crossover = ASTSubtreeCrossover()
        orig = (
            "def foo(x):\n"
            "    return x + 1\n"
            "def bar(y):\n"
            "    return y * 2\n"
        )
        parent_a = PatchCandidate(
            patch_id="pA",
            file_path="ops.py",
            mutation_kind=MutationKind.OPERATOR_INVERSION,
            original_code=orig,
            mutated_code="def foo(x):\n    return x - 1\ndef bar(y):\n    return y * 2\n",
            unified_diff="diffA",
            strategy_tag="stratA",
        )
        parent_b = PatchCandidate(
            patch_id="pB",
            file_path="ops.py",
            mutation_kind=MutationKind.CONSTANT_ADJUSTMENT,
            original_code=orig,
            mutated_code="def foo(x):\n    return x + 1\ndef bar(y):\n    return y * 10\n",
            unified_diff="diffB",
            strategy_tag="stratB",
        )

        child = crossover.crossover(parent_a, parent_b)
        self.assertIsNotNone(child)
        self.assertIn("def bar(y):", child.mutated_code)


if __name__ == "__main__":
    unittest.main()
