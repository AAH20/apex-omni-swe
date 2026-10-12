"""
APEX_OMNI_SWE AutoHarness Audit Ledger Plane (LED).
Cryptographic SHA-256 Provenance Chain Linking Skills to Episode Evidence.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class LedgerBlock:
    """A tamper-evident provenance block in the AutoHarness ledger chain."""
    block_index: int
    parent_hash: str
    block_hash: str
    skill_id: str
    episode_id: str
    action: str
    details: Dict[str, Any]
    timestamp_ns: int = field(default_factory=time.time_ns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_index": self.block_index,
            "parent_hash": self.parent_hash,
            "block_hash": self.block_hash,
            "skill_id": self.skill_id,
            "episode_id": self.episode_id,
            "action": self.action,
            "timestamp_ns": self.timestamp_ns,
        }


class AutoHarnessAuditLedger:
    """
    LED Plane: Cryptographic provenance ledger verifying the complete chain of custody
    from empirical episode executions to production skill deployments.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self._chain: List[LedgerBlock] = []

    def append_event(
        self,
        skill_id: str,
        episode_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> LedgerBlock:
        parent_hash = self._chain[-1].block_hash if self._chain else self.GENESIS_HASH
        idx = len(self._chain)
        det = details or {}
        raw = f"{idx}:{parent_hash}:{skill_id}:{episode_id}:{action}:{det}"
        b_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        block = LedgerBlock(
            block_index=idx,
            parent_hash=parent_hash,
            block_hash=b_hash,
            skill_id=skill_id,
            episode_id=episode_id,
            action=action,
            details=det,
        )
        self._chain.append(block)
        return block

    def verify_integrity(self) -> bool:
        """Verifies the unbroken cryptographic continuity of the provenance chain."""
        if not self._chain:
            return True

        for i, block in enumerate(self._chain):
            expected_parent = self.GENESIS_HASH if i == 0 else self._chain[i - 1].block_hash
            if block.parent_hash != expected_parent:
                return False

            raw = f"{block.block_index}:{block.parent_hash}:{block.skill_id}:{block.episode_id}:{block.action}:{block.details}"
            computed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if block.block_hash != computed:
                return False

        return True

    def block_count(self) -> int:
        return len(self._chain)

    def get_skill_history(self, skill_id: str) -> List[LedgerBlock]:
        return [b for b in self._chain if b.skill_id == skill_id]
