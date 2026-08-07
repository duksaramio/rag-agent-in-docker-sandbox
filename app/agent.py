import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from langfuse.decorators import observe

from app.config import settings
from app.embeddings import embedding_service
from app.vector_store import vector_store
from app.s3_client import s3_service

logger = logging.getLogger(__name__)

# Initialize OpenAI-compatible DeepSeek V4 Flash Model
deepseek_model = OpenAIModel(
    model_name=settings.llm_model,
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key
)

# Output Schema
class GxPResponse(BaseModel):
    answer: str = Field(description="Comprehensive and accurate answer based strictly on retrieved GxP documentation.")
    sources: List[str] = Field(default_factory=list, description="List of GxP document keys or SOP names cited.")
    confidence_level: str = Field(description="Confidence rating: High, Medium, or Low based on evidence.")

# System Prompt
SYSTEM_PROMPT = """You are an expert GxP Quality Assurance & Regulatory Compliance AI Agent.
Your role is to assist quality engineers, auditors, and compliance officers by answering queries using official GxP standard operating procedures (SOPs), deviation logs, and validation protocols.

Guidelines:
1. Always search the GxP knowledge base before answering technical or compliance questions.
2. Ground your responses strictly on retrieved facts from Qdrant and RustFS S3 storage.
3. Explicitly cite the document names / SOP references used in your answer.
4. If the retrieved documents do not contain enough information to answer confidently, explicitly state what is missing.
"""

gxp_agent = Agent(
    model=deepseek_model,
    result_type=GxPResponse,
    system_prompt=SYSTEM_PROMPT
)

@gxp_agent.tool
def search_gxp_knowledge_base(ctx: RunContext, query: str) -> str:
    """Search Qdrant vector database for relevant GxP quality document chunks.
    
    Args:
        query: Semantic search text (e.g. 'cleanroom sanitization protocol' or 'deviation handling SOP')
    """
    logger.info(f"Tool search_gxp_knowledge_base called with query: '{query}'")
    
    # 1. Embed query with Ollama local model (qwen3-embedding:8b)
    query_vector = embedding_service.embed_text(query)
    
    # 2. Search Qdrant
    hits = vector_store.search_similar(query_vector=query_vector, top_k=5)
    
    if not hits:
        return "No relevant GxP document chunks found in Qdrant vector database."
    
    # 3. Format context
    formatted_chunks = []
    for idx, hit in enumerate(hits, 1):
        formatted_chunks.append(
            f"--- Snippet {idx} [Doc: {hit['document_name']}, Score: {hit['score']:.4f}] ---\n"
            f"{hit['content']}\n"
        )
    
    return "\n".join(formatted_chunks)

@gxp_agent.tool
def fetch_s3_document_details(ctx: RunContext, document_name: str) -> str:
    """Fetch full document text directly from RustFS S3 bucket 'gxp-docs'.
    
    Args:
        document_name: S3 key/filename of the document (e.g. 'SOP-QA-001.txt')
    """
    logger.info(f"Tool fetch_s3_document_details called for object '{document_name}'")
    try:
        content = s3_service.get_document_content(document_name)
        return f"Content of document '{document_name}':\n\n{content[:4000]}"
    except Exception as e:
        return f"Error reading document '{document_name}' from RustFS S3: {str(e)}"

class AgentRunner:
    @observe(name="pydantic_ai_agent_run")
    def run_query(self, user_prompt: str) -> GxPResponse:
        """Run Pydantic AI agent against user prompt with Langfuse observability."""
        logger.info(f"Executing Pydantic AI Agent for query: '{user_prompt}'")
        result = gxp_agent.run_sync(user_prompt)
        return result.data

agent_runner = AgentRunner()
