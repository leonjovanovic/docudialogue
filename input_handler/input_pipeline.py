from haystack.components.writers import DocumentWriter
from haystack.components.converters import MarkdownToDocument, PyPDFToDocument, TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore

class PreprocessingPipeline:
    def __init__(self, config: dict) -> None:
        # FileTypeRouter will redirect each file to apporpriate Converter
        self._document_store = InMemoryDocumentStore()
        self._file_type_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/markdown"])
        self._text_file_converter = TextFileToDocument()
        self._markdown_converter = MarkdownToDocument()
        self._pdf_converter = PyPDFToDocument()
        # Joiner will join all Documents from different Converters
        self._document_joiner = DocumentJoiner()
        # Cleaning and Splitting each Document
        self._document_cleaner = DocumentCleaner()
        self._document_splitter = DocumentSplitter(split_by="word", split_length=config['split_length'], split_overlap=config['split_overlap'])
        # Embedding the Document and writing Doc with embeddings to Store
        # self._document_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        # self._document_writer = DocumentWriter(self._document_store)
        # Adding and conecting the components
        self._pipeline = Pipeline()
        self._pipeline.add_component(instance=self._file_type_router, name="file_type_router")
        self._pipeline.add_component(instance=self._text_file_converter, name="text_file_converter")
        self._pipeline.add_component(instance=self._markdown_converter, name="markdown_converter")
        self._pipeline.add_component(instance=self._pdf_converter, name="pypdf_converter")
        self._pipeline.add_component(instance=self._document_joiner, name="document_joiner")
        self._pipeline.add_component(instance=self._document_cleaner, name="document_cleaner")
        self._pipeline.add_component(instance=self._document_splitter, name="document_splitter")
        # self._pipeline.add_component(instance=self._document_embedder, name="document_embedder")
        # self._pipeline.add_component(instance=self._document_writer, name="document_writer")
        self._pipeline.connect("file_type_router.text/plain", "text_file_converter.sources")
        self._pipeline.connect("file_type_router.application/pdf", "pypdf_converter.sources")
        self._pipeline.connect("file_type_router.text/markdown", "markdown_converter.sources")
        self._pipeline.connect("text_file_converter", "document_joiner")
        self._pipeline.connect("pypdf_converter", "document_joiner")
        self._pipeline.connect("markdown_converter", "document_joiner")
        self._pipeline.connect("document_joiner", "document_cleaner")
        self._pipeline.connect("document_cleaner", "document_splitter")
        # self._pipeline.connect("document_splitter", "document_embedder")
        # self._pipeline.connect("document_embedder", "document_writer")

    def run(self, sources: list[str]):
        # Run the pipeline and output is stored in DocumentStore
        return self._pipeline.run(
            {
                "file_type_router": {
                    "sources": sources
                }
            }
        )
        # [
        #                 "content/vegan_sunflower_hemp_cheese_recipe.txt",
        #                 "content/vegan_keto_eggplant_recipe.pdf",
        #                 "content/vegan_flan_recipe.md",
        #             ]