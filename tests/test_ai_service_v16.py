import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock the return value chain for client.models.generate_content().text
    mock_ai_response_object = mocker.MagicMock()
    mock_ai_response_object.text = "This is a basic mocked AI response from generate_response."

    # Mock the generate_content method itself
    mock_generate_content_method = mocker.MagicMock(return_value=mock_ai_response_object)

    # Mock the 'models' attribute of the client
    mock_client_models = mocker.MagicMock()
    mock_client_models.generate_content = mock_generate_content_method

    # Mock the genai.Client instance that AIService.__init__ creates
    mock_genai_client_instance = mocker.MagicMock()
    mock_genai_client_instance.models = mock_client_models

    # Patch genai.Client in the module where AIService is defined
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance)

    # Patch get_settings to prevent actual configuration loading during AIService initialization
    mocker.patch('app.services.ai_service.get_settings', return_value=mocker.MagicMock(GOOGLE_API_KEY="dummy_api_key"))

    # Instantiate AIService (assuming AIService is imported/available in the test environment)
    from app.services.ai_service import AIService # Implicitly assumed as per problem statement
    ai_service = AIService()

    # Define a simple context for testing
    test_context = "This is a sample product context."

    # Call the generate_response method
    actual_response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify that the mock_generate_content_method was called exactly once
    mock_generate_content_method.assert_called_once()

    # 2. Verify the arguments passed to the generate_content method
    args, kwargs = mock_generate_content_method.call_args
    assert kwargs['model'] == "gemini-2.0-flash"
    assert "You are a helpful product assistant." in kwargs['contents']
    assert test_context in kwargs['contents']
    assert "Please provide a clear and concise answer" in kwargs['contents']

    # 3. Verify the returned response
    assert actual_response == "This is a basic mocked AI response from generate_response."
