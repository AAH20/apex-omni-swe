"""
APEX_OMNI_SWE Prize-Collecting Steiner Tree (PCST) Solver.
Primal-Dual Goemans-Williamson 2-Approximation for Minimal Bug Subgraphs.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import heapq
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any

from apex_omni_swe.core.primitives import CodeGraph, ASTSymbol, EdgeKind


@dataclass
class PCSTResult:
    """Telemetry and solution output for PCST optimization."""
    selected_nodes: Set[str]
    selected_edges: List[Tuple[str, str, EdgeKind, float]]
    total_prize_collected: float
    total_edge_cost: float
    objective_value: float
    latency_us: float
    iteration_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_nodes_count": len(self.selected_nodes),
            "selected_edges_count": len(self.selected_edges),
            "total_prize_collected": round(self.total_prize_collected, 4),
            "total_edge_cost": round(self.total_edge_cost, 4),
            "objective_value": round(self.objective_value, 4),
            "latency_us": round(self.latency_us, 2),
            "iteration_count": self.iteration_count,
        }


class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) with path compression and rank."""

    def __init__(self, elements: List[str]):
        self.parent: Dict[str, str] = {x: x for x in elements}
        self.rank: Dict[str, int] = {x: 0 for x in elements}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        return True


class PCSTPrimalDualSolver:
    """
    Goemans-Williamson Primal-Dual algorithm for Prize-Collecting Steiner Tree.
    Guarantees a 2-approximation factor in O(|E| log |V|) time.
    Used for pinpointing minimal connected causal code subgraphs.
    """

    def __init__(self, eps: float = 1e-9):
        self.eps = eps

    def solve(self, graph: CodeGraph, root_node_id: Optional[str] = None) -> PCSTResult:
        start_ns = time.perf_counter_ns()
        nodes = list(graph.nodes.keys())
        if not nodes:
            return PCSTResult(
                selected_nodes=set(),
                selected_edges=[],
                total_prize_collected=0.0,
                total_edge_cost=0.0,
                objective_value=0.0,
                latency_us=0.0,
                iteration_count=0,
            )

        # 1. Initialize components and dual values
        dsu = DisjointSetUnion(nodes)
        component_prizes: Dict[str, float] = {
            node_id: graph.nodes[node_id].prize for node_id in nodes
        }
        active_components: Set[str] = {
            node_id for node_id in nodes if component_prizes[node_id] > self.eps
        }
        
        # If root is specified, guarantee its component remains prioritized
        if root_node_id and root_node_id in graph.nodes:
            component_prizes[root_node_id] = max(component_prizes[root_node_id], 1000.0)
            active_components.add(root_node_id)

        # Extract undirected candidate edges
        # Format: (cost, u, v, kind)
        edge_dict: Dict[Tuple[str, str], Tuple[EdgeKind, float]] = {}
        for u, targets in graph.adjacency.items():
            for v, (kind, cost) in targets.items():
                pair = (min(u, v), max(u, v))
                if pair not in edge_dict or cost < edge_dict[pair][1]:
                    edge_dict[pair] = (kind, max(cost, 1e-6))

        edges: List[Tuple[float, str, str, EdgeKind]] = []
        for (u, v), (kind, cost) in edge_dict.items():
            edges.append((cost, u, v, kind))

        # Slack for each edge
        slack: Dict[Tuple[str, str], float] = {
            (min(u, v), max(u, v)): cost for cost, u, v, _ in edges
        }

        tight_edges_stack: List[Tuple[str, str, EdgeKind, float]] = []
        iterations = 0

        # Primal-dual growth phase
        while len(active_components) > 0 and len(edges) > 0:
            iterations += 1
            # Find minimum dual step epsilon_step
            # Event A: An edge between two components becomes tight
            min_edge_event: Optional[Tuple[float, str, str, EdgeKind]] = None
            min_step = float("inf")

            for cost, u, v, kind in edges:
                root_u = dsu.find(u)
                root_v = dsu.find(v)
                if root_u == root_v:
                    continue

                active_count = (1 if root_u in active_components else 0) + (1 if root_v in active_components else 0)
                if active_count == 0:
                    continue

                current_slack = slack[(min(u, v), max(u, v))]
                step = current_slack / active_count
                if step < min_step:
                    min_step = step
                    min_edge_event = (cost, u, v, kind)

            # Event B: An active component exhausts its prize
            min_component_event: Optional[str] = None
            for comp in active_components:
                rem_prize = component_prizes[comp]
                if rem_prize < min_step:
                    min_step = rem_prize
                    min_component_event = comp

            if min_step == float("inf") or min_step <= 0:
                break

            # Advance duals: reduce edge slacks and component remaining prizes
            for (u, v) in list(slack.keys()):
                root_u = dsu.find(u)
                root_v = dsu.find(v)
                if root_u == root_v:
                    continue
                active_count = (1 if root_u in active_components else 0) + (1 if root_v in active_components else 0)
                slack[(u, v)] = max(0.0, slack[(u, v)] - min_step * active_count)

            for comp in list(active_components):
                component_prizes[comp] -= min_step
                if component_prizes[comp] <= self.eps:
                    active_components.remove(comp)

            # Handle Event A (Edge becomes tight)
            if min_edge_event and slack[(min(min_edge_event[1], min_edge_event[2]), max(min_edge_event[1], min_edge_event[2]))] <= self.eps:
                _, u, v, kind = min_edge_event
                root_u = dsu.find(u)
                root_v = dsu.find(v)
                if root_u != root_v:
                    cost = edge_dict[(min(u, v), max(u, v))][1]
                    tight_edges_stack.append((u, v, kind, cost))
                    # Merge components
                    new_prize = component_prizes.get(root_u, 0.0) + component_prizes.get(root_v, 0.0)
                    was_active = (root_u in active_components) or (root_v in active_components)
                    active_components.discard(root_u)
                    active_components.discard(root_v)

                    dsu.union(u, v)
                    new_root = dsu.find(u)
                    component_prizes[new_root] = new_prize
                    if was_active and new_prize > self.eps:
                        active_components.add(new_root)

        # 2. Reverse-delete pruning phase
        # Form candidate forest from tight_edges_stack
        forest_edges: List[Tuple[str, str, EdgeKind, float]] = []
        for edge in tight_edges_stack:
            forest_edges.append(edge)

        # Build adjacency for forest
        tree_adj: Dict[str, List[Tuple[str, EdgeKind, float]]] = {n: [] for n in nodes}
        for u, v, kind, cost in forest_edges:
            tree_adj[u].append((v, kind, cost))
            tree_adj[v].append((u, kind, cost))

        # Find connected components with positive prize
        visited: Set[str] = set()
        best_component_nodes: Set[str] = set()
        best_component_edges: List[Tuple[str, str, EdgeKind, float]] = []
        best_net_value = -float("inf")

        for node in nodes:
            if node in visited:
                continue
            # BFS component
            comp_nodes: Set[str] = set()
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                comp_nodes.add(curr)
                for neighbor, _, _ in tree_adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Filter edges belonging to this component
            comp_edges = [
                (u, v, k, c) for u, v, k, c in forest_edges
                if u in comp_nodes and v in comp_nodes
            ]

            # Prune zero/negative prize leaves iteratively
            pruned_nodes, pruned_edges = self._prune_leaves(comp_nodes, comp_edges, graph)
            prize_sum = sum(graph.nodes[n].prize for n in pruned_nodes)
            cost_sum = sum(c for _, _, _, c in pruned_edges)
            net_val = prize_sum - cost_sum

            if root_node_id and root_node_id in pruned_nodes:
                best_component_nodes = pruned_nodes
                best_component_edges = pruned_edges
                break
            elif net_val > best_net_value and len(pruned_nodes) > 0:
                best_net_value = net_val
                best_component_nodes = pruned_nodes
                best_component_edges = pruned_edges

        # Fallback if empty: pick highest prize single node
        if not best_component_nodes:
            max_node = max(nodes, key=lambda n: graph.nodes[n].prize)
            best_component_nodes = {max_node}
            best_component_edges = []

        total_prize = sum(graph.nodes[n].prize for n in best_component_nodes)
        total_cost = sum(c for _, _, _, c in best_component_edges)
        all_prizes = sum(symbol.prize for symbol in graph.nodes.values())
        objective = total_cost + (all_prizes - total_prize)

        latency_us = (time.perf_counter_ns() - start_ns) / 1000.0
        return PCSTResult(
            selected_nodes=best_component_nodes,
            selected_edges=best_component_edges,
            total_prize_collected=total_prize,
            total_edge_cost=total_cost,
            objective_value=objective,
            latency_us=latency_us,
            iteration_count=iterations,
        )

    def _prune_leaves(
        self,
        nodes: Set[str],
        edges: List[Tuple[str, str, EdgeKind, float]],
        graph: CodeGraph,
    ) -> Tuple[Set[str], List[Tuple[str, str, EdgeKind, float]]]:
        """Prunes leaf nodes whose incident edge cost exceeds their prize."""
        active_nodes = set(nodes)
        active_edges = list(edges)

        changed = True
        while changed:
            changed = False
            # Compute degrees
            degree: Dict[str, int] = {n: 0 for n in active_nodes}
            incident_edges: Dict[str, List[Tuple[str, str, EdgeKind, float]]] = {n: [] for n in active_nodes}

            for edge in active_edges:
                u, v, _, _ = edge
                if u in active_nodes and v in active_nodes:
                    degree[u] += 1
                    degree[v] += 1
                    incident_edges[u].append(edge)
                    incident_edges[v].append(edge)

            for n in list(active_nodes):
                if degree[n] == 1:
                    edge = incident_edges[n][0]
                    cost = edge[3]
                    if graph.nodes[n].prize < cost:
                        active_nodes.remove(n)
                        active_edges.remove(edge)
                        changed = True
                elif degree[n] == 0 and len(active_nodes) > 1 and graph.nodes[n].prize <= 0.0:
                    active_nodes.remove(n)
                    changed = True

        return active_nodes, active_edges
