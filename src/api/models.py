"""
Pydantic models for API request and response validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., min_length=1, description="User's search query")
    project_id: Optional[str] = Field(default="default", description="Project context")
    limit: int = Field(default=10, ge=1, le=50, description="Max results")
    enable_web_search: bool = Field(default=False, description="Allow web search fallback")

class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    answer: str = Field(..., description="Generated answer")
    documents: List[Dict[str, Any]] = Field(..., description="Retrieved context documents")
    sources: List[str] = Field(..., description="Source filenames")
    confidence: str = Field(..., description="Confidence assessment")
    query_id: str = Field(..., description="Unique query ID")

class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    query_id: str = Field(..., description="Query ID to provide feedback for")
    score: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(None, description="Optional text feedback")

class IngestResponse(BaseModel):
    """Response model for ingestion."""
    filename: str
    status: str
    chunks_count: int
    message: str
