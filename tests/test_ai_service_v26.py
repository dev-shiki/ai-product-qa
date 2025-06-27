import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock dependencies required for AIService initialization
    # Mock app.utils.config.get_settings to provide a dummy API key
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key_for_test"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock ProductDataService as AIService.__init__ instantiates it,
    # but it's not used by generate_response itself.
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Mock google.genai.Client and its models.generate_content method.
    # This is essential as generate_response calls this external API.
    mock_genai_client = MagicMock()
    mock_ai_response = MagicMock()
    mock_ai_response.text = "Ini adalah respons AI yang di-mocking berdasarkan konteks yang diberikan."
    mock_genai_client.models.generate_content.return_value = mock_ai_response
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Instantiate the AIService.
    # Assumes AIService class is accessible (e.g., via 'from app.services.ai_service import AIService').
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "Pengguna ingin tahu lebih banyak tentang laptop gaming terbaik di bawah 20 juta."

    # Call the function under test
    actual_response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify that 'generate_content' method was called exactly once.
    mock_genai_client.models.generate_content.assert_called_once()

    # 2. Check the arguments passed to 'generate_content'.
    # It should use "gemini-2.0-flash" model and a prompt containing the context.
    call_args, call_kwargs = mock_genai_client.models.generate_content.call_args
    assert call_kwargs.get('model') == "gemini-2.0-flash"
    
    actual_prompt = call_kwargs.get('contents')
    assert actual_prompt is not None
    assert "You are a helpful product assistant." in actual_prompt
    assert test_context in actual_prompt
    assert "Please provide a clear and concise answer" in actual_prompt

    # 3. Verify the response returned by the function under test matches the mocked response.
    assert actual_response == mock_ai_response.text
