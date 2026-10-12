"""
Unit tests for APEX_OMNI_SWE AST deterministic mutator.
Verifies syntax invariance and grammar transformations.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import ast
import unittest
from apex_omni_swe.core.ast_mutator import ASTDeterministicMutator
from apex_omni_swe.core.primitives import MutationKind


class TestASTMutator(unittest.TestCase):
    def setUp(self):
        self.mutator = ASTDeterministicMutator()

    def test_syntax_verification(self):
        valid_code = "def add(a, b): return a + b"
        invalid_code = "def add(a, b): return a +"
        self.assertTrue(self.mutator.verify_syntax(valid_code))
        self.assertFalse(self.mutator.verify_syntax(invalid_code))

    def test_operator_inversion(self):
        source = (
            "def check_bound(x, limit):\n"
            "    if x < limit:\n"
            "        return True\n"
            "    return False\n"
        )
        patch = self.mutator.mutate(
            file_path="bound.py",
            source_code=source,
            mutation_kind=MutationKind.OPERATOR_INVERSION,
        )
        self.assertIsNotNone(patch)
        self.assertIn("<=", patch.mutated_code)
        # Invariant: Must compile cleanly
        self.assertTrue(self.mutator.verify_syntax(patch.mutated_code))

    def test_guard_insertion(self):
        source = (
            "def process_data(records):\n"
            "    return [r.upper() for r in records]\n"
        )
        patch = self.mutator.mutate(
            file_path="process.py",
            source_code=source,
            mutation_kind=MutationKind.GUARD_INSERTION,
            target_symbol_name="process_data",
        )
        self.assertIsNotNone(patch)
        self.assertIn("records is None", patch.mutated_code)
        self.assertTrue(self.mutator.verify_syntax(patch.mutated_code))

    def test_constant_adjustment(self):
        source = (
            "def index_lookup(idx):\n"
            "    return idx + 0\n"
        )
        patch = self.mutator.mutate(
            file_path="lookup.py",
            source_code=source,
            mutation_kind=MutationKind.CONSTANT_ADJUSTMENT,
        )
        self.assertIsNotNone(patch)
        self.assertIn("1", patch.mutated_code)
        self.assertTrue(self.mutator.verify_syntax(patch.mutated_code))

    def test_branch_swap(self):
        source = (
            "def eval_flag(flag):\n"
            "    if flag:\n"
            "        val = 1\n"
            "    else:\n"
            "        val = 2\n"
            "    return val\n"
        )
        patch = self.mutator.mutate(
            file_path="flag.py",
            source_code=source,
            mutation_kind=MutationKind.SUBTREE_SWAP,
        )
        self.assertIsNotNone(patch)
        self.assertTrue(self.mutator.verify_syntax(patch.mutated_code))

    def test_generate_all_candidates(self):
        source = (
            "def calc(val):\n"
            "    if val == 0:\n"
            "        return 100\n"
            "    return val * 2\n"
        )
        candidates = self.mutator.generate_all_candidates("calc.py", source)
        self.assertGreater(len(candidates), 0)
        for c in candidates:
            self.assertTrue(self.mutator.verify_syntax(c.mutated_code))
            self.assertGreater(len(c.unified_diff), 0)


if __name__ == "__main__":
    unittest.main()
