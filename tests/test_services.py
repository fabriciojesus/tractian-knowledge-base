"""
Unit tests for core services.
"""

import pytest

from app.services.pdf_processor import PDFProcessor, DocumentChunk


class TestPDFProcessor:
    """Tests for PDF processing and chunking."""

    def setup_method(self):
        self.processor = PDFProcessor(
            chunk_size=200, chunk_overlap=50
        )

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        pages = [
            {
                "text": "This is a test paragraph. " * 20,
                "page": 1,
                "source": "test.pdf",
            }
        ]
        chunks = self.processor.chunk_text(pages)
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.metadata["source"] == "test.pdf" for c in chunks)

    def test_chunk_text_preserves_metadata(self):
        """Test that chunking preserves page and source metadata."""
        pages = [
            {
                "text": "First page content. " * 30,
                "page": 1,
                "source": "doc.pdf",
            },
            {
                "text": "Second page content. " * 30,
                "page": 2,
                "source": "doc.pdf",
            },
        ]
        chunks = self.processor.chunk_text(pages)

        page_1_chunks = [c for c in chunks if c.metadata["page"] == 1]
        page_2_chunks = [c for c in chunks if c.metadata["page"] == 2]

        assert len(page_1_chunks) > 0
        assert len(page_2_chunks) > 0

    def test_chunk_text_empty_input(self):
        """Test chunking with empty input."""
        chunks = self.processor.chunk_text([])
        assert chunks == []

    def test_chunk_text_short_text(self):
        """Test chunking when text is shorter than chunk size."""
        pages = [
            {
                "text": "Short text.",
                "page": 1,
                "source": "test.pdf",
            }
        ]
        chunks = self.processor.chunk_text(pages)
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."

    def test_chunk_has_required_metadata(self):
        """Test that each chunk has required metadata fields."""
        pages = [
            {
                "text": "Test content for metadata validation. " * 20,
                "page": 3,
                "source": "metadata_test.pdf",
            }
        ]
        chunks = self.processor.chunk_text(pages)
        for chunk in chunks:
            assert "source" in chunk.metadata
            assert "page" in chunk.metadata
            assert "chunk_index" in chunk.metadata

    def test_extract_invalid_pdf(self):
        """Test that invalid PDF raises ValueError."""
        with pytest.raises(ValueError, match="Failed to process PDF"):
            self.processor.extract_text_from_pdf(
                b"not a pdf", "invalid.pdf"
            )

    def test_process_pdf_invalid(self):
        """Test full pipeline with invalid PDF."""
        with pytest.raises(ValueError):
            self.processor.process_pdf(b"invalid content", "bad.pdf")


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_creation(self):
        chunk = DocumentChunk(
            text="test text",
            metadata={"source": "test.pdf", "page": 1},
        )
        assert chunk.text == "test text"
        assert chunk.metadata["source"] == "test.pdf"
        assert chunk.metadata["page"] == 1
