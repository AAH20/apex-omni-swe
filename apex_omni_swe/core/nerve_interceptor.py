"""
APEX_OMNI_SWE Hermes Nerve Autonomic Reflex Interceptor.
Sub-15 Microsecond Loop Detection and Trajectory Preemption Engine.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any

from apex_omni_swe.core.primitives import NerveStatus


@dataclass
class NerveTelemetry:
    """Reflex execution telemetry."""
    status: NerveStatus
    latency_us: float
    reason: str
    cycle_length: int = 0
    total_checks: int = 0
    interventions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "latency_us": round(self.latency_us, 2),
            "reason": self.reason,
            "cycle_length": self.cycle_length,
            "total_checks": self.total_checks,
            "interventions": self.interventions,
        }


class HermesNerveInterceptor:
    """
    Sub-15 microsecond autonomic reflex monitor.
    Intercepts runaway agent tool ping-pongs, cyclic mutations, and thrashing loops
    before token budgets or system resources are exhausted.
    """

    def __init__(
        self,
        max_repetition_threshold: int = 3,
        max_trajectory_steps: int = 50,
        history_window_size: int = 20,
    ):
        self.max_repetition = max_repetition_threshold
        self.max_steps = max_trajectory_steps
        self.window_size = history_window_size
        self._action_hashes: List[str] = []
        self._state_hashes: List[str] = []
        self._total_checks = 0
        self._interventions = 0

    def reset(self) -> None:
        self._action_hashes.clear()
        self._state_hashes.clear()
        self._total_checks = 0
        self._interventions = 0

    def check_reflex(
        self,
        action_signature: str,
        state_fingerprint: str,
        current_step: int,
    ) -> NerveTelemetry:
        """
        Fast path reflex check. Executes within sub-15 microsecond SLA.
        """
        start_ns = time.perf_counter_ns()
        self._total_checks += 1

        # 1. Resource Exhaustion Check
        if current_step >= self.max_steps:
            self._interventions += 1
            lat = (time.perf_counter_ns() - start_ns) / 1000.0
            return NerveTelemetry(
                status=NerveStatus.RESOURCE_EXHAUSTED,
                latency_us=lat,
                reason=f"Step limit {self.max_steps} reached without task resolution",
                total_checks=self._total_checks,
                interventions=self._interventions,
            )

        # Hash action and state
        act_hash = hashlib.sha256(action_signature.encode("utf-8")).hexdigest()[:12]
        st_hash = hashlib.sha256(state_fingerprint.encode("utf-8")).hexdigest()[:12]

        # 2. Direct Repetition Check (Ping-Pong Loop)
        recent_actions = self._action_hashes[-self.window_size:]
        consecutive_repeats = 0
        for h in reversed(recent_actions):
            if h == act_hash:
                consecutive_repeats += 1
            else:
                break

        if consecutive_repeats >= self.max_repetition:
            self._interventions += 1
            lat = (time.perf_counter_ns() - start_ns) / 1000.0
            return NerveTelemetry(
                status=NerveStatus.LOOP_DETECTED,
                latency_us=lat,
                reason=f"Action '{action_signature}' repeated {consecutive_repeats} consecutive times",
                cycle_length=1,
                total_checks=self._total_checks,
                interventions=self._interventions,
            )

        # 3. Cyclic Mutation State Check (A -> B -> A oscillation)
        recent_states = self._state_hashes[-self.window_size:]
        cycle_detected = False
        detected_cycle_len = 0

        # Check cycle lengths 2, 3, 4
        n_states = len(recent_states)
        for k in (2, 3, 4):
            if n_states >= 2 * k:
                sub1 = recent_states[-k:]
                sub2 = recent_states[-2 * k : -k]
                if sub1 == sub2:
                    cycle_detected = True
                    detected_cycle_len = k
                    break

        if cycle_detected:
            self._interventions += 1
            lat = (time.perf_counter_ns() - start_ns) / 1000.0
            return NerveTelemetry(
                status=NerveStatus.CYCLIC_MUTATION,
                latency_us=lat,
                reason=f"Cyclic state oscillation detected with period {detected_cycle_len}",
                cycle_length=detected_cycle_len,
                total_checks=self._total_checks,
                interventions=self._interventions,
            )

        # Append to sliding history
        self._action_hashes.append(act_hash)
        self._state_hashes.append(st_hash)
        if len(self._action_hashes) > self.window_size * 2:
            self._action_hashes = self._action_hashes[-self.window_size:]
            self._state_hashes = self._state_hashes[-self.window_size:]

        lat = (time.perf_counter_ns() - start_ns) / 1000.0
        return NerveTelemetry(
            status=NerveStatus.CLEAR,
            latency_us=lat,
            reason="All invariants clear",
            total_checks=self._total_checks,
            interventions=self._interventions,
        )
