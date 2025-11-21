"""
Main FastAPI application.
Exposes endpoints for search, ingestion, and feedback.
"""

import logging
import uuid
import time
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.api.models import SearchRequest, SearchResponse, FeedbackRequest, IngestResponse
from src.api.auth import AuthHandler
from src.agents.langgraph_workflow import RAGWorkflow
from src.ingestion.pipeline import IngestionPipeline
from src.database.cloudsql_client import CloudSQLClient
from src.database.snowflake_client import SnowflakeClient
from src.observability.otel_instrumentation import setup_telemetry
from src.observability.metrics import QUERY_COUNTER, QUERY_LATENCY, FEEDBACK_SCORE

from config.settings import settings

# Setup logging
logging.basicConfig(level=settings.observability.log_level)
logger = logging.getLogger(__name__)

# Initialize services
rag_workflow = None
ingestion_pipeline = None
sql_client = None
snowflake_client = None
auth_handler = AuthHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    global rag_workflow, ingestion_pipeline, sql_client, snowflake_client
    
    # Startup
    logger.info("Starting RAG Service...")
    setup_telemetry()
    
    rag_workflow = RAGWorkflow()
    ingestion_pipeline = IngestionPipeline()
    sql_client = CloudSQLClient()
    snowflake_client = SnowflakeClient()
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Service...")
    # Close connections if needed

app = FastAPI(
    title="Scalable Context-Aware Search API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

from src.cache.decorators import cache_response

@app.post("/search", response_model=SearchResponse)
@cache_response(ttl=settings.redis.ttl, prefix="search")
async def search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(auth_handler.get_current_user)
):
    """
    Perform hybrid search with agentic orchestration.
    """
    start_time = time.time()
    QUERY_COUNTER.add(1)
    query_id = str(uuid.uuid4())
    
    try:
        # Execute RAG Workflow
        result = await rag_workflow.app.ainvoke({
            "question": request.query,
            "iterations": 0
        })
        
        generation = result.get("generation", "No answer generated.")
        documents = result.get("documents", [])
        
        # Calculate latency
        latency = time.time() - start_time
        QUERY_LATENCY.record(latency)
        
        # Background: Save interaction to memory
        background_tasks.add_task(
            sql_client.save_interaction,
            user_id=user_id,
            query=request.query,
            response=generation,
            embedding=[] # TODO: Get embedding from workflow
        )
        
        return SearchResponse(
            answer=generation,
            documents=[{"content": d} for d in documents], # Simplify for response
            sources=[], # Extract sources from metadata
            confidence="high", # Placeholder
            query_id=query_id
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    user_id: str = Depends(auth_handler.get_current_user)
):
    """
    Upload and ingest a PDF document.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    try:
        # Save temp file
        temp_path = f"{settings.storage.temp_upload_path}/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Process document
        result = await ingestion_pipeline.process_document(temp_path)
        
        return IngestResponse(
            filename=file.filename,
            status="success",
            chunks_count=result["chunks_count"],
            message="Document ingested successfully"
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    user_id: str = Depends(auth_handler.get_current_user)
):
    """
    Submit user feedback for quality monitoring.
    """
    try:
        FEEDBACK_SCORE.observe(request.score)
        
        snowflake_client.log_feedback({
            "query_id": request.query_id,
            "user_id": user_id,
            "feedback_score": request.score,
            "correction_comment": request.comment,
            # Other fields would be populated from logs/cache
            "prompt_text": "", 
            "retrieved_doc_ids": [],
            "response_text": ""
        })
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
