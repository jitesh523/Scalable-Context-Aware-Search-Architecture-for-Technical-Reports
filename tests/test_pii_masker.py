"""
Tests for PII masking functionality.
"""

import pytest
from src.privacy.pii_masker import PIIMasker, PIIType, MaskingStrategy


class TestPIIMasker:
    """Test PII detection and masking"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.masker = PIIMasker(strategy=MaskingStrategy.REPLACE)
    
    def test_email_detection(self):
        """Test email address detection"""
        text = "Contact me at john.doe@example.com for more info"
        entities = self.masker.detect_pii(text)
        
        assert len(entities) > 0
        assert any(e.type == PIIType.EMAIL for e in entities)
        assert any("john.doe@example.com" in e.text for e in entities)
    
    def test_phone_detection(self):
        """Test phone number detection"""
        text = "Call me at 555-123-4567 or (555) 987-6543"
        entities = self.masker.detect_pii(text)
        
        phone_entities = [e for e in entities if e.type == PIIType.PHONE]
        assert len(phone_entities) >= 1
    
    def test_ssn_detection(self):
        """Test SSN detection"""
        text = "My SSN is 123-45-6789"
        entities = self.masker.detect_pii(text)
        
        ssn_entities = [e for e in entities if e.type == PIIType.SSN]
        assert len(ssn_entities) == 1
    
    def test_credit_card_detection(self):
        """Test credit card detection"""
        text = "Card number: 4532-1488-0343-6467"
        entities = self.masker.detect_pii(text)
        
        cc_entities = [e for e in entities if e.type == PIIType.CREDIT_CARD]
        assert len(cc_entities) >= 1
    
    def test_masking_replace_strategy(self):
        """Test REPLACE masking strategy"""
        text = "Email me at test@example.com"
        masked_text, entities = self.masker.mask_text(text)
        
        assert "[EMAIL]" in masked_text
        assert "test@example.com" not in masked_text
    
    def test_masking_redact_strategy(self):
        """Test REDACT masking strategy"""
        masker = PIIMasker(strategy=MaskingStrategy.REDACT)
        text = "Email: test@example.com, Phone: 555-1234"
        masked_text, entities = masker.mask_text(text)
        
        assert "[REDACTED]" in masked_text
        assert "test@example.com" not in masked_text
    
    def test_masking_partial_strategy(self):
        """Test PARTIAL masking strategy"""
        masker = PIIMasker(strategy=MaskingStrategy.PARTIAL)
        text = "Card: 4532148803436467"
        masked_text, entities = masker.mask_text(text)
        
        # Should show last 4 digits
        assert "6467" in masked_text
        assert "4532148803436467" not in masked_text
    
    def test_unmask_text(self):
        """Test unmasking functionality"""
        text = "Contact: test@example.com"
        masked_text, entities = self.masker.mask_text(text)
        unmasked_text = self.masker.unmask_text(masked_text, entities)
        
        assert unmasked_text == text
    
    def test_query_response_masking(self):
        """Test masking both query and response"""
        query = "What is the status of order for john@example.com?"
        response = "The order for john@example.com is being processed."
        
        masked_query, masked_response, entities = self.masker.mask_query_response(query, response)
        
        assert "[EMAIL]" in masked_query
        assert "[EMAIL]" in masked_response
        assert "john@example.com" not in masked_query
        assert "john@example.com" not in masked_response
    
    def test_no_pii_in_text(self):
        """Test text with no PII"""
        text = "This is a normal sentence without any sensitive information."
        entities = self.masker.detect_pii(text)
        
        assert len(entities) == 0
    
    def test_multiple_pii_types(self):
        """Test detection of multiple PII types"""
        text = "Contact John at john@example.com or call 555-1234. SSN: 123-45-6789"
        entities = self.masker.detect_pii(text)
        
        types = {e.type for e in entities}
        assert PIIType.EMAIL in types
        assert PIIType.PHONE in types
        assert PIIType.SSN in types


@pytest.mark.asyncio
class TestPIIMaskerWithNER:
    """Test PII masking with NER model"""
    
    def test_person_name_detection(self):
        """Test person name detection with NER"""
        masker = PIIMasker(use_ner=True)
        
        if masker.ner_model is None:
            pytest.skip("spaCy model not available")
        
        text = "John Smith works at Acme Corporation"
        entities = masker.detect_pii(text)
        
        # Should detect person name
        person_entities = [e for e in entities if e.type == PIIType.PERSON_NAME]
        assert len(person_entities) > 0
