from abc import ABC, abstractmethod
import igraph as ig
import leidenalg

from graphs.community import Community
from graphs.graph_utils import create_outside_connections, summarize_descriptions
from llm_wrappers.prompts import SUMMARIZE_DESCRIPTIONS_PROMPT
from triplet_extraction.classes import Triplet

class AbstractTripletHandler(ABC):

    @abstractmethod
    def run(self) -> list[Triplet]:
        raise NotImplementedError

class GraphTripletHandler:
    def __init__(self, triplets: list[Triplet]):
        self._graph = ig.Graph(directed=False)
        self._initialize_graph(triplets)
        self._summarize_graph_descriptions()
        self._partition = leidenalg.find_partition(self._graph, leidenalg.ModularityVertexPartition)
        self._communities = self._create_communities()
    
    def _initialize_graph(self, triplets: list[Triplet]):
        vertex_map = {}
        
        for triplet in triplets:
            # Add nodes
            subj_id = triplet.subject.type + " " + triplet.subject.name
            obj_id = triplet.object.type + " " + triplet.object.name

            
            # Add or update subject & object node
            for id, entity in zip([subj_id, obj_id], [triplet.subject, triplet.object]):
                if id not in vertex_map:
                    vertex_id = self._graph.add_vertex(name=id, entity_name=entity.name, type=entity.type, descriptions=[entity.description], desc="").index
                    vertex_map[id] = vertex_id
                else:
                    vertex_id = vertex_map[id]
                    if entity.description not in self._graph.vs[vertex_id]["descriptions"]:
                        self._graph.vs[vertex_id]["descriptions"].append(entity.description)

            # Add or update edge
            subj_vertex_id = vertex_map[subj_id]
            obj_vertex_id = vertex_map[obj_id]
            edge = self._graph.es.select(_source=subj_vertex_id, _target=obj_vertex_id)

            if edge:
                edge = edge[0]
                if triplet.relationship.description not in edge["descriptions"]:
                    edge["descriptions"].append(triplet.relationship.description)
                edge["strength"] = max(edge["strength"], triplet.relationship.strength)
            else:
                self._graph.add_edge(subj_vertex_id, obj_vertex_id, descriptions=[triplet.relationship.description], strength=triplet.relationship.strength, desc="")
                
    def _summarize_graph_descriptions(self):
        for vertex in self._graph.vs:
            vertex['desc'] = summarize_descriptions(vertex['descriptions'], SUMMARIZE_DESCRIPTIONS_PROMPT)
        
        for edge in self._graph.es:
            edge['desc'] = summarize_descriptions(edge['descriptions'], SUMMARIZE_DESCRIPTIONS_PROMPT)

    def _create_communities(self) -> list[Community]:
        communities = []
        self.outside_connections = create_outside_connections(self._graph, self._partition)
        for idx, subgraph in enumerate(self._partition.subgraphs()):
            # Create outside connections
            communities.append(Community(self._graph, subgraph, self.outside_connections[idx]))
        return communities
    
    def run(self) -> list[Triplet]:
        pass