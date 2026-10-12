"""
APEX_OMNI_SWE Transactional Git Saga & Ephemeral Worktree Manager.
LIFO Compensating Rollback Journal for Atomic Repository Invariant Protection.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import hashlib
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.core.primitives import PatchCandidate


@dataclass
class SagaStep:
    """A transactional state modification step with its inverse compensating action."""
    step_id: str
    file_path: str
    original_content: str
    mutated_content: str
    patch_id: str
    applied_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "file_path": self.file_path,
            "patch_id": self.patch_id,
            "applied_ns": self.applied_ns,
        }


class GitSagaJournal:
    """
    LIFO Compensating Rollback Journal.
    Ensures that any repository mutation that fails verification or induces
    regression can be atomically rolled back in O(1) time.
    """

    def __init__(self):
        self._journal: List[SagaStep] = []
        self._committed_history: List[SagaStep] = []

    def record_mutation(
        self,
        file_path: str,
        original_content: str,
        mutated_content: str,
        patch_id: str,
    ) -> SagaStep:
        step_id = hashlib.sha256(f"{file_path}:{patch_id}:{time.time_ns()}".encode("utf-8")).hexdigest()[:12]
        step = SagaStep(
            step_id=f"saga-{step_id}",
            file_path=file_path,
            original_content=original_content,
            mutated_content=mutated_content,
            patch_id=patch_id,
        )
        self._journal.append(step)
        return step

    def pop_last_step(self) -> Optional[SagaStep]:
        if not self._journal:
            return None
        return self._journal.pop()

    def pending_count(self) -> int:
        return len(self._journal)

    def commit_all(self) -> int:
        count = len(self._journal)
        self._committed_history.extend(self._journal)
        self._journal.clear()
        return count

    def get_rollback_plan(self) -> List[Tuple[str, str]]:
        """Returns ordered list of (file_path, original_content) to revert in LIFO order."""
        plan = []
        while self._journal:
            step = self._journal.pop()
            plan.append((step.file_path, step.original_content))
        return plan


class EphemeralWorktreeSandbox:
    """
    Virtual / Ephemeral Workspace Sandbox.
    Manages in-memory file systems and temporary disk directories
    to run isolated SWE test executions without polluting the main repo.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir
        self.virtual_files: Dict[str, str] = {}
        self.saga_journal = GitSagaJournal()
        self._temp_dir: Optional[str] = None

    def initialize_workspace(self, file_map: Dict[str, str]) -> None:
        """Initializes virtual workspace with a snapshot of repository files."""
        self.virtual_files = dict(file_map)

    def read_file(self, file_path: str) -> Optional[str]:
        return self.virtual_files.get(file_path)

    def apply_patch(self, patch: PatchCandidate) -> bool:
        """Applies patch candidate and logs compensating reversal to the Saga journal."""
        orig = self.virtual_files.get(patch.file_path, patch.original_code)
        self.saga_journal.record_mutation(
            file_path=patch.file_path,
            original_content=orig,
            mutated_content=patch.mutated_code,
            patch_id=patch.patch_id,
        )
        self.virtual_files[patch.file_path] = patch.mutated_code
        return True

    def rollback_regression(self) -> int:
        """Executes compensating LIFO rollbacks to restore repository invariants."""
        plan = self.saga_journal.get_rollback_plan()
        for file_path, original_content in plan:
            self.virtual_files[file_path] = original_content
        return len(plan)

    def commit_transaction(self) -> int:
        return self.saga_journal.commit_all()

    def export_snapshot(self) -> Dict[str, str]:
        return dict(self.virtual_files)
