"""
Router Agent.
Classifies user queries to determine the appropriate retrieval strategy.
"""

import logging
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal["vectorstore", "web_search", "sql_db"] = Field(
        ...,
        description="Given a user question choose to route it to web_search, vectorstore, or sql_db.",
    )

class RouterAgent:
    """
    Agent responsible for routing queries.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model, 
            temperature=0,
            api_key=settings.llm.openai_api_key
        )
        self.structured_llm = self.llm.with_structured_output(RouteQuery)
        
        system = """You are an expert at routing a user question to a vectorstore, web search, or SQL database.
        The vectorstore contains technical reports, engineering specifications, and product manuals.
        Use the vectorstore for questions about specific technical details, parameters, or document content.
        Use web_search for questions about current events, general knowledge, or recent news.
        Use sql_db for questions requiring structured data analysis, counting, or aggregation of metadata.
        """
        
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{question}"),
            ]
        )
        
        self.router = self.prompt | self.structured_llm

    def route(self, question: str) -> str:
        """
        Route the question to the appropriate datasource.
        """
        logger.info(f"Routing question: {question}")
        try:
            result = self.router.invoke({"question": question})
            logger.info(f"Routed to: {result.datasource}")
            return result.datasource
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return "vectorstore" # Default fallback
