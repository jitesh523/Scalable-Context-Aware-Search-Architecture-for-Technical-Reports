from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from config.settings import settings

class QueryExpander:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model,
            temperature=0.2,
            api_key=settings.llm.openai_api_key
        )
        self.parser = CommaSeparatedListOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that generates synonyms and related technical terms for search queries. "
                       "Generate 3-5 synonyms or related terms for the user's query. "
                       "Return ONLY a comma-separated list of terms. Do not include the original query."),
            ("user", "{query}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def expand_query(self, query: str) -> List[str]:
        """
        Expand a search query with synonyms and related terms.
        
        Args:
            query: The original user query
            
        Returns:
            List of expanded terms including the original query
        """
        if not settings.features.enable_query_expansion:
            return [query]
            
        try:
            # Generate synonyms
            synonyms = await self.chain.ainvoke({"query": query})
            
            # Combine original query with synonyms
            expanded_terms = [query] + [term.strip() for term in synonyms if term.strip()]
            
            # Deduplicate while preserving order
            return list(dict.fromkeys(expanded_terms))
            
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return [query]
