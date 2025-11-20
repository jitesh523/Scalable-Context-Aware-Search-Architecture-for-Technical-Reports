"""
Advanced chunking strategies for technical documents.
Implements Hierarchical Chunking and Semantic Boundary Detection.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    parent_id: Optional[str] = None
    embedding: Optional[List[float]] = None

class ChunkingStrategy:
    """
    Implements hierarchical and semantic chunking strategies.
    """
    
    def __init__(self):
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        # Parent chunker (larger context)
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunking.parent_chunk_size,
            chunk_overlap=settings.chunking.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Child chunker (precise context)
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunking.chunk_size,
            chunk_overlap=settings.chunking.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.embeddings = OpenAIEmbeddings(
            model=settings.llm.embedding_model,
            api_key=settings.llm.openai_api_key
        )

    def hierarchical_chunking(self, markdown_text: str, base_metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Split text into parent and child chunks based on markdown structure.
        """
        # First split by headers to get logical sections
        header_splits = self.markdown_splitter.split_text(markdown_text)
        
        chunks = []
        
        for split in header_splits:
            # Create Parent Chunk
            parent_content = split.page_content
            parent_metadata = split.metadata.copy()
            parent_metadata.update(base_metadata)
            parent_metadata["type"] = "parent"
            
            parent_id = f"{base_metadata.get('filename', 'doc')}_{hash(parent_content)}"
            
            chunks.append(Chunk(
                content=parent_content,
                metadata=parent_metadata,
                chunk_id=parent_id
            ))
            
            # Create Child Chunks
            child_docs = self.child_splitter.create_documents([parent_content])
            
            for i, child in enumerate(child_docs):
                child_metadata = parent_metadata.copy()
                child_metadata["type"] = "child"
                child_metadata["parent_id"] = parent_id
                child_metadata["chunk_index"] = i
                
                child_id = f"{parent_id}_child_{i}"
                
                chunks.append(Chunk(
                    content=child.page_content,
                    metadata=child_metadata,
                    chunk_id=child_id,
                    parent_id=parent_id
                ))
                
        return chunks

    def semantic_boundary_chunking(self, text: str, threshold: float = 0.6) -> List[str]:
        """
        Split text based on semantic similarity changes between sentences.
        Useful for long narrative sections without headers.
        """
        # Simple sentence splitting (can be improved with NLTK/Spacy)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if not sentences:
            return []
            
        # Get embeddings for all sentences
        embeddings = self.embeddings.embed_documents(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(1, len(sentences)):
            sim = np.dot(embeddings[i-1], embeddings[i])
            
            if sim >= threshold:
                current_chunk.append(sentences[i])
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Generate embeddings for a list of chunks.
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embeddings.aembed_documents(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            
        return chunks
