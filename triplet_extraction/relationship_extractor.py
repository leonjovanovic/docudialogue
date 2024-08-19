from abc import ABC, abstractmethod
from classes import Entity, Relationship, Triplet


class RelationshipExtractor(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def extract(self, text: str) -> list[Relationship]:
        raise NotImplementedError


class LLMRelationshipExtractor(RelationshipExtractor):
    def __init__(self) -> None:
        super().__init__()

    def extract(
        self, text: str, entites: list[Entity]
    ) -> list[Triplet]:
        pass
