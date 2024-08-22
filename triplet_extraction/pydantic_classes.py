from pydantic import BaseModel


class EntityTypes(BaseModel):
    types: list[str]


class EntityBase(BaseModel):
    name: str
    type: str
    description: str


class EntityResponse(BaseModel):
    entities: list[EntityBase]


class RelationshipBase(BaseModel):
    subject: list[str]
    object: list[str]
    relationship_description: str
    relationship_strength: int


class RelationshipResponse(BaseModel):
    relationships: list[RelationshipBase]


class EntityRelationshipResponse(BaseModel):
    entities: EntityResponse
    relationships: RelationshipResponse