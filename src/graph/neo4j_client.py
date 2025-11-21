import logging
from typing import List, Dict, Any
from neo4j import GraphDatabase, AsyncGraphDatabase
from config.settings import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Client for Neo4j Graph Database.
    Handles entity and relationship storage and retrieval.
    """
    
    def __init__(self):
        # Use default credentials for now (should be in settings)
        self.uri = "bolt://localhost:7687"
        self.user = "neo4j"
        self.password = "password"
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    async def close(self):
        await self.driver.close()
        
    async def verify_connectivity(self):
        """Check if Neo4j is reachable."""
        try:
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    async def add_entity(self, label: str, name: str, properties: Dict[str, Any] = None):
        """
        Add a node to the graph.
        """
        if settings.features.mock_mode:
            logger.info(f"[MOCK] Added entity: {label}:{name}")
            return
            
        query = (
            f"MERGE (n:{label} {{name: $name}}) "
            "SET n += $properties "
            "RETURN n"
        )
        async with self.driver.session() as session:
            await session.run(query, name=name, properties=properties or {})

    async def add_relationship(self, source_name: str, target_name: str, relation_type: str):
        """
        Add a relationship between two nodes.
        """
        if settings.features.mock_mode:
            logger.info(f"[MOCK] Added relation: {source_name} -[{relation_type}]-> {target_name}")
            return

        query = (
            "MATCH (a {name: $source_name}), (b {name: $target_name}) "
            f"MERGE (a)-[r:{relation_type}]->(b) "
            "RETURN r"
        )
        async with self.driver.session() as session:
            await session.run(query, source_name=source_name, target_name=target_name)
            
    async def query_subgraph(self, entity_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieve connected nodes for a given entity.
        """
        if settings.features.mock_mode:
            return [{"source": entity_name, "target": "RelatedEntity", "type": "RELATED_TO"}]
            
        query = (
            "MATCH (n {name: $name})-[r*1..%d]-(m) "
            "RETURN n, r, m"
        ) % depth
        
        results = []
        async with self.driver.session() as session:
            result = await session.run(query, name=entity_name)
            async for record in result:
                results.append({
                    "source": record["n"]["name"],
                    "target": record["m"]["name"],
                    "type": type(record["r"]).__name__ # Simplified
                })
        return results
