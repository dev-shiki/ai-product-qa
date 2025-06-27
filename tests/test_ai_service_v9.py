import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to avoid actual config loading
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "mock_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock genai.Client to prevent actual API calls
    mock_gemini_client = mocker.MagicMock()
    mock_gemini_client.models.generate_content.return_value.text = "This is a mocked AI response based on the context."
    mocker.patch('google.genai.Client', return_value=mock_gemini_client)

    # Mock ProductDataService as AIService constructor initializes it, though it's not used by generate_response
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Import AIService after patching its dependencies
    from app.services.ai_service import AIService

    # Instantiate AIService
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "The user is asking about recommendations for gaming laptops."

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assert the expected outcome
    assert response == "This is a mocked AI response based on the context."

    # Optionally, assert that the underlying model was called with the correct prompt
    expected_prompt_template = """You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    expected_prompt = expected_prompt_template.format(test_context)

    ai_service.client.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
