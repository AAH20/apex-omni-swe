"""
APEX_OMNI_SWE Institutional Command Line Interface (CLI).
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import argparse
import json
import sys
import time

from apex_omni_swe.hypervisor import ApexOmniSWEHypervisor
from apex_omni_swe.sitl.swe_bench_runner import build_canonical_swe_task_suite


def run_solve_command(args: argparse.Namespace) -> int:
    """Executes the autonomous hypervisor against canonical benchmark tasks."""
    print("=" * 70)
    print("APEX_OMNI_SWE Sovereign Hypervisor: Autonomous Resolution Engine")
    print("Apex Growth Systems LLC | Zero External Dependencies")
    print("=" * 70)

    hypervisor = ApexOmniSWEHypervisor(token_budget=args.budget)
    tasks = build_canonical_swe_task_suite()

    if args.task_id:
        tasks = [t for t in tasks if t.issue_spec.issue_id == args.task_id]
        if not tasks:
            print(f"Error: Task ID '{args.task_id}' not found in canonical suite.")
            return 1

    resolved_count = 0
    total_count = len(tasks)

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{total_count}] Evaluating Issue: {task.issue_spec.issue_id} ({task.issue_spec.repo_name})")
        print(f"Problem: {task.issue_spec.problem_statement}")
        report = hypervisor.solve_issue(task)

        status_str = "RESOLVED" if report.is_resolved else "UNRESOLVED"
        print(f"Outcome: {status_str} in {report.total_latency_ms:.2f} ms")
        print(f"PCST Solved: {report.pcst_metrics.get('selected_nodes_count')} nodes, {report.pcst_metrics.get('latency_us'):.2f} us")
        print(f"Context Compaction: {report.submodular_metrics.get('total_tokens')} tokens (budget {report.submodular_metrics.get('token_budget')})")
        print(f"MAP-Elites Coverage: {report.map_elites_metrics.get('coverage_ratio') * 100:.1f}% ({report.map_elites_metrics.get('total_niches_illuminated')} niches)")
        print(f"AutoHarness Promotions: {len(report.autoharness_promotions)} | Ledger Hash: {report.ledger_block_hash[:16]}...")

        if report.winning_patch:
            print(f"Winning Patch Strategy: {report.winning_patch.strategy_tag} (AST Edit Dist: {report.winning_patch.ast_edit_distance})")
            if args.diff:
                print("Unified Diff:")
                print(report.winning_patch.unified_diff)

        if report.is_resolved:
            resolved_count += 1

    solve_rate = (resolved_count / float(total_count)) * 100.0
    print("\n" + "=" * 70)
    print(f"Benchmark Resolution Rate: {resolved_count}/{total_count} ({solve_rate:.1f}%)")
    print("=" * 70)
    return 0 if resolved_count == total_count else 1


def run_benchmark_command(args: argparse.Namespace) -> int:
    """Executes empirical latency and throughput benchmarks."""
    from apex_omni_swe.benchmarks.benchmark_runner import run_all_institutional_benchmarks
    return run_all_institutional_benchmarks()


def run_autoharness_command(args: argparse.Namespace) -> int:
    """Inspects the learned AutoHarness skill ecosystem and audit ledger."""
    print("=" * 70)
    print("APEX_OMNI_SWE AutoHarness Skill Library & Cryptographic Ledger")
    print("Apex Growth Systems LLC")
    print("=" * 70)

    hypervisor = ApexOmniSWEHypervisor()
    tasks = build_canonical_swe_task_suite()
    for task in tasks:
        hypervisor.solve_issue(task)

    skills = hypervisor.promoter.all_skills()
    print(f"\nTotal Active Skills: {len(skills)}")
    for s_id, s in skills.items():
        print(f"- [{s.skill_id}] {s.name} (Scope: {s.repo_scope}, Loads: {s.loads}, Conf: {s.confidence:.2f})")
        print(f"  Triggers: {', '.join(s.trigger_patterns)}")

    print(f"\nAudit Ledger Chain Blocks: {hypervisor.audit_ledger.block_count()}")
    print(f"Integrity Validated: {hypervisor.audit_ledger.verify_integrity()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="apex-omni-swe",
        description="APEX_OMNI_SWE: Sovereign Autonomous Software Engineering Hypervisor",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Solve command
    solve_parser = subparsers.add_parser("solve", help="Execute hypervisor on SWE-bench tasks")
    solve_parser.add_argument("--task-id", type=str, default=None, help="Specific task ID to solve")
    solve_parser.add_argument("--budget", type=int, default=4000, help="Token context budget")
    solve_parser.add_argument("--diff", action="store_true", help="Print unified diff for winning patches")
    solve_parser.set_defaults(func=run_solve_command)

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run comprehensive institutional benchmarks")
    bench_parser.set_defaults(func=run_benchmark_command)

    # AutoHarness command
    harness_parser = subparsers.add_parser("autoharness", help="Inspect AutoHarness skills and ledger")
    harness_parser.set_defaults(func=run_autoharness_command)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
