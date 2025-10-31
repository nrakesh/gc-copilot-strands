"""
Simple ChromaDB client wrapper for querying collections.
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Dict, List, Any, Optional
from threading import Lock


class ChromaClient:
    """Simple wrapper for ChromaDB operations with singleton pattern."""

    _instance: Optional['ChromaClient'] = None
    _lock: Lock = Lock()

    def __new__(cls, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2"):
        if hasattr(self, '_initialized'):
            return

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self._initialized = True

    @classmethod
    def get_instance(cls, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2") -> 'ChromaClient':
        """Get the singleton ChromaClient instance."""
        return cls(persist_directory, embedding_model)

    def query_collection(self, collection_name: str, query_text: str, n_results: int = 5) -> Optional[Dict[str, Any]]:
        """Query a ChromaDB collection."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )

            return results

        except Exception as e:
            print(f"Warning: Error querying collection {collection_name}: {e}")
            return None

    def list_collections(self) -> List[str]:
        """List available collections."""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            print(f"Warning: Error listing collections: {e}")
            return []
