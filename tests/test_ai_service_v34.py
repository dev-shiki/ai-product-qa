import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock genai.Client and its methods
    mock_genai_client_instance = mocker.MagicMock()
    # Configure the mock to return a predictable value when generate_content.text is accessed
    mock_genai_client_instance.models.generate_content.return_value.text = "This is a mocked AI response based on the context."

    # Patch genai.Client constructor used within AIService.__init__
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance)

    # Patch ProductDataService to prevent actual initialization issues (e.g., DB connection)
    mocker.patch('app.services.ai_service.ProductDataService')

    # Patch get_settings to provide a dummy API key, avoiding real config lookup
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key_for_test"
    mocker.patch('app.services.ai_service.get_settings', return_value=mock_settings)

    # Instantiate AIService (will use the mocked genai.Client and ProductDataService)
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple test context
    test_context = "User is asking about good quality smartphones with long battery life."

    # Call the generate_response function
    response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify the response is a string
    assert isinstance(response, str)
    # 2. Verify the response matches the mocked return value
    assert response == "This is a mocked AI response based on the context."
    
    # 3. Verify that generate_content was called exactly once
    mock_genai_client_instance.models.generate_content.assert_called_once()
    
    # 4. Verify the arguments passed to generate_content
    call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
    assert call_kwargs['model'] == "gemini-2.0-flash"
    
    # Verify the prompt structure and content
    prompt_content = call_kwargs['contents']
    assert "You are a helpful product assistant." in prompt_content
    assert test_context in prompt_content
    assert "Please provide a clear and concise answer that helps the user understand the products and make an informed decision." in prompt_content
