"""
Integration tests for the full RAG pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app

client = TestClient(app)

@pytest.fixture
def mock_auth():
    with patch("src.api.auth.AuthHandler.decode_token") as mock:
        mock.return_value = {"sub": "test-user"}
        yield mock

@pytest.fixture
def mock_services():
    with patch("src.api.main.rag_workflow") as mock_rag, \
         patch("src.api.main.ingestion_pipeline") as mock_ingest, \
         patch("src.api.main.sql_client") as mock_sql, \
         patch("src.api.main.snowflake_client") as mock_snow:
             
        # Mock RAG response
        mock_rag.app.ainvoke.return_value = {
            "generation": "Test answer",
            "documents": ["Test doc 1", "Test doc 2"]
        }
        
        # Mock Ingestion response
        mock_ingest.process_document.return_value = {"chunks_count": 10}
        
        yield mock_rag, mock_ingest, mock_sql, mock_snow

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_search_endpoint(mock_auth, mock_services):
    response = client.post(
        "/search",
        json={"query": "test query"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test answer"
    assert len(data["documents"]) == 2
    assert "query_id" in data

def test_ingest_endpoint(mock_auth, mock_services):
    files = {"file": ("test.pdf", b"dummy content", "application/pdf")}
    response = client.post(
        "/ingest",
        files=files,
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_count"] == 10

def test_feedback_endpoint(mock_auth, mock_services):
    response = client.post(
        "/feedback",
        json={"query_id": "123", "score": 5, "comment": "Great!"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
