import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to provide a dummy API key
    mock_settings = mocker.patch('app.utils.config.get_settings')
    mock_settings.return_value.GOOGLE_API_KEY = "dummy_key"

    # Mock the genai.Client and its methods
    # Mock genai.Client class itself
    mock_client_class = mocker.patch('google.genai.Client')
    # Get the mock instance that genai.Client() would return
    mock_client_instance = mock_client_class.return_value

    # Mock the response object that client.models.generate_content would return
    mock_response = mocker.MagicMock()
    mock_response.text = "Mocked AI response for your inquiry."
    
    # Configure the mock chain: client.models.generate_content(...)
    mock_client_instance.models.generate_content.return_value = mock_response

    # Mock ProductDataService as it's initialized in AIService.__init__
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Instantiate AIService (will use the mocked dependencies)
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "What are the best gaming laptops under 15 million Rupiah?"

    # Expected prompt structure that generate_response will create
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the function under test
    actual_response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify that genai.Client.models.generate_content was called with the correct arguments
    mock_client_instance.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash", # Verify the model specified in generate_response
        contents=expected_prompt
    )

    # 2. Verify that the function returned the mocked response text
    assert actual_response == "Mocked AI response for your inquiry."
