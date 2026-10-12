"""
APEX_OMNI_SWE Genetic AST Crossover & Differential Synthesizer.
Recombines AST Mutation Trees with Strict Syntax Verification.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import ast
import copy
import difflib
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.core.primitives import PatchCandidate, MutationKind


class ASTSubtreeCrossover:
    """
    Performs sexual crossover between two AST patch candidates.
    Recombines subtree modifications while enforcing syntax compilation invariants.
    """

    def __init__(self):
        pass

    def crossover(
        self,
        parent_a: PatchCandidate,
        parent_b: PatchCandidate,
    ) -> Optional[PatchCandidate]:
        """
        Recombines patches from parent_a and parent_b into an offspring patch.
        """
        if parent_a.file_path != parent_b.file_path:
            # Multi-file combination: pick parent_a as primary
            return copy.deepcopy(parent_a)

        try:
            tree_a = ast.parse(parent_a.mutated_code)
            tree_b = ast.parse(parent_b.mutated_code)
        except SyntaxError:
            return None

        # Extract function definitions from tree_b
        funcs_b = {node.name: node for node in ast.walk(tree_b) if isinstance(node, ast.FunctionDef)}

        # Replace matching functions in tree_a with tree_b's version
        class FunctionSwapper(ast.NodeTransformer):
            def __init__(self, target_funcs: Dict[str, ast.FunctionDef]):
                super().__init__()
                self.target_funcs = target_funcs
                self.swapped = False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                if node.name in self.target_funcs and not self.swapped:
                    self.swapped = True
                    return copy.deepcopy(self.target_funcs[node.name])
                return node

        swapper = FunctionSwapper(funcs_b)
        offspring_tree = swapper.visit(copy.deepcopy(tree_a))

        if not swapper.swapped:
            return None

        try:
            ast.fix_missing_locations(offspring_tree)
            mutated_code = ast.unparse(offspring_tree)
            # Critical compile verification
            compile(mutated_code, "<ast>", "exec")
        except Exception:
            return None

        diff_lines = list(difflib.unified_diff(
            parent_a.original_code.splitlines(keepends=True),
            mutated_code.splitlines(keepends=True),
            fromfile=f"a/{parent_a.file_path}",
            tofile=f"b/{parent_a.file_path}",
        ))
        unified_diff = "".join(diff_lines)
        patch_id = hashlib.sha256(unified_diff.encode("utf-8")).hexdigest()[:16]

        return PatchCandidate(
            patch_id=f"patch-cross-{patch_id}",
            file_path=parent_a.file_path,
            mutation_kind=MutationKind.SUBTREE_SWAP,
            original_code=parent_a.original_code,
            mutated_code=mutated_code,
            unified_diff=unified_diff,
            strategy_tag="ast_crossover_hybrid",
            ast_edit_distance=max(1, len(diff_lines)),
            token_cost=len(unified_diff.split()) + 25,
        )
