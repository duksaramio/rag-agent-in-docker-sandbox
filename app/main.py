import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.config import settings
from app.s3_client import s3_service
from app.ingestion import ingestion_pipeline
from app.agent import agent_runner, GxPResponse
from app.telemetry import init_telemetry

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("rag-agent")

# Initialize Langfuse observability
init_telemetry()

app = FastAPI(
    title="Pydantic AI RAG Agent Sandbox API",
    description="GxP Document RAG agent running in Docker sandbox with Qdrant, RustFS, Ollama, and Langfuse.",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    prompt: str

class IngestRequest(BaseModel):
    document_name: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Pydantic AI RAG Agent",
        "vector_db": "Qdrant",
        "storage": "RustFS (S3)",
        "observability": "Langfuse",
        "embedding_model": settings.embedding_model,
        "llm_model": settings.llm_model
    }

@app.get("/health")
def health_check():
    health = {
        "s3_storage": "unknown",
        "qdrant_db": "unknown"
    }
    try:
        s3_service.list_documents()
        health["s3_storage"] = "ok"
    except Exception as e:
        health["s3_storage"] = f"error: {str(e)}"

    try:
        from app.vector_store import vector_store
        vector_store.client.get_collections()
        health["qdrant_db"] = "ok"
    except Exception as e:
        health["qdrant_db"] = f"error: {str(e)}"

    return health

@app.get("/documents")
def list_documents():
    """List all documents currently in the RustFS gxp-docs bucket."""
    return {"bucket": settings.s3_bucket_name, "documents": s3_service.list_documents()}

@app.post("/ingest")
def ingest_single_document(request: IngestRequest):
    """Ingest a specific document from RustFS S3 into Qdrant vector DB."""
    try:
        res = ingestion_pipeline.ingest_document(request.document_name)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/all")
def ingest_all_documents():
    """Ingest all documents in RustFS gxp-docs bucket into Qdrant."""
    try:
        results = ingestion_pipeline.sync_all_documents()
        return {"status": "completed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=GxPResponse)
def query_agent(request: QueryRequest):
    """Execute Pydantic AI RAG agent query with DeepSeek V4 Flash and Qdrant retrieval."""
    try:
        response = agent_runner.run_query(request.prompt)
        return response
    except Exception as e:
        logger.error(f"Error executing agent query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
