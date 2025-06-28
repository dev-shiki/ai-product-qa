import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(monkeypatch):
    # Assume AIService and MagicMock are already imported in the test file scope.
    # For example:
    # from unittest.mock import MagicMock
    # from app.services.ai_service import AIService

    # Mocking genai.Client and its chained methods
    mock_ai_response = MagicMock()
    mock_ai_response.text = "Mocked AI response for the given context."

    mock_generate_content_method = MagicMock(return_value=mock_ai_response)

    mock_models_object = MagicMock()
    mock_models_object.generate_content = mock_generate_content_method

    mock_genai_client_instance = MagicMock()
    mock_genai_client_instance.models = mock_models_object

    mock_genai_client_class = MagicMock(return_value=mock_genai_client_instance)
    monkeypatch.setattr("google.genai.Client", mock_genai_client_class)

    # Mocking app.utils.config.get_settings, which is called in AIService.__init__
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "dummy_api_key" # Value doesn't matter for this test
    monkeypatch.setattr("app.utils.config.get_settings", lambda: mock_settings)

    # Mocking ProductDataService initialization (it's initialized but not used by generate_response)
    mock_product_data_service_class = MagicMock()
    monkeypatch.setattr("app.services.product_data_service.ProductDataService", mock_product_data_service_class)

    # Instantiate AIService (assuming AIService is imported/available)
    from app.services.ai_service import AIService # This line is usually at the top of the file, included here for clarity on what's assumed.
    from unittest.mock import MagicMock # This line is usually at the top of the file, included here for clarity on what's assumed.

    ai_service = AIService()

    # Define a simple test context
    test_context = "Saya mencari laptop untuk pekerjaan kantor dan sedikit gaming."

    # Call the function under test
    response = ai_service.generate_response(test_context)

    # Assertions
    # 1. Verify the return value matches the mocked response text
    assert response == "Mocked AI response for the given context."

    # 2. Verify that the client's generate_content method was called with the correct arguments
    expected_prompt = (
        "You are a helpful product assistant. Based on the following context, provide a helpful and informative response:\n\n"
        f"{test_context}\n\n"
        "Please provide a clear and concise answer that helps the user understand the products and make an informed decision."
    )

    mock_generate_content_method.assert_called_once_with(
        model="gemini-2.0-flash",
        contents=expected_prompt
    )
