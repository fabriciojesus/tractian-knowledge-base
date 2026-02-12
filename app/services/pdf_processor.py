"""
PDF processing service.
Handles PDF text extraction and text chunking for RAG pipeline.
"""

import io
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.config import settings


@dataclass
class DocumentChunk:
    """Represents a chunk of text extracted from a document."""

    text: str
    metadata: dict


class PDFProcessor:
    """Processes PDF files: extracts text and splits into chunks."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf(
        self, file_content: bytes, filename: str
    ) -> list[dict]:
        """
        Extract text from a PDF file, page by page.

        Args:
            file_content: Raw bytes of the PDF file.
            filename: Original filename for metadata.

        Returns:
            List of dicts with 'text', 'page', and 'source' keys.
        """
        pages = []
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(
                            {
                                "text": text.strip(),
                                "page": page_num,
                                "source": filename,
                            }
                        )
            logger.info(
                f"Extracted {len(pages)} pages from '{filename}'"
            )
        except Exception as e:
            logger.error(f"Error extracting text from '{filename}': {e}")
            raise ValueError(
                f"Failed to process PDF '{filename}': {e}"
            ) from e

        if not pages:
            logger.warning(f"No text extracted from '{filename}'")

        return pages

    def chunk_text(self, pages: list[dict]) -> list[DocumentChunk]:
        """
        Split extracted pages into smaller chunks for embedding.

        Args:
            pages: List of page dicts from extract_text_from_pdf.

        Returns:
            List of DocumentChunk objects.
        """
        chunks = []
        for page_data in pages:
            text = page_data["text"]
            page_chunks = self.text_splitter.split_text(text)

            for i, chunk_text in enumerate(page_chunks):
                chunk = DocumentChunk(
                    text=chunk_text,
                    metadata={
                        "source": page_data["source"],
                        "page": page_data["page"],
                        "chunk_index": i,
                    },
                )
                chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} chunks from {len(pages)} pages"
        )
        return chunks

    def process_pdf(
        self,
        file_content: bytes,
        filename: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[DocumentChunk]:
        """
        Full pipeline: extract text from PDF and chunk it.

        Args:
            file_content: Raw bytes of the PDF file.
            filename: Original filename.
            chunk_size: Optional override for chunk size.
            chunk_overlap: Optional override for chunk overlap.

        Returns:
            List of DocumentChunk objects ready for embedding.
        """
        pages = self.extract_text_from_pdf(file_content, filename)

        # If custom chunking parameters are provided, use a temporary splitter
        if chunk_size is not None or chunk_overlap is not None:
            size = chunk_size if chunk_size is not None else self.chunk_size
            overlap = (
                chunk_overlap
                if chunk_overlap is not None
                else self.chunk_overlap
            )
            logger.info(
                f"Using custom chunking: size={size}, overlap={overlap}"
            )
            temp_splitter = RecursiveCharacterTextSplitter(
                chunk_size=size,
                chunk_overlap=overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            chunks = []
            for page_data in pages:
                text = page_data["text"]
                page_chunks = temp_splitter.split_text(text)
                for i, chunk_text in enumerate(page_chunks):
                    chunk = DocumentChunk(
                        text=chunk_text,
                        metadata={
                            "source": page_data["source"],
                            "page": page_data["page"],
                            "chunk_index": i,
                        },
                    )
                    chunks.append(chunk)
            return chunks

        return self.chunk_text(pages)
