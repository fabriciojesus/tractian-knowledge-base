"""
Embedding service.
Generates vector embeddings from text using sentence-transformers.
"""

from sentence_transformers import SentenceTransformer
from loguru import logger

from app.config import settings


class EmbeddingService:
    """Generates text embeddings using sentence-transformers."""

    _instance: "EmbeddingService | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            logger.info(
                f"Loading embedding model: {settings.embedding_model}"
            )
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        model = self._get_model()
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        embeddings = model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a single query text.

        Args:
            query: Query string to embed.

        Returns:
            Embedding vector as list of floats.
        """
        model = self._get_model()
        embedding = model.encode([query], convert_to_numpy=True)
        return embedding[0].tolist()
