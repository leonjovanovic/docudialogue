import os
from igraph import Graph
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

def create_outside_connections(subgraph: Graph, partition: ModularityVertexPartition) -> dict:
    node_to_community_edges = {}

    for vertex in subgraph.vs:
        node = vertex.index
        community = partition.membership[node]
        node_to_community_edges[node] = []

        for neighbor in subgraph.neighbors(node):
            neighbor_community = partition.membership[neighbor]
            if community != neighbor_community:
                edge_id = subgraph.get_eid(node, neighbor)
                node_to_community_edges[node].append({
                    'edge': edge_id,
                    'to_community': neighbor_community,
                    'to_node': neighbor
                })

    # Example usage
    for node, edges in node_to_community_edges.items():
        if edges:
            print(f"Node {subgraph.vs[node]['name']} can leave community {partition.membership[node]} via edges: {edges}")
        else:
            print(f"Node {subgraph.vs[node]['name']} stays within its community {partition.membership[node]}")

    return {}