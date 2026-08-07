import httpx
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        base_url = settings.ollama_base_url.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        self.base_url = base_url
        self.model_name = settings.embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string using Ollama local model."""
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])
            if not embedding:
                raise ValueError("Received empty embedding vector from Ollama")
            return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of strings."""
        embeddings = []
        for idx, text in enumerate(texts):
            logger.info(f"Embedding chunk {idx+1}/{len(texts)} using {self.model_name}...")
            vector = self.embed_text(text)
            embeddings.append(vector)
        return embeddings

embedding_service = EmbeddingService()
