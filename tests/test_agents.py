"""
Unit tests for LangGraph agents and workflow.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.agents.router_agent import RouterAgent
from src.agents.retrieval_grader import RetrievalGrader
from src.agents.langgraph_workflow import RAGWorkflow

def test_router_agent():
    with patch("src.agents.router_agent.ChatOpenAI") as mock_llm:
        # Create a mock result object
        mock_result = Mock()
        mock_result.datasource = "vectorstore"
        mock_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_result
        
        agent = RouterAgent()
        result = agent.route("What is the maximum temperature?")
        assert result == "vectorstore"

def test_retrieval_grader():
    with patch("src.agents.retrieval_grader.ChatOpenAI") as mock_llm:
        # Create a mock result object
        mock_result = Mock()
        mock_result.binary_score = "yes"
        mock_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_result
        
        agent = RetrievalGrader()
        result = agent.grade("question", "document content")
        assert result == "yes"

@pytest.mark.asyncio
async def test_rag_workflow():
    with patch("src.agents.langgraph_workflow.RouterAgent"), \
         patch("src.agents.langgraph_workflow.RetrievalGrader"), \
         patch("src.agents.langgraph_workflow.HallucinationGrader"), \
         patch("src.agents.langgraph_workflow.HybridSearchEngine") as mock_engine, \
         patch("src.agents.langgraph_workflow.ChatOpenAI"):
             
        # Mock search engine
        mock_engine.return_value.search = AsyncMock(return_value=[{"content": "test doc"}])
        
        workflow = RAGWorkflow()
        assert workflow.app is not None
