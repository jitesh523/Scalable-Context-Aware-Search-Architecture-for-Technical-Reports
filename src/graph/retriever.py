import logging
from typing import List, Dict, Any
from src.graph.neo4j_client import Neo4jClient
from src.graph.extractor import GraphExtractor

logger = logging.getLogger(__name__)

class GraphRetriever:
    """
    Retrieves context from the Knowledge Graph.
    """
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.extractor = GraphExtractor()
        
    async def retrieve(self, query: str, depth: int = 1) -> List[str]:
        """
        Perform graph retrieval for a user query.
        1. Extract entities from the query.
        2. Find subgraphs for each entity.
        3. Format the results as text context.
        """
        # 1. Extract entities from query to know what to look for
        # We use the same extractor but applied to the query
        extraction = await self.extractor.extract(query)
        entities = [e["name"] for e in extraction.get("entities", [])]
        
        if not entities:
            logger.info("No entities found in query for graph retrieval.")
            return []
            
        logger.info(f"Graph retrieval for entities: {entities}")
        
        # 2. Query Neo4j for each entity
        graph_contexts = []
        for entity in entities:
            subgraph = await self.neo4j.query_subgraph(entity, depth=depth)
            
            # 3. Format results
            for relation in subgraph:
                # Format: "Entity A is RELATED_TO Entity B"
                context = f"{relation['source']} {relation['type']} {relation['target']}"
                graph_contexts.append(context)
                
        # Deduplicate
        return list(set(graph_contexts))
