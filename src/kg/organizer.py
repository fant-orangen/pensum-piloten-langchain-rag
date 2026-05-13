"""MST-based context organizer — implements the KG-based context organization from KG2RAG.

Given a set of weighted edges from the expanded subgraph, this module:
  1. Builds an undirected weighted graph (one edge per entity pair, keeping max weight)
  2. Finds connected components
  3. Computes the maximum spanning tree of each component
  4. Returns the surviving edges grouped by component

Each surviving edge carries a chunk_id. The caller reads these out to determine
which chunks form the final context. Weights must be assigned by the caller as
similarity(query, chunk) before calling build_mst_subgraphs.
"""

from dataclasses import dataclass

import networkx as nx


@dataclass
class WeightedEdge:
    """KG edge annotated with query relevance for MST filtering."""

    head: str      # entity name
    tail: str      # entity name
    relation: str  # relation label
    chunk_id: str  # source chunk this triplet was extracted from
    weight: float  # similarity(query, source_chunk) — assigned by caller


def build_mst_subgraphs(edges: list[WeightedEdge]) -> list[list[WeightedEdge]]:
    """Partition edges into connected components and return the MST of each.

    Multiple edges between the same entity pair are reduced to the one with the
    highest weight before the MST is computed. This is the pre-deduplication step
    required because nx.Graph (simple graph) only keeps one edge per pair, and
    maximum_spanning_tree requires a simple graph.

    Returns a list of components, each a list of WeightedEdges surviving the MST.
    Components are returned in descending order of mean edge weight.
    """
    if not edges:
        return []

    # Build a lookup: (canonical_pair) -> best WeightedEdge for that pair.
    # Canonical pair: (min(head,tail), max(head,tail)) so direction is ignored.
    best: dict[tuple[str, str], WeightedEdge] = {}
    for e in edges:
        key = (min(e.head, e.tail), max(e.head, e.tail))
        if key not in best or e.weight > best[key].weight:
            best[key] = e

    # Build simple undirected graph from best edges.
    G = nx.Graph()
    for key, e in best.items():
        G.add_edge(e.head, e.tail, weight=e.weight, key=key)

    # Process each connected component independently.
    components: list[list[WeightedEdge]] = []
    for node_set in nx.connected_components(G): # Organise into connected components
        subgraph = G.subgraph(node_set)
        mst = nx.maximum_spanning_tree(subgraph, weight="weight")

        component_edges: list[WeightedEdge] = []
        for u, v in mst.edges():
            key = (min(u, v), max(u, v))
            component_edges.append(best[key])

        if component_edges:
            components.append(component_edges)

    # Sort components by mean edge weight descending — most relevant first.
    components.sort(
        key=lambda comp: sum(e.weight for e in comp) / len(comp),
        reverse=True,
    )

    return components
