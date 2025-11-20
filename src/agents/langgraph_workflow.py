"""
LangGraph Workflow Definition.
Orchestrates the multi-agent RAG process.
"""

import logging
from typing import Dict, Any
from langgraph.graph import END, StateGraph

from src.agents.graph_state import GraphState
from src.agents.router_agent import RouterAgent
from src.agents.retrieval_grader import RetrievalGrader
from src.agents.hallucination_grader import HallucinationGrader
from src.search.hybrid_search import HybridSearchEngine
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

class RAGWorkflow:
    """
    Main RAG workflow using LangGraph.
    """
    
    def __init__(self):
        self.router = RouterAgent()
        self.retrieval_grader = RetrievalGrader()
        self.hallucination_grader = HallucinationGrader()
        self.search_engine = HybridSearchEngine()
        
        # Generator LLM
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model, 
            temperature=0,
            api_key=settings.llm.openai_api_key
        )
        
        # RAG Prompt
        prompt = ChatPromptTemplate.from_template(
            """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
            Question: {question} 
            Context: {context} 
            Answer:"""
        )
        self.rag_chain = prompt | self.llm | StrOutputParser()
        
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(GraphState)

        # Define Nodes
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("generate", self.generate)
        workflow.add_node("transform_query", self.transform_query)
        workflow.add_node("web_search_node", self.web_search_node)

        # Define Edges
        workflow.set_conditional_entry_point(
            self.route_question,
            {
                "web_search": "web_search_node",
                "vectorstore": "retrieve",
            },
        )
        
        workflow.add_edge("web_search_node", "generate")
        workflow.add_edge("retrieve", "grade_documents")
        
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )
        
        workflow.add_edge("transform_query", "retrieve")
        
        workflow.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "not supported": "generate",
                "useful": END,
                "not useful": "transform_query",
            },
        )
        
        return workflow

    # Node Functions
    async def retrieve(self, state):
        """Retrieve documents."""
        logger.info("---RETRIEVE---")
        question = state["question"]
        documents = await self.search_engine.search(question)
        return {"documents": [doc["content"] for doc in documents], "question": question}

    async def generate(self, state):
        """Generate answer."""
        logger.info("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        
        generation = self.rag_chain.invoke({"context": documents, "question": question})
        return {"documents": documents, "question": question, "generation": generation}

    def grade_documents(self, state):
        """Filter relevant documents."""
        logger.info("---CHECK DOCUMENT RELEVANCE---")
        question = state["question"]
        documents = state["documents"]
        
        filtered_docs = []
        web_search = "no"
        
        for d in documents:
            score = self.retrieval_grader.grade(question, d)
            if score == "yes":
                filtered_docs.append(d)
            else:
                continue
                
        if not filtered_docs:
            web_search = "yes"
            
        return {"documents": filtered_docs, "question": question, "web_search": web_search}

    def transform_query(self, state):
        """Transform query for better retrieval."""
        logger.info("---TRANSFORM QUERY---")
        question = state["question"]
        # Simple re-writing logic (can be enhanced with LLM)
        return {"question": question, "documents": state["documents"]}

    def web_search_node(self, state):
        """Web search fallback (placeholder)."""
        logger.info("---WEB SEARCH---")
        question = state["question"]
        return {"documents": ["Web search result placeholder"], "question": question}

    # Conditional Edge Functions
    def route_question(self, state):
        """Route question to web search or vectorstore."""
        logger.info("---ROUTE QUESTION---")
        question = state["question"]
        source = self.router.route(question)
        if source == "web_search":
            return "web_search"
        return "vectorstore"

    def decide_to_generate(self, state):
        """Decide whether to generate or re-retrieve."""
        logger.info("---ASSESS GRADED DOCUMENTS---")
        web_search = state["web_search"]
        
        if web_search == "yes":
            return "transform_query"
        return "generate"

    def grade_generation_v_documents_and_question(self, state):
        """Grade generation for hallucinations and relevance."""
        logger.info("---CHECK HALLUCINATIONS---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]
        
        score = self.hallucination_grader.check_hallucination(str(documents), generation)
        
        if score == "yes":
            logger.info("---DECISION: GENERATION IS GROUNDED---")
            score = self.hallucination_grader.check_answer(question, generation)
            if score == "yes":
                logger.info("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                logger.info("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            logger.info("---DECISION: GENERATION IS NOT GROUNDED---")
            return "not supported"
