"""
APEX_OMNI_SWE AST Grammar Tree Mutator.
Deterministic AST-Native Darwinian Mutations with Guaranteed Syntax Invariance.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import ast
import copy
import difflib
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.core.primitives import (
    MutationKind,
    PatchCandidate,
)


class OperatorInverter(ast.NodeTransformer):
    """Inverts comparison, boolean, and arithmetic operators."""

    def __init__(self, target_line: Optional[int] = None):
        super().__init__()
        self.target_line = target_line
        self.mutated = False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if self.mutated:
            return node
        if self.target_line is not None and getattr(node, "lineno", -1) != self.target_line:
            return node

        new_ops = []
        for op in node.ops:
            if isinstance(op, ast.Eq):
                new_ops.append(ast.NotEq())
                self.mutated = True
            elif isinstance(op, ast.NotEq):
                new_ops.append(ast.Eq())
                self.mutated = True
            elif isinstance(op, ast.Lt):
                new_ops.append(ast.LtE())
                self.mutated = True
            elif isinstance(op, ast.LtE):
                new_ops.append(ast.Lt())
                self.mutated = True
            elif isinstance(op, ast.Gt):
                new_ops.append(ast.GtE())
                self.mutated = True
            elif isinstance(op, ast.GtE):
                new_ops.append(ast.Gt())
                self.mutated = True
            elif isinstance(op, ast.In):
                new_ops.append(ast.NotIn())
                self.mutated = True
            elif isinstance(op, ast.NotIn):
                new_ops.append(ast.In())
                self.mutated = True
            elif isinstance(op, ast.Is):
                new_ops.append(ast.IsNot())
                self.mutated = True
            elif isinstance(op, ast.IsNot):
                new_ops.append(ast.Is())
                self.mutated = True
            else:
                new_ops.append(op)
        node.ops = new_ops
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        if self.mutated:
            return node
        if self.target_line is not None and getattr(node, "lineno", -1) != self.target_line:
            return node

        if isinstance(node.op, ast.And):
            node.op = ast.Or()
            self.mutated = True
        elif isinstance(node.op, ast.Or):
            node.op = ast.And()
            self.mutated = True
        return node


class GuardClauseInjector(ast.NodeTransformer):
    """Inserts defensive guard checks at function headers or vulnerable statements."""

    def __init__(self, target_function_name: Optional[str] = None):
        super().__init__()
        self.target_function_name = target_function_name
        self.mutated = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        if self.mutated:
            return node
        if self.target_function_name and node.name != self.target_function_name:
            return node

        # Inject guard checking first argument for None
        if node.args.args:
            first_arg = node.args.args[0].arg
            if first_arg != "self" and first_arg != "cls":
                guard_check = ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=first_arg, ctx=ast.Load()),
                        ops=[ast.Is()],
                        comparators=[ast.Constant(value=None)],
                    ),
                    body=[ast.Return(value=ast.Constant(value=None))],
                    orelse=[],
                )
                ast.copy_location(guard_check, node)
                node.body.insert(0, guard_check)
                self.mutated = True
        return node


class ConstantAdjuster(ast.NodeTransformer):
    """Adjusts off-by-one boundary constants, booleans, and indices."""

    def __init__(self, target_line: Optional[int] = None):
        super().__init__()
        self.target_line = target_line
        self.mutated = False

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.mutated:
            return node
        if self.target_line is not None and getattr(node, "lineno", -1) != self.target_line:
            return node

        if isinstance(node.value, bool):
            node.value = not node.value
            self.mutated = True
        elif isinstance(node.value, int) and not isinstance(node.value, bool):
            # Boundary shift: 0 -> 1, 1 -> 0, x -> x + 1
            if node.value == 0:
                node.value = 1
            elif node.value == 1:
                node.value = 0
            else:
                node.value = node.value + 1
            self.mutated = True
        return node


class BranchSwapper(ast.NodeTransformer):
    """Swaps if body and else body branches."""

    def __init__(self, target_line: Optional[int] = None):
        super().__init__()
        self.target_line = target_line
        self.mutated = False

    def visit_If(self, node: ast.If) -> ast.AST:
        self.generic_visit(node)
        if self.mutated:
            return node
        if self.target_line is not None and getattr(node, "lineno", -1) != self.target_line:
            return node

        if node.orelse and node.body:
            node.body, node.orelse = node.orelse, node.body
            self.mutated = True
        return node


class ReturnCoercer(ast.NodeTransformer):
    """Coerces return expressions to handle empty cases safely."""

    def __init__(self, target_function: Optional[str] = None):
        super().__init__()
        self.target_function = target_function
        self.mutated = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        if self.mutated:
            return node
        if self.target_function and node.name != self.target_function:
            return node

        # Append default safe return if last statement is not Return
        if node.body and not isinstance(node.body[-1], ast.Return):
            ret = ast.Return(value=ast.Constant(value=None))
            node.body.append(ret)
            self.mutated = True
        return node


class ASTDeterministicMutator:
    """
    Compiler-grade AST mutation engine.
    Applies algebraic grammar transformations and strictly verifies syntax invariance.
    """

    def __init__(self):
        pass

    def parse_source(self, source_code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(source_code)
        except SyntaxError:
            return None

    def unparse_ast(self, tree: ast.AST) -> Optional[str]:
        try:
            ast.fix_missing_locations(tree)
            return ast.unparse(tree)
        except Exception:
            return None

    def verify_syntax(self, source_code: str) -> bool:
        try:
            compile(source_code, "<ast>", "exec")
            return True
        except (SyntaxError, TypeError, ValueError):
            return False

    def generate_diff(self, file_path: str, original: str, mutated: str) -> str:
        orig_lines = original.splitlines(keepends=True)
        mut_lines = mutated.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            mut_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        return "".join(diff)

    def mutate(
        self,
        file_path: str,
        source_code: str,
        mutation_kind: MutationKind,
        target_line: Optional[int] = None,
        target_symbol_name: Optional[str] = None,
    ) -> Optional[PatchCandidate]:
        """
        Executes a targeted AST mutation and returns a verified PatchCandidate.
        Returns None if mutation is not applicable or violates syntax invariants.
        """
        start_ns = time.perf_counter_ns()
        original_tree = self.parse_source(source_code)
        if not original_tree:
            return None

        mutated_tree = copy.deepcopy(original_tree)
        mutator: ast.NodeTransformer

        if mutation_kind == MutationKind.OPERATOR_INVERSION:
            mutator = OperatorInverter(target_line=target_line)
        elif mutation_kind == MutationKind.GUARD_INSERTION:
            mutator = GuardClauseInjector(target_function_name=target_symbol_name)
        elif mutation_kind == MutationKind.CONSTANT_ADJUSTMENT:
            mutator = ConstantAdjuster(target_line=target_line)
        elif mutation_kind == MutationKind.SUBTREE_SWAP:
            mutator = BranchSwapper(target_line=target_line)
        elif mutation_kind == MutationKind.RETURN_REBINDING:
            mutator = ReturnCoercer(target_function=target_symbol_name)
        else:
            return None

        transformed = mutator.visit(mutated_tree)
        if not getattr(mutator, "mutated", False):
            return None

        unparsed = self.unparse_ast(transformed)
        if not unparsed or unparsed == source_code:
            return None

        # Critical invariant: Compiler validation
        if not self.verify_syntax(unparsed):
            return None

        diff = self.generate_diff(file_path, source_code, unparsed)
        patch_id = hashlib.sha256(diff.encode("utf-8")).hexdigest()[:16]

        edit_distance = len(diff.splitlines())

        return PatchCandidate(
            patch_id=f"patch-{patch_id}",
            file_path=file_path,
            mutation_kind=mutation_kind,
            original_code=source_code,
            mutated_code=unparsed,
            unified_diff=diff,
            strategy_tag=f"ast_{mutation_kind.value.lower()}",
            ast_edit_distance=max(1, edit_distance),
            token_cost=len(diff.split()) + 20,
        )

    def generate_all_candidates(
        self,
        file_path: str,
        source_code: str,
        target_symbol_name: Optional[str] = None,
    ) -> List[PatchCandidate]:
        """Generates all valid, syntax-verified mutation candidates across all strategies."""
        candidates: List[PatchCandidate] = []
        for kind in MutationKind:
            patch = self.mutate(
                file_path=file_path,
                source_code=source_code,
                mutation_kind=kind,
                target_symbol_name=target_symbol_name,
            )
            if patch:
                candidates.append(patch)
        return candidates
