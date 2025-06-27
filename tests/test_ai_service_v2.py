import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to avoid actual API key dependency
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key"
    mocker.patch('app.services.ai_service.get_settings', return_value=mock_settings)

    # Mock ProductDataService as it's initialized in AIService but not used by generate_response
    mocker.patch('app.services.ai_service.ProductDataService')

    # Mock the genai client and its generate_content method
    mock_genai_client_instance = MagicMock()
    # Configure the return value chain: client.models.generate_content().text
    mock_genai_client_instance.models.generate_content.return_value.text = "Mocked AI response for the provided context."
    mocker.patch('app.services.ai_service.genai.Client', return_value=mock_genai_client_instance)

    # Instantiate AIService (assuming AIService is imported in the test file)
    from app.services.ai_service import AIService
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "This is a simple test context about a product recommendation."

    # Define the expected prompt that the generate_response function should create
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the function to be tested
    actual_response = ai_service.generate_response(test_context)

    # Assert that genai.Client().models.generate_content was called with the correct arguments
    mock_genai_client_instance.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )

    # Assert that the function returns the expected mocked response text
    assert actual_response == "Mocked AI response for the provided context."
