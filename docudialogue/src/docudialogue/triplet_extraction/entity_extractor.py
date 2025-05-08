from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import logging

from docudialogue.triplet_extraction.classes import Entity
from docudialogue.llm_wrappers.llm_wrappers import OpenAIModel
from docudialogue.llm_wrappers.prompts import (
    ENTITY_GENERATION_PROMPT,
    ENTITY_TYPE_GENERATION_PROMPT,
)
from docudialogue.llm_wrappers.pydantic_classes import EntityResponse, EntityTypes

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EntityExtractor(ABC):

    @abstractmethod
    async def _extract(self, text: str) -> list[Entity]:
        raise NotImplementedError

    async def extract(self, text: str, entity_types: list[str]) -> list[Entity]:
        entities = await self._extract(text, entity_types)
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

    async def _extract(self, text: str, entity_types: list[str]) -> list[Entity]:
        logger.info(f"Searching for following entities: {entity_types}")
        response: EntityResponse = await self._model.parse(
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

    def _extract(self, text: str, entity_types: list[str]) -> list[Entity]:
        # TODO
        pass
