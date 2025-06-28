import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock dependencies for AIService initialization
    # AIService's __init__ method calls get_settings(), ProductDataService(), and genai.Client()
    mocker.patch('app.utils.config.get_settings').return_value.GOOGLE_API_KEY = "mock_api_key"
    mocker.patch('app.services.product_data_service.ProductDataService')
    
    # Mock genai.Client and its methods
    mock_genai_client_instance = mocker.MagicMock()
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Mock the return value of self.client.models.generate_content
    mock_response_object = mocker.MagicMock()
    mock_response_object.text = "Mocked AI response content for generate_response."
    mock_genai_client_instance.models.generate_content.return_value = mock_response_object

    # Instantiate AIService (assuming AIService class is imported in the test module's scope)
    # The AIService class itself needs to be available to instantiate it.
    # In a real test file, 'from app.services.ai_service import AIService' would be at the top.
    ai_service_instance = AIService()

    # Define a simple context for the function
    test_context = "This is a test context for the AI response generation."

    # Call the generate_response method
    response = ai_service_instance.generate_response(test_context)

    # Assertions
    assert response == "Mocked AI response content for generate_response."

    # Verify that generate_content was called with the correct arguments
    mock_genai_client_instance.models.generate_content.assert_called_once()
    
    # Check arguments: model and contents
    call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
    assert call_kwargs.get('model') == "gemini-2.0-flash"
    
    contents_arg = call_kwargs.get('contents')
    assert isinstance(contents_arg, str)
    assert test_context in contents_arg
    assert "You are a helpful product assistant." in contents_arg
    assert "Please provide a clear and concise answer" in contents_arg
