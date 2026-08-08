import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic_ai.embeddings import Embedder
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        base_url = settings.ollama_base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        
        self.model_name = settings.embedding_model
        provider = OpenAIProvider(
            base_url=base_url,
            api_key="ollama"
        )
        embedding_model = OpenAIEmbeddingModel(
            model_name=self.model_name,
            provider=provider
        )
        self.embedder = Embedder(embedding_model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string using Pydantic AI Embedder."""
        logger.info(f"Embedding query using Pydantic AI Embedder ({self.model_name})...")
        result = self.embedder.embed_query_sync(text)
        return result.embeddings[0] if result.embeddings else []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of strings using Pydantic AI Embedder."""
        if not texts:
            return []
        logger.info(f"Embedding batch of {len(texts)} chunks using Pydantic AI Embedder ({self.model_name})...")
        result = self.embedder.embed_documents_sync(texts)
        return result.embeddings

embedding_service = EmbeddingService()
