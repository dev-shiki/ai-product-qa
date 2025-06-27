import pytest
from app.services.ai_service import generate_response

import pytest
from unittest.mock import MagicMock

def test_generate_response_basic(mocker):
    # Mock get_settings for AIService initialization
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock genai.Client and its methods
    mock_genai_client = MagicMock()
    mock_generate_content = MagicMock()
    mock_generate_content.return_value.text = "Mocked AI response based on context."
    
    mock_genai_client.models.generate_content = mock_generate_content
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Import AIService after patching its dependencies to ensure mocks are in place
    from app.services.ai_service import AIService

    # Instantiate AIService
    ai_service = AIService()

    # Define a sample context
    sample_context = "User is asking about laptops under Rp 10.000.000."

    # Call the function under test
    response = ai_service.generate_response(sample_context)

    # Define the expected prompt that generate_content should receive
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{sample_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Assert that generate_content was called with the correct arguments
    mock_generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )

    # Assert the returned response matches the mocked AI response
    assert response == "Mocked AI response based on context."
