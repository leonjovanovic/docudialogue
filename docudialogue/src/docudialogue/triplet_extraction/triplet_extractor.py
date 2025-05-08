from abc import ABC, abstractmethod
import logging
import os

from docudialogue.src.docudialogue.utils import run_concurrent
from docudialogue.triplet_extraction.classes import Entity, Relationship, Triplet
from docudialogue.triplet_extraction.entity_extractor import (
    LLMEntityExtractor,
    TransformerEntityExtractor,
)
from docudialogue.llm_wrappers.llm_wrappers import OpenAIModel
from docudialogue.llm_wrappers.prompts import (
    ENTITY_TYPE_GENERATION_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)
from docudialogue.llm_wrappers.pydantic_classes import EntityRelationshipResponse, EntityTypes
from docudialogue.triplet_extraction.relationship_extractor import LLMRelationshipExtractor


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

    async def _detect_entity_types(self, docs: list[list[str]]) -> list[str]:
        if not self._entity_types:
            logger.info("Entity types not found! Quering LLM to find it...")
            input_text = " ".join([d for doc in docs for d in doc])
            respone = await self._model.parse(
                system_prompt="",
                user_prompt=ENTITY_TYPE_GENERATION_PROMPT.format(
                    input_text=input_text
                ),
                response_format=EntityTypes,
                model_name="gpt-4o-mini",
                temperature=0,
            )
            self._entity_types = respone.types
            logger.info(f"Following entity types found: {self._entity_types}")
        return self._entity_types

    async def run(self, docs: list[list[str]]) -> list[Triplet]:
        triplets = []
        await self._detect_entity_types(docs)
        for doc in docs:
            curr_triplets = await self.extractor.extract(doc, self._entity_types)
            logger.info(f"Found {len(curr_triplets)} triplets in document.")
            triplets.extend(curr_triplets)
        return triplets


class AbstractTripletExtractor(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        raise NotImplementedError

    async def extract(self, texts: list[str], entity_types: list[str]) -> list[Triplet]:
        async_funcs = [lambda t=text: self._extract_from_text(t, entity_types) for text in texts]
        results = await run_concurrent(async_funcs)
        triplets = [triplet for sublist in results for triplet in sublist]
        return self.postprocess_triplets(triplets)

    def postprocess_triplets(self, triplets: list[Triplet]) -> list[Triplet]:
        # Remove duplicates
        # Join similar
        return triplets


class CombinedTripletExtractor(AbstractTripletExtractor):
    def __init__(self, entity_types: list[str] | None = None) -> None:
        self._model = OpenAIModel(os.environ["LLM_API_KEY"])
        self._entity_types = entity_types
        logger.info("Combined Triplet Extractor initialized!")

    async def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        response: EntityRelationshipResponse = await self._model.parse(
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

    async def _extract_from_text(self, text: str, entity_types: list[str]) -> list[Triplet]:
        entites = await self._entity_extractor.extract(text, entity_types)
        return await self._relationship_extractor.extract(text, entites)
