from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # S3 / RustFS Storage Config
    s3_endpoint_url: str = "http://localhost:9100"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "gxp-docs"
    s3_region: str = "us-east-1"

    # Qdrant Vector Database Config
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "gxp_documents"

    # Ollama Local Embeddings Config
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "qwen3-embedding:8b"

    # Pydantic AI LLM Config
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_api_key: str = "sk-dummy-key"
    llm_model: str = "deepseek-v4-flash"

    # Langfuse Observability Config
    langfuse_public_key: str = "pk-lf-1234567890"
    langfuse_secret_key: str = "sk-lf-1234567890"
    langfuse_host: str = "http://localhost:3000"

settings = Settings()
