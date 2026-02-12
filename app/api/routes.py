"""
API route definitions for document upload and question answering.
"""

import time

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from app.api.models import (
    DocumentUploadResponse,
    ErrorResponse,
    HealthResponse,
    QuestionRequest,
    QuestionResponse,
)
from app.services.llm_service import LLMService
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import VectorStoreService

router = APIRouter()

# Service instances
pdf_processor = PDFProcessor()
vector_store = VectorStoreService()
llm_service = LLMService()


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Upload PDF documents",
    description="Upload one or more PDF documents to be indexed for RAG.",
)
async def upload_documents(
    files: list[UploadFile] = File(
        ..., description="One or more PDF files to upload"
    ),
) -> DocumentUploadResponse:
    """Upload and index PDF documents."""
    start_time = time.time()

    if not files:
        raise HTTPException(
            status_code=400, detail="No files provided."
        )

    total_chunks = 0
    documents_indexed = 0
    errors = []

    for file in files:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            errors.append(
                f"'{file.filename}': Not a PDF file, skipped."
            )
            continue

        try:
            # Read file content
            content = await file.read()

            if not content:
                errors.append(f"'{file.filename}': Empty file, skipped.")
                continue

            # Process PDF: extract text and chunk
            chunks = pdf_processor.process_pdf(content, file.filename)

            if not chunks:
                errors.append(
                    f"'{file.filename}': No text could be extracted."
                )
                continue

            # Store in vector database
            num_chunks = vector_store.add_chunks(chunks)
            total_chunks += num_chunks
            documents_indexed += 1

            logger.info(
                f"Indexed '{file.filename}': {num_chunks} chunks"
            )

        except Exception as e:
            logger.error(
                f"Error processing '{file.filename}': {e}"
            )
            errors.append(f"'{file.filename}': {str(e)}")

    elapsed = time.time() - start_time
    logger.info(
        f"Document upload completed in {elapsed:.2f}s: "
        f"{documents_indexed} docs, {total_chunks} chunks"
    )

    if documents_indexed == 0:
        error_detail = "No documents were successfully processed."
        if errors:
            error_detail += f" Errors: {'; '.join(errors)}"
        raise HTTPException(status_code=400, detail=error_detail)

    message = "Documents processed successfully"
    if errors:
        message += f" (with warnings: {'; '.join(errors)})"

    return DocumentUploadResponse(
        message=message,
        documents_indexed=documents_indexed,
        total_chunks=total_chunks,
    )


@router.get("/documents")
async def list_documents():
    """List all indexed documents."""
    documents = vector_store.list_documents()
    return {"documents": documents}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document and its embeddings."""
    success = vector_store.delete_document(filename)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Document '{filename}' not found"
        )
    return {"message": f"Document '{filename}' deleted successfully"}


@router.post(
    "/question",
    response_model=QuestionResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Ask a question",
    description="Ask a question about the uploaded documents.",
)
async def ask_question(
    request: QuestionRequest,
) -> QuestionResponse:
    """Answer a question using RAG pipeline."""
    start_time = time.time()

    logger.info(f"Question received: '{request.question[:80]}...'")

    try:
        # Step 1: Retrieve relevant chunks from vector store
        relevant_chunks = vector_store.query(request.question)

        # Step 2: Generate answer using LLM with context
        result = llm_service.generate_answer(
            question=request.question,
            context_chunks=relevant_chunks,
            provider=request.provider.value if request.provider else None,
        )

        elapsed = time.time() - start_time
        logger.info(f"Question answered in {elapsed:.2f}s")

        return QuestionResponse(
            answer=result["answer"],
            references=result["references"],
        )

    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}",
        ) from e


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health of the API and vector store.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    try:
        stats = vector_store.get_collection_stats()
        return HealthResponse(status="healthy", collection_stats=stats)
    except Exception:
        return HealthResponse(status="degraded", collection_stats=None)
