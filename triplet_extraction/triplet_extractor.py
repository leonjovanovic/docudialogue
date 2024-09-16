from abc import ABC, abstractmethod
import logging
import os

from triplet_extraction.classes import Entity, Relationship, Triplet
from triplet_extraction.entity_extractor import (
    LLMEntityExtractor,
    TransformerEntityExtractor,
)
from triplet_extraction.llm_wrappers import OpenAIModel
from triplet_extraction.prompts import (
    ENTITY_TYPE_GENERATION_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)
from triplet_extraction.pydantic_classes import EntityRelationshipResponse, EntityTypes
from triplet_extraction.relationship_extractor import LLMRelationshipExtractor


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TripletExtractionPipeline:
    def __init__(self, config: dict) -> None:
        self._model = OpenAIModel(os.environ["LLM_API_KEY"])
        self._entity_types = config["entity_types"]
        if config["extractor_type"] == "combined":
            self.extractor = CombinedTripletExtractor(self._model)
        elif config["extractor_type"] == "separated":
            self.extractor = SeparateTripletExtractor(
                self._model, config["entity_extractor_type"]
            )

    def run(self, texts: list[str]) -> list[Triplet]:
        if not self._entity_types:
            logger.info("Entity types not found! Quering LLM to find it...")
            self._entity_types = self._model.parse(
                system_prompt="",
                user_prompt=ENTITY_TYPE_GENERATION_PROMPT.format(
                    input_text=" ".join(texts)
                ),
                response_format=EntityTypes,
                model_name="gpt-4o-mini",
                temperature=0,
            ).types
            logger.info(f"Following entity types found: {self._entity_types}")
        return self.extractor.extract(texts, self._entity_types)


class AbstractTripletExtractor(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        raise NotImplementedError

    def extract(self, texts: list[str], entity_types: list[str]) -> list[Triplet]:
        triplets = []
        for text in texts:
            triplets.extend(self._extract_from_text(text, entity_types))
        triplets = self.postprocess_triplets(triplets)
        return triplets

    def postprocess_triplets(self, triplets: list[Triplet]) -> list[Triplet]:
        # Remove duplicates
        # Join similar
        return triplets


class CombinedTripletExtractor(AbstractTripletExtractor):
    def __init__(self, entity_types: list[str] | None = None) -> None:
        self._model = OpenAIModel(os.environ["LLM_API_KEY"])
        self._entity_types = entity_types
        logger.info("Combined Triplet Extractor initialized!")

    def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        response: EntityRelationshipResponse = self._model.parse(
            system_prompt="",
            user_prompt=ENTITY_RELATIONSHIPS_GENERATION_PROMPT.format(
                entity_types=entity_types, input_text=text
            ),
            response_format=EntityRelationshipResponse,
            model_name="gpt-4o-mini",
            temperature=0,
        )
        logger.info(
            f"Found {len(response.entities.entities)} entities and {len(response.relationships.relationships)} relationships!"
        )
        entities_dict = {
            (e.name, e.type): Entity(e.name, e.type, e.description)
            for e in response.entities.entities
        }
        triplets = []
        for rel in response.relationships.relationships:
            try:
                subject = entities_dict[(rel.subject[0], rel.subject[1])]
                object = entities_dict[(rel.object[0], rel.object[1])]
                relationship = Relationship(
                    rel.relationship_description, rel.relationship_strength
                )
                triplets.append(Triplet(subject, relationship, object))
            except:
                logger.warning(f"Relationship {rel} invalid!")
        return triplets


class SeparateTripletExtractor(AbstractTripletExtractor):
    def __init__(
        self, entity_extractor_type: str, entity_types: list[str] | None = None
    ) -> None:
        self._entity_extractor = (
            LLMEntityExtractor(entity_types=entity_types)
            if entity_extractor_type == "llm"
            else TransformerEntityExtractor()
        )
        self._relationship_extractor = LLMRelationshipExtractor()
        logger.info("Separate Triplet Extractor initialized!")

    def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        entites = self._entity_extractor.extract(text, entity_types)
        return self._relationship_extractor.extract(text, entites)
