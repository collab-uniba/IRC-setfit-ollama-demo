# Vector Store Service - Quick Reference

## Service URLs

**Local Development:**
- Vector Store API: http://localhost:8001
- API Documentation: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

**Docker (internal):**
- http://vector-store:8001

## Common Commands

### Start Service
```bash
docker compose up -d vector-store
```

### Check Logs
```bash
docker logs vector-store-service -f
```

### Stop Service
```bash
docker compose down vector-store
```

### Rebuild Service
```bash
docker compose build vector-store --no-cache
docker compose up -d vector-store
```

## Quick API Examples

### Search for Similar Issues
```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "memory leak in training",
    "top_k": 5,
    "rerank": true
  }'
```

### Check Health
```bash
curl http://localhost:8001/health
```

### Index New Issues
```bash
curl -X POST http://localhost:8001/index \
  -H "Content-Type: application/json" \
  -d '{
    "issues": [{
      "id": "test-123",
      "title": "Test Issue",
      "body": "This is a test issue",
      "labels": ["bug"],
      "state": "open",
      "metadata": {"url": "https://github.com/test/repo/issues/123"}
    }]
  }'
```

### Reindex from CSV
```bash
curl -X POST http://localhost:8001/reindex
```

## CSV Data Format

Place CSV files in `data/` directory:

```csv
title,body,label,url
"Issue Title","Issue body text","bug,enhancement","https://github.com/owner/repo/issues/123"
```

## Troubleshooting

### Service won't start
- Check Docker logs: `docker logs vector-store-service`
- Ensure port 8001 is not in use
- Verify internet access for model downloads

### No issues indexed
- Check CSV files exist in `data/` directory
- Verify CSV format matches schema
- Check logs for parsing errors

### Search returns empty results
- Verify collection has issues: `curl http://localhost:8001/health`
- Try broader search queries
- Use `/reindex` to reload data

## Model Downloads

On first startup, the service downloads:
- Embedding model: `all-mpnet-base-v2` (~400MB)
- Reranker model: `ms-marco-MiniLM-L-6-v2` (~90MB)

This takes approximately 5 minutes with a good internet connection.

## Data Persistence

Vector data persists in Docker volume `vector_store_data`:
- Survives container restarts
- Cleared with `docker compose down -v`
- Automatically reloads CSV on empty collection

## Performance

- Search: <2s for 50,000 issues
- Indexing: ~100-200 issues/second
- Memory: ~1-2GB base + ~100MB per 10K issues

## Integration

```python
import requests

VECTOR_STORE_URL = "http://localhost:8001"

def find_similar_issues(query: str, top_k: int = 5):
    response = requests.post(
        f"{VECTOR_STORE_URL}/search",
        json={"query": query, "top_k": top_k, "rerank": True}
    )
    return response.json()["results"]

# Example usage
similar = find_similar_issues("application crashes on startup")
for issue in similar:
    print(f"{issue['title']} (score: {issue['score']:.2f})")
```
