"""
Retrieval Grader Agent.
Evaluates the relevance of retrieved documents to the user's question.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

class RetrievalGrader:
    """
    Agent responsible for grading retrieved documents.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model, 
            temperature=0,
            api_key=settings.llm.openai_api_key
        )
        self.structured_llm = self.llm.with_structured_output(GradeDocuments)
        
        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )
        
        self.grader = self.prompt | self.structured_llm

    def grade(self, question: str, document: str) -> str:
        """
        Grade the relevance of a document.
        """
        try:
            score = self.grader.invoke({"question": question, "document": document})
            return score.binary_score
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            return "yes" # Default to keeping document
