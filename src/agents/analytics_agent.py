import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.python_executor import PythonExecutor
from config.settings import settings

logger = logging.getLogger(__name__)

class AnalyticsAgent:
    """
    Agent that generates and executes Python code for data analysis.
    """
    
    def __init__(self):
        self.executor = PythonExecutor()
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model,
            temperature=0.0,
            api_key=settings.llm.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Python data analyst. Generate Python code to answer the user's question. "
                       "Use pandas, numpy, or other standard libraries as needed. "
                       "The code should print the results. "
                       "Return ONLY the Python code, no explanations."),
            ("user", "Question: {question}\nContext: {context}\n\nGenerate Python code:")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
        
    async def analyze(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Generate and execute Python code to answer a data analysis question.
        
        Args:
            question: The analysis question
            context: Optional context (e.g., data description)
            
        Returns:
            Dict with 'code', 'output', 'error', 'artifacts'
        """
        if settings.features.mock_mode:
            return {
                "code": "print('Mock code')",
                "output": "Mock analysis result",
                "error": None,
                "artifacts": []
            }
        
        try:
            # Generate code
            code = await self.chain.ainvoke({
                "question": question,
                "context": context or "No additional context provided."
            })
            
            # Clean code (remove markdown formatting if present)
            code = self._clean_code(code)
            
            # Execute code
            result = self.executor.execute(code)
            
            return {
                "code": code,
                **result
            }
            
        except Exception as e:
            logger.error(f"Analytics agent failed: {e}")
            return {
                "code": "",
                "output": "",
                "error": str(e),
                "artifacts": []
            }
    
    def _clean_code(self, code: str) -> str:
        """Remove markdown code fences if present."""
        code = code.strip()
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        if code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        return code
