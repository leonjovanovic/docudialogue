import os
import networkx as nx

from llm_wrappers.llm_wrappers import OpenAIModel
from llm_wrappers.prompts import SUMMARIZE_DESCRIPTIONS_PROMPT
from triplet_extraction.classes import Triplet
from llm_wrappers.pydantic_classes import SummarizedDescription

class Graph:
    def __init__(self, triplets: list[Triplet]):
        self.graph = nx.Graph()
        self._initialize_graph(triplets)
        self._summarize_graph_descriptions()
    
    def _initialize_graph(self, triplets: list[Triplet]):
        for triplet in triplets:
            # Add nodes
            subj_id = triplet.subject.type + " " + triplet.subject.name
            obj_id = triplet.object.type + " " + triplet.object.name
            
            # Add or update subject & object node
            for id, entity in zip([subj_id, obj_id], [triplet.subject, triplet.object]):
                if self.graph.has_node(id) and entity.description not in self.graph.nodes[id]['descriptions']:
                    self.graph.nodes[id]['descriptions'].append(entity.description)
                else:
                    self.graph.add_node(id, type=entity.type, name=entity.name, descriptions=[entity.description], desc="")
            
            # Add edge
            if self.graph.has_edge(subj_id, obj_id):
                if triplet.relationship.description not in self.graph.edges[subj_id, obj_id]['descriptions']:
                    self.graph.edges[subj_id, obj_id]['descriptions'].append(triplet.relationship.description)
                self.graph.edges[subj_id, obj_id]['strength'] = max(self.graph.edges[subj_id, obj_id]['strength'], triplet.relationship.strength)
            else:
                self.graph.add_edge(subj_id, obj_id, descriptions=[triplet.relationship.description], strength=triplet.relationship.strength, desc="")

    def _summarize_graph_descriptions(self):
        for node in self.graph.nodes:
            descriptions = self.graph.nodes[node]['descriptions']
            self.graph.nodes[node]['desc'] = self._summarize_descriptions(descriptions)
        
        for edge in self.graph.edges:
            descriptions = self.graph.edges[edge]['descriptions']
            self.graph.edges[edge]['desc'] = self._summarize_descriptions(descriptions)

    @staticmethod
    def _summarize_descriptions(descriptions: list[str]) -> str:
        if len(descriptions) == 1:
            return descriptions[0]
        else:
            model = OpenAIModel(os.environ["LLM_API_KEY"])
            return model.parse(
                system_prompt="",
                user_prompt=SUMMARIZE_DESCRIPTIONS_PROMPT.format(
                    descriptions=descriptions
                ),
                response_format=SummarizedDescription,
                model_name="gpt-4o-mini",
                temperature=0,
            ).description