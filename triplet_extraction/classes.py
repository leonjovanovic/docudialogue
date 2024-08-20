class Entity:
    def __init__(self, name, type, description) -> None:
        self.name = name
        self.type = type
        self.description = description


class Relationship:
    def __init__(
        self, description: str, strength: int
    ) -> None:
        self.description = description
        self.strength = strength


class Triplet:
    def __init__(
        self, subject: Entity, relationship: Relationship, object: Entity
    ) -> None:
        self.subject = subject
        self.relationship = relationship
        self.object = object
