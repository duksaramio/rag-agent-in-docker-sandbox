#!/usr/bin/env bash
set -e

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MODEL_NAME="${EMBEDDING_MODEL:-qwen3-embedding:8b}"

echo "Waiting for Ollama service at ${OLLAMA_HOST} to be ready..."
until curl -s "${OLLAMA_HOST}/api/tags" > /dev/null; do
    sleep 2
done

echo "Pulling embedding model '${MODEL_NAME}' into Ollama..."
curl -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${MODEL_NAME}\"}"

echo "Ollama model '${MODEL_NAME}' successfully initialized!"
