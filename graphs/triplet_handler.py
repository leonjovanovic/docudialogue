from abc import ABC, abstractmethod
import igraph as ig
import leidenalg

from graphs.community import Community
from graphs.community_group import CommunityGroup
from graphs.graph_utils import (
    OrderType,
    find_neighbour_connections,
    order_list,
    order_nodes_by_centralization,
    summarize_descriptions,
)
from llm_wrappers.prompts import SUMMARIZE_DESCRIPTIONS_PROMPT
from triplet_extraction.classes import Entity, Relationship, Triplet


class AbstractTripletHandler(ABC):

    @abstractmethod
    def run(self) -> list[Triplet]:
        raise NotImplementedError


class GraphTripletHandler:
    def __init__(self, triplets: list[Triplet]):
        """
        GraphTripletHandler creates a graph structures from triplets.
        Steps:
        1. Create a graph with nodes and edges from triplets.
        2. Create communities from the graph using the Leiden algorithm
        3. Create traversal order for each community using a modified DFS algorithm
        which has multiple potential and exits (connections to other communities).
        4. Create a new graph with communities as nodes and edges between them.
        5. Create traversal order for new graph using same way as for each community.
        6. Using all traversal orders, visit every node and create a global traversal
        order for the whole graph.
        """

        self._graph = ig.Graph(directed=False)
        self._initialize_graph(triplets)
        # self._summarize_graph_descriptions()
        self._communities = self._create_communities()
        self._community_groups = self._create_community_groups()
        self._community_groups_traversal_order = self._order_groups_for_traversal()
        self.global_traversal, self.global_traversal_parents = (
            self.visit_community_groups()
        )

    def _add_or_update_node(self, entity: Entity, added_entites: dict) -> str:
        entity_id = entity.type + " " + entity.name
        if entity_id not in added_entites:
            node_id = self._graph.add_vertex(
                name=entity_id,
                entity_name=entity.name,
                type=entity.type,
                descriptions=[entity.description],
                desc="",
            ).index
            added_entites[entity_id] = node_id
        else:
            node_id = added_entites[entity_id]
            if entity.description not in self._graph.vs[node_id]["descriptions"]:
                self._graph.vs[node_id]["descriptions"].append(entity.description)
        return node_id

    def _add_or_update_edge(
        self, source_node_id: str, target_node_id: str, rel: Relationship
    ):
        edge = self._graph.es.select(_source=source_node_id, _target=target_node_id)
        if edge:
            edge = edge[0]
            if rel.description not in edge["descriptions"]:
                edge["descriptions"].append(rel.description)
            edge["strength"] = max(edge["strength"], rel.strength)
        else:
            self._graph.add_edge(
                source_node_id,
                target_node_id,
                descriptions=[rel.description],
                strength=rel.strength,
                desc="",
            )

    def _initialize_graph(self, triplets: list[Triplet]):
        """Add subject and object entites to graph as vertices (nodes) and relationship
        as edge. If either of those already exists, update its description."""

        existing_nodes = {}

        for triplet in triplets:
            subject_node_id = self._add_or_update_node(triplet.subject, existing_nodes)
            object_node_id = self._add_or_update_node(triplet.object, existing_nodes)

            self._add_or_update_edge(
                subject_node_id, object_node_id, triplet.relationship
            )

    def _summarize_graph_descriptions(self):
        """ "Create cohesive description out of dscription list.
        Summarization will be done if list has more than 1 element."""

        for vertex in self._graph.vs:
            vertex["desc"] = summarize_descriptions(
                vertex["descriptions"], SUMMARIZE_DESCRIPTIONS_PROMPT
            )

        for edge in self._graph.es:
            edge["desc"] = summarize_descriptions(
                edge["descriptions"], SUMMARIZE_DESCRIPTIONS_PROMPT
            )

    def _create_communities(self) -> list[Community]:
        """
        Create communities from iGraph:
        1. Apply the Leiden algorithm on iGraph we previously populated with entites and relationships.
        2. For each community, find connections that connect that community to neightbouring communties.
            Connection represent 3 ids:
                a) current community exit node id
                b) neighbour community enter node id
                c) connecting edge id
        3. Create Community object for each community and add it to the list of communities.
        4. Return the list of communities.
        """
        partition = leidenalg.find_partition(
            self._graph, leidenalg.ModularityVertexPartition
        )
        communities = []
        self._neighbour_connections = find_neighbour_connections(self._graph, partition)
        for idx, subgraph in enumerate(partition.subgraphs()):
            communities.append(
                Community(idx, self._graph, subgraph, self._neighbour_connections[idx])
            )
        return communities

    def _create_community_groups(self) -> dict[int, CommunityGroup]:
        """
        Create community groups from iGraph:
        1. Create a new graph from the partition of the original graph using the aggregate_partition method.
        2. Order all nodes (1 node = 1 community) of the new graph by their centrality.
        3. Create a CommunityGroup object for each community in the partition and add it to the dictionary of community groups.
        """
        group_graph = self._group_communities()
        community_ids_ordered = order_nodes_by_centralization(group_graph)
        community_groups = {}
        community_groups_from_partition = group_graph.connected_components()
        for idx, community_ids in enumerate(community_groups_from_partition):
            community_group = CommunityGroup(
                id=idx,
                parent_graph=group_graph,
                communities={id: self._communities[id] for id in community_ids},
                community_ids_ordered=community_ids_ordered,
                neighbour_connections=self._neighbour_connections,
            )
            community_groups[idx] = community_group
        return community_groups

    def _group_communities(self) -> ig.Graph:
        partition = leidenalg.find_partition(
            self._graph, leidenalg.ModularityVertexPartition
        )
        aggregate_partition = partition.aggregate_partition(partition)
        return aggregate_partition.graph

    def _order_groups_for_traversal(self) -> list[int]:
        """
        Order community groups for traversal. The order is determined by
        the number of communities in each group. The groups are traversed
        iteratively from both ends towards the center to "buffer" small
        communities between big.

        Returns: a list of group ids in the order they should be traversed.
        """
        groups = list(self._community_groups.values())
        groups_sorted_by_size = sorted(groups, key=lambda cg: len(cg.communities), reverse=True)
        traverse_order = order_list(len(groups_sorted_by_size), OrderType.FROM_ENDS)

        traverse_order_group_ids = []
        for graph_id in traverse_order:
            group_in_sorted_list = groups_sorted_by_size[graph_id]
            traverse_order_group_ids.append(group_in_sorted_list.id)
        return traverse_order_group_ids

    def visit_community_groups(self):
        """
        Based on previously defined traversal order within each community,
        community group and all community groups, visit all nodes in the graph.
        During the global traversal, keep track of both global node ids and their parents.
        """

        traverse_order, traverse_order_parents = [], []
        for group_id in self._community_groups_traversal_order:
            group = self._community_groups[group_id]
            group.traverse_through_group()
            # First we store traversal parents because we need to set first
            # parent based on last visited community in the previous group.
            # First parent will stay None.
            if traverse_order:
                group.global_traversal_parents[0] = traverse_order[-1]
            traverse_order_parents.extend(group.global_traversal_parents)
            # Take global node ids from traversed community
            # and add them to the global traversal order
            traverse_order.extend(group.global_traversal)
        return traverse_order, traverse_order_parents
