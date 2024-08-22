from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import logging

from triplet_extraction.classes import Entity
from triplet_extraction.llm_wrappers import OpenAIModel
from triplet_extraction.prompts import (
    ENTITY_GENERATION_PROMPT,
    ENTITY_TYPE_GENERATION_PROMPT,
)
from triplet_extraction.pydantic_classes import EntityResponse, EntityTypes

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EntityExtractor(ABC):

    @abstractmethod
    def _extract(self, text: str) -> list[Entity]:
        raise NotImplementedError

    def extract(self, text: str) -> list[Entity]:
        entities = self._extract(text)
        return self.postprocess_entites(entities)

    def postprocess_entites(self, entites: list[Entity]) -> list[Entity]:
        # TODO
        # Remove duplicates
        # Join similar
        # ...
        return entites


class LLMEntityExtractor(EntityExtractor):
    def __init__(self, entity_types: list[str] | None = None) -> None:
        self._model = OpenAIModel(os.environ["LLM_API_KEY"])
        self._entity_types = entity_types
        logger.info("LLM Entity Extractor initialized!")

    def _extract(self, text: str) -> list[Entity]:
        if not self._entity_types:
            logger.info("Entity types not found! Quering LLM to find it...")
            entity_types = self._model.parse(
                system_prompt="",
                user_prompt=ENTITY_TYPE_GENERATION_PROMPT.format(
                    entity_types=self._entity_types, input_text=text
                ),
                response_format=EntityTypes,
                model_name="gpt-4o-mini",
                temperature=0,
            ).types
        else:
            entity_types = self._entity_types
        logger.info(f"Searching for following entities: {entity_types}")
        response: EntityResponse = self._model.parse(
            system_prompt="",
            user_prompt=ENTITY_GENERATION_PROMPT.format(
                entity_types=entity_types, input_text=text
            ),
            response_format=EntityResponse,
            model_name="gpt-4o-mini",
            temperature=0,
        )
        logger.info(f"Found {len(response.entities)} entities!")
        return [
            Entity(ent.name, ent.type, ent.description) for ent in response.entities
        ]


class TransformerEntityExtractor(EntityExtractor):
    def __init__(self) -> None:
        # TODO
        logger.info("Transformer Entity Extractor initialized!")
        pass

    def _extract(self, text: str) -> list[Entity]:
        # TODO
        pass
