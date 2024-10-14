from igraph import Graph

from graphs.community import Community
from graphs.graph_utils import order_each_group_for_traversal


class CommunityGroup:
    def __init__(
        self, id: int, parent_graph: Graph, communities: dict[int, Community], community_ids_ordered: list[int]
    ) -> None:
        self.id = id
        self.parent_graph = parent_graph
        self.communities = communities
        self.traversal_order = order_each_group_for_traversal(list(self.communities.keys()), community_ids_ordered)
        self._traverse_through_communities()

    def _traverse_through_communities(self) -> None:
        # TODO
        # Ovde cemo ici jednu po jednu community i raditi traversal sa pocetkom i krajnjom tackom.
        pass
