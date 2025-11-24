"""
PII (Personally Identifiable Information) detection and masking.
Uses regex patterns and NER models for comprehensive PII detection.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of PII"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    URL = "url"
    PERSON_NAME = "person_name"
    ADDRESS = "address"
    DATE = "date"
    CUSTOM = "custom"


class MaskingStrategy(str, Enum):
    """PII masking strategies"""
    REPLACE = "replace"  # Replace with placeholder
    REDACT = "redact"    # Replace with [REDACTED]
    HASH = "hash"        # Replace with hash
    PARTIAL = "partial"  # Show partial (e.g., last 4 digits)


@dataclass
class PIIEntity:
    """Detected PII entity"""
    type: PIIType
    text: str
    start: int
    end: int
    confidence: float = 1.0
    replacement: Optional[str] = None


class PIIMasker:
    """
    PII detection and masking service.
    """
    
    # Regex patterns for common PII
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        PIIType.SSN: r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b',
        PIIType.CREDIT_CARD: r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        PIIType.URL: r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
    }
    
    # Default replacements
    REPLACEMENTS = {
        PIIType.EMAIL: "[EMAIL]",
        PIIType.PHONE: "[PHONE]",
        PIIType.SSN: "[SSN]",
        PIIType.CREDIT_CARD: "[CREDIT_CARD]",
        PIIType.IP_ADDRESS: "[IP_ADDRESS]",
        PIIType.URL: "[URL]",
        PIIType.PERSON_NAME: "[NAME]",
        PIIType.ADDRESS: "[ADDRESS]",
        PIIType.DATE: "[DATE]"
    }
    
    def __init__(
        self,
        strategy: MaskingStrategy = MaskingStrategy.REPLACE,
        use_ner: bool = False,
        sensitivity: float = 0.7
    ):
        """
        Initialize PII masker.
        
        Args:
            strategy: Masking strategy to use
            use_ner: Whether to use NER model for person names
            sensitivity: Confidence threshold for NER (0.0 to 1.0)
        """
        self.strategy = strategy
        self.use_ner = use_ner
        self.sensitivity = sensitivity
        self.ner_model = None
        
        if use_ner:
            self._init_ner_model()
        
        logger.info(f"Initialized PIIMasker: strategy={strategy}, use_ner={use_ner}")
    
    def _init_ner_model(self):
        """Initialize spaCy NER model"""
        try:
            import spacy
            try:
                self.ner_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Download with: python -m spacy download en_core_web_sm")
                self.ner_model = None
        except ImportError:
            logger.warning("spaCy not installed. Install with: pip install spacy")
            self.ner_model = None
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text.
        
        Args:
            text: Input text
        
        Returns:
            List of detected PII entities
        """
        entities = []
        
        # Regex-based detection
        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text):
                entities.append(PIIEntity(
                    type=pii_type,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0
                ))
        
        # NER-based detection for person names
        if self.use_ner and self.ner_model:
            ner_entities = self._detect_with_ner(text)
            entities.extend(ner_entities)
        
        # Sort by start position
        entities.sort(key=lambda e: e.start)
        
        # Remove overlapping entities (keep higher confidence)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _detect_with_ner(self, text: str) -> List[PIIEntity]:
        """Detect PII using NER model"""
        entities = []
        
        doc = self.ner_model(text)
        
        for ent in doc.ents:
            # Detect person names
            if ent.label_ == "PERSON":
                entities.append(PIIEntity(
                    type=PIIType.PERSON_NAME,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.8  # NER confidence is typically lower
                ))
            
            # Detect locations (addresses)
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                entities.append(PIIEntity(
                    type=PIIType.ADDRESS,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.7
                ))
            
            # Detect dates
            elif ent.label_ == "DATE":
                entities.append(PIIEntity(
                    type=PIIType.DATE,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.9
                ))
        
        return entities
    
    def _remove_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove overlapping entities, keeping higher confidence ones"""
        if not entities:
            return []
        
        result = [entities[0]]
        
        for entity in entities[1:]:
            last = result[-1]
            
            # Check for overlap
            if entity.start < last.end:
                # Keep entity with higher confidence
                if entity.confidence > last.confidence:
                    result[-1] = entity
            else:
                result.append(entity)
        
        return result
    
    def mask_text(
        self,
        text: str,
        entities: Optional[List[PIIEntity]] = None
    ) -> Tuple[str, List[PIIEntity]]:
        """
        Mask PII in text.
        
        Args:
            text: Input text
            entities: Pre-detected entities (optional)
        
        Returns:
            Tuple of (masked_text, detected_entities)
        """
        if entities is None:
            entities = self.detect_pii(text)
        
        if not entities:
            return text, []
        
        # Apply masking strategy
        masked_text = text
        offset = 0
        
        for entity in entities:
            replacement = self._get_replacement(entity)
            entity.replacement = replacement
            
            # Adjust positions based on previous replacements
            start = entity.start + offset
            end = entity.end + offset
            
            masked_text = masked_text[:start] + replacement + masked_text[end:]
            
            # Update offset
            offset += len(replacement) - (entity.end - entity.start)
        
        return masked_text, entities
    
    def _get_replacement(self, entity: PIIEntity) -> str:
        """Get replacement text based on strategy"""
        if self.strategy == MaskingStrategy.REPLACE:
            return self.REPLACEMENTS.get(entity.type, "[REDACTED]")
        
        elif self.strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"
        
        elif self.strategy == MaskingStrategy.HASH:
            import hashlib
            hash_value = hashlib.md5(entity.text.encode()).hexdigest()[:8]
            return f"[{entity.type.value.upper()}_{hash_value}]"
        
        elif self.strategy == MaskingStrategy.PARTIAL:
            # Show last 4 characters for some types
            if entity.type in [PIIType.PHONE, PIIType.CREDIT_CARD]:
                if len(entity.text) > 4:
                    return "****" + entity.text[-4:]
            return self.REPLACEMENTS.get(entity.type, "[REDACTED]")
        
        return "[REDACTED]"
    
    def unmask_text(
        self,
        masked_text: str,
        entities: List[PIIEntity]
    ) -> str:
        """
        Unmask text by restoring original PII.
        
        Args:
            masked_text: Masked text
            entities: Entities with original text
        
        Returns:
            Original text
        """
        unmasked_text = masked_text
        
        # Reverse order to maintain positions
        for entity in reversed(entities):
            if entity.replacement:
                unmasked_text = unmasked_text.replace(
                    entity.replacement,
                    entity.text,
                    1  # Replace only first occurrence
                )
        
        return unmasked_text
    
    def mask_query_response(
        self,
        query: str,
        response: str
    ) -> Tuple[str, str, List[PIIEntity]]:
        """
        Mask PII in both query and response.
        
        Args:
            query: User query
            response: LLM response
        
        Returns:
            Tuple of (masked_query, masked_response, entities)
        """
        # Detect PII in query
        query_entities = self.detect_pii(query)
        masked_query, _ = self.mask_text(query, query_entities)
        
        # For response, we need to be careful not to mask legitimate content
        # Only mask if the same PII appears in the response
        response_entities = []
        for entity in query_entities:
            if entity.text in response:
                # Find all occurrences in response
                for match in re.finditer(re.escape(entity.text), response):
                    response_entities.append(PIIEntity(
                        type=entity.type,
                        text=entity.text,
                        start=match.start(),
                        end=match.end(),
                        confidence=entity.confidence
                    ))
        
        masked_response, _ = self.mask_text(response, response_entities)
        
        return masked_query, masked_response, query_entities
