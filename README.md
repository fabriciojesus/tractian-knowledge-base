# 🔧 Tractian Knowledge Base - RAG System

A **Retrieval-Augmented Generation (RAG)** system that allows users to upload PDF documents and ask questions about their contents. Built with FastAPI, FAISS, and OpenAI.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  Streamlit   │────▶│              FastAPI Backend              │
│  Frontend    │◀────│                                          │
└─────────────┘     │  ┌─────────────┐   ┌──────────────────┐  │
                    │  │ PDF Process  │   │  LLM Service     │  │
                    │  │ - Extract    │   │  - OpenAI GPT-4  │  │
                    │  │ - Chunk      │   │  - Prompt Eng.   │  │
                    │  └──────┬───────┘   └────────▲─────────┘  │
                    │         │                    │             │
                    │  ┌──────▼────────────────────┴──────────┐ │
                    │  │          Vector Store (FAISS)         │ │
                    │  │  - Embeddings (sentence-transformers) │ │
                    │  │  - Cosine Similarity Search           │ │
                    │  └──────────────────────────────────────┘ │
                    └──────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Gemini Key

### 1. Clone & Install

```bash
git clone https://github.com/fabriciojesus/tractian-knowledge-base.git
cd Tractian_KB

# This will create a virtual environment and install dependencies
make install
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Run

```bash
# Start the API
make run-api

# In another terminal, start the frontend
make run-frontend
```

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501

## 📡 API Specification

### POST /documents

Upload PDF documents to be indexed.

```bash
curl -X POST "http://localhost:8000/documents" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

**Response:**
```json
{
  "message": "Documents processed successfully",
  "documents_indexed": 2,
  "total_chunks": 128
}
```

### POST /question

Ask a question about uploaded documents.

```bash
curl -X POST "http://localhost:8000/question" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the power consumption of the motor?"}'
```

**Response:**
```json
{
  "answer": "The motor's power consumption is 2.3 kW.",
  "references": [
    "the motor xxx requires 2.3kw to operate at a 60hz line frequency"
  ]
}
```

### GET /health

Health check endpoint.

```bash
curl http://localhost:8000/health
```

## 🐳 Docker

```bash
# Build and start all services
make docker-build
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

## 🧪 Testing

```bash
# Run all tests with coverage
make test

# Run unit tests only
make test-unit

# Run API tests only
make test-api
```

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── models.py        # Pydantic models
│   └── services/
│       ├── pdf_processor.py # PDF extraction & chunking
│       ├── embeddings.py    # Embedding generation
│       ├── vector_store.py  # ChromaDB operations
│       └── llm_service.py   # LLM integration
├── frontend/
│   └── streamlit_app.py     # Streamlit UI
├── tests/
│   ├── test_api.py          # API integration tests
│   └── test_services.py     # Unit tests
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## 🔧 Configuration

All configuration is managed via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4` | LLM model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `CHUNK_SIZE` | `1000` | Text chunk size in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `3` | Number of chunks for context |
| `LLM_TEMPERATURE` | `0.1` | LLM temperature (lower = more deterministic) |

## 🧠 Technical Decisions

### Why FAISS?
Facebook AI Similarity Search is extremely fast for vector similarity queries. Used with normalized vectors and inner product for cosine similarity. Persists to disk with JSON metadata — no external server needed.

### Why sentence-transformers (all-MiniLM-L6-v2)?
Fast, lightweight embedding model with good multilingual support. Runs locally without API calls, reducing latency and cost.

### Why Recursive Character Text Splitter?
Preserves semantic meaning by splitting on natural boundaries (paragraphs → sentences → words). The 200-character overlap ensures context continuity across chunks.

### Why pdfplumber?
Superior text extraction compared to PyPDF2, especially for documents with tables, columns, and complex layouts — common in industrial/engineering PDFs.

## 📝 License

MIT
