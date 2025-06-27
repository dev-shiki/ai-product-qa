import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock AIService dependencies for initialization
    mock_settings = mocker.patch('app.utils.config.get_settings')
    mock_settings.return_value = mocker.Mock(GOOGLE_API_KEY="dummy_test_key")

    mock_genai_client_class = mocker.patch('google.genai.Client')
    
    # Configure the mock for client.models.generate_content
    # This mock represents the object returned by client.models.generate_content
    mock_ai_response_object = mocker.Mock()
    mock_ai_response_object.text = "This is a basic mocked AI response."
    mock_genai_client_class.return_value.models.generate_content.return_value = mock_ai_response_object

    # Mock ProductDataService as it's initialized in AIService.__init__
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Assuming AIService is accessible in the test environment
    from app.services.ai_service import AIService 
    ai_service_instance = AIService()

    # Define a simple input context
    test_context = "Tell me about the importance of good sleep."

    # Call the generate_response method
    actual_response = ai_service_instance.generate_response(test_context)

    # Assert that the response matches the mocked output
    expected_response = "This is a basic mocked AI response."
    assert actual_response == expected_response

    # Verify that the generate_content method was called with the correct arguments
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n{test_context}\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    
    mock_genai_client_class.return_value.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
