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
        for idx in range(len(self.traversal_order)):
            community_id = self.traversal_order[idx]

            first_node_id, last_node_id = self._find_border_node_ids(idx, community_id)

            

            print("=======")
            print(f"Current community {community_id}")

            print(f"Outside conns: {self.outside_connections[community_id]}")
            print(f"first node id: {first_node_id}")
            print(f"last node id: {last_node_id}")
            # self.communities[community_id]._traverse(first_node, last_node)
            # outs = self.communities[community_id].outside_connections_locallized
            # for neighbor_community_id, vertices in outs.items():
            #     print(f"We can go to community {neighbor_community_id} with nodes {vertices}")

    def _find_border_node_ids(self, idx: int, community_id: int) -> tuple[int, int]:
        first_node_id = self._find_first_node_id(idx, community_id)
        last_node_id = self._find_last_node_id(idx, community_id, first_node_id)
        return first_node_id, last_node_id
    
    def _find_first_node_id(self, idx: int, community_id: int) -> int:
        previous_community_id = self.traversal_order_parents[idx]
        if previous_community_id == -1:
            first_node_id = -1
        else:
            first_node_id = list(self.outside_connections[community_id][previous_community_id].keys())[0]
            return first_node_id
    
    def _find_last_node_id(self, idx: int, community_id: int, first_node_id: int) -> int:
        previous_community_id = self.traversal_order_parents[idx]
        if idx == len(self.traversal_order) - 1:
            # next_community_id = -1
            last_node_id = -1
        elif previous_community_id == self.traversal_order_parents[idx + 1]:
            # next_community_id = previous_community_id
            last_node_id = first_node_id
        else:
            next_community_id = self.traversal_order[idx + 1]
            last_node_id = self.outside_connections[community_id][next_community_id]
        return last_node_id
    
    # TODO:
    # 1. Promeni outside connections da lepo ima node iz source, koji edge i node iz target communitija za svaki crossing
    # 2. Onda za svaki community 
        # 2a prvi node dobijas od prethodnog ili -1 a napravi sve moguce last node (njih moze imati vise) 
        # za SVAKI community kojem si previous. Last node ce biti list[list[int]] ili tako nesto
        # 2b probaj redom kombinacije dok ne nadjes neku koju moze da funkcionise
        # 2c lock-inuj tu kombinaciju, storuj tranziciju izmedju communitija i najavi sledecem koji mu je prvi node.