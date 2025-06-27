import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(mocker):
    # Mock get_settings to avoid actual config loading
    mock_settings = mocker.patch("app.utils.config.get_settings")
    mock_settings.return_value.GOOGLE_API_KEY = "test_api_key"

    # Mock the genai.Client and its generate_content method
    # This allows us to control the AI's response without making actual API calls
    mock_genai_client_instance = mocker.Mock()
    mock_genai_client_instance.models.generate_content.return_value.text = "Mocked AI response for the given context."
    mocker.patch("google.genai.Client", return_value=mock_genai_client_instance)

    # Import AIService after mocking, or mock the genai.Client path directly if AIService is already imported
    # For simplicity, assuming AIService will be imported at the top level of the test file
    # and we need to patch the Client it tries to initialize.
    from app.services.ai_service import AIService

    # Instantiate AIService (it will use our mocked client)
    ai_service = AIService()

    # Define a simple context for the test
    test_context = "User is asking about a generic product recommendation. Context: 'Tell me about good laptops.'"
    
    # Expected prompt structure that generate_response builds
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assert that generate_content was called exactly once with the correct arguments
    mock_genai_client_instance.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )

    # Assert that the function returned the mocked AI response
    assert response == "Mocked AI response for the given context."
