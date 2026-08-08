# Pydantic AI RAG Agent in Docker Sandbox

An enterprise-grade **Pydantic AI Retrieval-Augmented Generation (RAG) agent** running inside a Docker sandbox environment, integrated with:

- 🎯 **Qdrant Vector Database**: Vector storage and similarity search at `http://localhost:6333`
- 📦 **RustFS / MinIO S3 Object Server**: High-performance S3-compatible document storage holding `gxp-docs` at `http://localhost:9100`
- 🔍 **Langfuse**: LLM observability and tracing platform at `http://localhost:3000`
- 🤖 **Ollama**: Local embedding model server running `qwen3-embedding:8b` at `http://localhost:11434` integrated via **Pydantic AI's native `Embedder`** (`pydantic_ai.embeddings.Embedder`)
- ⚡ **Pydantic AI Agent**: DeepSeek model (`deepseek-chat` / `deepseek-v4-flash`) powered by **Pydantic AI v2.26.0+**.

---

## 🚀 Execution Modes

### Mode 1: Docker Sandboxes CLI (`sbx create` & `sbx run`)

For interactive management inside the **Docker Sandboxes (`sbx`) Dashboard & TUI**:

1. Create the sandbox:
   ```bash
   sbx create --name rag-agent-sbx -p 8000:8000 shell .
   ```

2. Run or attach to the interactive agent sandbox:
   ```bash
   sbx run --name rag-agent-sbx
   ```

3. Launch the RAG agent API server inside the sandbox:
   ```bash
   sbx exec rag-agent-sbx python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. View active sandboxes in the `sbx` dashboard:
   ```bash
   sbx ls
   # or interactive dashboard:
   sbx tui
   ```

---

### Mode 2: Docker Compose (`docker compose up -d`)

If Qdrant (`:6333`), RustFS (`:9100`), Langfuse (`:3000`), and Ollama (`:11434`) are running on your host machine:

1. Configure `.env`:
   ```env
   S3_ENDPOINT_URL=http://localhost:9100
   S3_ACCESS_KEY_ID=RFS8K9X2M4P7Q1W3V6N5
   S3_SECRET_ACCESS_KEY=a7F9mK2vX8pQ5wL1zN4bR0cT6yH3jS8d
   S3_BUCKET_NAME=gxp-docs

   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_COLLECTION_NAME=gxp_documents

   OLLAMA_BASE_URL=http://localhost:11434
   EMBEDDING_MODEL=qwen3-embedding:8b

   OPENAI_BASE_URL=https://api.deepseek.com/v1
   OPENAI_API_KEY=your-deepseek-api-key
   LLM_MODEL=deepseek-chat

   LANGFUSE_PUBLIC_KEY=pk-lf-8d6eb8e5-c24b-4914-a8c7-b9e21ff9290c
   LANGFUSE_SECRET_KEY=sk-lf-b29640ce-6ec0-4298-8a10-5262a727f2bd
   LANGFUSE_HOST=http://localhost:3000
   ```

2. Start the containerized agent sandbox:
   ```bash
   docker compose up -d --build rag-agent
   ```

---

## 📄 Document Seeding & Vector Ingestion

To upload sample GxP Standard Operating Procedures (SOPs) into RustFS S3 (`gxp-docs` bucket) and index vector embeddings into Qdrant using Ollama `qwen3-embedding:8b`:

```bash
python scripts/seed_gxp_docs.py
```

---

## 📡 API Endpoints

The containerized RAG Agent API exposes endpoints on `http://localhost:8000`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System status & service configuration |
| `GET` | `/health` | Connectivity check for S3 (RustFS) & Qdrant DB |
| `GET` | `/documents` | List objects in `gxp-docs` bucket |
| `POST` | `/ingest` | Ingest a single document by S3 key |
| `POST` | `/ingest/all` | Sync all documents in `gxp-docs` into Qdrant |
| `POST` | `/query` | Execute Pydantic AI agent RAG query |

### Example Query Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the gowning requirements and wet contact time for Class B cleanroom sanitization?"
  }'
```

### Example JSON Response
```json
{
  "answer": "Based on SOP-QA-001_Cleanroom_Sanitization.txt, personnel entering Class B areas must wear sterile non-linting coveralls, triple gloves, sterile face mask, safety goggles, and sterile dedicated footwear. Sanitization requires a minimum of 10 minutes wet contact time for all surfaces.",
  "sources": [
    "SOP-QA-001_Cleanroom_Sanitization.txt"
  ],
  "confidence_level": "High"
}
```

---

## 🔍 Observability with Langfuse

- Navigate to **[http://localhost:3000](http://localhost:3000)**.
- Traces show full execution telemetry for:
  - Document ingestion & text chunking
  - Local embedding calls via Pydantic AI's native `Embedder` (`qwen3-embedding:8b`)
  - Qdrant similarity searches (`gxp_documents` collection)
  - S3 raw document fetches from RustFS
  - DeepSeek LLM reasoning & Pydantic AI tool invocations.

---

## 🏗 System Architecture

```
                 +--------------------------+
                 |  RustFS (S3 Object Store)|
                 |    http://localhost:9100 |
                 |     Bucket: gxp-docs     |
                 +------------+-------------+
                              |
                     1. Upload / Fetch
                              v
+-----------------------------+-----------------------------+
|        Pydantic AI Agent (Docker Sandbox / sbx)           |
|                   (app.main / app.agent)                  |
+--------------+------------------------------+-------------+
               |                              |
 2. Generate   |               3. Vector      | 4. Traces
 Embeddings    v               Search         v & Metrics
+--------------+----------+   +---------------+----------+   +------------------------+
|      Ollama Service     |   |    Qdrant Vector DB    |   |    Langfuse Platform   |
|   http://localhost:11434|   | http://localhost:6333|   |  http://localhost:3000 |
| model: qwen3-embedding:8b|  | Collection: gxp_docs  |   |    OpenTelemetry/SDK   |
+-------------------------+   +--------------------------+   +------------------------+
```
