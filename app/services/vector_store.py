"""
Vector store service.
Manages FAISS index for storing and retrieving document embeddings.
Uses a persistent JSON metadata store alongside the FAISS index.
"""

import json
import uuid
from pathlib import Path

import faiss
import numpy as np
from loguru import logger

from app.config import settings
from app.services.embeddings import EmbeddingService


class VectorStoreService:
    """Manages document embeddings using FAISS."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self._index: faiss.IndexFlatIP | None = None
        self._documents: list[dict] = []
        self._persist_dir = Path(settings.chroma_persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._persist_dir / "faiss.index"
        self._meta_path = self._persist_dir / "metadata.json"
        self._load()

    def _load(self):
        """Load persisted index and metadata from disk."""
        if self._index_path.exists() and self._meta_path.exists():
            try:
                self._index = faiss.read_index(str(self._index_path))
                with open(self._meta_path, "r") as f:
                    self._documents = json.load(f)
                logger.info(
                    f"Loaded FAISS index with {self._index.ntotal} vectors"
                )
            except Exception as e:
                logger.warning(f"Failed to load persisted index: {e}")
                self._index = None
                self._documents = []
        else:
            self._index = None
            self._documents = []

    def _save(self):
        """Persist index and metadata to disk."""
        if self._index is not None:
            faiss.write_index(self._index, str(self._index_path))
            with open(self._meta_path, "w") as f:
                json.dump(self._documents, f)
            logger.debug("FAISS index persisted to disk")

    def _ensure_index(self, dimension: int):
        """Create index if it doesn't exist."""
        if self._index is None:
            # Using IndexFlatIP (inner product) with normalized vectors = cosine similarity
            self._index = faiss.IndexFlatIP(dimension)
            logger.info(
                f"Created new FAISS index with dimension {dimension}"
            )

    def add_chunks(self, chunks: list) -> int:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects.

        Returns:
            Number of chunks added.
        """
        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)

        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(embeddings_np)

        # Ensure index exists with correct dimension
        self._ensure_index(embeddings_np.shape[1])

        # Add to FAISS
        self._index.add(embeddings_np)

        # Store metadata
        for text, meta in zip(texts, metadatas):
            self._documents.append(
                {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "metadata": meta,
                }
            )

        # Persist to disk
        self._save()

        logger.info(f"Added {len(chunks)} chunks to vector store")
        return len(chunks)

    def query(
        self, question: str, top_k: int | None = None
    ) -> list[dict]:
        """
        Query the vector store for relevant document chunks.

        Args:
            question: User question to search for.
            top_k: Number of results to return.

        Returns:
            List of dicts with 'text', 'metadata', and 'distance' keys.
        """
        top_k = top_k or settings.top_k_results

        if self._index is None or self._index.ntotal == 0:
            logger.warning("Vector store is empty, no results to return")
            return []

        # Clamp top_k to available documents
        top_k = min(top_k, self._index.ntotal)

        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(question)
        query_np = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Search
        distances, indices = self._index.search(query_np, top_k)

        # Format results
        formatted = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            formatted.append(
                {
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "distance": float(dist),
                }
            )

        logger.info(
            f"Query returned {len(formatted)} results for: "
            f"'{question[:50]}...'"
        )
        return formatted

    def get_collection_stats(self) -> dict:
        """Get statistics about the current index."""
        count = self._index.ntotal if self._index else 0
        return {
            "collection_name": settings.chroma_collection_name,
            "total_documents": len(self.list_documents()),
            "total_chunks": count,
        }

    def list_documents(self) -> list[str]:
        """
        Return a list of unique document names indexed in the store.
        """
        if not self._documents:
            return []

        sources = {doc["metadata"].get("source") for doc in self._documents}
        return sorted([s for s in sources if s])

    def delete_document(self, source_name: str) -> bool:
        """
        Delete all chunks associated with a specific source name.
        """
        if self._index is None or not self._documents:
            return False

        # Filter out chunks from this source
        new_docs = []
        for doc in self._documents:
            if doc["metadata"].get("source") != source_name:
                new_docs.append(doc)

        if len(new_docs) == len(self._documents):
            return False  # Nothing found to delete

        # Rebuild index if something was deleted
        if not new_docs:
            # Entire store was deleted
            self.reset_collection()
        else:
            # Re-create FAISS index with remaining data
            texts = [doc["text"] for doc in new_docs]
            embeddings = self.embedding_service.embed_texts(texts)
            embeddings_np = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_np)

            # Re-init index
            self._index = faiss.IndexFlatIP(embeddings_np.shape[1])
            self._index.add(embeddings_np)
            self._documents = new_docs

            # Save changes
            self._save()

        logger.info(f"Document '{source_name}' deleted from vector store")
        return True

    def reset_collection(self) -> None:
        """Delete the index and all metadata."""
        self._index = None
        self._documents = []
        if self._index_path.exists():
            self._index_path.unlink()
        if self._meta_path.exists():
            self._meta_path.unlink()
        logger.info("Vector store reset successfully")
