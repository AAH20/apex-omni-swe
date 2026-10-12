"""
APEX_OMNI_SWE AutoHarness Lifecycle & Capacity Manager (MNG).
Opportunity-Relative Usage Rate Ranking and Bounded Capacity Eviction.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.autoharness.reflection_plane import SkillDefinition


@dataclass
class EvictionReport:
    """Report detailing skills evicted to respect capacity bounds."""
    evicted_skill_ids: List[str]
    capacity_limit: int
    current_count: int
    retained_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evicted_count": len(self.evicted_skill_ids),
            "evicted_skill_ids": self.evicted_skill_ids,
            "capacity_limit": self.capacity_limit,
            "retained_count": self.retained_count,
        }


class AutoHarnessLifecycleManager:
    """
    MNG Plane: Tracks opportunity-relative usage rates across sessions
    and enforces maximum skill capacity caps to prevent context degradation.
    """

    def __init__(self, capacity_cap: int = 50):
        self.capacity_cap = capacity_cap

    def calculate_usage_rate(self, skill: SkillDefinition) -> float:
        """
        Usage Rate = Loads / Sessions Since Creation
        """
        denominator = max(1, skill.sessions_since_creation)
        return skill.loads / float(denominator)

    def advance_session(self, skills: Dict[str, SkillDefinition]) -> None:
        """Increments sessions_since_creation for all existing skills."""
        for skill in skills.values():
            skill.sessions_since_creation += 1

    def record_usage(self, skill: SkillDefinition) -> None:
        """Increments skill load count."""
        skill.loads += 1

    def enforce_capacity(self, skills: Dict[str, SkillDefinition]) -> EvictionReport:
        """
        If current skills exceed capacity_cap, evict the lowest-usage-rate skills.
        """
        if len(skills) <= self.capacity_cap:
            return EvictionReport(
                evicted_skill_ids=[],
                capacity_limit=self.capacity_cap,
                current_count=len(skills),
                retained_count=len(skills),
            )

        # Sort by usage rate ascending (lowest rate first)
        ranked = sorted(
            skills.values(),
            key=lambda s: (self.calculate_usage_rate(s), s.confidence),
        )

        excess_count = len(skills) - self.capacity_cap
        evicted_ids: List[str] = []
        for s in ranked[:excess_count]:
            evicted_ids.append(s.skill_id)
            del skills[s.skill_id]

        return EvictionReport(
            evicted_skill_ids=evicted_ids,
            capacity_limit=self.capacity_cap,
            current_count=len(skills) + len(evicted_ids),
            retained_count=len(skills),
        )
