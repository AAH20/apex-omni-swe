"""
APEX_OMNI_SWE Sovereign Autonomous Software Engineering Hypervisor.
Master 5-Pillar Architecture Unifying GraphRAG, AutoHarness, AST Evolution & Ephemeral Sagas.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import ast
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

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
from apex_omni_swe.core.ast_mutator import ASTDeterministicMutator
from apex_omni_swe.core.git_saga import EphemeralWorktreeSandbox
from apex_omni_swe.core.nerve_interceptor import HermesNerveInterceptor, NerveTelemetry
from apex_omni_swe.graphrag.pcst_solver import PCSTPrimalDualSolver, PCSTResult
from apex_omni_swe.graphrag.causal_tracer import CausalPathTracer
from apex_omni_swe.graphrag.submodular_compactor import SubmodularContextCompactor, CompactedContextResult
from apex_omni_swe.autoharness.capture_plane import AutoHarnessCapturePlane
from apex_omni_swe.autoharness.reflection_plane import AutoHarnessReflectionPlane, SkillDefinition, SkillIntent
from apex_omni_swe.autoharness.promoter import AutoHarnessPromoter, PromotionResult
from apex_omni_swe.autoharness.index_surfacing import AutoHarnessIndexSurfacing
from apex_omni_swe.autoharness.lifecycle_manager import AutoHarnessLifecycleManager
from apex_omni_swe.autoharness.audit_ledger import AutoHarnessAuditLedger, LedgerBlock
from apex_omni_swe.evolution.map_elites_swe import MAPElitesSWEArchive, EliteCell
from apex_omni_swe.evolution.genetic_crossover import ASTSubtreeCrossover
from apex_omni_swe.evolution.fitness_evaluator import SWEFitnessEvaluator
from apex_omni_swe.sitl.swe_bench_runner import SWEBenchmarkTask, SWEBenchSandboxRunner


@dataclass
class SWESolutionReport:
    """Institutional execution summary for a resolved or evaluated SWE issue."""
    task_id: str
    is_resolved: bool
    winning_patch: Optional[PatchCandidate]
    verification_report: Optional[VerificationReport]
    pcst_metrics: Dict[str, Any]
    submodular_metrics: Dict[str, Any]
    map_elites_metrics: Dict[str, Any]
    nerve_telemetry: Dict[str, Any]
    autoharness_promotions: List[Dict[str, Any]]
    ledger_block_hash: str
    total_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "is_resolved": self.is_resolved,
            "has_winning_patch": self.winning_patch is not None,
            "patch_id": self.winning_patch.patch_id if self.winning_patch else None,
            "unified_diff": self.winning_patch.unified_diff if self.winning_patch else "",
            "verification": self.verification_report.to_dict() if self.verification_report else {},
            "pcst_metrics": self.pcst_metrics,
            "submodular_metrics": self.submodular_metrics,
            "map_elites_metrics": self.map_elites_metrics,
            "nerve_telemetry": self.nerve_telemetry,
            "autoharness_promotions": self.autoharness_promotions,
            "ledger_block_hash": self.ledger_block_hash,
            "total_latency_ms": round(self.total_latency_ms, 2),
        }


class ApexOmniSWEHypervisor:
    """
    Sovereign Autonomous Software Engineering Hypervisor.
    Bridges SWE-bench benchmarks with AutoHarness self-learning skills,
    dual GraphRAG NP-hard solvers, AST-native Darwinian evolution, and
    Hermes nerve reflex saga rollbacks.
    """

    def __init__(self, token_budget: int = 4000):
        self.token_budget = token_budget

        # 1. GraphRAG Solvers
        self.pcst_solver = PCSTPrimalDualSolver()
        self.causal_tracer = CausalPathTracer()
        self.submodular_compactor = SubmodularContextCompactor(default_budget=token_budget)

        # 2. Core Engine
        self.ast_mutator = ASTDeterministicMutator()
        self.nerve_interceptor = HermesNerveInterceptor()
        self.sandbox = EphemeralWorktreeSandbox()

        # 3. AutoHarness Planes
        self.cap_plane = AutoHarnessCapturePlane()
        self.ref_plane = AutoHarnessReflectionPlane()
        self.promoter = AutoHarnessPromoter()
        self.idx_surfacing = AutoHarnessIndexSurfacing()
        self.mng_lifecycle = AutoHarnessLifecycleManager()
        self.audit_ledger = AutoHarnessAuditLedger()

        # 4. Evolutionary Core
        self.map_elites = MAPElitesSWEArchive()
        self.crossover = ASTSubtreeCrossover()
        self.fitness_evaluator = SWEFitnessEvaluator()

        # 5. SITL Sandbox Runner
        self.test_runner = SWEBenchSandboxRunner()

    def build_code_graph_from_repo(self, repo_files: Dict[str, str], issue_spec: IssueSpec) -> CodeGraph:
        """
        Parses all repository files into an in-memory CodeGraph with semantic prizes.
        """
        graph = CodeGraph()
        issue_tokens = set(issue_spec.problem_statement.lower().replace("_", " ").split())
        for f in issue_spec.target_files:
            issue_tokens.add(f.lower())

        for file_path, source in repo_files.items():
            tree = self.ast_mutator.parse_source(source)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = node.name
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    node_src = ast.get_source_segment(source, node) or ""
                    doc = ast.get_docstring(node) or ""

                    # Calculate semantic relevance prize
                    name_tokens = set(name.lower().replace("_", " ").split())
                    relevance = len(name_tokens & issue_tokens) * 15.0
                    if file_path in issue_spec.target_files:
                        relevance += 25.0
                    if doc:
                        doc_tokens = set(doc.lower().split())
                        relevance += len(doc_tokens & issue_tokens) * 2.0

                    symbol_id = f"{file_path}::{name}"
                    symbol = ASTSymbol(
                        symbol_id=symbol_id,
                        symbol_name=name,
                        file_path=file_path,
                        line_start=getattr(node, "lineno", 1),
                        line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                        kind=kind,
                        source_code=node_src,
                        docstring=doc,
                        prize=max(0.0, relevance),
                        token_cost=max(10, len(node_src.split())),
                        ast_node=node,
                    )
                    graph.add_symbol(symbol)

        # Wire call edges between symbols
        for sym_id, symbol in graph.nodes.items():
            for target_id, target_sym in graph.nodes.items():
                if sym_id != target_id and target_sym.symbol_name in symbol.source_code:
                    graph.add_edge(sym_id, target_id, EdgeKind.CALLS, cost=1.0)

        return graph

    def solve_issue(self, task: SWEBenchmarkTask) -> SWESolutionReport:
        """
        Executes sovereign 5-pillar software engineering synthesis loop.
        """
        start_ns = time.perf_counter_ns()
        issue = task.issue_spec

        # 1. Ingress & AutoHarness Index Surfacing (IDX & CAP)
        self.cap_plane.start_episode(issue.repo_name, issue.problem_statement)
        matched_skills = self.idx_surfacing.match_skills(
            task_query=issue.problem_statement,
            skills=self.promoter.all_skills(),
            repo_name=issue.repo_name,
        )
        for s in matched_skills:
            self.mng_lifecycle.record_usage(s)

        # 2. GraphRAG Fault Localization & Submodular Compaction
        code_graph = self.build_code_graph_from_repo(task.repository_files, issue)
        pcst_res = self.pcst_solver.solve(code_graph)

        candidate_symbol_ids = pcst_res.selected_nodes if pcst_res.selected_nodes else set(code_graph.nodes.keys())
        compact_res = self.submodular_compactor.compact(
            candidate_ids=candidate_symbol_ids,
            graph=code_graph,
            token_budget=self.token_budget,
        )

        self.cap_plane.record_turn(
            tool_name="graphrag_pcst_submodular",
            tool_input={"nodes_selected": len(compact_res.selected_symbols)},
            tool_output=f"Extracted {len(compact_res.selected_symbols)} culprit symbols within {compact_res.total_tokens} tokens",
            latency_ms=pcst_res.latency_us / 1000.0,
        )

        # 3. Evolutionary MAP-Elites Generation & AST Mutation
        self.sandbox.initialize_workspace(task.repository_files)
        self.nerve_interceptor.reset()

        candidate_patches: List[PatchCandidate] = []

        # Target symbols identified by GraphRAG
        target_files = {sym.file_path for sym in compact_res.selected_symbols}
        if not target_files:
            target_files = set(task.repository_files.keys())

        for file_path in target_files:
            source = task.repository_files.get(file_path, "")
            if not source:
                continue

            # Mutate all applicable grammar kinds
            generated = self.ast_mutator.generate_all_candidates(file_path, source)
            candidate_patches.extend(generated)

            # Targeted line mutations (e.g. line-by-line boundary adjustments)
            lines = source.splitlines()
            for line_idx in range(1, len(lines) + 1):
                p_op = self.ast_mutator.mutate(
                    file_path=file_path,
                    source_code=source,
                    mutation_kind=MutationKind.OPERATOR_INVERSION,
                    target_line=line_idx,
                )
                if p_op:
                    candidate_patches.append(p_op)

                p_const = self.ast_mutator.mutate(
                    file_path=file_path,
                    source_code=source,
                    mutation_kind=MutationKind.CONSTANT_ADJUSTMENT,
                    target_line=line_idx,
                )
                if p_const:
                    candidate_patches.append(p_const)

        # Generate sexual crossover offspring between diverse parent candidates
        if len(candidate_patches) >= 2:
            offspring = self.crossover.crossover(candidate_patches[0], candidate_patches[1])
            if offspring:
                candidate_patches.append(offspring)

        # 4. Interactive Test Verification Arena & Hermes Nerve Reflex Loop
        winning_patch: Optional[PatchCandidate] = None
        winning_report: Optional[VerificationReport] = None
        last_nerve_telemetry: Optional[NerveTelemetry] = None
        current_step = 0

        for patch in candidate_patches:
            current_step += 1
            # Check nerve reflex
            nerve_tel = self.nerve_interceptor.check_reflex(
                action_signature=f"apply_{patch.strategy_tag}",
                state_fingerprint=hashlib.sha256(patch.mutated_code.encode("utf-8")).hexdigest(),
                current_step=current_step,
            )
            last_nerve_telemetry = nerve_tel

            if nerve_tel.status != NerveStatus.CLEAR:
                # Preempt thrashing trajectory
                continue

            # Apply candidate to virtual workspace
            self.sandbox.apply_patch(patch)

            # Execute verification test suite
            report = self.test_runner.verify_patch(task, patch)
            self.map_elites.consider_candidate(patch, report, localization_precision=2)

            self.cap_plane.record_turn(
                tool_name="verify_patch",
                tool_input={"patch_id": patch.patch_id, "strategy": patch.strategy_tag},
                tool_output=f"Resolved: {report.is_resolved}, F2P: {report.fail_to_pass_passed}/{report.fail_to_pass_total}, P2P: {report.pass_to_pass_passed}/{report.pass_to_pass_total}",
                is_error=report.regression_detected or not report.is_resolved,
                latency_ms=report.execution_latency_ms,
            )

            if report.is_resolved:
                winning_patch = patch
                winning_report = report
                self.sandbox.commit_transaction()
                break
            else:
                # Compensating LIFO rollback to guarantee zero repository contamination
                self.sandbox.rollback_regression()

        # If not resolved via direct mutations, sample best from MAP-Elites
        if not winning_patch:
            best_cell = self.map_elites.best_resolved_elite()
            if best_cell:
                winning_patch = best_cell.patch
                winning_report = best_cell.verification_report

        is_resolved = (winning_report is not None and winning_report.is_resolved)

        # 5. AutoHarness Reflection Plane, Promoter & Cryptographic Provenance Ledger
        episode_trace = self.cap_plane.conclude_episode(is_success=is_resolved)
        intents = self.ref_plane.reflect(episode_trace, self.promoter.all_skills())

        promotions: List[Dict[str, Any]] = []
        for intent in intents:
            prom_res = self.promoter.promote(intent)
            promotions.append(prom_res.to_dict())

            # Append to immutable SHA-256 Merkle Ledger
            self.audit_ledger.append_event(
                skill_id=intent.target_skill_id,
                episode_id=episode_trace.episode_id,
                action=intent.intent_type.value,
                details=intent.to_dict(),
            )

        # Enforce skill capacity caps
        self.mng_lifecycle.enforce_capacity(self.promoter.active_skills)

        # Ledger head hash
        ledger_head = (
            self.audit_ledger._chain[-1].block_hash
            if self.audit_ledger.block_count() > 0
            else self.audit_ledger.GENESIS_HASH
        )

        total_latency_ms = (time.perf_counter_ns() - start_ns) / 1000000.0

        return SWESolutionReport(
            task_id=issue.issue_id,
            is_resolved=is_resolved,
            winning_patch=winning_patch,
            verification_report=winning_report,
            pcst_metrics=pcst_res.to_dict(),
            submodular_metrics=compact_res.to_dict(),
            map_elites_metrics={
                "coverage_ratio": round(self.map_elites.coverage_ratio(), 4),
                "total_niches_illuminated": self.map_elites.cell_count(),
                "total_evaluations": self.map_elites.total_evaluations,
            },
            nerve_telemetry=last_nerve_telemetry.to_dict() if last_nerve_telemetry else {},
            autoharness_promotions=promotions,
            ledger_block_hash=ledger_head,
            total_latency_ms=total_latency_ms,
        )
