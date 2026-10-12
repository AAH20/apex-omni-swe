"""
APEX_OMNI_SWE Evolutionary Optimization Engine.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from apex_omni_swe.evolution.fitness_evaluator import SWEFitnessEvaluator
from apex_omni_swe.evolution.genetic_crossover import ASTSubtreeCrossover
from apex_omni_swe.evolution.map_elites_swe import MAPElitesSWEArchive, EliteCell

__all__ = [
    "SWEFitnessEvaluator",
    "ASTSubtreeCrossover",
    "MAPElitesSWEArchive",
    "EliteCell",
]
