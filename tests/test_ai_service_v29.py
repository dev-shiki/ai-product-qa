import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(monkeypatch):
    # Mock get_settings to avoid actual config loading
    class MockSettings:
        GOOGLE_API_KEY = "dummy_api_key"
    monkeypatch.setattr("app.utils.config.get_settings", MockSettings)

    # Mock ProductDataService as it's initialized in AIService.__init__
    monkeypatch.setattr("app.services.product_data_service.ProductDataService", Mock())

    # Mock genai.Client and its methods
    mock_generate_content_response = Mock()
    mock_generate_content_response.text = "This is a test AI response based on the provided context."

    mock_models = Mock()
    mock_models.generate_content.return_value = mock_generate_content_response

    mock_client = Mock()
    mock_client.models = mock_models

    monkeypatch.setattr("google.genai.Client", Mock(return_value=mock_client))
    
    # Initialize AIService (assuming AIService class is available in scope)
    # The actual import `from app.services.ai_service import AIService`
    # would be at the top of the test file, not inside this function,
    # adhering to the "JANGAN menambahkan import statement" rule.
    ai_service = AIService()

    # Define test input context
    test_context = "User is asking about a reliable smartphone under 5 million."
    
    # Define the expected prompt that generate_response builds internally
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the function under test
    actual_response = ai_service.generate_response(test_context)

    # Assert the returned response
    assert actual_response == mock_generate_content_response.text

    # Verify that the AI client's generate_content method was called correctly
    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
