import json
import logging
import os
from haystack import Document
from uuid import uuid4

from input_handler.input_pipeline import PreprocessingPipeline
from triplet_extraction.classes import Triplet
from triplet_extraction.triplet_extractor import TripletExtractionPipeline

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DocumentPipeline:
    def __init__(self, config: dict) -> None:
        self._config = config
        self._preprocessing_pipeline = PreprocessingPipeline(
            self._config["preprocessing_pipeline"]
        )
        self._triplet_extraction_pipeline = TripletExtractionPipeline(
            self._config["triplet_extraction"]
        )

    def run(self):
        docs: list[Document] = self._preprocessing_pipeline.run(
            self._config["input"]["file_path"]
        )['document_splitter']['documents']
        logger.info(f"Document was split into {len(docs)} documents")
        if bool(self._config["input"]["load_saved_file"]):
            self.triplets = self._load_triplets(
                self._config["input"]["saved_file_path"]
            )
        else:
            self.triplets = self._triplet_extraction_pipeline.run(
                [doc.content for doc in docs]
            )
        logger.info(f"Total number of triplets: {len(self.triplets)}")
        self._store(self._config["output"], docs, self.triplets)
        return self.triplets

    def _load_triplets(self, path: str) -> list[Triplet]:
        with open(path, "r") as f:
            processed_doc = json.load(f)
        self.triplets = [Triplet.from_dict(t) for t in processed_doc["triplets"]]
        return self.triplets

    def _store(self, config: dict, docs: list[Document], triplets: list[Triplet]) -> None:
        if not config["store_output"]:
            return
        
        storage = {
            "name": os.path.basename(docs[0].meta["file_path"]),
            "num_pages": docs[-1].meta["page_number"],
            "config": self._config,
            "triplets": [t.to_dict() for t in triplets],
        }
        
        if not os.path.exists(config["folder_path"]):
            os.makedirs(config["folder_path"])
        with open(f"storage/{str(uuid4())}.json", "w") as f:
            json.dump(storage, f, indent=4)
