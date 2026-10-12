"""
APEX_OMNI_SWE Multi-Objective Fitness Evaluator.
FAIL_TO_PASS and PASS_TO_PASS Invariant Scoring Engine.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from apex_omni_swe.core.primitives import (
    PatchCandidate,
    VerificationReport,
    IssueSpec,
)


class SWEFitnessEvaluator:
    """
    Computes multi-objective fitness for candidate patches based on
    SWE-bench verification invariants:
        F = 100 * I(FAIL_TO_PASS) + 50 * (N_PASS_TO_PASS / N_TOTAL) - 0.1 * Delta_AST - 0.05 * T_latency
    """

    def __init__(
        self,
        weight_fail_to_pass: float = 100.0,
        weight_pass_to_pass: float = 50.0,
        penalty_ast_distance: float = 0.1,
        penalty_latency: float = 0.05,
    ):
        self.w_f2p = weight_fail_to_pass
        self.w_p2p = weight_pass_to_pass
        self.p_ast = penalty_ast_distance
        self.p_lat = penalty_latency

    def evaluate(
        self,
        patch: PatchCandidate,
        report: VerificationReport,
    ) -> float:
        """
        Calculates scalar fitness value. Penalizes syntax errors and regressions severely.
        """
        if not report.syntax_valid:
            return -1000.0

        if report.regression_detected:
            # Significant penalty for breaking existing working tests
            base_score = -200.0
        else:
            base_score = 0.0

        # FAIL_TO_PASS satisfaction
        if report.fail_to_pass_total > 0:
            f2p_ratio = report.fail_to_pass_passed / float(report.fail_to_pass_total)
        else:
            f2p_ratio = 1.0 if report.is_resolved else 0.0

        # PASS_TO_PASS preservation
        if report.pass_to_pass_total > 0:
            p2p_ratio = report.pass_to_pass_passed / float(report.pass_to_pass_total)
        else:
            p2p_ratio = 1.0

        score = (
            base_score
            + (self.w_f2p * f2p_ratio)
            + (self.w_p2p * p2p_ratio)
            - (self.p_ast * float(patch.ast_edit_distance))
            - (self.p_lat * float(report.execution_latency_ms))
        )
        return round(score, 4)
