import base64
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from config.settings import settings

logger = logging.getLogger(__name__)

class VLMClient:
    """
    Vision Language Model Client for image captioning.
    Uses GPT-4o to generate descriptive captions for images extracted from PDFs.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o", # Use multimodal model
            api_key=settings.llm.openai_api_key,
            max_tokens=300
        )
        
    async def generate_caption(self, image_base64: str) -> str:
        """
        Generate a description for an image.
        """
        if settings.features.mock_mode:
            return "A mock description of the image containing charts and data."
            
        try:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Describe this image in detail, focusing on any data, charts, or text visible. Provide a concise summary suitable for search indexing."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ]
            )
            
            response = await self.llm.ainvoke([message])
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate caption: {e}")
            return "Error generating caption."
