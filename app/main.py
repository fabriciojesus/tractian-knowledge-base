"""
FastAPI application entry point.
Configures the application with CORS, logging, and routes.
"""

import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.config import settings

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    level="INFO",
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="DEBUG",
)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown tasks."""
    logger.info("=" * 60)
    logger.info("Tractian Knowledge Base RAG API starting up")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Chunk Size: {settings.chunk_size}")
    logger.info(f"Chunk Overlap: {settings.chunk_overlap}")
    logger.info(f"Top-K Results: {settings.top_k_results}")
    logger.info("=" * 60)
    yield


# Create FastAPI application
app = FastAPI(
    title="Tractian Knowledge Base - RAG API",
    description=(
        "A Retrieval-Augmented Generation (RAG) system that allows users "
        "to upload PDF documents and ask questions about their contents. "
        "Built for the Tractian ML Engineering challenge."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details and response time."""
    start_time = time.time()
    response = await call_next(request)
    elapsed = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} ({elapsed:.3f}s)"
    )
    return response


# Include API routes
app.include_router(router)
