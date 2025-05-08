class Entity:
    def __init__(self, name: str, type: str, description: str) -> None:
        self.name = name
        self.type = type
        self.description = description

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, entity: dict) -> 'Entity':
        return cls(
            name=entity['name'],
            type=entity['type'],
            description=entity['description']
        )


class Relationship:
    def __init__(
        self, description: str, strength: int
    ) -> None:
        self.description = description
        self.strength = strength

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "strength": self.strength,
        }
    
    @classmethod
    def from_dict(cls, relationship: dict) -> 'Relationship':
        return cls(
            description=relationship['description'],
            strength=relationship['strength']
        )


class Triplet:
    def __init__(
        self, subject: Entity, relationship: Relationship, object: Entity
    ) -> None:
        self.subject = subject
        self.object = object
        self.relationship = relationship        

    def to_dict(self) -> dict:
        return {
            "subject": self.subject.to_dict(),
            "object": self.object.to_dict(),
            "relationship": self.relationship.to_dict()
        }
    
    @classmethod
    def from_dict(cls, triplet: dict) -> 'Triplet':
        return cls(
            subject=Entity.from_dict(triplet['subject']),
            relationship=Relationship.from_dict(triplet['relationship']),
            object=Entity.from_dict(triplet['object'])
        )
