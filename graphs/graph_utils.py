from __future__ import annotations
from collections import defaultdict
from enum import Enum
import os
from igraph import Graph
from leidenalg import ModularityVertexPartition
import networkx

from llm_wrappers.llm_wrappers import OpenAIModel
from llm_wrappers.pydantic_classes import SummarizedDescription


class CommunityNeighbourConnections:
    def __init__(self, community_id: int):
        self.community_id = community_id
        self.connections = defaultdict(list)

    def add_connection(
        self, neighbor_community_id: int, connection: tuple[int, int, int]
    ) -> None:
        self.connections[neighbor_community_id].append(connection)


class BorderNodes:
    """
    Class representing possible exits for one border in the graph.
    Border represents a connection between two communities.
    """

    def __init__(self, node_ids: list[int]) -> None:
        self.node_ids = node_ids


class GlobalBorderNodes(BorderNodes):

    def localize(self, mapping: dict) -> LocalBorderNodes:
        return LocalBorderNodes([mapping[node_id] for node_id in self.node_ids])


class LocalBorderNodes(BorderNodes):

    def globalize(self, mapping: dict) -> GlobalBorderNodes:
        return GlobalBorderNodes([mapping[node_id] for node_id in self.node_ids])


class OrderType(Enum):
    """Enum for ordering types."""

    FROM_ENDS = "FRONT_ENDS"


def summarize_descriptions(descriptions: list[str] | dict, prompt: str) -> str:
    if isinstance(descriptions, list) and len(descriptions) == 1:
        return descriptions[0]
    else:
        model = OpenAIModel(os.environ["LLM_API_KEY"])
        return model.parse(
            system_prompt="",
            user_prompt=prompt.format(descriptions=descriptions),
            response_format=SummarizedDescription,
            model_name="gpt-4o-mini",
            temperature=0,
        ).description


def _find_neighbour_connections(
    community_id: int, graph: Graph, partition: ModularityVertexPartition
) -> CommunityNeighbourConnections:
    """Finds all connections between communities in the graph."""
    outside_connections = CommunityNeighbourConnections(community_id)
    for edge_id, crossing_exists in enumerate(partition.crossing()):
        if crossing_exists:
            node1, node2 = graph.es[edge_id].tuple
            node1_in_curr_community = partition.membership[node1] == community_id
            node2_in_curr_community = partition.membership[node2] == community_id

            if node1_in_curr_community or node2_in_curr_community:
                if node1_in_curr_community:
                    curr_community_node = node1
                    neighbor_community_node = node2
                else:
                    curr_community_node = node2
                    neighbor_community_node = node1

                neighbour_community_id = partition.membership[neighbor_community_node]

                connection = (curr_community_node, edge_id, neighbor_community_node)
                outside_connections.add_connection(neighbour_community_id, connection)
    return outside_connections


def find_neighbour_connections(
    graph: Graph, partition: ModularityVertexPartition
) -> dict[str, CommunityNeighbourConnections]:
    """
    Finds all connections between communities in the graph.
    Returns a dictionary where keys are community IDs and values
    are lists of connections.
    """
    outside_connections = {}
    for community_id in range(len(partition.subgraphs())):
        outside_connections[community_id] = _find_neighbour_connections(
            community_id, graph, partition
        )
    return outside_connections


def map_nodes_between_graphs(
    parent_graph: Graph, child_graph: Graph
) -> dict[str, dict[str, str]]:
    """
    Maps nodes, both ways, between the parent graph and child graph (subgraph).
    This is useful for traversing between 2 subgraphs and finding the connections between them via parent graph.
    """
    mapping = {
        "parent_to_child": _map_parent_to_child_graph_nodes(parent_graph, child_graph),
        "child_to_parent": _map_child_to_parent_graph_nodes(parent_graph, child_graph),
    }
    return mapping


def _map_parent_to_child_graph_nodes(
    parent_graph: Graph, child_graph: Graph
) -> dict[str, str]:
    mapping = {}
    for child_node in child_graph.vs:
        node_id_in_parent = parent_graph.vs.find(child_node["name"]).index
        mapping[node_id_in_parent] = child_node.index
    return mapping


def _map_child_to_parent_graph_nodes(
    parent_graph: Graph, child_graph: Graph
) -> dict[str, str]:
    mapping = {}
    for node in child_graph.vs:
        node_id_in_parent = parent_graph.vs.find(node["name"]).index
        mapping[node.index] = node_id_in_parent
    return mapping


def order_list(length: int, order: OrderType) -> list[int]:
    if order == OrderType.FROM_ENDS:
        # Iterate through the list in the specified manner:
        # First element, last element, second element, second to last element, etc.
        group_order = []
        for i in range(length // 2):
            group_order.append(i)
            group_order.append(length - 1 - i)
        # If the length is odd, add the middle element at the end
        if length % 2 != 0:
            group_order.append(length // 2)
        return group_order
    else:
        raise NotImplementedError()


def order_nodes_by_centralization(graph: Graph) -> list[int]:
    """
    Order nodes by their Katz centrality in the graph.
    The nodes with the most centrality are ordered first.
    """
    graph_networkx = networkx.Graph()
    graph_networkx.add_edges_from(graph.get_edgelist())
    for vertex in graph.vs:
        graph_networkx.nodes[vertex.index].update(vertex.attributes())
    katz_centrality = networkx.katz_centrality(graph_networkx, alpha=0.1, beta=1.0)
    least_centralized_order = sorted(
        katz_centrality, key=katz_centrality.get, reverse=False
    )
    return least_centralized_order


def order_group_nodes_for_traversal(
    group_node_ids: list[int], graph_node_ids_ordered: list[int], graph: Graph
) -> tuple[list[int], list[int]]:
    """
    Order nodes in the group for traversal:
    1. Find the first node in the ordered list that is also in the group node IDs.
    2. Perform a DFS traversal starting from that node.
    3. Return the ordered community IDs and the previous community IDs.
    """
    starter_node_id = _find_starter_node_in_group(
        group_node_ids, graph_node_ids_ordered
    )
    community_ids_ordered, previous_community_ids = graph.dfs(starter_node_id)
    return community_ids_ordered, previous_community_ids


def _find_starter_node_in_group(
    group_node_ids: list[int], ordered_nodes: list[int]
) -> int:
    starter_node_id = None
    for node_id in ordered_nodes:
        if node_id in group_node_ids:
            starter_node_id = node_id
            break
    return starter_node_id


def modified_dfs(
    graph: Graph,
    entry_node_id: int,
    mid_borders: list[LocalBorderNodes],
    last_border: LocalBorderNodes,
):
    """
    Perform a modified DFS traversal on the graph to ensure
    it starts and ends with specific nodes.
    """

    # Helper function to perform DFS
    def dfs(
        node_id: int,
        mid_ids: list[list[int]],
        end_ids: list[int],
        visited: set,
        path: list[int],
        mid_order: list[int],
        go_back_idx: int = None,
    ):
        # if go_back_idx != None:
        #     print(f"(Backtracking {go_back_idx}) Node {node_id} Next potential: {graph.neighbors(node_id)}, Curr state: Path: {path}, Mids: {mid_ids}, Ends: {end_ids}")
        # else:
        #     print(f"Node {node_id} Next potential: {graph.neighbors(node_id)}, Curr state: Path: {path}, Mids: {mid_ids}, Ends: {end_ids}")

        visited.add(node_id)
        path.append(node_id)
        cur_mids = []
        if len(mid_order) < len(mid_ids):
            cur_mids = mid_ids[len(mid_order)]
            if node_id in cur_mids:
                mid_order.append((node_id, len(path)))
                cur_mids = (
                    mid_ids[len(mid_order)] if len(mid_order) < len(mid_ids) else []
                )
        else:
            # If we've visited all nodes and the last node is the end node, we are done
            if node_id in end_ids or not end_ids:
                # print(f"END CHECKING {visited}, {len(visited)}=={graph.vcount()}")
                if len(visited) == graph.vcount():
                    return True

        # Explore neighbors to find new mid nodes
        for neighbor in graph.neighbors(node_id):
            if (
                neighbor not in visited
                and neighbor not in end_ids
                and neighbor in cur_mids
            ):
                if dfs(neighbor, mid_ids, end_ids, visited, path, mid_order):
                    return True

        # Explore neighbors to find new non ending nodes
        for neighbor in graph.neighbors(node_id):
            if (
                neighbor not in visited
                and neighbor not in end_ids
                and neighbor not in cur_mids
            ):
                if dfs(neighbor, mid_ids, end_ids, visited, path, mid_order):
                    return True

        # Explore neighbors to find new ending nodes
        for neighbor in graph.neighbors(node_id):
            if neighbor not in visited and neighbor in end_ids:
                if dfs(neighbor, mid_ids, end_ids, visited, path, mid_order):
                    return True

        # Explore neighbors to backtrack
        for neighbor in graph.neighbors(node_id):
            if go_back_idx != None:
                # We have already gone back and we need to follow certain path
                # If we backtracked to start, we cant go further.
                if go_back_idx > 0:
                    if neighbor == path[go_back_idx - 1]:
                        # WRAP IN FUNCTION Get first appearence of that node
                        for idx, _ in enumerate(path):
                            if path[idx] == neighbor:
                                go_back_idx = idx
                                break
                        if dfs(
                            neighbor,
                            mid_ids,
                            end_ids,
                            visited,
                            path,
                            mid_order,
                            go_back_idx,
                        ):
                            return True
            else:
                # This is first time to potentially backtrack
                if len(path) > 1:
                    if neighbor == path[-2]:
                        # WRAP IN FUNCTION Get first appearence of that node
                        for idx, _ in enumerate(path):
                            if path[idx] == neighbor:
                                go_back_idx = idx
                                break
                        if dfs(
                            neighbor,
                            mid_ids,
                            end_ids,
                            visited,
                            path,
                            mid_order,
                            go_back_idx,
                        ):
                            return True

        # Backtrack if no valid path found from current node
        # print(f"Failed, backtracking path: {path}, visited: {visited}, {node_id}")
        if mid_order and mid_order[-1][1] == len(path):
            mid_order.pop()
        path.pop()
        if node_id not in path:
            visited.remove(node_id)
        return False

    visited = set()
    path = []
    mid_order = []
    mid_node_ids = [border.node_ids for border in mid_borders]
    print(
        f"Starting DFS from node {entry_node_id} with mid nodes {mid_node_ids} and end nodes {last_border.node_ids}"
    )
    found_path = dfs(
        node_id=entry_node_id,
        mid_ids=mid_node_ids,
        end_ids=last_border.node_ids,
        visited=visited,
        path=path,
        mid_order=mid_order,
    )

    mid_exits = [m[0] for m in mid_order]
    return found_path, path, mid_exits
