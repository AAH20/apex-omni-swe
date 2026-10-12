"""
Comprehensive End-to-End SWE Verification Matrix for APEX_OMNI_SWE.
Validates 5-Pillar Autonomous Hypervisor against Canonical SWE Benchmark Suite.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import unittest
from apex_omni_swe.hypervisor import ApexOmniSWEHypervisor
from apex_omni_swe.sitl.swe_bench_runner import build_canonical_swe_task_suite


class TestE2ESWEFramework(unittest.TestCase):
    def setUp(self):
        self.hypervisor = ApexOmniSWEHypervisor(token_budget=4000)
        self.tasks = build_canonical_swe_task_suite()

    def test_e2e_canonical_benchmark_resolution(self):
        resolved_count = 0
        total_tasks = len(self.tasks)

        for task in self.tasks:
            report = self.hypervisor.solve_issue(task)
            self.assertTrue(report.is_resolved, f"Failed to resolve task: {task.issue_spec.issue_id}")
            self.assertIsNotNone(report.winning_patch)
            self.assertIsNotNone(report.verification_report)

            # Assert invariants
            self.assertTrue(report.verification_report.syntax_valid)
            self.assertFalse(report.verification_report.regression_detected)
            self.assertEqual(
                report.verification_report.fail_to_pass_passed,
                report.verification_report.fail_to_pass_total,
            )
            self.assertEqual(
                report.verification_report.pass_to_pass_passed,
                report.verification_report.pass_to_pass_total,
            )

            # Assert GraphRAG boundaries
            self.assertLessEqual(report.submodular_metrics["total_tokens"], 4000)
            self.assertGreater(report.pcst_metrics["selected_nodes_count"], 0)

            resolved_count += 1

        self.assertEqual(resolved_count, total_tasks)

        # Assert AutoHarness accumulated knowledge
        skills = self.hypervisor.promoter.all_skills()
        self.assertGreater(len(skills), 0)

        # Assert Audit Ledger cryptographic continuity
        self.assertTrue(self.hypervisor.audit_ledger.verify_integrity())
        self.assertGreater(self.hypervisor.audit_ledger.block_count(), 0)


if __name__ == "__main__":
    unittest.main()
