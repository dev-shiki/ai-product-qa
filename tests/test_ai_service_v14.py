import pytest
from app.services.ai_service import generate_response

from unittest.mock import patch, MagicMock
from app.services.ai_service import AIService

def test_generate_response_basic():
    # Mock settings to prevent errors during AIService __init__
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_key"

    # Mock the genai.Client and its methods
    # Patch get_settings and google.genai.Client at the module level
    with patch('app.utils.config.get_settings', return_value=mock_settings), \
         patch('google.genai.Client') as MockGenaiClient:
        
        # Configure the mock AI client response
        mock_ai_response = MagicMock()
        mock_ai_response.text = "Mocked AI response for basic test."
        
        # Set up the chain of mocks: Client() -> instance -> models -> generate_content -> mock_ai_response
        mock_genai_client_instance = MagicMock()
        MockGenaiClient.return_value = mock_genai_client_instance
        mock_genai_client_instance.models.generate_content.return_value = mock_ai_response

        # Instantiate AIService (this will use the mocked components)
        ai_service_instance = AIService()

        # Define a simple context for the test
        test_context = "Test context for AI response generation."

        # Call the function under test
        result = ai_service_instance.generate_response(test_context)

        # Assertions for basic functionality
        # 1. Ensure the result is a string
        assert isinstance(result, str)
        # 2. Ensure the result matches the mocked AI response
        assert result == "Mocked AI response for basic test."

        # 3. Verify that generate_content was called exactly once
        mock_genai_client_instance.models.generate_content.assert_called_once()
        
        # 4. Get the arguments with which generate_content was called
        call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
        
        # 5. Verify the AI model used
        assert call_kwargs['model'] == "gemini-2.0-flash"
        
        # 6. Verify the full prompt content passed to the AI model
        expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
        assert call_kwargs['contents'] == expected_prompt
