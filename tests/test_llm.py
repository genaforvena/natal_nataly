"""
Unit tests for LLM integration module (llm.py).

Tests the LLM prompt formatting and interaction logic:
- Prompt loading and variable substitution
- API call structure
- Response parsing
"""

import json
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

    @patch('src.llm.load_personality')
    @patch('src.llm.load_response_prompt')
    @patch('src.llm.client')
    def test_call_llm_response_prompt(self, mock_client, mock_load_response, mock_load_personality):
        """Test calling LLM with a response prompt (with personality)."""
        # Setup mock
        mock_load_response.return_value = "Respond to: {query}"
        mock_load_personality.return_value = "CORE PERSONALITY"
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated response"))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call function
        result = call_llm(
            prompt_type="responses/natal_reading",
            variables={"query": "test query"},
            temperature=0.8
        )
        
        # Verify response prompt was loaded without personality (it's added to system message)
        mock_load_response.assert_called_once_with("natal_reading", include_personality=False)

        # Verify personality was loaded
        mock_load_personality.assert_called_once()
        
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

    @patch('src.llm.call_llm')
    def test_extract_birth_data_with_conversation_history(self, mock_call_llm):
        """Test that extract_birth_data passes conversation history to call_llm."""
        from src.llm import extract_birth_data
        import json
        
        # Setup mock to return valid birth data JSON
        mock_call_llm.return_value = json.dumps({
            "dob": "1989-11-13",
            "time": "05:16",
            "lat": 56.3269,
            "lng": 44.0059,
            "missing_fields": []
        })
        
        # Create conversation history
        conversation_history = [
            {"role": "user", "content": "13 Ноября 1989 года, Нижний Новгород"},
            {"role": "assistant", "content": "Спасибо! Мне нужно ещё узнать точное время вашего рождения..."}
        ]
        
        # Call function with conversation history
        result = extract_birth_data("05:16", conversation_history=conversation_history)
        
        # Verify call_llm was called
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args
        
        # Verify conversation_context was included in variables
        variables = call_args.kwargs['variables']
        assert 'conversation_context' in variables
        assert '13 Ноября 1989 года' in variables['conversation_context']
        
        # Verify result structure
        assert result['dob'] == "1989-11-13"
        assert result['time'] == "05:16"
        assert result['lat'] == 56.3269
        assert result['lng'] == 44.0059
        assert result['missing_fields'] == []

    @patch('src.llm.call_llm')
    def test_extract_birth_data_without_conversation_history(self, mock_call_llm):
        """Test that extract_birth_data works without conversation history."""
        from src.llm import extract_birth_data
        import json
        
        # Setup mock
        mock_call_llm.return_value = json.dumps({
            "dob": "1990-05-15",
            "time": "14:30",
            "lat": 40.7128,
            "lng": -74.0060,
            "missing_fields": []
        })
        
        # Call function without conversation history
        result = extract_birth_data("May 15, 1990 at 2:30 PM in New York")
        
        # Verify call_llm was called
        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args
        
        # Verify conversation_context is empty string when no history
        variables = call_args.kwargs['variables']
        assert 'conversation_context' in variables
        assert variables['conversation_context'] == ""
        
        # Verify result
        assert result['dob'] == "1990-05-15"
        assert result['time'] == "14:30"


@pytest.mark.unit
class TestEnhancedIntentParsing:
    """Tests for enhanced intent parsing with normalization."""

    @patch('src.llm.call_llm')
    def test_classify_intent_returns_normalized_output(self, mock_call_llm):
        """Test that classify_intent returns original and normalized prompts."""
        from src.llm import classify_intent
        
        # Mock LLM response with new structure
        mock_call_llm.return_value = json.dumps({
            "intent": "provide_birth_data",
            "confidence": 0.98,
            "original_prompt": "Я родился 15 мая 1990 года в 14:30 в Москве",
            "normalized_prompt": "Дата рождения: 15 мая 1990, время: 14:30, место: Москва"
        })
        
        # Call function
        result = classify_intent("Я родился 15 мая 1990 года в 14:30 в Москве")
        
        # Verify structure
        assert result['intent'] == "provide_birth_data"
        assert result['confidence'] == 0.98
        assert 'original_prompt' in result
        assert 'normalized_prompt' in result
        assert result['original_prompt'] == "Я родился 15 мая 1990 года в 14:30 в Москве"
        assert "Дата рождения: 15 мая 1990" in result['normalized_prompt']

    @patch('src.llm.call_llm')
    def test_classify_intent_change_profile(self, mock_call_llm):
        """Test that change_profile intent is properly classified."""
        from src.llm import classify_intent
        
        # Mock LLM response for change_profile intent
        mock_call_llm.return_value = json.dumps({
            "intent": "change_profile",
            "confidence": 0.96,
            "original_prompt": "Переключись на профиль Маши",
            "normalized_prompt": "Сменить активный профиль на профиль Маши"
        })
        
        # Call function
        result = classify_intent("Переключись на профиль Маши")
        
        # Verify intent
        assert result['intent'] == "change_profile"
        assert result['confidence'] >= 0.9
        assert 'normalized_prompt' in result

    @patch('src.llm.call_llm')
    def test_extract_birth_data_returns_normalized_fields(self, mock_call_llm):
        """Test that extract_birth_data returns original and normalized inputs."""
        from src.llm import extract_birth_data
        
        # Mock LLM response with new structure
        mock_call_llm.return_value = json.dumps({
            "dob": "1990-05-15",
            "time": "14:30",
            "lat": 40.7128,
            "lng": -74.0060,
            "location": "New York",
            "original_input": "I was born on May 15, 1990 at 2:30 PM in New York",
            "normalized_input": "DOB: 1990-05-15, Time: 14:30, Location: New York (40.7128, -74.0060)",
            "missing_fields": []
        })
        
        # Call function
        result = extract_birth_data("I was born on May 15, 1990 at 2:30 PM in New York")
        
        # Verify structure
        assert result['dob'] == "1990-05-15"
        assert result['time'] == "14:30"
        assert 'location' in result
        assert result['location'] == "New York"
        assert 'original_input' in result
        assert 'normalized_input' in result
        assert "I was born" in result['original_input']
        assert "DOB: 1990-05-15" in result['normalized_input']

    @patch('src.llm.call_llm')
    def test_extract_birth_data_with_missing_fields(self, mock_call_llm):
        """Test normalization when some fields are missing."""
        from src.llm import extract_birth_data
        
        # Mock LLM response with missing time
        mock_call_llm.return_value = json.dumps({
            "dob": "1985-03-20",
            "time": None,
            "lat": 55.7558,
            "lng": 37.6173,
            "location": "Moscow",
            "original_input": "Born 1985-03-20, morning, Moscow",
            "normalized_input": "DOB: 1985-03-20, Time: unknown (morning), Location: Moscow (55.7558, 37.6173)",
            "missing_fields": ["time"]
        })
        
        # Call function
        result = extract_birth_data("Born 1985-03-20, morning, Moscow")
        
        # Verify structure
        assert result['dob'] == "1985-03-20"
        assert result['time'] is None
        assert result['missing_fields'] == ["time"]
        assert 'original_input' in result
        assert 'normalized_input' in result
        assert "morning" in result['original_input']


@pytest.mark.unit
class TestIntentRouting:
    """Tests for intent routing with change_profile support."""

    @patch('src.services.intent_router.classify_intent')
    def test_detect_request_type_change_profile(self, mock_classify):
        """Test that change_profile intent is properly routed."""
        from src.services.intent_router import detect_request_type
        
        # Mock classify_intent to return change_profile
        mock_classify.return_value = {
            "intent": "change_profile",
            "confidence": 0.96,
            "original_prompt": "Переключись на профиль Маши",
            "normalized_prompt": "Сменить активный профиль на профиль Маши"
        }
        
        # Call function
        result = detect_request_type("Переключись на профиль Маши")
        
        # Verify routing
        assert result == "change_profile"

    @patch('src.services.intent_router.classify_intent')
    def test_detect_request_type_birth_input(self, mock_classify):
        """Test that provide_birth_data is routed to birth_input."""
        from src.services.intent_router import detect_request_type
        
        # Mock classify_intent
        mock_classify.return_value = {
            "intent": "provide_birth_data",
            "confidence": 0.98,
            "original_prompt": "Я родился 15 мая 1990",
            "normalized_prompt": "Дата рождения: 15 мая 1990"
        }
        
        # Call function
        result = detect_request_type("Я родился 15 мая 1990")
        
        # Verify routing
        assert result == "birth_input"

    @patch('src.services.intent_router.classify_intent')
    def test_detect_request_type_natal_question_fallback(self, mock_classify):
        """Test that other intents are routed to natal_question."""
        from src.services.intent_router import detect_request_type
        
        # Mock classify_intent
        mock_classify.return_value = {
            "intent": "ask_about_chart",
            "confidence": 0.90,
            "original_prompt": "Почему я такой упрямый?",
            "normalized_prompt": "Почему я обладаю упрямством?"
        }
        
        # Call function
        result = detect_request_type("Почему я такой упрямый?")
        
        # Verify routing
        assert result == "natal_question"
