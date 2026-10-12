"""
APEX_OMNI_SWE AutoHarness Reflection Plane (REF).
Automated Episode Reflection and Deterministic Skill Intent Synthesis.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any

from apex_omni_swe.core.primitives import SkillIntentType
from apex_omni_swe.autoharness.capture_plane import EpisodeTrace


@dataclass
class SkillDefinition:
    """Formal AutoHarness skill specification."""
    skill_id: str
    name: str
    description: str
    trigger_patterns: List[str]
    recipe_steps: List[str]
    repo_scope: str = "*"
    confidence: float = 0.8
    version: int = 1
    loads: int = 0
    sessions_since_creation: int = 1

    def to_markdown(self) -> str:
        triggers_md = "\n".join(f"- `{t}`" for t in self.trigger_patterns)
        steps_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.recipe_steps))
        return (
            f"# Skill: {self.name}\n"
            f"**ID:** {self.skill_id} | **Scope:** {self.repo_scope} | **Version:** {self.version}\n\n"
            f"## Description\n{self.description}\n\n"
            f"## Triggers\n{triggers_md}\n\n"
            f"## Execution Recipe\n{steps_md}\n"
        )


@dataclass
class SkillIntent:
    """Structured intent emitted by the REF plane for the promoter."""
    intent_type: SkillIntentType
    target_skill_id: str
    proposed_skill: Optional[SkillDefinition]
    rationale: str
    source_episode_id: str
    timestamp_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type.value,
            "target_skill_id": self.target_skill_id,
            "rationale": self.rationale,
            "source_episode_id": self.source_episode_id,
            "has_proposed_skill": self.proposed_skill is not None,
        }


class AutoHarnessReflectionPlane:
    """
    REF Plane: Analyzes episodic trajectories and synthesizes concrete skill intents
    (ADD, MERGE, PATCH, DELETE) to accelerate future problem-solving.
    """

    def __init__(self):
        pass

    def reflect(
        self,
        trace: EpisodeTrace,
        existing_skills: Dict[str, SkillDefinition],
    ) -> List[SkillIntent]:
        """
        Synthesizes skill intents from an episode trace.
        Deterministic heuristics:
        1. If success and no matching skill exists for repo/task, emit ADD.
        2. If failure repeated on known skill pattern, emit PATCH or DELETE.
        3. If two skills share > 60% trigger overlap, emit MERGE.
        """
        intents: List[SkillIntent] = []
        if not trace.turns:
            return intents

        # Extract tools used and key operations
        tools_used = [t.tool_name for t in trace.turns]
        successful_tools = [t.tool_name for t in trace.turns if not t.is_error]

        # Case 1: Successful episode -> ADD new skill if novel
        if trace.is_success and len(successful_tools) >= 2:
            skill_name = f"{trace.repo_name.replace('/', '_')}_harness_recipe"
            skill_id = f"skill-{hashlib.sha256(skill_name.encode('utf-8')).hexdigest()[:10]}"

            if skill_id not in existing_skills:
                steps = [
                    f"Invoke {t.tool_name} with parameters tailored to {trace.task_goal[:40]}"
                    for t in trace.turns if not t.is_error
                ]
                new_skill = SkillDefinition(
                    skill_id=skill_id,
                    name=skill_name,
                    description=f"Automated verification and harness recipe for {trace.repo_name}",
                    trigger_patterns=[trace.repo_name, "test_harness", "verification_recipe"],
                    recipe_steps=steps if steps else ["Run test suite and verify invariants"],
                    repo_scope=trace.repo_name,
                    confidence=0.9,
                )
                intents.append(
                    SkillIntent(
                        intent_type=SkillIntentType.ADD,
                        target_skill_id=skill_id,
                        proposed_skill=new_skill,
                        rationale=f"Episode {trace.episode_id} successfully validated execution trajectory",
                        source_episode_id=trace.episode_id,
                    )
                )

        # Case 2: Failed episode on existing skill -> PATCH
        if not trace.is_success:
            for skill_id, skill in existing_skills.items():
                if skill.repo_scope == trace.repo_name or skill.repo_scope == "*":
                    if any(t in trace.task_goal.lower() for t in skill.trigger_patterns):
                        # Skill failed in this context: emit PATCH to refine recipe
                        patched = SkillDefinition(
                            skill_id=skill.skill_id,
                            name=skill.name,
                            description=skill.description + " (Refined after failure)",
                            trigger_patterns=list(skill.trigger_patterns),
                            recipe_steps=skill.recipe_steps + ["Add defensive boundary guard before execution"],
                            repo_scope=skill.repo_scope,
                            confidence=max(0.5, skill.confidence - 0.1),
                            version=skill.version + 1,
                        )
                        intents.append(
                            SkillIntent(
                                intent_type=SkillIntentType.PATCH,
                                target_skill_id=skill_id,
                                proposed_skill=patched,
                                rationale=f"Episode {trace.episode_id} failed under existing recipe; injecting defensive guard",
                                source_episode_id=trace.episode_id,
                            )
                        )
                        break

        # Case 3: Overlapping triggers check -> MERGE
        skills_list = list(existing_skills.values())
        for i in range(len(skills_list)):
            for j in range(i + 1, len(skills_list)):
                s1 = skills_list[i]
                s2 = skills_list[j]
                if s1.repo_scope == s2.repo_scope:
                    set1 = set(s1.trigger_patterns)
                    set2 = set(s2.trigger_patterns)
                    overlap = len(set1 & set2) / max(1, len(set1 | set2))
                    if overlap >= 0.6:
                        merged_name = f"merged_{s1.name}"
                        merged_id = f"skill-{hashlib.sha256(merged_name.encode('utf-8')).hexdigest()[:10]}"
                        merged_skill = SkillDefinition(
                            skill_id=merged_id,
                            name=merged_name,
                            description=f"Unified recipe combining {s1.name} and {s2.name}",
                            trigger_patterns=list(set1 | set2),
                            recipe_steps=list(dict.fromkeys(s1.recipe_steps + s2.recipe_steps)),
                            repo_scope=s1.repo_scope,
                            confidence=max(s1.confidence, s2.confidence),
                            version=max(s1.version, s2.version) + 1,
                        )
                        intents.append(
                            SkillIntent(
                                intent_type=SkillIntentType.MERGE,
                                target_skill_id=s1.skill_id,
                                proposed_skill=merged_skill,
                                rationale=f"High trigger overlap ({round(overlap*100, 1)}%) between {s1.name} and {s2.name}",
                                source_episode_id=trace.episode_id,
                            )
                        )

        return intents
