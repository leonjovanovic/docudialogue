from classes import Triplet
from entity_extractor import LLMEntityExtractor, TransformerEntityExtractor
from relationship_extractor import LLMRelationshipExtractor


class TripletExtractor:
    def __init__(self, entity_extractor: str) -> None:
        self.entity_extractor = (
            LLMEntityExtractor()
            if entity_extractor == "llm"
            else TransformerEntityExtractor()
        )
        self.relationship_extractor = LLMRelationshipExtractor()

    def extract_triplets(self, texts: list[str]) -> list[Triplet]:
        triplets = []
        for text in texts:
            triplets.extend(self._extract_triplets(text))
        return triplets

    def _extract_triplets(self, text: str) -> list[Triplet]:
        entites = self.entity_extractor.extract(text)
        return self.relationship_extractor.extract(text, entites)
    
    def postprocess_triplets(self, triplets: list[Triplet]) -> list[Triplet]:
        #Remove duplicates
        #Join similar
        return triplets