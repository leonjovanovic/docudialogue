import os
from neo4j import GraphDatabase
import re
from tqdm import tqdm

from triplet_extraction.classes import Entity, Triplet


class Neo4JGraph:
    def __init__(self) -> None:
        self._driver = self._connect()

    def populate(self, triplets: list[Triplet]):
        with self._driver.session() as session:
            for triplet in tqdm(triplets):                
                # Create subject and object entities
                session.write_transaction(Neo4JGraph.create_entity, triplet.subject)
                session.write_transaction(Neo4JGraph.create_entity, triplet.object)                
                # Create relationship
                session.write_transaction(Neo4JGraph.create_relationship, triplet)

    def open_connection(self):
        self._driver = self._connect()

    def close_connection(self):
        self._driver.close()
    
    @staticmethod
    def _connect():
        uri = os.environ["NEO4J_URI"]
        username = os.environ["NEO4J_USERNAME"]
        password = os.environ["NEO4J_PASSWORD"]
        return GraphDatabase.driver(uri, auth=(username, password))
    
    @staticmethod
    def create_entity(tx, entity: Entity):
        query = (
            f"MERGE (e:{entity.type} {{name: $name}}) "
            "ON CREATE SET e.description = $description "
            "RETURN e"
        )
        tx.run(query, name=entity.name, description=entity.description)

    @staticmethod
    def create_relationship(tx, triplet: Triplet):
        formatted_rel_desc = Neo4JGraph.format_for_cypher(triplet.relationship.description)
        query = (
            f"MATCH (s:{triplet.subject.type} {{name: $subject_name}}), (o:{triplet.object.type} {{name: $object_name}}) "
            f"MERGE (s)-[r:{formatted_rel_desc}]->(o) "
            "ON CREATE SET r.strength = $strength "
            "RETURN s, r, o"
        )
        tx.run(query, subject_name=triplet.subject.name, object_name=triplet.object.name, strength=triplet.relationship.strength)

    @staticmethod
    def format_for_cypher(sentence: str) -> str:
        # Replace spaces and special characters with underscores
        formatted = re.sub(r'[^\w\s]', '_', sentence)  # Replace non-alphanumeric chars with underscores
        formatted = re.sub(r'\s+', '_', formatted)     # Replace whitespace with underscores
        formatted = formatted.upper()                  # Convert to uppercase
        return formatted
