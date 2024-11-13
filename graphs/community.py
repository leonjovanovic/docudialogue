from collections import defaultdict
from igraph import Graph, Vertex, Edge

from graphs.graph_utils import CommunityOutsideConnections, localize_node_ids, modified_dfs, summarize_descriptions
from llm_wrappers.prompts import SUMMARIZE_GRAPH_PROMPT


class Community:
    def __init__(
        self, id: int, parent_graph: Graph, graph: Graph, outside_connections: CommunityOutsideConnections
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.graph = graph
        self.outside_connections = outside_connections
        self.localized_node_ids = localize_node_ids(parent_graph, graph)
        self.traversal_order = None
        self.traversal_order_parents = None
        # self.summary = self.summarize_community()

    def traverse(self, first_node_ids: list[int], ordered_border_node_ids: list[list[int]]) -> None:
        # Lokalizuj sve nodove
        ordered_border_node_ids_local = []
        for community_exits in ordered_border_node_ids:
            community_exits_local = [self.localized_node_ids[node_id] for node_id in community_exits]
            ordered_border_node_ids_local.append(community_exits_local)

        mid_ids, end_ids = [], []
        if len(ordered_border_node_ids_local) > 0:
            end_ids = ordered_border_node_ids_local[-1]
            if len(ordered_border_node_ids_local) > 1:
                mid_ids = ordered_border_node_ids_local[:-1]

        best_attempt = []
        path = []

        if first_node_ids:
            first_node_ids_local = [self.localized_node_ids[id] for id in first_node_ids]
        else:
            first_node_ids_local = self.graph.vs.indices
            for id in end_ids:
                first_node_ids_local.remove(id)
            for ids in mid_ids[1:]:
                for id in ids:
                    first_node_ids_local.remove(id)
            
        print(self.graph.vs.indices)
        for start_id in first_node_ids_local:
            print(start_id, mid_ids, end_ids)
            found_path, path = modified_dfs(self.graph, start_id, mid_ids, end_ids)
            print(f"Izlaz: {found_path}, {path}")
            if not found_path:
                if len(path) > len(best_attempt):
                    best_attempt = path
            else:
                break

    def summarize_community(self):
        vertex_descriptions = [
            desc for vertex in self.graph.vs for desc in vertex["desc"]
        ]
        edge_descriptions = [desc for edge in self.graph.es for desc in edge["desc"]]
        descriptions = {
            "vertex_descriptions": vertex_descriptions,
            "edge_descriptions": edge_descriptions,
        }
        return summarize_descriptions(descriptions, SUMMARIZE_GRAPH_PROMPT)
