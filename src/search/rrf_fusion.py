"""
Reciprocal Rank Fusion (RRF) implementation.
Merges results from semantic and lexical search.
"""

from typing import List, Dict, Any
from collections import defaultdict

from config.settings import settings

class RRFFusion:
    """
    Implements Reciprocal Rank Fusion algorithm.
    Score = sum(1 / (k + rank_i))
    """
    
    def __init__(self):
        self.k = settings.hybrid_search.rrf_k_constant
        
    def fuse(self, 
             semantic_results: List[Dict[str, Any]], 
             lexical_results: List[Dict[str, Any]], 
             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fuse results from multiple rank lists.
        """
        # Map to store fused scores and document data
        doc_scores = defaultdict(float)
        doc_data = {}
        
        # Process Semantic Results
        for rank, doc in enumerate(semantic_results):
            doc_id = doc["id"]
            score = 1 / (self.k + rank + 1)
            doc_scores[doc_id] += score * settings.hybrid_search.semantic_weight
            doc_data[doc_id] = doc
            
        # Process Lexical Results
        for rank, doc in enumerate(lexical_results):
            doc_id = doc["id"]
            score = 1 / (self.k + rank + 1)
            doc_scores[doc_id] += score * settings.hybrid_search.lexical_weight
            
            # If doc wasn't in semantic results, add its data
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
                
        # Sort by fused score
        sorted_docs = sorted(
            doc_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Format final results
        final_results = []
        for doc_id, score in sorted_docs[:limit]:
            doc = doc_data[doc_id]
            doc["rrf_score"] = score
            final_results.append(doc)
            
        return final_results
