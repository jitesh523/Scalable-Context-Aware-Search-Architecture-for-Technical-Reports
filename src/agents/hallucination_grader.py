"""
Hallucination Grader Agent.
Checks if the generated answer is grounded in the documents and addresses the question.
"""

import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

class GradeHallucinations(BaseModel):
    """Binary score for hallucination check in generation."""
    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

class HallucinationGrader:
    """
    Agent responsible for checking hallucinations and answer quality.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model, 
            temperature=0,
            api_key=settings.llm.openai_api_key
        )
        
        # Hallucination Checker
        self.hallucination_llm = self.llm.with_structured_output(GradeHallucinations)
        hallucination_system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
        Give a binary score 'yes' or 'no'. 'yes' means that the answer is grounded in / supported by the set of facts."""
        
        self.hallucination_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", hallucination_system),
                ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
            ]
        )
        self.hallucination_grader = self.hallucination_prompt | self.hallucination_llm
        
        # Answer Checker
        self.answer_llm = self.llm.with_structured_output(GradeAnswer)
        answer_system = """You are a grader assessing whether an answer addresses / resolves a question. \n 
        Give a binary score 'yes' or 'no'. 'yes' means that the answer resolves the question."""
        
        self.answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", answer_system),
                ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
            ]
        )
        self.answer_grader = self.answer_prompt | self.answer_llm

    def check_hallucination(self, documents: str, generation: str) -> str:
        """Check if generation is grounded in documents."""
        try:
            score = self.hallucination_grader.invoke({"documents": documents, "generation": generation})
            return score.binary_score
        except Exception as e:
            logger.error(f"Hallucination check failed: {e}")
            return "yes"

    def check_answer(self, question: str, generation: str) -> str:
        """Check if generation answers the question."""
        try:
            score = self.answer_grader.invoke({"question": question, "generation": generation})
            return score.binary_score
        except Exception as e:
            logger.error(f"Answer check failed: {e}")
            return "yes"
