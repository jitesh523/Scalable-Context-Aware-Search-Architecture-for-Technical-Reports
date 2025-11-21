from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from config.settings import settings

class Entity(BaseModel):
    name: str = Field(description="Name of the entity")
    type: str = Field(description="Type of the entity (e.g., PERSON, ORG, CONCEPT)")

class Relationship(BaseModel):
    source: str = Field(description="Name of the source entity")
    target: str = Field(description="Name of the target entity")
    type: str = Field(description="Type of relationship (e.g., DEPENDS_ON, AUTHORED_BY)")

class GraphExtraction(BaseModel):
    entities: List[Entity] = Field(description="List of extracted entities")
    relationships: List[Relationship] = Field(description="List of extracted relationships")

class GraphExtractor:
    """
    Extracts knowledge graph elements (entities and relationships) from text.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm.openai_model,
            temperature=0.0,
            api_key=settings.llm.openai_api_key
        )
        
        self.parser = JsonOutputParser(pydantic_object=GraphExtraction)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at extracting knowledge graphs from technical text. "
                       "Extract key entities (Concepts, Technologies, Organizations, Metrics) and their relationships. "
                       "Return the result in JSON format matching the schema.\n{format_instructions}"),
            ("user", "{text}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and relationships from a text chunk.
        """
        if settings.features.mock_mode:
            return {
                "entities": [{"name": "MockEntity", "type": "CONCEPT"}],
                "relationships": []
            }
            
        try:
            return await self.chain.ainvoke({
                "text": text,
                "format_instructions": self.parser.get_format_instructions()
            })
        except Exception as e:
            print(f"Graph extraction failed: {e}")
            return {"entities": [], "relationships": []}
