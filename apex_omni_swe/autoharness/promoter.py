"""
APEX_OMNI_SWE AutoHarness Promoter Plane (promoter).
In-Memory Intent Validation and Atomic Skill Store.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.core.primitives import SkillIntentType
from apex_omni_swe.autoharness.reflection_plane import SkillDefinition, SkillIntent


@dataclass
class PromotionResult:
    """Telemetry and outcome of a skill promotion attempt."""
    success: bool
    skill_id: str
    intent_type: str
    reason: str
    latency_us: float
    timestamp_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "skill_id": self.skill_id,
            "intent_type": self.intent_type,
            "reason": self.reason,
            "latency_us": round(self.latency_us, 2),
        }


class AutoHarnessPromoter:
    """
    Promoter Plane: The exclusive writer for the AutoHarness skill ecosystem.
    Lints intents in memory for safety, structural completeness, and trigger placement,
    then executes atomic commits into the active skill registry.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        self.active_skills: Dict[str, SkillDefinition] = {}

    def lint_intent(self, intent: SkillIntent) -> Tuple[bool, str]:
        """
        Validates safety, structural completeness, and trigger hygiene.
        """
        if intent.intent_type == SkillIntentType.DELETE:
            if not intent.target_skill_id:
                return False, "Target skill ID required for DELETE"
            return True, "Valid DELETE intent"

        if not intent.proposed_skill:
            return False, "Missing proposed skill object"

        skill = intent.proposed_skill
        if not skill.name or not skill.name.strip():
            return False, "Skill name cannot be empty"

        if not skill.trigger_patterns:
            return False, "Skill must specify at least one trigger pattern"

        if not skill.recipe_steps:
            return False, "Skill must contain at least one recipe step"

        # Safety lint: Disallow dangerous shell patterns
        dangerous_tokens = ["rm -rf", "mkfs", ":(){ :|:& };:", "drop database"]
        for step in skill.recipe_steps:
            for tok in dangerous_tokens:
                if tok in step.lower():
                    return False, f"Safety violation: Step contains dangerous token '{tok}'"

        return True, "Lint passed"

    def promote(self, intent: SkillIntent) -> PromotionResult:
        """
        Applies validated intent atomically into active registry.
        """
        start_ns = time.perf_counter_ns()
        is_valid, lint_msg = self.lint_intent(intent)
        if not is_valid:
            lat = (time.perf_counter_ns() - start_ns) / 1000.0
            return PromotionResult(
                success=False,
                skill_id=intent.target_skill_id,
                intent_type=intent.intent_type.value,
                reason=f"Lint failed: {lint_msg}",
                latency_us=lat,
            )

        if intent.intent_type == SkillIntentType.ADD:
            self.active_skills[intent.proposed_skill.skill_id] = intent.proposed_skill
            reason = f"Skill '{intent.proposed_skill.name}' added"
        elif intent.intent_type == SkillIntentType.PATCH:
            self.active_skills[intent.target_skill_id] = intent.proposed_skill
            reason = f"Skill '{intent.target_skill_id}' patched to version {intent.proposed_skill.version}"
        elif intent.intent_type == SkillIntentType.MERGE:
            self.active_skills[intent.proposed_skill.skill_id] = intent.proposed_skill
            reason = f"Skill merged into '{intent.proposed_skill.name}'"
        elif intent.intent_type == SkillIntentType.DELETE:
            if intent.target_skill_id in self.active_skills:
                del self.active_skills[intent.target_skill_id]
                reason = f"Skill '{intent.target_skill_id}' pruned"
            else:
                reason = f"Skill '{intent.target_skill_id}' not found for deletion"

        lat = (time.perf_counter_ns() - start_ns) / 1000.0
        return PromotionResult(
            success=True,
            skill_id=intent.target_skill_id,
            intent_type=intent.intent_type.value,
            reason=reason,
            latency_us=lat,
        )

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self.active_skills.get(skill_id)

    def all_skills(self) -> Dict[str, SkillDefinition]:
        return dict(self.active_skills)
