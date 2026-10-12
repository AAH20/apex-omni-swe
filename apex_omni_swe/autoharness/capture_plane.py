"""
APEX_OMNI_SWE AutoHarness Capture Plane (CAP).
Turn Hook Capture and Deterministic Reflection Threshold Triggers.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class TurnEvent:
    """A discrete turn execution event within an agent trajectory."""
    turn_index: int
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: str
    is_error: bool
    latency_ms: float
    timestamp_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output_summary": self.tool_output[:200] if len(self.tool_output) > 200 else self.tool_output,
            "is_error": self.is_error,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp_ns": self.timestamp_ns,
        }


@dataclass
class EpisodeTrace:
    """Complete episodic trajectory captured for AutoHarness reflection."""
    episode_id: str
    repo_name: str
    task_goal: str
    turns: List[TurnEvent]
    is_success: bool
    created_ns: int = field(default_factory=time.time_ns)

    def total_turns(self) -> int:
        return len(self.turns)

    def error_count(self) -> int:
        return sum(1 for t in self.turns if t.is_error)

    def fingerprint(self) -> str:
        raw = f"{self.repo_name}:{self.task_goal}:{len(self.turns)}:{self.is_success}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class AutoHarnessCapturePlane:
    """
    CAP Plane: Intercepts all agent turns, tools, and stdout/stderr streams.
    Triggers reflection when turn count exceeds threshold or on episode termination.
    """

    def __init__(self, reflection_threshold: int = 5):
        self.reflection_threshold = reflection_threshold
        self._current_turns: List[TurnEvent] = []
        self._episode_id: Optional[str] = None
        self._repo_name: str = ""
        self._task_goal: str = ""

    def start_episode(self, repo_name: str, task_goal: str) -> str:
        self._current_turns.clear()
        self._repo_name = repo_name
        self._task_goal = task_goal
        ep_hash = hashlib.sha256(f"{repo_name}:{task_goal}:{time.time_ns()}".encode("utf-8")).hexdigest()[:12]
        self._episode_id = f"ep-{ep_hash}"
        return self._episode_id

    def record_turn(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str,
        is_error: bool = False,
        latency_ms: float = 0.0,
    ) -> bool:
        """
        Records a turn event. Returns True if reflection threshold is reached.
        """
        turn = TurnEvent(
            turn_index=len(self._current_turns) + 1,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            is_error=is_error,
            latency_ms=latency_ms,
        )
        self._current_turns.append(turn)
        return len(self._current_turns) >= self.reflection_threshold

    def conclude_episode(self, is_success: bool) -> EpisodeTrace:
        trace = EpisodeTrace(
            episode_id=self._episode_id or f"ep-{time.time_ns()}",
            repo_name=self._repo_name,
            task_goal=self._task_goal,
            turns=list(self._current_turns),
            is_success=is_success,
        )
        self._current_turns.clear()
        return trace
