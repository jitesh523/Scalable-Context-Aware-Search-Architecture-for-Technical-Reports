"""
Model router for intelligent selection between cloud and local LLMs.
"""

import logging
from typing import Optional, Literal, AsyncGenerator
from enum import Enum

from openai import AsyncOpenAI
from .ollama_client import OllamaClient
from .localai_client import LocalAIClient
from config.settings import settings

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCALAI = "localai"


class ModelRouter:
    """
    Routes requests to appropriate LLM provider based on:
    - Privacy mode setting
    - Query complexity
    - Model availability
    - Performance requirements
    """
    
    def __init__(
        self,
        default_provider: ModelProvider = ModelProvider.OPENAI,
        privacy_mode: bool = False,
        ollama_base_url: str = "http://localhost:11434",
        localai_base_url: str = "http://localhost:8080/v1"
    ):
        self.default_provider = default_provider
        self.privacy_mode = privacy_mode
        
        # Initialize clients
        self.openai_client = AsyncOpenAI(api_key=settings.llm.openai_api_key)
        self.ollama_client = OllamaClient(base_url=ollama_base_url)
        self.localai_client = LocalAIClient(base_url=localai_base_url)
        
        # Provider availability cache
        self._provider_health = {
            ModelProvider.OPENAI: True,  # Assume OpenAI is always available
            ModelProvider.OLLAMA: False,
            ModelProvider.LOCALAI: False
        }
        
        logger.info(f"Initialized ModelRouter: default={default_provider}, privacy_mode={privacy_mode}")
    
    async def initialize(self):
        """Check health of all providers"""
        self._provider_health[ModelProvider.OLLAMA] = await self.ollama_client.health_check()
        self._provider_health[ModelProvider.LOCALAI] = await self.localai_client.health_check()
        
        logger.info(f"Provider health: {self._provider_health}")
    
    def select_provider(
        self,
        query: str,
        force_provider: Optional[ModelProvider] = None,
        privacy_required: Optional[bool] = None
    ) -> ModelProvider:
        """
        Select the best provider for a query.
        
        Args:
            query: User query
            force_provider: Force specific provider
            privacy_required: Override privacy mode setting
        
        Returns:
            Selected ModelProvider
        """
        # Force provider if specified
        if force_provider:
            if self._provider_health.get(force_provider, False):
                return force_provider
            logger.warning(f"Forced provider {force_provider} not available, falling back")
        
        # Privacy mode: prefer local models
        privacy_mode = privacy_required if privacy_required is not None else self.privacy_mode
        
        if privacy_mode:
            # Try local providers first
            if self._provider_health[ModelProvider.OLLAMA]:
                logger.info("Selected Ollama for privacy mode")
                return ModelProvider.OLLAMA
            elif self._provider_health[ModelProvider.LOCALAI]:
                logger.info("Selected LocalAI for privacy mode")
                return ModelProvider.LOCALAI
            else:
                logger.warning("Privacy mode enabled but no local providers available, using OpenAI")
                return ModelProvider.OPENAI
        
        # Analyze query complexity
        complexity = self._estimate_complexity(query)
        
        # For complex queries, prefer cloud models
        if complexity > 0.7:
            logger.info(f"High complexity query ({complexity:.2f}), using OpenAI")
            return ModelProvider.OPENAI
        
        # For simple queries, use local if available
        if self._provider_health[ModelProvider.OLLAMA]:
            logger.info(f"Low complexity query ({complexity:.2f}), using Ollama")
            return ModelProvider.OLLAMA
        
        # Default fallback
        return self.default_provider
    
    def _estimate_complexity(self, query: str) -> float:
        """
        Estimate query complexity (0.0 to 1.0).
        
        Simple heuristic based on:
        - Query length
        - Presence of technical terms
        - Question complexity
        """
        # Length factor
        length_score = min(len(query) / 500, 1.0)
        
        # Technical terms
        technical_terms = [
            "algorithm", "implementation", "architecture", "optimization",
            "performance", "scalability", "distributed", "machine learning",
            "neural network", "deep learning", "database", "query"
        ]
        tech_score = sum(1 for term in technical_terms if term in query.lower()) / len(technical_terms)
        
        # Question complexity (multi-part questions)
        question_marks = query.count("?")
        multi_part_score = min(question_marks / 3, 1.0)
        
        # Weighted average
        complexity = (
            0.3 * length_score +
            0.5 * tech_score +
            0.2 * multi_part_score
        )
        
        return complexity
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        provider: Optional[ModelProvider] = None,
        **kwargs
    ) -> str:
        """
        Generate text using selected provider.
        
        Args:
            prompt: Input prompt
            system: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            provider: Force specific provider
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        """
        selected_provider = provider or self.select_provider(prompt)
        
        try:
            if selected_provider == ModelProvider.OPENAI:
                return await self._generate_openai(prompt, system, temperature, max_tokens, **kwargs)
            elif selected_provider == ModelProvider.OLLAMA:
                return await self.ollama_client.generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs)
            elif selected_provider == ModelProvider.LOCALAI:
                return await self.localai_client.generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs)
            else:
                raise ValueError(f"Unknown provider: {selected_provider}")
                
        except Exception as e:
            logger.error(f"Generation failed with {selected_provider}: {e}")
            
            # Fallback to OpenAI if local provider fails
            if selected_provider != ModelProvider.OPENAI:
                logger.info("Falling back to OpenAI")
                return await self._generate_openai(prompt, system, temperature, max_tokens, **kwargs)
            raise
    
    async def _generate_openai(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> str:
        """Generate using OpenAI"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=settings.llm.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or settings.llm.max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        provider: Optional[ModelProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream text generation.
        
        Args:
            prompt: Input prompt
            system: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            provider: Force specific provider
            **kwargs: Additional parameters
        
        Yields:
            Generated text chunks
        """
        selected_provider = provider or self.select_provider(prompt)
        
        try:
            if selected_provider == ModelProvider.OPENAI:
                async for chunk in self._generate_stream_openai(prompt, system, temperature, max_tokens, **kwargs):
                    yield chunk
            elif selected_provider == ModelProvider.OLLAMA:
                async for chunk in self.ollama_client.generate_stream(prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs):
                    yield chunk
            elif selected_provider == ModelProvider.LOCALAI:
                async for chunk in self.localai_client.generate_stream(prompt, system=system, temperature=temperature, max_tokens=max_tokens, **kwargs):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Streaming failed with {selected_provider}: {e}")
            raise
    
    async def _generate_stream_openai(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream using OpenAI"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        stream = await self.openai_client.chat.completions.create(
            model=settings.llm.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or settings.llm.max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
