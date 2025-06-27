import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Assume AIService is imported from app.services.ai_service
    from app.services.ai_service import AIService

    # Mock get_settings to provide a dummy API key
    mock_settings = mocker.patch('app.utils.config.get_settings')
    mock_settings.return_value.GOOGLE_API_KEY = "dummy_api_key_for_test"

    # Mock google.genai.Client and its methods
    mock_genai_client = mocker.patch('google.genai.Client')
    
    # Mock the response object returned by generate_content
    mock_response_object = mocker.MagicMock()
    mock_response_object.text = "This is a simulated AI response based on your context."
    mock_genai_client.return_value.models.generate_content.return_value = mock_response_object

    # Mock ProductDataService during AIService initialization (not directly used by generate_response but required for init)
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Instantiate AIService (will use mocked dependencies)
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "The user is asking about recommendations for a budget-friendly laptop for students."

    # Call the generate_response method
    response = ai_service.generate_response(test_context)

    # Assertions
    assert isinstance(response, str)
    assert "simulated AI response" in response
    assert response == "This is a simulated AI response based on your context."

    # Verify that generate_content was called with the correct arguments
    mock_genai_client.return_value.models.generate_content.assert_called_once()
    
    # Check the call arguments
    args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
    assert kwargs['model'] == "gemini-2.0-flash"
    
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n{test_context}\n\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    assert kwargs['contents'] == expected_prompt
