"""
APEX_OMNI_SWE AutoHarness Surfacing Plane (IDX).
Session-Start Truncated Skill Index Injection and Trigger Matching.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.autoharness.reflection_plane import SkillDefinition


class AutoHarnessIndexSurfacing:
    """
    IDX Plane: Surfaces relevant skills at session boot and query time.
    Provides compact representations to minimize context token consumption.
    """

    def __init__(self, max_index_tokens: int = 500):
        self.max_index_tokens = max_index_tokens

    def build_session_index(self, skills: Dict[str, SkillDefinition]) -> str:
        """
        Builds a compact summary table of available skills for prompt injection.
        """
        if not skills:
            return "No prior AutoHarness skills registered in library."

        lines = [
            "# AutoHarness Knowledge Index",
            "| Skill ID | Name | Scope | Triggers | Confidence |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for s in skills.values():
            triggers_str = ", ".join(s.trigger_patterns[:3])
            lines.append(
                f"| `{s.skill_id}` | {s.name} | `{s.repo_scope}` | {triggers_str} | {round(s.confidence, 2)} |"
            )

        return "\n".join(lines)

    def match_skills(
        self,
        task_query: str,
        skills: Dict[str, SkillDefinition],
        repo_name: Optional[str] = None,
        top_k: int = 3,
    ) -> List[SkillDefinition]:
        """
        Retrieves top-k relevant skills by keyword overlap and repository scope.
        """
        q_tokens = set(task_query.lower().replace("_", " ").replace("-", " ").split())
        scored: List[Tuple[float, SkillDefinition]] = []

        for skill in skills.values():
            score = 0.0
            # Scope matching bonus
            if repo_name and (skill.repo_scope == repo_name or skill.repo_scope == "*"):
                score += 5.0

            # Trigger matching
            for trig in skill.trigger_patterns:
                trig_tokens = set(trig.lower().split())
                if trig_tokens & q_tokens:
                    score += 3.0 * len(trig_tokens & q_tokens)

            # Description token overlap
            desc_tokens = set(skill.description.lower().split())
            overlap = len(desc_tokens & q_tokens)
            score += 0.5 * overlap

            score *= skill.confidence
            if score > 0.0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored[:top_k]]
