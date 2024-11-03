from collections import defaultdict
import os
from igraph import Graph
from leidenalg import ModularityVertexPartition
import networkx

from llm_wrappers.llm_wrappers import OpenAIModel
from llm_wrappers.pydantic_classes import SummarizedDescription
    

class CommunityOutsideConnections:
    def __init__(self, community_id: int):
        self.community_id = community_id
        self.connections = defaultdict(list)

    def add_connection(self, neighbor_community_id: int, connection: tuple[int, int, int]) -> None:
        self.connections[neighbor_community_id].append(connection)


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


def create_community_outside_connections(
    community_id: int, graph: Graph, partition: ModularityVertexPartition
) -> CommunityOutsideConnections:
    outside_connections = CommunityOutsideConnections(community_id)
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


def create_outside_connections(
    graph: Graph, partition: ModularityVertexPartition
) -> dict:
    outside_connections = {}
    for community_id in range(len(partition.subgraphs())):
        outside_connections[community_id] = create_community_outside_connections(
            community_id, graph, partition
        )
    return outside_connections


def localize_node_ids(graph: Graph, subgraph: Graph) -> dict:
    localized_node_ids = {}
    for node in subgraph.vs:
        global_vertex_id = graph.vs.find(node["name"]).index
        localized_node_ids[global_vertex_id] = node.index
    print(localized_node_ids)
    return localized_node_ids


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
) -> tuple[list[int], list[int]]:
    starter_node_id = find_starter_node_in_group(
        community_ids, all_community_ids_ordered
    )
    community_ids_ordered, previous_community_ids = graph.dfs(starter_node_id)
    return community_ids_ordered, previous_community_ids


def find_starter_node_in_group(
    group_node_ids: list[int], ordered_nodes: list[int]
) -> int:
    starter_node_id = None
    for node_id in ordered_nodes:
        if node_id in group_node_ids:
            starter_node_id = node_id
            break
    return starter_node_id

def modified_dfs(graph: Graph, current: int, target_list: list[int], target: int, visited: set, path: list[int]):
    # Mark the current node as visited and add it to the path
    visited.add(current)
    path.append(current)
    
    # Check if the current node matches the next required node in the target list
    if target in target_list and current == target:
        target_list.pop(0)
        target = target_list[0] if len(target_list) > 0 else -1  # Move to the next target node
    
    # Explore neighbors
    print(current)
    for neighbor in graph.neighbors(current, mode="out"):
        neighbor_id = graph.vs[neighbor]["id"]  # Get the actual ID of the neighbor
        if neighbor_id not in visited:
            modified_dfs(graph, neighbor_id, target_list, target, visited, path)
    
    # Backtrack
    visited.remove(current)


def modified_dfs(graph: Graph, start_id: int, end_ids: list[int]):
    """Perform a modified DFS traversal on the graph to ensure it starts and ends with specific nodes."""
    # Helper function to perform DFS
    def dfs(node_id: int, end_ids_curr: list[int], visited: set, path: list[int], best_attempt: list[int]):
        visited.add(node_id)
        path.append(node_id)
        
        # If we've visited all nodes and the last node is the end node, we are done
        if node_id in end_ids_curr:
            end_ids_curr.remove(node_id)

            if len(visited) == graph.vcount():
                return True
            else:
                if len(end_ids_curr) == 0:
                    best_attempt = path 
                    return False
        
        # Explore neighbors
        for neighbor in graph.neighbors(node_id):
            if neighbor not in visited:
                if dfs(neighbor, visited, path, best_attempt):
                    return True
        
        # Backtrack if no valid path found from current node
        visited.remove(node_id)
        path.pop()
        if node_id in end_ids:
            end_ids_curr.append(node_id)
        return False
    
    end_ids_curr = [id for id in end_ids]
    visited = set()
    path = []
    best_attempt = []

    if dfs(start_id, end_ids_curr, visited, path, best_attempt):
        return True, path
    else:
        return False, best_attempt
    
    # Input: Graph, start, mids, end
    # Krcemo od start noda (dodajemo start u visited i u path)
    # Obilazimo neighbor po neighbor u for petlji
    # Ukoliko neko od njih je end ali nismo obisli sve, zabelezi ako je duza od prethodne zabelezene path i return False
        # ako su sve obidjene return True -- ovde cemo prosiriti da return True samo ako zadovoljava uslov da su mdis po pravom rasporedu
