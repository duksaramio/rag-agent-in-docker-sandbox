import os
import logging
from langfuse import Langfuse, observe
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Langfuse client
langfuse_client = None

def init_telemetry():
    global langfuse_client
    try:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

        langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host
        )
        logger.info(f"Langfuse observability initialized pointing to {settings.langfuse_host}")
        return langfuse_client
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse telemetry: {e}")
        return None

def get_langfuse():
    global langfuse_client
    if langfuse_client is None:
        langfuse_client = init_telemetry()
    return langfuse_client
