import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock settings for AIService.__init__ to provide a dummy API key
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key_for_test"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock genai.Client and its methods that generate_response calls
    mock_genai_client = mocker.MagicMock()
    mock_response_object = mocker.MagicMock()
    mock_response_object.text = "This is a mocked AI response for the user's query."
    # Configure the mock client to return our desired mock response object
    mock_genai_client.models.generate_content.return_value = mock_response_object
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Mock ProductDataService initialization to prevent actual service calls in __init__
    mocker.patch('app.services.ai_service.ProductDataService')

    # Instantiate AIService. Assuming 'from app.services.ai_service import AIService' is provided externally.
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple context string for the test
    test_context = "User wants to know more about the latest gaming laptops."

    # Call the generate_response function with the test context
    actual_response = ai_service.generate_response(context=test_context)

    # Assert that the returned response matches our mocked expectation
    assert actual_response == "This is a mocked AI response for the user's query."

    # Verify that the underlying AI client method was called correctly
    mock_genai_client.models.generate_content.assert_called_once()
    
    # Extract the arguments with which generate_content was called
    call_args, call_kwargs = mock_genai_client.models.generate_content.call_args
    
    # Assert the model used was correct
    assert call_kwargs['model'] == "gemini-2.0-flash"
    
    # Assert that the prompt contains the expected structure and the test_context
    assert "You are a helpful product assistant." in call_kwargs['contents']
    assert test_context in call_kwargs['contents']
    assert "Please provide a clear and concise answer" in call_kwargs['contents']
