import json
import logging
import os
from haystack import Document

from dialog_generator.graphs.triplet_handler import AbstractTripletHandler, GraphTripletHandler
from dialog_generator.input_handler.input_pipeline import PreprocessingPipeline
from dialog_generator.triplet_extraction.classes import Triplet
from dialog_generator.triplet_extraction.triplet_extractor import TripletExtractionPipeline
from dialog_generator.utils import load_pickle, save_pickle

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentPipeline:
    def __init__(self) -> None:
        self.config = None
        self.preprocessing_pipeline: PreprocessingPipeline = None
        self.docs: list[list[Document]] = None
        self.triplet_extraction_pipeline: TripletExtractionPipeline = None
        self.triplets: list[Triplet] = None
        self.triplet_handler: AbstractTripletHandler = None

    def run(self, config_path: str):
        # Step 1: Initialize pipeline
        self._initialize_pipeline(config_path)

        # # Step 2: Process all documents
        self.docs = [
            self.preprocessing_pipeline.run(path)["document_splitter"]["documents"]
            for path in self.config["input"]["file_paths"]
        ]
        logger.info(f"Document was split into {len(self.docs)} documents")

        # # Step 3: Extract triplets from each chunk
        self.triplets = self.triplet_extraction_pipeline.run(
            [[chunk.content for chunk in doc] for doc in self.docs]
        )
        logger.info(f"Total number of triplets: {len(self.triplets)}")

        # Step 4: Create triplet handler
        self.triplet_handler = GraphTripletHandler(self.triplets)
        logger.info(
            f"Triplet handler created with {self.triplet_handler._graph.vcount()} nodes and {self.triplet_handler._graph.ecount()} edges."
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
        save_pickle(self.triplet_handler, os.path.join(folder_path, "triplet_handler.pkl"))

    def load(self, folder_path: str):
        self.config = json.load(open(os.path.join(folder_path, "config.json"), "r"))
        self.triplets = load_pickle(os.path.join(folder_path, "triplets.pkl"))
        # self.triplet_handler = load_pickle(os.path.join(folder_path, "triplet_handler.pkl"))
