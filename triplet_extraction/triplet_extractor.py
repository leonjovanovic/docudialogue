import logging

from triplet_extraction.classes import Triplet
from triplet_extraction.entity_extractor import LLMEntityExtractor, TransformerEntityExtractor
from triplet_extraction.relationship_extractor import LLMRelationshipExtractor


logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TripletExtractor:
    def __init__(self, entity_extractor: str, entity_types: list[str] | None = None) -> None:
        self.entity_extractor = (
            LLMEntityExtractor(entity_types=entity_types)
            if entity_extractor == "llm"
            else TransformerEntityExtractor()
        )
        self.relationship_extractor = LLMRelationshipExtractor()

    def extract(self, texts: list[str]) -> list[Triplet]:
        triplets = []
        for text in texts:
            triplets.extend(self._extract(text))
        triplets = self.postprocess_triplets(triplets)
        return triplets

    def _extract(self, text: str) -> list[Triplet]:
        entites = self.entity_extractor.extract(text)
        return self.relationship_extractor.extract(text, entites)

    def postprocess_triplets(self, triplets: list[Triplet]) -> list[Triplet]:
        # Remove duplicates
        # Join similar
        return triplets
