"""
Vector Store API Service

Provides semantic search over GitHub issues using vector embeddings,
with retrieval and reranking capabilities.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder
import logging
import os
from pathlib import Path
from load_csv_data import load_issues_from_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
chroma_client = None
collection = None
embedding_model = None
reranker_model = None

# Configuration
CHROMA_DATA_PATH = os.getenv("CHROMA_DATA_PATH", "/data/chroma")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
COLLECTION_NAME = "github_issues"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# Pydantic models
class IssueMetadata(BaseModel):
    """Metadata for an issue"""
    number: Optional[int] = None
    url: Optional[str] = None
    user: Optional[str] = None
    comments: Optional[int] = None


class Issue(BaseModel):
    """Issue data model"""
    id: str
    title: str
    body: str
    labels: List[str] = Field(default_factory=list)
    state: str = "open"
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexRequest(BaseModel):
    """Request model for indexing issues"""
    issues: List[Issue]


class SearchRequest(BaseModel):
    """Request model for searching similar issues"""
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    rerank: bool = True
    rerank_top_k: int = Field(default=5, ge=1, le=50)
    filter_labels: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    title: str
    body: str
    labels: List[str]
    state: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response model for search results"""
    results: List[SearchResult]
    query: str
    total_results: int


def initialize_models():
    """Initialize embedding and reranker models"""
    global embedding_model, reranker_model
    
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    logger.info(f"Loading reranker model: {RERANKER_MODEL_NAME}")
    reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
    
    logger.info("Models loaded successfully")


def initialize_chroma():
    """Initialize ChromaDB client and collection"""
    global chroma_client, collection
    
    # Ensure data directory exists
    Path(CHROMA_DATA_PATH).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing ChromaDB at {CHROMA_DATA_PATH}")
    
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_DATA_PATH,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Get or create collection
    try:
        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "GitHub issues vector store"}
        )
        logger.info(f"Collection '{COLLECTION_NAME}' initialized with {collection.count()} items")
    except Exception as e:
        logger.error(f"Error initializing collection: {str(e)}")
        raise


def load_csv_data_on_startup():
    """Load CSV data if collection is empty"""
    global collection
    
    if collection.count() == 0:
        logger.info("Collection is empty, loading data from CSV files...")
        
        issues = load_issues_from_csv(DATA_DIR)
        
        if not issues:
            logger.warning("No issues loaded from CSV files")
            return
        
        # Index issues in batches
        batch_size = 100
        total_indexed = 0
        
        for i in range(0, len(issues), batch_size):
            batch = issues[i:i + batch_size]
            
            try:
                index_issues_batch(batch)
                total_indexed += len(batch)
                logger.info(f"Indexed {total_indexed}/{len(issues)} issues")
            except Exception as e:
                logger.error(f"Error indexing batch: {str(e)}")
        
        logger.info(f"CSV loading complete: {total_indexed} issues indexed")
    else:
        logger.info(f"Collection already contains {collection.count()} issues, skipping CSV load")


def index_issues_batch(issues: List[Dict]):
    """Index a batch of issues into ChromaDB"""
    global collection, embedding_model
    
    if not issues:
        return
    
    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []
    
    for issue in issues:
        # Create searchable text from title and body
        doc_text = f"{issue['title']}\n\n{issue['body']}"
        
        # Prepare metadata (ChromaDB requires flat dict with string/int/float values)
        metadata = {
            'title': issue['title'],
            'state': issue['state'],
            'labels': ','.join(issue['labels']),  # Store as comma-separated string
        }
        
        # Add optional metadata fields
        if issue.get('created_at'):
            metadata['created_at'] = issue['created_at']
        
        if issue.get('metadata'):
            for key, value in issue['metadata'].items():
                if isinstance(value, (str, int, float)):
                    metadata[key] = value
        
        ids.append(issue['id'])
        documents.append(doc_text)
        metadatas.append(metadata)
    
    # Generate embeddings
    embeddings = embedding_model.encode(documents, convert_to_tensor=False).tolist()
    
    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting Vector Store API...")
    
    try:
        initialize_models()
        initialize_chroma()
        load_csv_data_on_startup()
        logger.info("Vector Store API ready")
        yield
    finally:
        # Shutdown
        logger.info("Shutting down Vector Store API...")


# Initialize FastAPI app
app = FastAPI(
    title="Vector Store API",
    description="Semantic search for GitHub issues using vector embeddings",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint with collection statistics"""
    try:
        count = collection.count() if collection else 0
        return {
            "status": "healthy",
            "collection": COLLECTION_NAME,
            "indexed_issues": count,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "reranker_model": RERANKER_MODEL_NAME
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index")
async def index_issues(request: IndexRequest):
    """Index new issues into the vector store"""
    try:
        issues_data = [issue.model_dump() for issue in request.issues]
        index_issues_batch(issues_data)
        
        return {
            "status": "success",
            "indexed": len(request.issues),
            "total_issues": collection.count()
        }
    except Exception as e:
        logger.error(f"Error indexing issues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_similar_issues(request: SearchRequest):
    """Search for similar issues using semantic search"""
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode(
            request.query,
            convert_to_tensor=False
        ).tolist()
        
        # Retrieve candidates from ChromaDB
        # Request more results for reranking if enabled
        n_results = request.top_k if not request.rerank else max(request.top_k * 3, 20)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count())
        )
        
        # Parse results
        candidates = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                
                # Parse labels back from comma-separated string
                labels_str = metadata.get('labels', '')
                labels = [l.strip() for l in labels_str.split(',') if l.strip()]
                
                # Apply label filter if specified
                if request.filter_labels:
                    if not any(label in labels for label in request.filter_labels):
                        continue
                
                candidate = {
                    'id': results['ids'][0][i],
                    'title': metadata.get('title', ''),
                    'body': results['documents'][0][i].split('\n\n', 1)[1] if '\n\n' in results['documents'][0][i] else '',
                    'labels': labels,
                    'state': metadata.get('state', 'open'),
                    'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': {k: v for k, v in metadata.items() if k not in ['title', 'state', 'labels']}
                }
                candidates.append(candidate)
        
        # Rerank if requested
        if request.rerank and candidates:
            # Prepare pairs for reranking
            pairs = [[request.query, f"{c['title']}\n\n{c['body']}"] for c in candidates]
            
            # Get reranking scores
            rerank_scores = reranker_model.predict(pairs, convert_to_tensor=False)
            
            # Update scores and sort
            for i, score in enumerate(rerank_scores):
                candidates[i]['score'] = float(score)
            
            candidates.sort(key=lambda x: x['score'], reverse=True)
            candidates = candidates[:request.rerank_top_k]
        else:
            candidates = candidates[:request.top_k]
        
        return SearchResponse(
            results=candidates,
            query=request.query,
            total_results=len(candidates)
        )
        
    except Exception as e:
        logger.error(f"Error searching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/issue/{issue_id}")
async def get_issue(issue_id: str):
    """Get a specific issue by ID"""
    try:
        result = collection.get(ids=[issue_id])
        
        if not result['ids']:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        metadata = result['metadatas'][0]
        labels_str = metadata.get('labels', '')
        labels = [l.strip() for l in labels_str.split(',') if l.strip()]
        
        return {
            'id': result['ids'][0],
            'title': metadata.get('title', ''),
            'body': result['documents'][0].split('\n\n', 1)[1] if '\n\n' in result['documents'][0] else '',
            'labels': labels,
            'state': metadata.get('state', 'open'),
            'metadata': {k: v for k, v in metadata.items() if k not in ['title', 'state', 'labels']}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving issue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collection")
async def clear_collection():
    """Clear all data from the collection (admin operation)"""
    try:
        global collection, chroma_client
        
        # Delete and recreate collection
        chroma_client.delete_collection(name=COLLECTION_NAME)
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "GitHub issues vector store"}
        )
        
        logger.info("Collection cleared successfully")
        
        return {
            "status": "success",
            "message": "Collection cleared",
            "indexed_issues": 0
        }
    except Exception as e:
        logger.error(f"Error clearing collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reindex")
async def reindex_from_csv():
    """Clear collection and reload all CSV files from data directory"""
    try:
        global collection, chroma_client
        
        logger.info("Starting reindex operation...")
        
        # Clear existing collection
        chroma_client.delete_collection(name=COLLECTION_NAME)
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "GitHub issues vector store"}
        )
        
        # Load and index CSV data
        issues = load_issues_from_csv(DATA_DIR)
        
        if not issues:
            return {
                "status": "success",
                "message": "No issues found in CSV files",
                "indexed_issues": 0
            }
        
        # Index in batches
        batch_size = 100
        total_indexed = 0
        
        for i in range(0, len(issues), batch_size):
            batch = issues[i:i + batch_size]
            index_issues_batch(batch)
            total_indexed += len(batch)
            logger.info(f"Reindexed {total_indexed}/{len(issues)} issues")
        
        logger.info(f"Reindex complete: {total_indexed} issues indexed")
        
        return {
            "status": "success",
            "message": "Reindex completed successfully",
            "indexed_issues": total_indexed
        }
        
    except Exception as e:
        logger.error(f"Error during reindex: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
