from abc import ABC, abstractmethod
import logging
import os

from pydantic import BaseModel
from triplet_extraction.classes import Entity, Relationship, Triplet
from triplet_extraction.llm_wrappers import OpenAIModel
from triplet_extraction.prompts import RELATIONSHIPS_GENERATION_PROMPT


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RelationshipBase(BaseModel):
    subject: list[str]
    object: list[str]
    relationship_description: str
    relationship_strength: int


class RelationshipResponse(BaseModel):
    relationships: list[RelationshipBase]


class RelationshipExtractor(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def extract(self, text: str) -> list[Relationship]:
        raise NotImplementedError


class LLMRelationshipExtractor(RelationshipExtractor):
    def __init__(self) -> None:
        self.model = OpenAIModel(os.environ["LLM_API_KEY"])
        logger.info("LLM Relationship Extractor initialized!")

    def extract(self, text: str, entities: list[Entity]) -> list[Triplet]:
        # TODO if entities are None, we should apply different prompt to extract everything at once
        entities_lst = [[e.name, e.type] for e in entities]
        logger.info(f"Searching for relationships between given entities ({entities_lst})...")
        response: RelationshipResponse = self.model.parse(
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
