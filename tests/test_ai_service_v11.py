import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to allow AIService instantiation without actual API key
    mock_settings = mocker.Mock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock ProductDataService as it's initialized in AIService.__init__
    # but not directly used by generate_response
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Mock the genai.Client and its methods used by generate_response
    mock_gemini_response = mocker.Mock()
    mock_gemini_response.text = "This is a mocked AI response."

    mock_genai_client_instance = mocker.Mock()
    mock_genai_client_instance.models.generate_content.return_value = mock_gemini_response
    
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Import AIService here to ensure it's available in the test scope
    # (Assuming AIService is imported in the actual test file)
    from app.services.ai_service import AIService 

    # Instantiate the AIService
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "User is asking about budget-friendly smartphones."

    # Call the generate_response method
    response = ai_service.generate_response(test_context)

    # Assertions
    assert response == "This is a mocked AI response."

    # Verify that the AI client's generate_content method was called correctly
    mock_genai_client_instance.models.generate_content.assert_called_once()
    call_args, call_kwargs = mock_genai_client_instance.models.generate_content.call_args
    assert call_kwargs['model'] == "gemini-2.0-flash"
    assert "You are a helpful product assistant." in call_kwargs['contents']
    assert test_context in call_kwargs['contents']
