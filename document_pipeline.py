import json
import logging
import os
from haystack import Document
from uuid import uuid4

from graphs.graph import Graph
from input_handler.input_pipeline import PreprocessingPipeline
from triplet_extraction.classes import Triplet
from triplet_extraction.triplet_extractor import TripletExtractionPipeline
from utils import load_pickle, save_pickle

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentPipeline:
    def __init__(self) -> None:
        self.config = None
        self.preprocessing_pipeline = None
        self.docs = None
        self.triplet_extraction_pipeline = None
        self.triplets = None
        self.graph = None

    def run(self, config_path: str):
        # Step 1: Initialize pipeline
        self._initialize_pipeline(config_path)

        # Step 2: Process all documents
        self.docs: list[list[Document]] = [
            self.preprocessing_pipeline.run(path)["document_splitter"]["documents"]
            for path in self.config["input"]["file_paths"]
        ]
        logger.info(f"Document was split into {len(self.docs)} documents")

        # Step 3: Extract triplets from each chunk
        self.triplets = self.triplet_extraction_pipeline.run(
            [[chunk.content for chunk in doc] for doc in self.docs]
        )
        logger.info(f"Total number of triplets: {len(self.triplets)}")

        # Step 4: Create graph
        self.graph = Graph(self.triplets)
        logger.info(
            f"Graph created with {len(self.graph.graph.nodes)} nodes and {len(self.graph.graph.edges)} edges."
        )

    def _initialize_pipeline(self, config_path: str) -> None:
        self.config = json.load(open(config_path, "r"))
        self.preprocessing_pipeline = PreprocessingPipeline(
            self.config["preprocessing_pipeline"]
        )
        self.triplet_extraction_pipeline = TripletExtractionPipeline(
            self.config["triplet_extraction"]
        )

    def save(self, folder_path: str):
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        with open(os.path.join(folder_path, "config.json"), "w") as f:
            json.dump(self.config, f, indent=4)
        save_pickle(self.triplets, os.path.join(folder_path, "triplets.pkl"))
        save_pickle(self.graph, os.path.join(folder_path, "graph.pkl"))

    def load(self, folder_path: str):
        self.config = json.load(open(os.path.join(folder_path, "config.json"), "r"))
        self.triplets = load_pickle(os.path.join(folder_path, "triplets.pkl"))
        self.graph = load_pickle(os.path.join(folder_path, "graph.pkl"))
