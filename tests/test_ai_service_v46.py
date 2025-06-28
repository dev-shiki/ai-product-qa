import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to prevent actual config loading and API key access
    mock_settings = mocker.Mock()
    mock_settings.GOOGLE_API_KEY = "test_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock genai.Client and its methods
    mock_genai_client = mocker.Mock()
    mock_models = mocker.Mock()
    mock_generate_content = mocker.Mock()
    
    # Configure the mock response object
    mock_response_object = mocker.Mock()
    mock_response_object.text = "This is a mocked AI response."
    mock_generate_content.return_value = mock_response_object

    mock_models.generate_content = mock_generate_content
    mock_genai_client.models = mock_models
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Mock ProductDataService to prevent actual database/service calls
    mocker.patch('app.services.product_data_service.ProductDataService')

    from app.services.ai_service import AIService

    # Instantiate the service
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "User is asking about laptops."

    # Call the generate_response method
    response = ai_service.generate_response(test_context)

    # Assertions
    assert isinstance(response, str)
    assert response == "This is a mocked AI response."

    # Verify that generate_content was called with the correct model and prompt
    expected_prompt_part = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n{test_context}\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    mock_generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt_part
    )
