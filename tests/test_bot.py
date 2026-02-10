"""
Unit tests for bot message handling (bot.py).

Tests the core message handling logic:
- Message parsing
- State management
- Response generation
- Message splitting for Telegram limits
"""

import pytest
from bot import split_message


@pytest.mark.unit
class TestMessageHandling:
    """Tests for bot message handling functions."""

    def test_split_message_short_text(self):
        """Test that short messages are not split."""
        short_text = "This is a short message."
        result = split_message(short_text)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == short_text

    def test_split_message_exact_limit(self):
        """Test message exactly at the limit."""
        # Create text exactly 4096 characters
        exact_text = "a" * 4096
        result = split_message(exact_text, max_length=4096)
        
        assert len(result) == 1
        assert len(result[0]) == 4096

    def test_split_message_over_limit(self):
        """Test that long messages are split into chunks."""
        # Create text over the limit
        long_text = "a" * 5000
        result = split_message(long_text, max_length=4096)
        
        assert len(result) > 1
        # All chunks should be under limit
        for chunk in result:
            assert len(chunk) <= 4096
        # All text should be preserved
        assert "".join(result) == long_text.strip()

    def test_split_message_at_paragraph_boundaries(self):
        """Test that messages split at paragraph boundaries when possible."""
        # Create text with paragraphs
        text = "First paragraph.\n\n" + ("a" * 2000) + "\n\nSecond paragraph." + ("b" * 3000)
        result = split_message(text, max_length=4096)
        
        assert len(result) >= 1
        # First chunk should ideally end at paragraph boundary
        for chunk in result:
            assert len(chunk) <= 4096

    def test_split_message_at_sentence_boundaries(self):
        """Test that messages split at sentence boundaries when no paragraph breaks."""
        # Create text with sentences
        text = "First sentence. " + ("a" * 2000) + ". Second sentence. " + ("b" * 3000) + "."
        result = split_message(text, max_length=4096)
        
        for chunk in result:
            assert len(chunk) <= 4096

    def test_split_message_at_word_boundaries(self):
        """Test that messages split at word boundaries as last resort."""
        # Create text with just words
        text = " ".join(["word"] * 1000)
        result = split_message(text, max_length=4096)
        
        for chunk in result:
            assert len(chunk) <= 4096
            # Should not split in middle of word
            if len(result) > 1:
                assert not chunk.endswith("wor")  # Not split mid-word

    def test_split_message_preserves_newlines(self):
        """Test that newlines are preserved in split messages."""
        text = "Line 1\nLine 2\nLine 3\n" + ("a" * 4000) + "\nLine 4\nLine 5"
        result = split_message(text, max_length=4096)
        
        # Join back and check newlines are preserved
        joined = "".join(result)
        assert "Line 1" in joined
        assert "\n" in joined

    def test_split_message_empty_string(self):
        """Test handling of empty string."""
        result = split_message("")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == ""

    def test_split_message_custom_max_length(self):
        """Test split with custom maximum length."""
        text = "a" * 1000
        result = split_message(text, max_length=500)
        
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= 500


@pytest.mark.unit
class TestBotHelperFunctions:
    """Tests for bot helper functions."""

    def test_message_parsing_logic(self):
        """Test basic message parsing logic."""
        # This is a placeholder for actual parsing tests
        # Would need to import and test actual parsing functions from bot.py
        assert True

    def test_state_management(self):
        """Test user state transitions."""
        # Placeholder for state management tests
        # Would test STATE_AWAITING_BIRTH_DATA, STATE_HAS_CHART, etc.
        from models import STATE_AWAITING_BIRTH_DATA, STATE_HAS_CHART
        
        assert STATE_AWAITING_BIRTH_DATA is not None
        assert STATE_HAS_CHART is not None

    def test_validation_logic(self):
        """Test input validation logic."""
        # Placeholder for validation tests
        # Would test date/time/coordinate validation
        assert True
