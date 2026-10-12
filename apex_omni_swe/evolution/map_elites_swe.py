"""
APEX_OMNI_SWE MAP-Elites 4D Quality-Diversity Archive.
Multi-Dimensional Quality-Diversity Illumination for Software Engineering Repairs.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from apex_omni_swe.core.primitives import PatchCandidate, VerificationReport
from apex_omni_swe.evolution.fitness_evaluator import SWEFitnessEvaluator


@dataclass
class EliteCell:
    """An illuminated niche in the MAP-Elites archive."""
    coordinates: Tuple[int, int, int, int]
    patch: PatchCandidate
    fitness: float
    verification_report: VerificationReport
    generation_discovered: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coordinates": self.coordinates,
            "patch_id": self.patch.patch_id,
            "fitness": self.fitness,
            "is_resolved": self.verification_report.is_resolved,
            "generation": self.generation_discovered,
        }


class MAPElitesSWEArchive:
    """
    4-Dimensional MAP-Elites Quality-Diversity grid:
        Dim 0: Fault Localization Precision (0: Low, 1: Med, 2: Pinpoint)
        Dim 1: Patch Compactness (0: Minimal <= 5 lines, 1: Medium 6-15, 2: Broad > 15)
        Dim 2: Test Rigor (0: Degraded, 1: Partial, 2: Invariant-Preserved 100%)
        Dim 3: Token Economy (0: Ultracompact < 60 tokens, 1: Normal 60-150, 2: Verbose > 150)
    Total Niche Space: 3 x 3 x 3 x 3 = 81 discrete behavioural cells.
    """

    def __init__(self):
        self.grid: Dict[Tuple[int, int, int, int], EliteCell] = {}
        self.fitness_evaluator = SWEFitnessEvaluator()
        self.total_evaluations = 0
        self.current_generation = 0

    def compute_niche(
        self,
        patch: PatchCandidate,
        report: VerificationReport,
        localization_precision: int = 2,
    ) -> Tuple[int, int, int, int]:
        # Dim 0: Localization (0, 1, 2)
        d0 = max(0, min(2, localization_precision))

        # Dim 1: Patch Compactness
        if patch.ast_edit_distance <= 5:
            d1 = 0
        elif patch.ast_edit_distance <= 15:
            d1 = 1
        else:
            d1 = 2

        # Dim 2: Test Rigor
        if report.regression_detected or report.pass_to_pass_passed < report.pass_to_pass_total:
            d2 = 0
        elif report.pass_to_pass_total > 0 and report.pass_to_pass_passed == report.pass_to_pass_total:
            d2 = 2
        else:
            d2 = 1

        # Dim 3: Token Economy
        if patch.token_cost < 60:
            d3 = 0
        elif patch.token_cost <= 150:
            d3 = 1
        else:
            d3 = 2

        return (d0, d1, d2, d3)

    def consider_candidate(
        self,
        patch: PatchCandidate,
        report: VerificationReport,
        localization_precision: int = 2,
    ) -> bool:
        """
        Evaluates candidate and replaces existing elite in its niche if fitness is superior.
        Returns True if candidate became a new elite.
        """
        self.total_evaluations += 1
        fitness = self.fitness_evaluator.evaluate(patch, report)
        coords = self.compute_niche(patch, report, localization_precision)

        existing = self.grid.get(coords)
        if existing is None or fitness > existing.fitness:
            self.grid[coords] = EliteCell(
                coordinates=coords,
                patch=patch,
                fitness=fitness,
                verification_report=report,
                generation_discovered=self.current_generation,
            )
            return True
        return False

    def sample_elites(self, count: int = 2) -> List[PatchCandidate]:
        """Samples up to `count` distinct elite patches uniformly from the populated niches."""
        if not self.grid:
            return []
        cells = list(self.grid.values())
        k = min(count, len(cells))
        sampled = random.sample(cells, k)
        return [cell.patch for cell in sampled]

    def best_elite(self) -> Optional[EliteCell]:
        if not self.grid:
            return None
        return max(self.grid.values(), key=lambda cell: cell.fitness)

    def best_resolved_elite(self) -> Optional[EliteCell]:
        resolved = [c for c in self.grid.values() if c.verification_report.is_resolved]
        if not resolved:
            return None
        return max(resolved, key=lambda cell: cell.fitness)

    def coverage_ratio(self) -> float:
        total_niches = 81.0
        return len(self.grid) / total_niches

    def cell_count(self) -> int:
        return len(self.grid)
