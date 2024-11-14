from igraph import Graph

from graphs.community import Community
from graphs.graph_utils import order_each_group_for_traversal


class CommunityGroup:
    def __init__(
        self, id: int, parent_graph: Graph, communities: dict[int, Community], community_ids_ordered: list[int], outside_connections:  dict[int, dict[int: list[int]]]
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.communities = communities
        self.outside_connections = outside_connections
        self.traversal_order, self.traversal_order_parents = order_each_group_for_traversal(list(self.communities.keys()), community_ids_ordered, self.parent_graph)
        print(f"traversal order: {self.traversal_order}")
        print(f"traversal_order_parents order: {self.traversal_order_parents}")
        self._traverse_through_communities()

    def _traverse_through_communities(self) -> None:
        # TODO
        # Ovde cemo ici jednu po jednu community i raditi traversal sa pocetkom i krajnjom tackom.
        print(f"CommunityGroup: {self.id}")
        entrances = dict()
        first_node_ids = []
        for community_id, prev_community_id in zip(self.traversal_order, self.traversal_order_parents):
            # TODO Mozda izbaciti IDX i direktno uzimati community_id
            # TODO takodje inicijalizuj community = ...
            outside_connections = self.communities[community_id].outside_connections.connections
            print("=======")
            print(f"Current community {community_id}")

            key = f"{prev_community_id}=>{community_id}"
            first_node_ids = entrances[key] if key in entrances else []
            print(f"First nodes are {first_node_ids}")

            # print(f"Outside conns: {self.communities[community_id].outside_connections.connections}")
            ordered_border_node_ids = []
            for child_community_id, parent_communitity_id in zip(self.traversal_order, self.traversal_order_parents):
                if parent_communitity_id == community_id:
                    connections_towards_community = outside_connections[child_community_id]
                    ordered_border_node_ids.append([conn[0] for conn in connections_towards_community])
            if not ordered_border_node_ids:
                ordered_border_node_ids.append(first_node_ids)
            print(f"ordered_border_node_ids: {ordered_border_node_ids}")
            print("ENTERINGGGG")
            decided_border_node_ids = self.communities[community_id].traverse(first_node_ids, ordered_border_node_ids)
            print(f"decided_border_node_ids: {decided_border_node_ids}")
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
            print(f"entrances: {entrances}")
            print("EXITINGGGGG")
    
    # TODO:
    # 1. Promeni outside connections da lepo ima node iz source, koji edge i node iz target communitija za svaki crossing
    # 2. Onda za svaki community 
        # 2a prvi node dobijas od prethodnog ili -1 a napravi sve moguce last node (njih moze imati vise) 
        # za SVAKI community kojem si previous. Last node ce biti list[list[int]] ili tako nesto
        # 2b probaj redom kombinacije dok ne nadjes neku koju moze da funkcionise
        # 2c lock-inuj tu kombinaciju, storuj tranziciju izmedju communitija i najavi sledecem koji mu je prvi node.