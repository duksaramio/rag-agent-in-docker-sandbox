import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = settings.qdrant_collection_name

    def ensure_collection(self, vector_size: int = 4096):
        """Ensure Qdrant vector collection exists with specified dimensions."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with vector size {vector_size}...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Collection '{self.collection_name}' created successfully.")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {e}")

    def upsert_chunks(self, points: List[PointStruct]):
        """Upsert a list of PointStruct items into Qdrant."""
        if not points:
            return
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points into Qdrant collection '{self.collection_name}'")

    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search Qdrant collection for vectors nearest to query_vector."""
        self.ensure_collection(vector_size=len(query_vector))
        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )
        hits = []
        for point in res.points:
            hits.append({
                "id": point.id,
                "score": point.score if hasattr(point, 'score') else 0.0,
                "content": point.payload.get("content", ""),
                "document_name": point.payload.get("document_name", ""),
                "chunk_index": point.payload.get("chunk_index", 0),
                "s3_key": point.payload.get("s3_key", "")
            })
        return hits

vector_store = QdrantVectorStore()
