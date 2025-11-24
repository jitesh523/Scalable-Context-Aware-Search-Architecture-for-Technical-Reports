"""
Prompt optimizer for Small Language Models (SLMs).
Provides model-specific templates and context compression.
"""

import logging
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Supported model types"""
    LLAMA3 = "llama3"
    PHI3 = "phi3"
    MISTRAL = "mistral"
    GEMMA = "gemma"
    GENERIC = "generic"


class PromptOptimizer:
    """
    Optimizes prompts for Small Language Models.
    """
    
    # Model-specific prompt templates
    TEMPLATES = {
        ModelType.LLAMA3: {
            "system_start": "<|start_header_id|>system<|end_header_id|>\n\n",
            "system_end": "<|eot_id|>",
            "user_start": "<|start_header_id|>user<|end_header_id|>\n\n",
            "user_end": "<|eot_id|>",
            "assistant_start": "<|start_header_id|>assistant<|end_header_id|>\n\n",
            "assistant_end": "<|eot_id|>",
        },
        ModelType.PHI3: {
            "system_start": "<|system|>\n",
            "system_end": "<|end|>\n",
            "user_start": "