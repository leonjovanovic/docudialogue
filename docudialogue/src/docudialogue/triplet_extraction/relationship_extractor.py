from abc import ABC, abstractmethod
import logging
import os

from docudialogue.triplet_extraction.classes import Entity, Relationship, Triplet
from docudialogue.llm_wrappers.llm_wrappers import OpenAIModel
from docudialogue.llm_wrappers.prompts import RELATIONSHIPS_GENERATION_PROMPT
from docudialogue.llm_wrappers.pydantic_classes import RelationshipResponse


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RelationshipExtractor(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    async def extract(self, text: str) -> list[Relationship]:
        raise NotImplementedError


class LLMRelationshipExtractor(RelationshipExtractor):
    def __init__(self) -> None:
        self._model = OpenAIModel(os.environ["LLM_API_KEY"])
        logger.info("LLM Relationship Extractor initialized!")

    async def extract(self, text: str, entities: list[Entity]) -> list[Triplet]:
        entities_lst = [[e.name, e.type] for e in entities]
        logger.info(f"Searching for relationships between given entities ({entities_lst})...")
        response: RelationshipResponse = await self._model.parse(
            system_prompt="",
            user_prompt=RELATIONSHIPS_GENERATION_PROMPT.format(
                entities=entities_lst, input_text=text
            ),
            response_format=RelationshipResponse,
            model_name="gpt-4o-mini",
            temperature=0,
        )
        logger.info(f"Found {len(response.relationships)} relationships!")
        entities_dict = {(e.name, e.type): e for e in entities}
        triplets = []
        for rel in response.relationships:
            try:
                subject = entities_dict[(rel.subject[0], rel.subject[1])]
                object = entities_dict[(rel.object[0], rel.object[1])]
                relationship = Relationship(rel.relationship_description, rel.relationship_strength)
                triplets.append(Triplet(subject, relationship, object))
            except:
                logger.warning(f"Relationship {rel} invalid!")
        return triplets
