import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any
from qdrant_client.models import PointStruct
from langfuse import observe

from app.s3_client import s3_service
from app.embeddings import embedding_service
from app.vector_store import vector_store

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Split raw document text into overlapping chunks for semantic retrieval."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += (chunk_size - overlap)
        
    return [c for c in chunks if len(c) > 20]

class IngestionPipeline:
    @observe(name="rag_document_ingestion")
    def ingest_document(self, object_name: str) -> Dict[str, Any]:
        """Fetch a document from RustFS S3, chunk it, embed via Ollama, and store vectors in Qdrant."""
        logger.info(f"Starting ingestion workflow for S3 object '{object_name}'...")
        
        # 1. Fetch content from RustFS
        content = s3_service.get_document_content(object_name)
        if not content:
            logger.warning(f"No content found for document '{object_name}'")
            return {"status": "error", "message": "Document empty or not found"}
        
        # 2. Chunk text
        chunks = chunk_text(content)
        logger.info(f"Split document '{object_name}' into {len(chunks)} chunks.")
        
        if not chunks:
            return {"status": "skipped", "message": "No valid text chunks generated"}

        # 3. Generate Embeddings via Ollama (qwen3-embedding:8b)
        embeddings = embedding_service.embed_documents(chunks)
        vector_dim = len(embeddings[0]) if embeddings else 4096
        
        # Ensure collection exists
        vector_store.ensure_collection(vector_size=vector_dim)
        
        # 4. Prepare Qdrant Points
        points = []
        namespace_uuid = uuid.NAMESPACE_DNS
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(namespace_uuid, f"{object_name}_chunk_{idx}"))
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_name": object_name,
                    "s3_key": object_name,
                    "chunk_index": idx,
                    "content": chunk,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            ))

        # 5. Save to Qdrant
        vector_store.upsert_chunks(points)
        
        return {
            "status": "success",
            "document_name": object_name,
            "chunks_ingested": len(points),
            "vector_dimension": vector_dim
        }

    @observe(name="rag_sync_all_bucket_docs")
    def sync_all_documents(self) -> List[Dict[str, Any]]:
        """Sync all documents in RustFS gxp-docs bucket into Qdrant vector database."""
        docs = s3_service.list_documents()
        results = []
        for doc in docs:
            res = self.ingest_document(doc["key"])
            results.append(res)
        return results

ingestion_pipeline = IngestionPipeline()
