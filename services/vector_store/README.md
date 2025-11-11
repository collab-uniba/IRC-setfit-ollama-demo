# Vector Store Service

A microservice that provides semantic search over GitHub issues using vector embeddings, with retrieval and reranking capabilities.

## Features

- **Semantic Search**: Find similar issues using natural language queries
- **Vector Storage**: Persistent storage of GitHub issue embeddings with metadata
- **Reranking**: Refine search results using cross-encoder models for improved relevance
- **CSV Data Loading**: Automatically load and index issues from CSV files on startup
- **Batch Indexing**: Efficiently index multiple issues in batches
- **Label Discovery**: Get labels from similar issues to assist with classification
- **REST API**: FastAPI-based API with OpenAPI documentation

## Architecture

The service uses:
- **ChromaDB**: Vector database for similarity search
- **Sentence Transformers**: `all-mpnet-base-v2` for generating embeddings
- **Cross-Encoder**: `ms-marco-MiniLM-L-6-v2` for result reranking
- **FastAPI**: Web framework with automatic API documentation
- **Docker**: Containerized deployment

## Prerequisites

- Docker and Docker Compose
- Internet access (for downloading ML models on first run)
- At least 2GB RAM for the service

## Quick Start

### Using Docker Compose

1. Ensure you have the `.env` file configured (run `make setup-env` from the project root)

2. Start the service:
```bash
docker compose up -d vector-store
```

3. Check service health:
```bash
curl http://localhost:8001/health
```

4. View API documentation:
Open http://localhost:8001/docs in your browser

### CSV Data Format

Place CSV files in the `data/` directory with the following schema:

```csv
title,body,label,url
"Issue title","Issue description","bug,enhancement","https://github.com/owner/repo/issues/123"
```

**Fields:**
- `title`: Issue title (required)
- `body`: Issue description (optional)
- `label`: Single label or comma-separated multiple labels (optional)
- `url`: GitHub issue URL (required, used to generate unique ID)

The service automatically loads all CSV files from `data/` on first startup.

## API Endpoints

### Health Check
```bash
GET /health
```

Returns service status and statistics:
```json
{
  "status": "healthy",
  "collection": "github_issues",
  "indexed_issues": 1234,
  "embedding_model": "sentence-transformers/all-mpnet-base-v2",
  "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
}
```

### Search Similar Issues
```bash
POST /search
Content-Type: application/json

{
  "query": "Memory leak in training loop",
  "top_k": 10,
  "rerank": true,
  "rerank_top_k": 5,
  "filter_labels": ["bug", "performance"]
}
```

Response:
```json
{
  "results": [
    {
      "id": "abc123",
      "title": "GPU memory not released",
      "body": "After model inference, GPU memory...",
      "labels": ["bug", "memory"],
      "state": "open",
      "score": 0.89,
      "metadata": {
        "url": "https://github.com/..."
      }
    }
  ],
  "query": "Memory leak in training loop",
  "total_results": 5
}
```

### Index Issues
```bash
POST /index
Content-Type: application/json

{
  "issues": [
    {
      "id": "issue-123",
      "title": "Add new feature",
      "body": "Feature description",
      "labels": ["enhancement"],
      "state": "open",
      "metadata": {
        "url": "https://github.com/owner/repo/issues/123"
      }
    }
  ]
}
```

### Get Issue by ID
```bash
GET /issue/{issue_id}
```

### Reindex from CSV
```bash
POST /reindex
```

Clears the collection and reloads all CSV files from the data directory.

### Clear Collection
```bash
DELETE /collection
```

Removes all indexed issues (admin operation).

## Utility Scripts

### Index GitHub Issues from API

Use the provided script to fetch and index issues directly from GitHub:

```bash
cd services/vector_store

# Install dependencies
pip install -r requirements.txt

# Fetch and index issues
python index_github_issues.py \
  --owner pytorch \
  --repo pytorch \
  --token $GITHUB_TOKEN \
  --max-issues 5000 \
  --vector-store-url http://localhost:8001
```

**Options:**
- `--owner`: Repository owner (required)
- `--repo`: Repository name (required)
- `--token`: GitHub personal access token (recommended for rate limits)
- `--max-issues`: Maximum number of issues to fetch (default: 1000)
- `--state`: Filter by state: open, closed, all (default: all)
- `--vector-store-url`: Vector store API URL (default: http://localhost:8001)
- `--batch-size`: Batch size for indexing (default: 50)

## Configuration

Environment variables:

- `VECTOR_STORE_HOST`: Service host (default: 0.0.0.0)
- `VECTOR_STORE_PORT`: Service port (default: 8001)
- `CHROMA_DATA_PATH`: Path for ChromaDB data persistence (default: /data/chroma)
- `DATA_DIR`: Path to CSV data files (default: /app/data)

## Data Persistence

Vector embeddings are persisted in a Docker volume (`vector_store_data`) and survive container restarts. To reset the data:

```bash
# Stop and remove containers and volumes
docker compose down -v

# Restart service (will reload CSV data)
docker compose up -d vector-store
```

## Development

### Running Locally (without Docker)

1. Install dependencies:
```bash
cd services/vector_store
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export CHROMA_DATA_PATH=/tmp/chroma
export DATA_DIR=../../data
```

3. Start the service:
```bash
uvicorn vector_store_api:app --host 0.0.0.0 --port 8001 --reload
```

### Testing CSV Loading

Create a test CSV file in `data/test_issues.csv` and restart the service. Check logs to verify loading:

```bash
docker logs vector-store-service
```

You should see:
```
INFO - Found 1 CSV file(s) to process
INFO - Processing file: test_issues.csv
INFO - Loaded 10 issues from test_issues.csv (0 errors)
INFO - CSV loading complete: 10 issues loaded from 1 file(s) with 0 total errors
```

## Performance

- **Search latency**: < 2 seconds for collections up to 50,000 issues
- **Indexing speed**: ~100-200 issues per second (depending on text length)
- **Memory usage**: ~1-2GB base + ~100MB per 10,000 issues

## Troubleshooting

### Models fail to download

**Symptom**: Service hangs on startup trying to download models from HuggingFace

**Cause**: No internet access or firewall blocking HuggingFace.co

**Solution**: 
- Ensure the container has internet access
- If behind a proxy, configure Docker to use it
- Pre-download models and mount them as a volume

### CSV files not loaded

**Symptom**: Health check shows 0 indexed issues

**Cause**: CSV files missing, malformed, or wrong location

**Solution**:
- Check that CSV files exist in `data/` directory
- Verify CSV schema matches expected format
- Check service logs for parsing errors: `docker logs vector-store-service`

### Search returns no results

**Cause**: Empty collection or query too specific

**Solution**:
- Verify issues are indexed: `curl http://localhost:8001/health`
- Try broader queries
- Use `/reindex` endpoint to reload data

## Integration Example

```python
import requests

# Search for similar issues
response = requests.post(
    "http://localhost:8001/search",
    json={
        "query": "Application crashes on startup",
        "top_k": 5,
        "rerank": True
    }
)

results = response.json()['results']

for issue in results:
    print(f"Similar issue: {issue['title']}")
    print(f"  Labels: {', '.join(issue['labels'])}")
    print(f"  Similarity: {issue['score']:.2f}")
    print(f"  URL: {issue['metadata'].get('url', 'N/A')}")
    print()
```

## Future Enhancements

- Multi-repository support with separate collections
- Incremental indexing via GitHub webhooks
- Real-time CSV file watching
- Advanced filtering (date ranges, authors)
- Multilingual support
- Query expansion and reformulation
- Analytics dashboard

## License

This service is part of the IRC-setfit-ollama-demo project.

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [GitHub REST API - Issues](https://docs.github.com/en/rest/issues/issues)
