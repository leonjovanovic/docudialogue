from abc import ABC, abstractmethod
import igraph as ig
import leidenalg

from graphs.community import Community
from graphs.community_group import CommunityGroup
from graphs.graph_utils import (
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

        communities = []
        partition = leidenalg.find_partition(
            self._graph, leidenalg.ModularityVertexPartition
        )
        self._outside_connections = find_neighbour_connections(self._graph, partition)
        for idx, subgraph in enumerate(partition.subgraphs()):
            communities.append(
                Community(idx, self._graph, subgraph, self._outside_connections[idx])
            )
        return communities

    def _create_community_groups(self) -> dict[int, CommunityGroup]:
        group_graph = self._group_communities()
        groups = group_graph.connected_components()
        community_groups = self._instantiate_community_groups(group_graph, groups)
        return community_groups

    def _group_communities(self) -> ig.Graph:
        partition = leidenalg.find_partition(
            self._graph, leidenalg.ModularityVertexPartition
        )
        aggregate_partition = partition.aggregate_partition(partition)
        return aggregate_partition.graph

    def _instantiate_community_groups(
        self, group_graph: ig.Graph, groups: list[list[int]]
    ) -> dict[int, CommunityGroup]:
        community_ids_ordered_by_centralization = order_nodes_by_centralization(
            group_graph
        )
        community_groups = {}
        for idx, community_ids in enumerate(groups):
            # print(f"NEW COMMUNITY GROUP WOOO = {idx} {community_ids}")
            group_communities = {id: self._communities[id] for id in community_ids}
            community_group = CommunityGroup(
                idx,
                group_graph,
                group_communities,
                community_ids_ordered_by_centralization,
                self._outside_connections,
            )
            community_groups[idx] = community_group
        return community_groups

    def _order_groups_for_traversal(self) -> list[int]:
        community_groups = list(self._community_groups.values())
        community_groups_sorted = sorted(
            community_groups, key=lambda cg: len(cg.communities)
        )
        groups_traverse_order = order_list(len(community_groups_sorted))
        community_groups_ordered = [
            community_groups_sorted[group_id] for group_id in groups_traverse_order
        ]
        community_groups_traversal_order = [
            group.id for group in community_groups_ordered
        ]
        return community_groups_traversal_order

    def visit_community_groups(self):
        traverse_order = []
        traverse_order_parents = []
        prev_group = None
        for group in self._community_groups.values():
            group.visit_communities()
            traverse_order.extend(group.global_traversal)
            parents = group.global_traversal_parents
            parents[0] = prev_group.global_traversal[-1] if prev_group else None
            traverse_order_parents.extend(parents)
            prev_group = group
        return traverse_order, traverse_order_parents

    def _handle_community(
        self, community_id: int, start_node: int, end_community: int
    ) -> list[Triplet]:
        pass

    def _handle_transition(
        self, community_id: int, start_node: int, end_community: int
    ):
        edges = self._outside_connections[community_id][end_community][start_node]

    def run(self) -> list[Triplet]:
        # For dialog. QA should be different
        group_graph = self._group_communities()
        # For each group decide the community traverse order
        order_of_groups, order_within_group = get_traverse_order(group_graph)
        # CONTINUE HERE TODO
        for group_id in order_of_groups:
            # Handle single group
            order_of_communities, order_of_communities_parents = order_within_group[
                group_id
            ]
            prev_community_id = None
            for community_id in order_of_communities:
                community = self._communities[community_id]
                if prev_community_id:
                    _, order_within_community = get_traverse_order_first(
                        community.graph
                    )
                else:
                    _, order_within_community = get_traverse_order(community.graph)
                    order_of_nodes = order_within_community[0]
                prev_community_id = community_id
        # Decide a starting point within first community with respect to the next community
        # Will probably need a function which detects if we need multiple passes through same community,
        # if so we need to simulate all passes with lowest possible overlay
        # Probably DFS and then add non-visited later on
        start_node = None
        #
        pass
