"""
API integration tests.
"""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    """Create a minimal valid PDF for testing."""
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000360 00000 n 

trailer
<< /Size 6 /Root 1 0 R >>
startxref
441
%%EOF"""
    return pdf_content


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")


class TestDocumentUpload:
    """Tests for document upload endpoint."""

    def test_upload_no_files(self, client):
        """Test upload with no files raises 422."""
        response = client.post("/documents")
        assert response.status_code == 422

    def test_upload_non_pdf(self, client):
        """Test upload with non-PDF file."""
        files = [
            ("files", ("test.txt", b"not a pdf", "text/plain"))
        ]
        response = client.post("/documents", files=files)
        assert response.status_code == 400

    def test_upload_invalid_pdf(self, client):
        """Test upload with invalid PDF content."""
        files = [
            ("files", ("test.pdf", b"not valid pdf content", "application/pdf"))
        ]
        response = client.post("/documents", files=files)
        assert response.status_code == 400


class TestQuestionEndpoint:
    """Tests for question answering endpoint."""

    def test_question_empty(self, client):
        """Test question with empty string."""
        response = client.post(
            "/question",
            json={"question": ""},
        )
        assert response.status_code == 422

    def test_question_missing_field(self, client):
        """Test question with missing field."""
        response = client.post(
            "/question",
            json={},
        )
        assert response.status_code == 422

    def test_question_invalid_content_type(self, client):
        """Test question with wrong content type."""
        response = client.post(
            "/question",
            data="not json",
        )
        assert response.status_code == 422
