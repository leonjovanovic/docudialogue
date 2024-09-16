import networkx as nx

from triplet_extraction.classes import Triplet

class Graph:
    def __init__(self, triplets: list[Triplet]):
        self.graph = nx.Graph()
        self._initialize_graph(triplets)
    
    def _initialize_graph(self, triplets: list[Triplet]):
        for triplet in triplets:
            # Add nodes
            subj_id = triplet.subject.type + " " + triplet.subject.name
            obj_id = triplet.object.type + " " + triplet.object.name
            
            # Add or update subject node
            if self.graph.has_node(subj_id):
                self.graph.nodes[subj_id]['descriptions'].append(triplet.subject.description)
            else:
                self.graph.add_node(subj_id, type=triplet.subject.type, name=triplet.subject.name, descriptions=[triplet.subject.description])
            
            # Add or update object node
            if self.graph.has_node(obj_id):
                self.graph.nodes[obj_id]['descriptions'].append(triplet.object.description)
            else:
                self.graph.add_node(obj_id, type=triplet.object.type, name=triplet.object.name, descriptions=[triplet.object.description])
            
            # Add edge
            if self.graph.has_edge(subj_id, obj_id):
                self.graph.edges[subj_id, obj_id]['descriptions'].append(triplet.relationship.description)
                self.graph.edges[subj_id, obj_id]['strengths'].append(triplet.relationship.strength)
            else:
                self.graph.add_edge(subj_id, obj_id, descriptions=[triplet.relationship.description], strengths=[triplet.relationship.strength])
