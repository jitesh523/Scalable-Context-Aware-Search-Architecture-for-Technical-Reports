"""
State definition for LangGraph workflow.
"""

from typing import TypedDict, List, Annotated
import operator

class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        question: User's initial question
        generation: The generated answer
        documents: List of retrieved document contexts
        relevance: Flag 'yes' or 'no' indicating document relevance
        web_search: Flag 'yes' or 'no' indicating if web search is needed
        iterations: Number of self-correction loops
    """
    question: str
    generation: str
    documents: List[str]
    relevance: str
    web_search: str
    iterations: int
