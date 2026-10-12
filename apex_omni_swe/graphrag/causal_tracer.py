"""
APEX_OMNI_SWE Causal Trace & Constrained Shortest Path Solver (WCSPP).
Label-Setting Dynamic Programming for Causal Execution Paths under Token Constraints.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import heapq
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any

from apex_omni_swe.core.primitives import CodeGraph, ASTSymbol, EdgeKind


@dataclass
class CausalTraceResult:
    """Execution telemetry and optimal causal path."""
    source_id: str
    target_id: str
    path: List[str]
    total_cost: float
    total_weight: float
    is_feasible: bool
    latency_us: float
    labels_explored: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "path_length": len(self.path),
            "total_cost": round(self.total_cost, 4),
            "total_weight": round(self.total_weight, 4),
            "is_feasible": self.is_feasible,
            "latency_us": round(self.latency_us, 2),
            "labels_explored": self.labels_explored,
        }


class CausalPathTracer:
    """
    Weight-Constrained Shortest Path Problem (WCSPP) solver for causal code tracing.
    Solves for the causal chain of calls leading from bug symptom to culprit function,
    bounded by token window constraints W_max.
    """

    def __init__(self, max_weight_bound: float = 4000.0):
        self.max_weight_bound = max_weight_bound

    def trace(
        self,
        graph: CodeGraph,
        source_id: str,
        target_id: str,
        max_weight: Optional[float] = None,
    ) -> CausalTraceResult:
        start_ns = time.perf_counter_ns()
        weight_limit = max_weight if max_weight is not None else self.max_weight_bound

        if source_id not in graph.nodes or target_id not in graph.nodes:
            return CausalTraceResult(
                source_id=source_id,
                target_id=target_id,
                path=[],
                total_cost=float("inf"),
                total_weight=0.0,
                is_feasible=False,
                latency_us=0.0,
                labels_explored=0,
            )

        if source_id == target_id:
            latency_us = (time.perf_counter_ns() - start_ns) / 1000.0
            node_weight = float(graph.nodes[source_id].token_cost)
            return CausalTraceResult(
                source_id=source_id,
                target_id=target_id,
                path=[source_id],
                total_cost=0.0,
                total_weight=node_weight,
                is_feasible=node_weight <= weight_limit,
                latency_us=latency_us,
                labels_explored=1,
            )

        # Label-setting priority queue: (cost, weight, current_node, path)
        pq: List[Tuple[float, float, str, List[str]]] = []
        source_weight = float(graph.nodes[source_id].token_cost)
        heapq.heappush(pq, (0.0, source_weight, source_id, [source_id]))

        # Pareto-optimal label frontier for each node: list of (cost, weight)
        frontier: Dict[str, List[Tuple[float, float]]] = {source_id: [(0.0, source_weight)]}
        labels_explored = 0

        best_target_path: Optional[List[str]] = None
        best_target_cost = float("inf")
        best_target_weight = float("inf")

        while pq:
            cost, weight, curr, path = heapq.heappop(pq)
            labels_explored += 1

            if curr == target_id:
                if cost < best_target_cost:
                    best_target_cost = cost
                    best_target_weight = weight
                    best_target_path = path
                break

            # Explore neighbors
            neighbors = graph.get_neighbors(curr)
            for nxt, kind, edge_cost in neighbors:
                nxt_node = graph.nodes.get(nxt)
                if not nxt_node:
                    continue
                nxt_weight = weight + float(nxt_node.token_cost)
                if nxt_weight > weight_limit:
                    continue
                nxt_cost = cost + edge_cost

                # Pareto dominance check
                is_dominated = False
                existing_labels = frontier.get(nxt, [])
                for f_cost, f_weight in existing_labels:
                    if f_cost <= nxt_cost and f_weight <= nxt_weight:
                        is_dominated = True
                        break

                if not is_dominated:
                    # Prune existing labels dominated by the new label
                    new_frontier = [
                        (fc, fw) for fc, fw in existing_labels
                        if not (nxt_cost <= fc and nxt_weight <= fw)
                    ]
                    new_frontier.append((nxt_cost, nxt_weight))
                    frontier[nxt] = new_frontier

                    heapq.heappush(pq, (nxt_cost, nxt_weight, nxt, path + [nxt]))

        latency_us = (time.perf_counter_ns() - start_ns) / 1000.0

        if best_target_path is not None:
            return CausalTraceResult(
                source_id=source_id,
                target_id=target_id,
                path=best_target_path,
                total_cost=best_target_cost,
                total_weight=best_target_weight,
                is_feasible=True,
                latency_us=latency_us,
                labels_explored=labels_explored,
            )

        # Fallback: simple shortest path unconstrained if no budget-feasible path exists
        return CausalTraceResult(
            source_id=source_id,
            target_id=target_id,
            path=[],
            total_cost=float("inf"),
            total_weight=float("inf"),
            is_feasible=False,
            latency_us=latency_us,
            labels_explored=labels_explored,
        )
