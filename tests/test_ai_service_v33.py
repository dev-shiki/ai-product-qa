import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock app.utils.config.get_settings to provide a dummy API key
    mock_settings = mocker.MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key_for_test"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock google.genai.Client and its methods
    mock_client_instance = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.text = "Here is a helpful AI response based on your context."
    mock_client_instance.models.generate_content.return_value = mock_response
    mocker.patch('google.genai.Client', return_value=mock_client_instance)

    # Mock app.services.product_data_service.ProductDataService as AIService's __init__ uses it
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Import AIService class (assuming it's available in the test file's scope as per instructions)
    from app.services.ai_service import AIService

    # Instantiate the AIService
    ai_service = AIService()

    # Define a simple test context
    test_context = "User is looking for a good smartphone recommendation for under 5 million IDR."

    # Call the generate_response method
    response = ai_service.generate_response(context=test_context)

    # Assertions:
    # 1. Check if the response is a string
    assert isinstance(response, str)
    # 2. Check if the response matches the mocked response text
    assert response == "Here is a helpful AI response based on your context."

    # 3. Verify that the generate_content method was called with the correct arguments
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    mock_client_instance.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash", # As defined in generate_response function
        contents=expected_prompt
    )
