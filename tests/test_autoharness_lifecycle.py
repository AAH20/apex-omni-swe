"""
Unit tests for APEX_OMNI_SWE AutoHarness 6-plane self-learning lifecycle.
Covers CAP, REF, promoter, IDX, MNG, and LED planes.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import unittest
from apex_omni_swe.core.primitives import SkillIntentType
from apex_omni_swe.autoharness.capture_plane import AutoHarnessCapturePlane
from apex_omni_swe.autoharness.reflection_plane import (
    AutoHarnessReflectionPlane,
    SkillDefinition,
    SkillIntent,
)
from apex_omni_swe.autoharness.promoter import AutoHarnessPromoter
from apex_omni_swe.autoharness.index_surfacing import AutoHarnessIndexSurfacing
from apex_omni_swe.autoharness.lifecycle_manager import AutoHarnessLifecycleManager
from apex_omni_swe.autoharness.audit_ledger import AutoHarnessAuditLedger


class TestAutoHarnessLifecycle(unittest.TestCase):
    def test_capture_and_reflection(self):
        cap = AutoHarnessCapturePlane(reflection_threshold=3)
        ep_id = cap.start_episode("my_repo", "Fix pagination bug")

        triggered1 = cap.record_turn("run_test", {"test": "t1"}, "FAIL", is_error=True)
        self.assertFalse(triggered1)
        triggered2 = cap.record_turn("apply_patch", {"patch": "p1"}, "OK", is_error=False)
        self.assertFalse(triggered2)
        triggered3 = cap.record_turn("run_test", {"test": "t1"}, "PASS", is_error=False)
        self.assertTrue(triggered3)

        trace = cap.conclude_episode(is_success=True)
        self.assertEqual(trace.total_turns(), 3)
        self.assertTrue(trace.is_success)

        ref = AutoHarnessReflectionPlane()
        intents = ref.reflect(trace, {})
        self.assertGreater(len(intents), 0)
        self.assertEqual(intents[0].intent_type, SkillIntentType.ADD)
        self.assertIsNotNone(intents[0].proposed_skill)

    def test_promoter_lint_and_storage(self):
        promoter = AutoHarnessPromoter()
        # Test safe skill
        good_skill = SkillDefinition(
            skill_id="s-01",
            name="safe_skill",
            description="A safe test recipe",
            trigger_patterns=["test", "verify"],
            recipe_steps=["Run pytest -k test_safe", "Check exit status"],
        )
        good_intent = SkillIntent(
            intent_type=SkillIntentType.ADD,
            target_skill_id="s-01",
            proposed_skill=good_skill,
            rationale="Valid test",
            source_episode_id="ep-01",
        )
        res = promoter.promote(good_intent)
        self.assertTrue(res.success)
        self.assertIsNotNone(promoter.get_skill("s-01"))

        # Test dangerous skill (must fail safety lint)
        bad_skill = SkillDefinition(
            skill_id="s-02",
            name="dangerous_skill",
            description="Destructive action",
            trigger_patterns=["destroy"],
            recipe_steps=["rm -rf /tmp/data"],
        )
        bad_intent = SkillIntent(
            intent_type=SkillIntentType.ADD,
            target_skill_id="s-02",
            proposed_skill=bad_skill,
            rationale="Malicious",
            source_episode_id="ep-02",
        )
        bad_res = promoter.promote(bad_intent)
        self.assertFalse(bad_res.success)
        self.assertIn("Safety violation", bad_res.reason)

    def test_index_surfacing_and_matching(self):
        idx = AutoHarnessIndexSurfacing()
        skills = {
            "s1": SkillDefinition("s1", "db_recipe", "PostgreSQL database migrations", ["database", "postgres"], ["Run migrate"]),
            "s2": SkillDefinition("s2", "ui_recipe", "React frontend state management", ["react", "frontend"], ["Run yarn test"]),
        }
        table = idx.build_session_index(skills)
        self.assertIn("db_recipe", table)
        self.assertIn("ui_recipe", table)

        matches = idx.match_skills("Help me with postgres migration failure", skills)
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0].name, "db_recipe")

    def test_lifecycle_manager_capacity(self):
        mng = AutoHarnessLifecycleManager(capacity_cap=2)
        skills = {
            "s1": SkillDefinition("s1", "skill1", "", ["t1"], ["step1"], loads=10, sessions_since_creation=2),
            "s2": SkillDefinition("s2", "skill2", "", ["t2"], ["step2"], loads=5, sessions_since_creation=2),
            "s3": SkillDefinition("s3", "skill3", "", ["t3"], ["step3"], loads=1, sessions_since_creation=5),
        }
        report = mng.enforce_capacity(skills)
        self.assertEqual(len(report.evicted_skill_ids), 1)
        self.assertIn("s3", report.evicted_skill_ids)
        self.assertEqual(len(skills), 2)

    def test_audit_ledger_integrity(self):
        ledger = AutoHarnessAuditLedger()
        b1 = ledger.append_event("s1", "ep1", "ADD", {"note": "initial"})
        b2 = ledger.append_event("s1", "ep2", "PATCH", {"note": "patch v2"})
        b3 = ledger.append_event("s2", "ep3", "ADD", {"note": "new skill"})

        self.assertEqual(ledger.block_count(), 3)
        self.assertTrue(ledger.verify_integrity())

        # Tamper check: alter a block hash
        ledger._chain[1].block_hash = "tampered_hash_0000000000"
        self.assertFalse(ledger.verify_integrity())


if __name__ == "__main__":
    unittest.main()
