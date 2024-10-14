from collections import defaultdict
import os
from igraph import Graph
from leidenalg import ModularityVertexPartition
import networkx

from llm_wrappers.llm_wrappers import OpenAIModel
from llm_wrappers.pydantic_classes import SummarizedDescription


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


def create_outside_connections_community(
    community_id: int, graph: Graph, partition: ModularityVertexPartition
) -> dict:
    outside_connections = {}
    for idx, crossing in enumerate(partition.crossing()):
        if crossing:
            node1, node2 = graph.es[idx].tuple
            if (
                partition.membership[node1] == community_id
                or partition.membership[node2] == community_id
            ):
                community_node = (
                    node1 if partition.membership[node1] == community_id else node2
                )
                neighbor_node = node1 if community_node == node2 else node2
                neighbour_community_id = partition.membership[neighbor_node]
                if neighbour_community_id not in outside_connections:
                    outside_connections[neighbour_community_id] = defaultdict(list)
                outside_connections[neighbour_community_id][community_node].append(idx)
    return {
        comm_id: {node_id: list(edges) for node_id, edges in vertices.items()}
        for comm_id, vertices in outside_connections.items()
    }


def create_outside_connections(
    graph: Graph, partition: ModularityVertexPartition
) -> dict:
    outside_connections = {}
    for community_id in range(len(partition.subgraphs())):
        outside_connections[community_id] = create_outside_connections_community(
            community_id, graph, partition
        )
    return outside_connections


def localize_connections(graph: Graph, subgraph: Graph, connections: dict) -> dict:
    localized_connections = {}
    for neighbor_community_id, vertices in connections.items():
        if neighbor_community_id not in localized_connections:
            localized_connections[neighbor_community_id] = []
        for vertex_id in vertices.keys():
            vertex_name = graph.vs[vertex_id]["name"]
            local_vertex_id = subgraph.vs.find(vertex_name).index
            localized_connections[neighbor_community_id].append(local_vertex_id)
    return localized_connections


def order_list(length: int, order="from_ends") -> list[int]:
    if order == "from_ends":
        group_order = []
        # Iterate through the list in the specified manner
        for i in range(length // 2):
            group_order.append(i)  # First element, second element, etc.
            group_order.append(
                length - 1 - i
            )  # Last element, second last element, etc.
        # If the list has an odd number of elements, print the middle element
        if length % 2 != 0:
            group_order.append(length // 2)
        return group_order
    else:
        raise NotImplementedError()


def order_nodes_by_centralization(graph: Graph) -> list[int]:
    graph_networkx = networkx.Graph()
    graph_networkx.add_edges_from(graph.get_edgelist())
    for vertex in graph.vs:
        graph_networkx.nodes[vertex.index].update(vertex.attributes())
    katz_centrality = networkx.katz_centrality(graph_networkx, alpha=0.1, beta=1.0)
    least_centralized_order = sorted(
        katz_centrality, key=katz_centrality.get, reverse=False
    )
    return least_centralized_order


def order_each_group_for_traversal(
    community_ids: list[int], all_community_ids_ordered: list[int], graph: Graph
) -> list[int]:
    starter_node_id = find_starter_node_in_group(
        community_ids, all_community_ids_ordered
    )
    community_ids_ordered = graph.dfs(starter_node_id)
    return community_ids_ordered


def find_starter_node_in_group(
    group_node_ids: list[int], ordered_nodes: list[int]
) -> int:
    starter_node_id = None
    for node_id in ordered_nodes:
        if node_id in group_node_ids:
            starter_node_id = node_id
            break
    return starter_node_id
