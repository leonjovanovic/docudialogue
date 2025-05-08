from igraph import Graph

from dialog_generator.graphs.graph_utils import (
    CommunityNeighbourConnections,
    GlobalBorderNodes,
    LocalBorderNodes,
    map_nodes_between_graphs,
    modified_dfs,
    summarize_descriptions,
)
from dialog_generator.llm_wrappers.prompts import SUMMARIZE_GRAPH_PROMPT


class Community:
    """
    Class representing a community in the graph.
    It contains methods for traversing the community and summarizing its contents.
    """

    def __init__(
        self,
        id: int,
        parent_graph: Graph,
        graph: Graph,
        neighbour_connections: CommunityNeighbourConnections,
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.graph = graph
        self.neighbour_connections = neighbour_connections
        self.mapped_nodes = map_nodes_between_graphs(parent_graph, graph)
        self.traversal_order = None # To be set in traverse method
        self.traversal_order_parents = None # To be set in traverse method
        # self.summary = self.summarize_community()

    def _split_borders_into_mid_and_last(
        self, borders_exit_nodes: list[LocalBorderNodes]
    ) -> tuple[list[LocalBorderNodes], LocalBorderNodes]:
        """
        Splits the borders into middle exits and last exit.
        Mid borders are all but the last border.
        """

        mid_borders, last_border = [], None
        if len(borders_exit_nodes) > 0:
            last_border = borders_exit_nodes[-1]
            if len(borders_exit_nodes) > 1:
                mid_borders = borders_exit_nodes[:-1]
        return mid_borders, last_border

    def _init_entry_node_ids(
        self,
        entry_node_ids: GlobalBorderNodes | None,
        mid_borders: list[LocalBorderNodes],
        last_border: LocalBorderNodes,
    ) -> LocalBorderNodes:
        """
        If entry_node_ids are provided, localize them.
        Otherwise, use all nodes in the graph as entry points, but remove nodes
        that are in the end border and mid borders from entry_node_ids.
        """
        if entry_node_ids:
            entry_node_ids_local = entry_node_ids.localize(self.mapped_nodes["parent_to_child"])
        else:
            all_graph_node_ids: list[int] = self.graph.vs.indices

            all_border_node_ids = set()
            for border in mid_borders:
                all_border_node_ids.update(border.node_ids)
            all_border_node_ids.update(last_border.node_ids)

            for node_id in all_border_node_ids:
                if node_id in all_graph_node_ids:
                    all_graph_node_ids.remove(node_id)

            if not all_graph_node_ids:
                all_graph_node_ids = last_border.node_ids
            entry_node_ids_local = LocalBorderNodes(all_graph_node_ids)

        return entry_node_ids_local
    
    def format_chosen_borders(self, mid_borders_chosen_ids: list[int], best_attempt: list[int]) -> list[int]:
        border_node_ids_global = []
        if mid_borders_chosen_ids:
            for node_id in mid_borders_chosen_ids:
                border_node_ids_global.append(
                    self.mapped_nodes["child_to_parent"][node_id]
                )
        if best_attempt:
            border_node_ids_global.append(
                self.mapped_nodes["child_to_parent"][best_attempt[-1]]
            )
        return border_node_ids_global

    def _traverse(
        self,
        entry_node_ids_local: LocalBorderNodes,
        mid_borders: list[LocalBorderNodes],
        last_border: LocalBorderNodes,
    ) -> tuple[list[int], list[int]]:
        """
        Traverse the community graph using a modified DFS algorithm.
        It finds the best path through the community graph and returns it.
        It also returns the chosen mid borders.
        """
        best_attempt = []
        path = []
        mid_borders_chosen_ids = []
        for start_id in entry_node_ids_local.node_ids:
            found_path, path, mid_borders_chosen_ids = modified_dfs(
                self.graph, start_id, mid_borders, last_border
            )
            if not found_path:
                raise NotImplementedError("TODO")
            else:
                best_attempt = path
                break
        print(best_attempt)
        global_exit_ids = self.format_chosen_borders(mid_borders_chosen_ids, best_attempt)
        return best_attempt, global_exit_ids

    def find_best_traversal_through_community(
        self,
        entry_node_ids: GlobalBorderNodes | None,
        ordered_borders_exit_nodes: list[GlobalBorderNodes],
    ) -> list[int]:
        """
        Given allowed entry points and in which order should he reach border nodes,
        traverse the community graph to find the best path through it.
        Each border is a list of node ids, where any node from the border can be used to exit the community.
        This method uses a modified depth-first search (DFS) algorithm to find the path.
        It also creates a traversal path and stores the traversal order and parents.
        """
        ordered_borders_exit_nodes_local = [
            border_exit_nodes.localize(self.mapped_nodes["parent_to_child"])
            for border_exit_nodes in ordered_borders_exit_nodes
        ]

        mid_borders, last_border = self._split_borders_into_mid_and_last(
            ordered_borders_exit_nodes_local
        )
        entry_node_ids_local = self._init_entry_node_ids(
            entry_node_ids, mid_borders, last_border
        )

        best_attempt, global_exit_ids = self._traverse(entry_node_ids_local, mid_borders, last_border)

        self.create_traversal_path(best_attempt, global_exit_ids)
        return global_exit_ids

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
            self.mapped_nodes["child_to_parent"][node_id]
            for node_id in self.traversal_order_loc
        ]
        self.traversal_order_parents = [
            self.mapped_nodes["child_to_parent"][node_id] if node_id != -1 else -1
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
