"""
Application configuration using pydantic-settings.
Loads settings from environment variables or .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"

    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Vector Store Configuration
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "tractian_documents"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Retrieval Configuration
    top_k_results: int = 3

    # LLM Configuration
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # Upload Configuration
    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton settings instance
settings = Settings()
