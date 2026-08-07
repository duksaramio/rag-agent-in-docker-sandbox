# Pydantic AI RAG Agent in Docker Sandbox

An enterprise-grade **Pydantic AI Retrieval-Augmented Generation (RAG) agent** running inside a Docker sandbox environment, integrated with:

- 🎯 **Qdrant Vector Database**: Vector storage and similarity retrieval at `http://localhost:6333`
- 📦 **RustFS / MinIO S3 Object Server**: High-performance S3-compatible document storage holding `gxp-docs` at `http://localhost:9100`
- 🔍 **Langfuse**: LLM observability and tracing platform at `http://localhost:3000`
- 🤖 **Ollama**: Local embedding model server running `qwen3-embedding:8b` at `http://localhost:11434`
- ⚡ **Pydantic AI Agent**: DeepSeek V4 Flash (`deepseek-v4-flash`) via OpenAI compatible API format.

---

## 🚀 Execution Modes

### Mode A: Run Agent Sandbox with Existing Host Containers (Recommended if services are already running)

If Qdrant, RustFS, Langfuse, or Ollama are already running on your host machine:

1. Update `.env` to point to `host.docker.internal`:
   ```env
   S3_ENDPOINT_URL=http://host.docker.internal:9100
   QDRANT_HOST=host.docker.internal
   QDRANT_PORT=6333
   LANGFUSE_HOST=http://host.docker.internal:3000
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   OPENAI_BASE_URL=https://api.deepseek.com/v1
   OPENAI_API_KEY=your-deepseek-api-key
   ```

2. Build and start **only the agent sandbox container**:
   ```bash
   docker compose up -d rag-agent
   ```

---

### Mode B: Spin Up the Full Stack (Isolated Docker Sandbox)

To launch all infrastructure services in Docker from scratch:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Start all containers (Qdrant, RustFS, Langfuse DB/Redis/Server, Ollama, and RAG Agent):
   ```bash
   docker compose up -d --build
   ```
3. Pull the Ollama embedding model:
   ```bash
   docker exec -it ollama-embedding-server ollama pull qwen3-embedding:8b
   ```

---

## 📄 Document Seeding & Ingestion

Run the seed script to upload sample GxP standard operating procedures (SOPs) into RustFS (`gxp-docs` bucket) and ingest vectors into Qdrant:
```bash
python scripts/seed_gxp_docs.py
```

---

## 📡 API Endpoints

The RAG Agent API runs on `http://localhost:8000`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System status and service metadata |
| `GET` | `/health` | Check S3 (RustFS) & Qdrant connectivity |
| `GET` | `/documents` | List objects in `gxp-docs` bucket |
| `POST` | `/ingest` | Ingest a single document by S3 object key |
| `POST` | `/ingest/all` | Sync all documents in `gxp-docs` into Qdrant |
| `POST` | `/query` | Execute Pydantic AI agent query with DeepSeek V4 Flash |

### Example Query via cURL
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the gowning requirements and wet contact time for Class B cleanroom sanitization?"
  }'
```

---

## 🔍 Observability with Langfuse

1. Open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.
2. Sign in with initialized admin credentials:
   - **Email**: `admin@gxp.local`
   - **Password**: `adminpassword123`
3. View real-time traces for document ingestion, Ollama embeddings, Qdrant vector searches, and Pydantic AI DeepSeek generation calls!

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
|                     Pydantic AI RAG Agent                 |
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
