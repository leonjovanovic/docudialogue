from collections import defaultdict
from igraph import Graph

from dialog_generator.graphs.community import Community
from dialog_generator.graphs.graph_utils import (
    CommunityNeighbourConnections,
    order_group_nodes_for_traversal,
    GlobalBorderNodes,
)


class CommunityGroup:
    def __init__(
        self,
        id: int,
        parent_graph: Graph,
        communities: dict[int, Community],
        community_ids_ordered: list[int],
        neighbour_connections: dict[str, CommunityNeighbourConnections],
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.communities = communities
        self.neighbour_connections = neighbour_connections
        self.traversal_order, self.traversal_order_prev = (
            order_group_nodes_for_traversal(
                group_node_ids=list(self.communities.keys()),
                graph_node_ids_ordered=community_ids_ordered,
                graph=self.parent_graph,
            )
        )
        self.global_traversal, self.global_traversal_parents = [], []
        self.ordered_exits = defaultdict(list)
        self._find_best_traversal_through_group()

    def _find_community_border_info(
        self,
        community_id: int,
        neighbour_connections: dict[int, tuple[int, int, int]],
        first_node_ids: GlobalBorderNodes | None,
    ) -> tuple[list[GlobalBorderNodes], list[int]]:
        """
        Find all border nodes towards the current community
        and order them based on the traversal order of the community
        (i.e. the order in which they are visited)
        """
        ordered_border_node_ids = []
        for curr_community_id, prev_community_id in zip(
            self.traversal_order, self.traversal_order_prev
        ):
            # If the previous community is the current one, it means current community has neighbours to whom we are going next.
            if prev_community_id == community_id:
                connections_towards_community = neighbour_connections[curr_community_id]
                # We store the border nodes from the current community towards the next community
                border_nodes = [conn[0] for conn in connections_towards_community]
                ordered_border_node_ids.append(GlobalBorderNodes(border_nodes))

        # If there are no border nodes, add the entrance node as exit node
        # If there is no entrance node, it means we are in the last community and we dont have any exit node
        if not ordered_border_node_ids:
            if first_node_ids:
                ordered_border_node_ids.append(first_node_ids)
            else:
                ordered_border_node_ids.append(GlobalBorderNodes([]))
        return ordered_border_node_ids

    def _add_new_entrances(
        self,
        entrances: dict[str, int],
        community_id: int,
        neighbour_connections: dict[int, tuple[int, int, int]],
        decided_border_node_ids: list[int],
    ) -> None:
        """
        Add new entrances to the community based on the decided border node ids.
        The entrances are stored in the entrances dictionary with the key as the community id and the value as the list of entrances.
        """
        # Find all entraces based on each node in 'decided_border_node_ids'
        i = 0
        for curr_community_id, prev_community_id in zip(
            self.traversal_order, self.traversal_order_prev
        ):
            if prev_community_id == community_id:
                connections_towards_community = neighbour_connections[curr_community_id]
                node_id = decided_border_node_ids[i]
                comm_entraces = []
                for conn in connections_towards_community:
                    if conn[0] == node_id:
                        comm_entraces.append(conn[2])
                entrances[f"{community_id}=>{curr_community_id}"] = comm_entraces
                i += 1

    def _assing_community_exits(self, community: Community) -> None:
        """
        Assign exits to the community based on the traversal order of the community.
        The exits are stored in the ordered_exits dictionary with the key as the community id
        and the value as the list of exit node id and id of community we are going to.
        """
        ordered_next_communities = []
        for curr_community_id, prev_community_id in zip(
            self.traversal_order, self.traversal_order_prev
        ):
            if prev_community_id == community.id:
                ordered_next_communities.append(curr_community_id)

        for exit_node_id, next_community_id in zip(
            community.exits, ordered_next_communities
        ):
            self.ordered_exits[community.id].append((exit_node_id, next_community_id))

    def _find_best_traversal_through_group(self) -> None:
        """
        Traverse through all communities in the group:
        1. Find all entrances to the current community based on previously maintained entrances.
        2. Find all border nodes from the current community to the next communities.
        3. Traverse through the community and save the path.
        4. Add new entrances to the community based on the decided border node ids (exits).
        5. Assign exits to the community based on the traversal order of the community.
        """
        entrances = dict()
        first_node_ids = []
        for community_id, prev_community_id in zip(
            self.traversal_order, self.traversal_order_prev
        ):
            community = self.communities[community_id]
            neighbour_connections = community.neighbour_connections.connections

            key = f"{prev_community_id}=>{community_id}"
            first_node_ids = (
                GlobalBorderNodes(entrances[key]) if key in entrances else None
            )

            ordered_border_node_ids = self._find_community_border_info(
                community_id, neighbour_connections, first_node_ids
            )

            # Traverse through community (it will save path) and get the chosen border node ids
            # (i.e. the border nodes that are actually used to traverse to the next community)
            decided_border_node_ids = community.find_best_traversal_through_community(
                first_node_ids, ordered_border_node_ids
            )

            self._add_new_entrances(
                entrances, community_id, neighbour_connections, decided_border_node_ids
            )

            self._assing_community_exits(community)

    def traverse_through_group(self):
        """
        Based on previously created group traversal, visit all communities in
        the group in selected order. First parent in each community will last
        node from previous community (None if first community).
        """

        for community_id in self.traversal_order:
            community = self.communities[community_id]
            if self.global_traversal:
                community.traversal_order_parents[0] = self.global_traversal[-1]
            self.global_traversal_parents.extend(community.traversal_order_parents)
            self.global_traversal.extend(community.traversal_order)
