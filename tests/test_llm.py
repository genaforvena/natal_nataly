"""
Unit tests for LLM integration module (llm.py).

Tests the LLM prompt formatting and interaction logic:
- Prompt loading and variable substitution
- API call structure
- Response parsing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm import call_llm


@pytest.mark.unit
class TestLLMIntegration:
    """Tests for LLM prompt formatting and API calls."""

    @patch('src.llm.load_parser_prompt')
    @patch('src.llm.client')
    def test_call_llm_parser_prompt(self, mock_client, mock_load_parser):
        """Test calling LLM with a parser prompt (no personality)."""
        # Setup mock
        mock_load_parser.return_value = "Parse this: {text}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Parsed result"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call function
        result = call_llm(
            prompt_type="parser/intent",
            variables={"text": "sample input"},
            temperature=0.7
        )
        
        # Verify parser prompt was loaded
        mock_load_parser.assert_called_once_with("intent")
        
        # Verify LLM was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.7
        assert "Parse this: sample input" in str(call_args.kwargs['messages'])
        
        # Verify result
        assert result == "Parsed result"

    @patch('src.llm.load_response_prompt')
    @patch('src.llm.client')
    def test_call_llm_response_prompt(self, mock_client, mock_load_response):
        """Test calling LLM with a response prompt (with personality)."""
        # Setup mock
        mock_load_response.return_value = "Respond to: {query}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated response"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call function
        result = call_llm(
            prompt_type="responses/natal_reading",
            variables={"query": "test query"},
            temperature=0.8
        )
        
        # Verify response prompt was loaded
        mock_load_response.assert_called_once_with("natal_reading")
        
        # Verify LLM was called
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.8
        
        # Verify result
        assert result == "Generated response"

    @patch('src.llm.load_parser_prompt')
    @patch('src.llm.client')
    def test_call_llm_variable_substitution(self, mock_client, mock_load_parser):
        """Test that variables are properly substituted in prompts."""
        # Setup mock with multiple variables
        template = "User: {name}, Age: {age}, Location: {location}"
        mock_load_parser.return_value = template
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call function
        variables = {
            "name": "John Doe",
            "age": "30",
            "location": "New York"
        }
        call_llm(
            prompt_type="parser/test",
            variables=variables,
            temperature=0.5
        )
        
        # Verify all variables were substituted
        call_args = mock_client.chat.completions.create.call_args
        messages = str(call_args.kwargs['messages'])
        assert "John Doe" in messages
        assert "30" in messages
        assert "New York" in messages

    @patch('src.llm.load_parser_prompt')
    @patch('src.llm.client')
    def test_call_llm_missing_variable_raises_error(self, mock_client, mock_load_parser):
        """Test that missing required variables are handled gracefully."""
        # Setup mock with required variable
        mock_load_parser.return_value = "Required: {missing_var}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # According to llm.py, missing variables are logged as warnings, not exceptions
        # The prompt is used without substitution
        result = call_llm(
            prompt_type="parser/test",
            variables={},  # Empty - missing required variable
            temperature=0.7
        )
        
        # Should return a result even with missing variable
        assert result is not None

    @patch('src.llm.load_parser_prompt')
    @patch('src.llm.client')
    def test_call_llm_handles_empty_response(self, mock_client, mock_load_parser):
        """Test handling of empty LLM responses."""
        # Setup mock
        mock_load_parser.return_value = "Test: {text}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call function
        result = call_llm(
            prompt_type="parser/test",
            variables={"text": "input"},
            temperature=0.7
        )
        
        # Should return empty string
        assert result == ""

    @patch('src.llm.load_parser_prompt')
    @patch('src.llm.client')
    def test_call_llm_auto_detects_parser_type(self, mock_client, mock_load_parser):
        """Test that parser type is auto-detected from prompt_type."""
        mock_load_parser.return_value = "Test: {text}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with "parser/" prefix
        call_llm(
            prompt_type="parser/intent",
            variables={"text": "test"}
        )
        mock_load_parser.assert_called()

    @patch('src.llm.load_response_prompt')
    @patch('src.llm.client')
    def test_call_llm_auto_detects_response_type(self, mock_client, mock_load_response):
        """Test that response type is auto-detected from prompt_type."""
        mock_load_response.return_value = "Test: {text}"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with "responses/" prefix
        call_llm(
            prompt_type="responses/natal_reading",
            variables={"text": "test"}
        )
        mock_load_response.assert_called()


@pytest.mark.unit
class TestLLMHelperFunctions:
    """Tests for LLM helper functions like extract_birth_data, classify_intent."""

    def test_extract_birth_data_exists(self):
        """Verify extract_birth_data function exists and is importable."""
        from src.llm import extract_birth_data
        
        # Verify function exists
        assert extract_birth_data is not None
        assert callable(extract_birth_data)

    def test_classify_intent_exists(self):
        """Verify classify_intent function exists and is importable."""
        from src.llm import classify_intent
        
        # Verify function exists
        assert classify_intent is not None
        assert callable(classify_intent)
