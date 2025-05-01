"""Utilities for processing graph data for visualization."""

import igraph as ig
from typing import List, Tuple, Dict, Optional, Any

from graphs.triplet_handler import AbstractTripletHandler

def extract_communities_from_pipeline(triplet_handler: AbstractTripletHandler) -> List[List[int]]:
    """
    Extracts node lists for each community from a triplet_handler object.

    Assumes a specific structure within the triplet_handler object.

    Args:
        triplet_handler: The triplet_handler object containing community group data.

    Returns:
        A list where each inner list contains the node IDs of a community.
    """
    communities = []
    try:
        for community_group in triplet_handler._community_groups.values():
            if not hasattr(community_group, 'communities'):
                continue
            for community in community_group.communities.values():
                 parent_nodes = list(community.mapped_nodes.get("parent_to_child", {}).keys())
                 if parent_nodes: # Only add non-empty communities
                    communities.append(parent_nodes)
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Warning: Error extracting communities from pipeline object: {e}")
    return communities

def prepare_traversal_arrows(
    traversal_path: List[int],
    parent_nodes: List[Optional[int]],
    graph: ig.Graph
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Determines edges for highlighting traversal paths.

    Generates two lists of edges:
    1. Red Arrows: From parent node to current node in traversal.
    2. Blue Arrows: From previous node to parent node, if they differ.

    Args:
        traversal_path: List of node indices representing the traversal order.
        parent_nodes: List of parent node indices corresponding to traversal_path.
                      The i-th element is the parent of traversal_path[i].
                      Can contain None.
        graph: The igraph.Graph object.

    Returns:
        A tuple containing two lists: (red_arrow_edges, blue_arrow_edges).
    """
    red_arrow_edges = []
    blue_arrow_edges = []
    n_vertices = graph.vcount()

    if len(traversal_path) < 2:
        print("Traversal path has less than 2 nodes. No arrows generated.")
        return [], []

    # Ensure parent_nodes list aligns with traversal_path (skip first element's parent)
    if len(parent_nodes) != len(traversal_path):
         print(f"Warning: Mismatch between traversal path length ({len(traversal_path)}) and parent nodes length ({len(parent_nodes)}). Arrow generation might be incorrect.")
         # Attempt to align if possible, or return empty
         # Assuming parent_nodes[i] corresponds to traversal_path[i]
         # We need parents for traversal_path[1] onwards
         aligned_parents = parent_nodes

    else:
        aligned_parents = parent_nodes # Assume direct correspondence

    for i in range(1, len(traversal_path)):
        current_node = traversal_path[i]
        previous_node = traversal_path[i-1]

        # Need parent for the *current* node, index i in traversal/parent lists
        if i >= len(aligned_parents):
            print(f"Warning: Missing parent information for traversal step {i}. Skipping.")
            continue
        parent_node = aligned_parents[i]


        # --- Boundary and Validity Checks ---
        valid_current = 0 <= current_node < n_vertices
        valid_previous = 0 <= previous_node < n_vertices
        valid_parent = parent_node is None or (0 <= parent_node < n_vertices)

        if not (valid_current and valid_previous and valid_parent):
            print(f"Warning: Node index out of bounds at step {i}. "
                  f"Current: {current_node}({valid_current}), "
                  f"Prev: {previous_node}({valid_previous}), "
                  f"Parent: {parent_node}({valid_parent}). Skipping arrow drawing for this step.")
            continue
        # --- End Boundary Checks ---


        if parent_node is not None:
            # Red arrow: Parent -> Current
            red_arrow_edges.append((parent_node, current_node))

            # Blue arrow: Previous -> Parent (only if different)
            if previous_node != parent_node:
                 # We already validated previous_node and parent_node above
                blue_arrow_edges.append((previous_node, parent_node))

    return red_arrow_edges, blue_arrow_edges

def ensure_node_labels(graph: ig.Graph) -> None:
    """Adds default numeric labels to graph vertices if they don't exist."""
    if "label" not in graph.vs.attributes():
        print("Assigning default numerical labels to vertices.")
        graph.vs["label"] = [str(i) for i in range(graph.vcount())]