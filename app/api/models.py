"""
Pydantic models for API request and response validation.
"""

from enum import Enum

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Available LLM providers."""

    GEMINI = "gemini"
    OPENAI = "openai"


class QuestionRequest(BaseModel):
    """Request model for the /question endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to ask about uploaded documents.",
        json_schema_extra={
            "example": "What is the power consumption of the motor?"
        },
    )
    provider: LLMProvider | None = Field(
        default=None,
        description="LLM provider to use: 'gemini' or 'openai'. If not set, uses default fallback order.",
    )


class QuestionResponse(BaseModel):
    """Response model for the /question endpoint."""

    answer: str = Field(
        ...,
        description="The LLM-generated answer based on document context.",
    )
    references: list[str] = Field(
        default_factory=list,
        description="Relevant text chunks used to generate the answer.",
    )


class DocumentUploadResponse(BaseModel):
    """Response model for the /documents endpoint."""

    message: str = Field(
        default="Documents processed successfully",
        description="Status message.",
    )
    documents_indexed: int = Field(
        ...,
        description="Number of documents successfully processed.",
    )
    total_chunks: int = Field(
        ...,
        description="Total number of text chunks created.",
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(..., description="Error description.")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "healthy"
    collection_stats: dict | None = None
