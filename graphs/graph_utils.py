from collections import defaultdict
import os
from igraph import Graph
import igraph
from leidenalg import ModularityVertexPartition

from llm_wrappers.llm_wrappers import OpenAIModel
from llm_wrappers.pydantic_classes import SummarizedDescription


def summarize_descriptions(descriptions: list[str] | dict, prompt: str) -> str:
    if isinstance(descriptions, list) and len(descriptions) == 1:
        return descriptions[0]
    else:
        model = OpenAIModel(os.environ["LLM_API_KEY"])
        return model.parse(
            system_prompt="",
            user_prompt=prompt.format(
                descriptions=descriptions
            ),
            response_format=SummarizedDescription,
            model_name="gpt-4o-mini",
            temperature=0,
        ).description

def create_outside_connections_community(community_id: int, graph: Graph, partition: ModularityVertexPartition) -> dict:
    outside_connections = {}
    for idx, crossing in enumerate(partition.crossing()):
        if crossing:
            node1, node2 = graph.es[idx].tuple
            if partition.membership[node1] == community_id or partition.membership[node2] == community_id:
                community_node = node1 if partition.membership[node1] == community_id else node2
                neighbor_node = node1 if community_node == node2 else node2
                neighbour_community_id = partition.membership[neighbor_node]
                if neighbour_community_id not in outside_connections:
                    outside_connections[neighbour_community_id] = defaultdict(list)
                outside_connections[neighbour_community_id][community_node].append(idx)
    return {comm_id: {node_id: list(edges) for node_id, edges in vertices.items()} for comm_id, vertices in outside_connections.items()}


def create_outside_connections(graph: Graph, partition: ModularityVertexPartition) -> dict:
    outside_connections = {}
    for community_id in range(len(partition.subgraphs())):
        outside_connections[community_id] = create_outside_connections_community(community_id, graph, partition)
    return outside_connections

def localize_connections(graph: Graph, subgraph: Graph, connections: dict) -> dict:
    localized_connections = {}
    for neighbor_community_id, vertices in connections.items():
        if neighbor_community_id not in localized_connections:
            localized_connections[neighbor_community_id] = []
        for vertex_id in vertices.keys():
            vertex_name = graph.vs[vertex_id]['name']
            local_vertex_id = subgraph.vs.find(vertex_name).index
            localized_connections[neighbor_community_id].append(local_vertex_id)
    return localized_connections