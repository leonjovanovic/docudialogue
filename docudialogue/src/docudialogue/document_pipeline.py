import json
import logging
import os
from typing import Any, List, Tuple
from haystack import Document

from docudialogue.graphs.triplet_handler import TripletGraph
from docudialogue.input_handler.input_pipeline import PreprocessingPipeline
from docudialogue.triplet_extraction.classes import Triplet
from docudialogue.triplet_extraction.triplet_extractor import TripletExtractionPipeline
from docudialogue.utils import load_pickle, save_pickle

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentPipeline:

    def __init__(self, config_path: str = "config.json"):
        self._config = self._load_config(config_path)
        self._cache_folder_path = self._config["cache_folder_path"]

    async def run(self, file_paths: List[str]):
        # Step 1: Preprocess documents
        docs = self._preprocess_documents(file_paths)
        # Step 2: Extract triplets from each chunk
        triplets = await self._extract_triplets(docs)
        # Step 3: Create triplet graph
        graph = self._create_triplet_graph(triplets)
        conversation = self._create_conversation(graph)


    def _load_config(self, config_path: str) -> None:
        config = json.load(open(config_path, "r"))
        return config

    def _preprocess_documents(self, file_paths: List[str]) -> None:
        preprocessing_pipeline = PreprocessingPipeline(self._config["preprocessing_pipeline"])
        docs = [
            preprocessing_pipeline.run(path)["document_splitter"]["documents"]
            for path in file_paths
        ]
        logger.info(f"Document was split into {len(docs)} documents")
        return docs
    
    async def _extract_triplets(self, docs: list[list[Document]]) -> list[Triplet]:
        triplet_extraction_pipeline = TripletExtractionPipeline(self._config["triplet_extraction"])
        triplets = await triplet_extraction_pipeline.run(
            [[chunk.content for chunk in doc] for doc in docs]
        )
        logger.info(f"Total number of triplets: {len(triplets)}")
        self._save(triplets, "triplets", self._cache_folder_path)
        return triplets

    def _create_triplet_graph(self, triplets: list[Triplet]) -> TripletGraph:
        triplet_graph = TripletGraph(triplets)
        logger.info(
            f"Triplet handler created with {triplet_graph._graph.vcount()} nodes and {triplet_graph._graph.ecount()} edges."
        )
        self._save(triplet_graph, "triplet_graph", self._cache_folder_path)
        return triplet_graph
    
    def _create_conversation(self, triplet_graph: TripletGraph) -> List[Tuple[str, str]]:
        pass

    def _save(self, pickable_object: Any, pickable_name: str, folder_path: str):
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        path = os.path.join(folder_path, f"{pickable_name}.pkl")
        save_pickle(pickable_object, path)

    def load(self, folder_path: str):
        triplets = load_pickle(os.path.join(folder_path, "triplets.pkl"))
        triplet_graph = load_pickle(os.path.join(folder_path, "triplet_graph.pkl"))
        return triplets, triplet_graph
