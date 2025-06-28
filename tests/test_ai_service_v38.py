import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock app.utils.config.get_settings as it's called during AIService initialization
    mock_settings = mocker.Mock()
    mock_settings.GOOGLE_API_KEY = "mock_api_key"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # Mock google.genai.Client to prevent actual API calls
    mock_genai_client_instance = mocker.Mock()
    mocker.patch('google.genai.Client', return_value=mock_genai_client_instance)

    # Mock app.services.product_data_service.ProductDataService
    # This is needed because AIService.__init__ calls ProductDataService()
    mocker.patch('app.services.product_data_service.ProductDataService')

    # Configure the mock response for client.models.generate_content
    mock_ai_response = mocker.Mock()
    mock_ai_response.text = "This is a simulated AI response based on your context."
    mock_genai_client_instance.models.generate_content.return_value = mock_ai_response

    # Instantiate AIService (assuming AIService is imported at the top of the test file)
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a sample context to pass to generate_response
    sample_context = "User is looking for a durable laptop for students with a budget of around 8 million IDR."

    # Call the target function
    actual_response = ai_service.generate_response(sample_context)

    # Assert that the response matches the mocked AI response
    assert actual_response == "This is a simulated AI response based on your context."

    # Verify that the client.models.generate_content method was called with the correct arguments
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{sample_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    mock_genai_client_instance.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
