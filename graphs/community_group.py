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
        self._traverse_through_communities()

    def _traverse_through_communities(self) -> None:
        # TODO
        # Ovde cemo ici jednu po jednu community i raditi traversal sa pocetkom i krajnjom tackom.
        print(f"CommunityGroup: {self.id}")
        first_node_ids = []
        for idx in range(len(self.traversal_order)):
            # TODO Mozda izbaciti IDX i direktno uzimati community_id
            # TODO takodje inicijalizuj community = ...
            community_id = self.traversal_order[idx]
            outside_connections = self.communities[community_id].outside_connections.connections
            print("=======")
            print(f"Current community {community_id}")
            # print(f"Outside conns: {self.communities[community_id].outside_connections.connections}")
            ordered_next_connections, ordered_border_node_ids = [], []
            for child_community_id, parent_communitity_id in zip(self.traversal_order, self.traversal_order_parents):
                if parent_communitity_id == community_id:
                    connections_towards_community = outside_connections[child_community_id]
                    ordered_next_connections.append(connections_towards_community)
                    ordered_border_node_ids.append([conn[0] for conn in connections_towards_community])
            print(ordered_next_connections)
            print(ordered_border_node_ids)
            print("ENTERINGGGG")
            self.communities[community_id].traverse(first_node_ids, ordered_border_node_ids)
            print("EXITINGGGGG")
            break # TODO DELETE
    
    # TODO:
    # 1. Promeni outside connections da lepo ima node iz source, koji edge i node iz target communitija za svaki crossing
    # 2. Onda za svaki community 
        # 2a prvi node dobijas od prethodnog ili -1 a napravi sve moguce last node (njih moze imati vise) 
        # za SVAKI community kojem si previous. Last node ce biti list[list[int]] ili tako nesto
        # 2b probaj redom kombinacije dok ne nadjes neku koju moze da funkcionise
        # 2c lock-inuj tu kombinaciju, storuj tranziciju izmedju communitija i najavi sledecem koji mu je prvi node.