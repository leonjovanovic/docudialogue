from abc import ABC, abstractmethod
import os
from pydantic import BaseModel
from triplet_extraction.classes import Entity
from triplet_extraction.llm_wrappers import LLMModel, OpenAIModel
from dotenv import load_dotenv

from triplet_extraction.prompts import ENTITY_GENERATION_JSON_PROMPT

load_dotenv()

class EntityBase(BaseModel):
    name: str
    type: str
    description: str

class EntityResponse(BaseModel):
    entities: list[EntityBase]

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
        #...
        return entites


class LLMEntityExtractor(EntityExtractor):
    def __init__(self, entity_types: list[str] | None) -> None:
        self.model = OpenAIModel(os.environ["LLM_API_KEY"])
        # TODO query llm for entity types if user doesnt provide them himself
        self.entity_types = ["PERSON", "ORG", "GPE"]

    def _extract(self, text: str) -> list[Entity]:
        response: EntityResponse = self.model.parse(
            system_prompt="",
            user_prompt=ENTITY_GENERATION_JSON_PROMPT.format(entity_types=self.entity_types, input_text=text),
            response_format=EntityResponse,
            model_name="gpt-4o-mini",
            temperature=0,
        )
        return [Entity(ent.name, ent.type, ent.description) for ent in response.entities]


class TransformerEntityExtractor(EntityExtractor):
    def __init__(self) -> None:
        # TODO
        pass

    def extract(self, text: str) -> list[Entity]:
        # TODO
        pass
