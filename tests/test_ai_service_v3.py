import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock dependencies for AIService.__init__ to prevent actual external calls
    mock_settings_instance = mocker.MagicMock()
    mock_settings_instance.GOOGLE_API_KEY = "dummy_api_key_for_test"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_instance)
    
    # Mock genai.Client and its internal structure that AIService expects
    mock_genai_client_instance = mocker.MagicMock()
    mock_genai_client_instance.models = mocker.MagicMock() # Ensure .models attribute exists
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Mock ProductDataService as it's initialized in AIService.__init__
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Import AIService here to ensure it uses the patched dependencies
    from app.services.ai_service import AIService
    
    # Initialize AIService
    ai_service = AIService()

    # Define a sample context and the expected AI response from our mock
    test_context = "Saya ingin tahu lebih banyak tentang smartphone terbaru."
    expected_mocked_ai_response_text = "Smartphone terbaru menawarkan berbagai fitur menarik seperti kamera canggih, performa cepat, dan baterai tahan lama. Apakah Anda mencari rekomendasi merek tertentu?"

    # Mock the specific method called by generate_response: client.models.generate_content
    mock_generate_content_return_value = mocker.MagicMock()
    mock_generate_content_return_value.text = expected_mocked_ai_response_text
    
    # Assign the mock's return value to the method path on the service's client
    ai_service.client.models.generate_content.return_value = mock_generate_content_return_value

    # Call the function under test
    actual_response = ai_service.generate_response(test_context)

    # Assert that the function returned the expected mocked response
    assert actual_response == expected_mocked_ai_response_text

    # Construct the exact prompt that generate_response would have passed to the AI model
    expected_prompt_for_ai = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Verify that client.models.generate_content was called exactly once with the correct arguments
    ai_service.client.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt_for_ai
    )
