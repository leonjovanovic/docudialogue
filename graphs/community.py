from collections import defaultdict
from igraph import Graph, Vertex, Edge

from graphs.graph_utils import (
    CommunityOutsideConnections,
    globalize_node_ids,
    localize_node_ids,
    modified_dfs,
    summarize_descriptions,
)
from llm_wrappers.prompts import SUMMARIZE_GRAPH_PROMPT


class Community:
    def __init__(
        self,
        id: int,
        parent_graph: Graph,
        graph: Graph,
        outside_connections: CommunityOutsideConnections,
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.graph = graph
        self.outside_connections = outside_connections
        self.localized_node_ids = localize_node_ids(parent_graph, graph)
        self.globalized_node_ids = globalize_node_ids(parent_graph, graph)
        self.traversal_order = None
        self.traversal_order_parents = None
        # self.summary = self.summarize_community()

    def traverse(
        self, first_node_ids: list[int], ordered_border_node_ids: list[list[int]]
    ) -> None:
        ordered_border_node_ids_local = []
        for community_exits in ordered_border_node_ids:
            community_exits_local = [
                self.localized_node_ids[node_id] for node_id in community_exits
            ]
            ordered_border_node_ids_local.append(community_exits_local)

        mid_ids, end_ids = [], []
        if len(ordered_border_node_ids_local) > 0:
            end_ids = ordered_border_node_ids_local[-1]
            if len(ordered_border_node_ids_local) > 1:
                mid_ids = ordered_border_node_ids_local[:-1]

        best_attempt = []
        path = []
        mid_exits = []

        if first_node_ids:
            first_node_ids_local = [
                self.localized_node_ids[id] for id in first_node_ids
            ]
        else:
            first_node_ids_local = self.graph.vs.indices
            for id in end_ids:
                first_node_ids_local.remove(id)
            for ids in mid_ids[1:]:
                for id in ids:
                    first_node_ids_local.remove(id)

        # print(f"all graph indices: {self.graph.vs.indices}")
        # print(f"first nodes local: {first_node_ids_local}")
        for start_id in first_node_ids_local:
            # print(f"=> Starting: {start_id}, mid: {mid_ids}, end: {end_ids}")
            found_path, path, mid_exits = modified_dfs(
                self.graph, start_id, mid_ids, end_ids
            )
            # print(f"=> Izlaz: {found_path}, {path}, {mid_exits}")
            if not found_path:
                raise NotImplementedError("TODO")
            else:
                best_attempt = path
                break


        decided_border_node_ids = []
        for mid_exit in mid_exits:
            decided_border_node_ids.append(self.globalized_node_ids[mid_exit])
        decided_border_node_ids.append(self.globalized_node_ids[best_attempt[-1]])
        # print(decided_border_node_ids)
        self.create_traversal_path(best_attempt, decided_border_node_ids)
        return decided_border_node_ids

    def create_traversal_path(self, path: list[int], border_node_ids: list[int]):
        self.traversal_order_loc = []
        self.traversal_order_parents_loc = []
        visited = set()
        for idx, node_id in enumerate(path):
            if idx == 0:
                visited.add(node_id)
                self.traversal_order_parents_loc.append(-1)
                self.traversal_order_loc.append(node_id)
            elif idx == len(path) - 1 and idx != 0:
                parent_id = path[idx - 1]
                self.traversal_order_parents_loc.append(parent_id)
                self.traversal_order_loc.append(node_id)
            elif node_id not in visited:
                visited.add(node_id)
                self.traversal_order_loc.append(node_id)
                if idx == 0:
                    self.traversal_order_parents_loc.append(-1)
                else:
                    parent_id = path[idx - 1]
                    self.traversal_order_parents_loc.append(parent_id)

        self.traversal_order = [
            self.globalized_node_ids[node_id] for node_id in self.traversal_order_loc
        ]
        self.traversal_order_parents = [
            self.globalized_node_ids[node_id] if node_id != -1 else -1
            for node_id in self.traversal_order_parents_loc
        ]
        curr_exit_id = 0
        mid_exits = border_node_ids[:-1]
        self.exits = []
        if mid_exits:
            for idx, node_id in enumerate(self.traversal_order):
                if node_id == mid_exits[curr_exit_id]:
                    self.exits.append(idx)
                    curr_exit_id += 1
                    if curr_exit_id == len(mid_exits):
                        break
        self.exits.append(len(self.traversal_order) - 1)
            

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
