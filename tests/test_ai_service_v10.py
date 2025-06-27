import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to prevent actual config loading and API key dependency
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_test_api_key"
    mocker.patch('app.services.ai_service.get_settings', return_value=mock_settings)

    # Mock google.genai.Client and its methods
    # This mock ensures that when AIService initializes self.client, it gets a controlled mock object.
    mock_genai_client_instance = mocker.MagicMock()
    
    # Configure the return value for the generate_content call
    # The actual method called will be mock_genai_client_instance.models.generate_content(...)
    expected_ai_response = "Ini adalah respons AI yang di-mock untuk pengujian fungsi generate_response."
    mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response
    
    # Patch the genai.Client class itself so that when AIService() calls genai.Client(), it returns our mock instance
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance)

    # Mock ProductDataService during AIService initialization.
    # While generate_response doesn't use it, AIService.__init__ does.
    mocker.patch('app.services.ai_service.ProductDataService')

    # Instantiate AIService - this will use the mocked dependencies
    ai_service = AIService()

    # Define a simple context string to pass to the function
    test_context = "User is asking about product availability."

    # Call the generate_response method
    actual_response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify that client.models.generate_content was called exactly once
    mock_genai_client_instance.models.generate_content.assert_called_once()
    
    # 2. Check the arguments passed to generate_content
    # Get the arguments used in the call
    call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
    
    # Assert the model name
    assert call_kwargs['model'] == "gemini-2.0-flash"
    
    # Assert that the context is part of the prompt
    # The prompt structure is defined within generate_response
    expected_prompt_prefix = "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
    expected_prompt_suffix = "\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."
    
    assert call_kwargs['contents'].startswith(expected_prompt_prefix)
    assert test_context in call_kwargs['contents']
    assert call_kwargs['contents'].endswith(expected_prompt_suffix)

    # 3. Assert that the function returned the mocked AI response
    assert actual_response == expected_ai_response
