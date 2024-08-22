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
    def __init__(self, config_path: str) -> None:
        with open(config_path, "r") as f:
            self._config = json.load(f)
        self._preprocessing_pipeline = PreprocessingPipeline(self._config["input_pipeline"])
        self._triplet_extraction_pipeline = TripletExtractionPipeline(self._config["triplet_extraction"])
        if bool(self._config['storage']['load_from_json']):
            self.triplets = self._load_triplets(self._config['storage']['path'])

    def run(self, doc_path: str):
        docs: list[Document] = self._preprocessing_pipeline.run(doc_path)
        logger.info(f"Document was split into {len(docs)} documents")
        self.triplets = self._triplet_extraction_pipeline.run([doc.content for doc in docs['document_splitter']['documents']])
        logger.info(f"Total number of triplets: {len(self.triplets)}")
        self._store(docs, self.triplets)
        return self.triplets
    
    def _load_triplets(self, path: str) -> list[Triplet]:
        with open(path, "r") as f:
            processed_doc = json.load(f)
        self.triplets = [Triplet.from_dict(t) for t in processed_doc['triplets']]
        return self.triplets


    def _store(self, docs: list[Document], triplets: list[Triplet]) -> None:
        storage = {
            "name": os.path.basename(docs[0].meta['file_path']),
            "num_pages": docs[-1].meta['page_number'],
            "config": self._config,
            "triplets": [t.to_dict() for t in triplets]
        }
        with open(f"storage/{str(uuid4())}.json", 'w') as f:
            json.dump(storage, f, indent=4)

