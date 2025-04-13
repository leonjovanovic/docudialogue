from collections import defaultdict
from igraph import Graph

from graphs.community import Community
from graphs.graph_utils import order_each_group_for_traversal, GlobalBorderNodes


class CommunityGroup:
    def __init__(
        self, id: int, parent_graph: Graph, communities: dict[int, Community], community_ids_ordered: list[int], outside_connections:  dict[int, dict[int: list[int]]]
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.communities = communities
        self.outside_connections = outside_connections
        self.traversal_order, self.traversal_order_parents = order_each_group_for_traversal(list(self.communities.keys()), community_ids_ordered, self.parent_graph)
        self.global_traversal = None
        self.ordered_exits = dict()
        self._traverse_through_communities()

    def _traverse_through_communities(self) -> None:
        # TODO
        # Ovde cemo ici jednu po jednu community i raditi traversal sa pocetkom i krajnjom tackom.
        # print(f"CommunityGroup: {self.id}")
        entrances = dict()
        first_node_ids = []
        print(self.traversal_order)
        print(self.traversal_order_parents)
        for community_id, prev_community_id in zip(self.traversal_order, self.traversal_order_parents):
            print(community_id, prev_community_id)
            community = self.communities[community_id]
            outside_connections = community.outside_connections.connections
            # print("=======")
            # print(f"Current community {community_id}")

            key = f"{prev_community_id}=>{community_id}"
            first_node_ids = entrances[key] if key in entrances else []
            # print(f"First nodes are {first_node_ids}")

            # print(f"Outside conns: {community.outside_connections.connections}")
            ordered_border_node_ids, ordered_next_communities = [], []
            for child_community_id, parent_communitity_id in zip(self.traversal_order, self.traversal_order_parents):
                if parent_communitity_id == community_id:
                    connections_towards_community = outside_connections[child_community_id]
                    ordered_border_node_ids.append([conn[0] for conn in connections_towards_community])
                    ordered_next_communities.append(child_community_id)
            if not ordered_border_node_ids:
                ordered_border_node_ids.append(first_node_ids)
            # print(f"ordered_border_node_ids: {ordered_border_node_ids}")
            # print("ENTERINGGGG")
            # TODO HEREEEE
            first_node_ids = GlobalBorderNodes(first_node_ids) if first_node_ids else None
            ordered_border_node_ids = [GlobalBorderNodes(node_ids) for node_ids in ordered_border_node_ids]
            decided_border_node_ids = community.traverse(first_node_ids, ordered_border_node_ids)
            # print(f"decided_border_node_ids: {decided_border_node_ids}")

            # Find all entraces based on each node in 'decided_border_node_ids'
            i = 0
            for child_community_id, parent_communitity_id in zip(self.traversal_order, self.traversal_order_parents):
                if parent_communitity_id == community_id:
                    connections_towards_community = outside_connections[child_community_id]
                    node_id = decided_border_node_ids[i]
                    i += 1
                    comm_entraces = []
                    for conn in connections_towards_community:
                        if conn[0] == node_id:
                            comm_entraces.append(conn[2])
                    entrances[f"{community_id}=>{child_community_id}"] = comm_entraces

            # Assign exit node so we know which exit id (1st, 2nd, 3rd etc. we cant use node id
            #  as same value can be used multiple time) leads to which community
            self.ordered_exits[community_id] = []
            for exit, next_community_id in zip(community.exits, ordered_next_communities):
                self.ordered_exits[community_id].append((exit, next_community_id))
    
    def _visit_community(self, community_id: int, first_parent: int = -1):
        print(f"Visiting community {community_id}")
        community = self.communities[community_id]
        nodes = community.traversal_order
        parents = community.traversal_order_parents
        parents[0] = first_parent
        community_exits = self.ordered_exits[community_id]
        curr_exit = 0

        for idx, node_id in enumerate(nodes):
            # Visit node
            self.global_traversal.append(node_id)
            self.global_traversal_parents.append(parents[idx])
            if curr_exit < len(community_exits):
                exit_node_id = community_exits[curr_exit][0]
                next_community_id = community_exits[curr_exit][1]
                if idx == exit_node_id:
                    # Detour into new community
                    self._visit_community(next_community_id, nodes[exit_node_id])
                    curr_exit += 1

    def visit_communities(self):
        self.global_traversal = []
        self.global_traversal_parents = []
        first_community_id = self.traversal_order[0]
        self._visit_community(first_community_id)