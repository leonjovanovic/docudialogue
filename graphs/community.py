import os
from igraph import Graph, Vertex, Edge

from graphs.graph_utils import localize_connections, summarize_descriptions
from llm_wrappers.prompts import SUMMARIZE_GRAPH_PROMPT


class Community:
    def __init__(
        self, parent_graph: Graph, graph: Graph, outside_connections: dict[int, dict[int: list[int]]]
    ) -> None:
        self.parent_graph = parent_graph
        self.graph = graph
        self.outside_connections = outside_connections
        self.outside_connections_locallized = localize_connections(parent_graph, graph, outside_connections)
        # self.summary = self.summarize_community()

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
