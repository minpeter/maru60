#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["pydantic>=2,<3"]
# ///
# ─── How to run ───
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
# Run from repository root: uv run .omo/evidence/pcb-routing-20261109/guard-classification/classify.py
# ──────────────────
"""Replay admitted material connectivity and classify rejected-contact consequences."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, NewType

from pydantic import BaseModel, ConfigDict

NodeId = NewType("NodeId", str)
ObjectId = NewType("ObjectId", str)
EdgeId = NewType("EdgeId", str)
OUT: Final = Path(__file__).resolve().parent
ROOT: Final = OUT.parents[3]
SOURCE: Final = ROOT / "pcb/experiments/resume-20261106-usb-pendant-prototype"
BOARD: Final = SOURCE / "pcb/maru60.kicad_pcb"
GRAPH: Final = SOURCE / "qa/material-graph.json"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Node(Frozen):
    kind: Literal["object", "zone"]
    uuid: ObjectId
    layer: str
    index: int
    area_mm2: float
    net: str


class Pad(Frozen):
    ref: str
    pad: str
    net: str


class Barrel(Frozen):
    uuid: ObjectId
    type: str
    nodes: tuple[NodeId, ...]
    proof: str


class Rejected(Frozen):
    kind: Literal["direct", "zone"]
    a: NodeId
    b: NodeId
    unguarded_area_mm2: float
    guarded_area_mm2: float


class MaterialGraph(Frozen):
    board_sha256: str
    source_path: str
    material_nodes: dict[NodeId, Node]
    material_edges: tuple[tuple[NodeId, NodeId, float, float], ...]
    barrel_joins: tuple[Barrel, ...]
    guard_failing_material_edges: tuple[Rejected, ...]
    material_roots: dict[NodeId, NodeId]
    object_nodes_by_layer: dict[ObjectId, dict[str, list[NodeId]]]
    object_material_roots: dict[ObjectId, list[NodeId]]
    pad_inventory: dict[ObjectId, Pad]
    pad_partitions_by_net: dict[str, list[list[ObjectId]]]


@dataclass(frozen=True, slots=True)
class EvidenceFailure(Exception):
    criterion: str

    def __str__(self) -> str:
        return self.criterion


def require(condition: bool, criterion: str) -> None:
    """Stop on a failed proof condition, including under python -O."""
    if not condition:
        raise EvidenceFailure(criterion)


@dataclass(frozen=True, slots=True)
class Edge:
    a: NodeId
    b: NodeId
    source_pointer: str
    raw_area_mm2: float | None
    guarded_area_mm2: float | None
    barrel_proof: str | None


@dataclass(frozen=True, slots=True)
class Witness:
    nodes: tuple[NodeId, ...]
    edges: tuple[EdgeId, ...]


@dataclass(frozen=True, slots=True)
class AcceptedGraph:
    """Mutable graph buffers are populated once, then used only for traversal."""
    adjacency: dict[NodeId, list[tuple[NodeId, EdgeId]]]
    edges: dict[EdgeId, Edge]

    def roots(self) -> dict[NodeId, NodeId]:
        """Compute canonical components without consulting persisted roots."""
        result: dict[NodeId, NodeId] = {}
        for seed in self.adjacency:
            if seed in result:
                continue
            seen = {seed}
            pending = deque([seed])
            while pending:
                for neighbor, _ in self.adjacency[pending.popleft()]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        pending.append(neighbor)
            canonical = min(seen)
            result.update((node, canonical) for node in seen)
        return result

    def path(self, endpoints: tuple[NodeId, NodeId]) -> Witness | None:
        """Find an admitted-edge shortest path, or exhaust the start component."""
        start, target = endpoints
        predecessors: dict[NodeId, tuple[NodeId, EdgeId]] = {}
        pending = deque([start])
        seen = {start}
        while pending and target not in seen:
            current = pending.popleft()
            for neighbor, edge_id in self.adjacency[current]:
                if neighbor not in seen:
                    predecessors[neighbor] = (current, edge_id)
                    seen.add(neighbor)
                    pending.append(neighbor)
        if target not in seen:
            return None
        nodes, edges = [target], []
        while nodes[-1] != start:
            previous, edge_id = predecessors[nodes[-1]]
            nodes.append(previous)
            edges.append(edge_id)
        return Witness(tuple(reversed(nodes)), tuple(reversed(edges)))

    def validate(self, witness: Witness, endpoints: tuple[NodeId, NodeId]) -> None:
        """Validate every supplied hop against admitted source evidence."""
        require(bool(witness.edges), "witness must contain at least one admitted edge")
        require(len(witness.nodes) == len(witness.edges) + 1, "witness hop count")
        require((witness.nodes[0], witness.nodes[-1]) == endpoints, "witness endpoints")
        for a, b, edge_id in zip(witness.nodes, witness.nodes[1:], witness.edges, strict=False):
            require(edge_id in self.edges, f"missing admitted edge: {edge_id}")
            edge = self.edges[edge_id]
            require({edge.a, edge.b} == {a, b}, f"edge endpoint mismatch: {edge_id}")


def main() -> None:
    """Produce source-bound classification and falsification receipts."""
    from dataclasses import asdict

    graph_bytes = GRAPH.read_bytes()
    source = MaterialGraph.model_validate_json(graph_bytes)
    board_hash = hashlib.sha256(BOARD.read_bytes()).hexdigest()
    require(board_hash == source.board_sha256, "current board SHA256 equals preserved graph board SHA256")
    edges: dict[EdgeId, Edge] = {}
    for index, (a, b, raw, guarded) in enumerate(source.material_edges):
        require(raw > 0 and guarded > 0, f"accepted contact areas positive: {index}")
        require(source.material_nodes[a].layer == source.material_nodes[b].layer, "contact layer agreement")
        edges[EdgeId(f"material_edges/{index}")] = Edge(a, b, f"/material_edges/{index}", raw, guarded, None)
    for index, barrel in enumerate(source.barrel_joins):
        require(bool(barrel.proof) and len(barrel.nodes) > 1, "barrel evidence present")
        require(all(source.material_nodes[n].uuid == barrel.uuid for n in barrel.nodes), "barrel object identity")
        for hop, (a, b) in enumerate(zip(barrel.nodes, barrel.nodes[1:])):
            edges[EdgeId(f"barrel_joins/{index}/{hop}")] = Edge(a, b, f"/barrel_joins/{index}", None, None, barrel.proof)
    adjacency: dict[NodeId, list[tuple[NodeId, EdgeId]]] = {n: [] for n in source.material_nodes}
    for edge_id, edge in edges.items():
        require(source.material_nodes[edge.a].net == source.material_nodes[edge.b].net, "admitted edge net agreement")
        adjacency[edge.a].append((edge.b, edge_id))
        adjacency[edge.b].append((edge.a, edge_id))
    accepted = AcceptedGraph(adjacency, edges)
    roots = accepted.roots()
    require(roots == source.material_roots, "recomputed roots equal stored roots for every node")
    objects: dict[ObjectId, dict[str, list[NodeId]]] = {
        uid: {layer: [] for layer in layers} for uid, layers in source.object_nodes_by_layer.items()
    }
    for node_id, node in source.material_nodes.items():
        if node.kind in {"object"}:
            objects.setdefault(node.uuid, {}).setdefault(node.layer, []).append(node_id)
    require(objects == source.object_nodes_by_layer, "reconstructed object layer membership")
    object_roots = {u: sorted({roots[n] for ns in layers.values() for n in ns}) for u, layers in objects.items()}
    require(object_roots == source.object_material_roots, "recomputed object roots")
    pad_groups: dict[str, dict[NodeId, list[ObjectId]]] = defaultdict(lambda: defaultdict(list))
    component_pads: dict[NodeId, list[ObjectId]] = defaultdict(list)
    for uid, pad in source.pad_inventory.items():
        require(len(object_roots[uid]) == 1, "every named pad has one accepted component")
        root = object_roots[uid][0]
        pad_groups[pad.net][root].append(uid)
        component_pads[root].append(uid)
    partitions = {net: sorted(sorted(group) for group in groups.values()) for net, groups in pad_groups.items()}
    require(partitions == source.pad_partitions_by_net, "recomputed named pad partitions")
    rows, controls = [], []
    used_edges: set[EdgeId] = set()
    members: dict[NodeId, list[NodeId]] = defaultdict(list)
    for node_id, root in roots.items():
        members[root].append(node_id)
    for index, rejected in enumerate(source.guard_failing_material_edges):
        a, b = rejected.a, rejected.b
        require(source.material_nodes[a].net == source.material_nodes[b].net, "rejected endpoint nets agree")
        require(rejected.unguarded_area_mm2 > 0 and rejected.guarded_area_mm2 <= 0, "rejected area criterion")
        require(all({edge.a, edge.b} != {a, b} for edge in edges.values()), "rejected pair absent from admitted edges")
        witness = accepted.path((a, b))
        same = roots[a] == roots[b]
        require((witness is not None) == same, "BFS witness agrees with recomputed components")
        consequence = "admitting this rejected edge cannot change any component or named-pad partition" if same else "admitting this edge merges distinct material components"
        pad_merge = not same and bool(component_pads[roots[a]]) and bool(component_pads[roots[b]])
        anchor = a if component_pads[roots[a]] else b
        require(bool(component_pads[roots[anchor]]), "at least one endpoint component contains named pads")
        pad_node = next(n for n in members[roots[anchor]] if n != anchor and source.material_nodes[n].uuid in source.pad_inventory)
        support = accepted.path((anchor, pad_node))
        if support is None:
            raise EvidenceFailure("missing named pad anchor support")
        if witness is not None:
            accepted.validate(witness, (a, b))
            used_edges.update(witness.edges)
        accepted.validate(support, (anchor, pad_node))
        used_edges.update(support.edges)
        removed_id = support.edges[0]
        mutated = AcceptedGraph(adjacency, {key: edge for key, edge in edges.items() if key != removed_id})
        try:
            mutated.validate(support, (anchor, pad_node))
        except EvidenceFailure as error:
            require(str(error) == f"missing admitted edge: {removed_id}", "negative control failed for intended reason")
            controls.append({"diagnostic_index": index, "witness_purpose": "named-pad-side support, NOT a rejected-endpoint bypass", "removed_edge_id": removed_id, "validator_rejected": True, "reason": str(error)})
        else:
            raise EvidenceFailure("negative control accepted a missing edge")
        rows.append({"diagnostic_index": index, "source_pointer": f"/guard_failing_material_edges/{index}", **rejected.model_dump(), "net": source.material_nodes[a].net, "endpoint_metadata": {a: source.material_nodes[a].model_dump(), b: source.material_nodes[b].model_dump()}, "recomputed_roots": [roots[a], roots[b]], "same_accepted_component": same, "accepted_bypass": asdict(witness) if witness else None, "endpoint_component_named_pad_counts": [len(component_pads[roots[a]]), len(component_pads[roots[b]])], "adding_this_edge_changes_named_pad_partition": pad_merge, "consequence": consequence})
        rows[-1]["named_pad_side_support_path"] = {"anchor": anchor, "pad_node": pad_node, "pad": source.pad_inventory[source.material_nodes[pad_node].uuid].model_dump(), **asdict(support)}
        rows[-1]["endpoint_component_node_counts"] = [len(members[roots[a]]), len(members[roots[b]])]
    augmented_adjacency = {node: list(hops) for node, hops in adjacency.items()}
    for index, rejected in enumerate(source.guard_failing_material_edges):
        augmented_adjacency[rejected.a].append((rejected.b, EdgeId(f"counterfactual/{index}")))
        augmented_adjacency[rejected.b].append((rejected.a, EdgeId(f"counterfactual/{index}")))
    augmented_roots = AcceptedGraph(augmented_adjacency, edges).roots()
    augmented_pads: dict[str, dict[NodeId, list[ObjectId]]] = defaultdict(lambda: defaultdict(list))
    for uid, pad in source.pad_inventory.items():
        augmented_pads[pad.net][augmented_roots[object_roots[uid][0]]].append(uid)
    augmented_partitions = {net: sorted(sorted(group) for group in groups.values()) for net, groups in augmented_pads.items()}
    require(augmented_partitions == partitions, "admitting all 51 rejected contacts leaves named pad partition unchanged")
    report = {"board_path": str(BOARD), "board_sha256": board_hash, "graph_path": str(GRAPH), "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(), "stored_graph_source_path": source.source_path, "material_node_count": len(roots), "accepted_material_edge_count": len(source.material_edges), "accepted_barrel_hop_count": len(edges) - len(source.material_edges), "recomputed_component_count": len(set(roots.values())), "named_pad_count": len(source.pad_inventory), "all_stored_roots_and_pad_partitions_recomputed_equal": True, "diagnostic_count_by_net": dict(Counter(source.material_nodes[d.a].net for d in source.guard_failing_material_edges)), "diagnostics": rows, "used_admitted_edge_evidence": {key: asdict(edges[key]) for key in sorted(used_edges)}, "component_named_pads": {root: {uid: source.pad_inventory[uid].model_dump() for uid in ids} for root, ids in component_pads.items()}, "limits": ["Topology replay of preserved native CAD material graph; no independent geometry renderer or fresh geometric-contact calculation.", "Admitted edge and barrel evidence is inherited from the source-hash-bound export; this pass validates graph consistency and paths, not the geometric proof implementation.", "Two-nanometre inward guard is an inherited numerical contact criterion, not fabrication tolerance or manufacturing margin.", "No DFM, SI, PDN, impedance, thermal, current-carrying, hardware, or fabrication qualification.", "A deleted witness edge invalidates that supplied witness; alternate paths may still exist in the mutated graph."]}
    require(hashlib.sha256(BOARD.read_bytes()).hexdigest() == board_hash, "board unchanged during classification")
    require(GRAPH.read_bytes() == graph_bytes, "preserved graph unchanged during classification")
    report["counterfactual_all_rejected_edges_admitted"] = {"component_count": len(set(augmented_roots.values())), "named_pad_partitions_unchanged": augmented_partitions == partitions}
    endpoint_roots = {roots[n] for d in source.guard_failing_material_edges for n in (d.a, d.b)}
    report["endpoint_components"] = {root: {"nodes": members[root], "named_pad_count": len(component_pads[root]), "admitted_boundary_edge_count": sum(roots[neighbor] != root for n in members[root] for neighbor, _ in adjacency[n])} for root in sorted(endpoint_roots)}
    (OUT / "classification.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "negative-controls.json").write_text(json.dumps(controls, indent=2) + "\n")
    print(json.dumps({"diagnostics": len(rows), "bypasses": sum(roots[d.a] == roots[d.b] for d in source.guard_failing_material_edges), "negative_controls": len(controls), "components": len(set(roots.values())), "board_sha256": board_hash, "status": "PASS"}))


if __name__ == "__main__":
    main()
