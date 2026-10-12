"""
APEX_OMNI_SWE Sovereign Autonomous Software Engineering Hypervisor.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from apex_omni_swe.hypervisor import ApexOmniSWEHypervisor, SWESolutionReport
from apex_omni_swe.core.primitives import (
    ASTSymbol,
    CodeGraph,
    EdgeKind,
    IssueSpec,
    MutationKind,
    NerveStatus,
    PatchCandidate,
    SkillIntentType,
    VerificationReport,
)

__version__ = "1.0.0"

__all__ = [
    "ApexOmniSWEHypervisor",
    "SWESolutionReport",
    "ASTSymbol",
    "CodeGraph",
    "EdgeKind",
    "IssueSpec",
    "MutationKind",
    "NerveStatus",
    "PatchCandidate",
    "SkillIntentType",
    "VerificationReport",
]
