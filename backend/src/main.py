from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.auth.router import router as auth_router
from src.config import settings
from src.documents.router import router as documents_router
from src.embeddings.service import embedding_service
from src.rag.reranker import reranker_service
from src.rag.router import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: loading embedding model...")
    embedding_service.load()
    if settings.RERANKER_ENABLED:
        logger.info("Loading reranker model...")
        reranker_service.load()
    logger.info("Application ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Internal Knowledge RAG API",
    description="RAG-powered internal knowledge base API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(rag_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
