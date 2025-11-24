"""
LocalAI client as an alternative to Ollama.
Provides OpenAI-compatible API for local models.
"""

import logging
from typing import Optional, AsyncGenerator, Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LocalAIClient:
    """
    Client for LocalAI server (OpenAI-compatible).
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        model: str = "llama3",
        api_key: str = "not-needed",
        timeout: int = 120
    ):
        self.base_url = base_url
        self.model = model
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
        
        logger.info(f"Initialized LocalAI client: {self.base_url}, model={self.model}")
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            model: Model name (overrides default)
            system: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        """
        model_name = model or self.model
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LocalAI generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream text completion.
        
        Args:
            prompt: Input prompt
            model: Model name
            system: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Yields:
            Generated text chunks
        """
        model_name = model or self.model
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"LocalAI streaming failed: {e}")
            raise
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            Assistant's response
        """
        model_name = model or self.model
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LocalAI chat failed: {e}")
            raise
    
    async def list_models(self) -> list[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if LocalAI server is healthy.
        
        Returns:
            True if server is reachable
        """
        try:
            await self.client.models.list()
            return True
        except:
            return False
