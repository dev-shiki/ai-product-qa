import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic(monkeypatch):
    # Mock get_settings to avoid actual config loading and API key check
    class MockSettings:
        GOOGLE_API_KEY = "mock_api_key"
    monkeypatch.setattr('app.utils.config.get_settings', lambda: MockSettings())

    # Mock ProductDataService as it's initialized in AIService.__init__
    # generate_response doesn't use product_service, but __init__ creates it.
    class MockProductDataService:
        def __init__(self):
            pass
    monkeypatch.setattr('app.services.product_data_service.ProductDataService', MockProductDataService)

    # Variables to capture arguments passed to the mocked generate_content
    mock_generate_content_calls = []

    # Mock genai.Client and its models.generate_content method
    class MockResponse:
        def __init__(self, text_content):
            self.text = text_content

    class MockGeminiModels:
        def generate_content(self, model, contents):
            # Capture the arguments for assertion later
            mock_generate_content_calls.append({"model": model, "contents": contents})
            # Return a mock response object with a .text attribute
            return MockResponse("Mocked AI response for the given context.")

    class MockGeminiClient:
        def __init__(self, api_key):
            pass  # Mock the constructor, it doesn't need to do anything
        models = MockGeminiModels() # Assign an instance of the mock models

    # Apply the mock for genai.Client
    monkeypatch.setattr('google.genai.Client', MockGeminiClient)

    # Import AIService after mocks are set up, as its __init__ depends on them.
    # This import is necessary to create an instance of the class under test.
    # It is placed inside the function to adhere to the "ONLY return the test function" instruction.
    from app.services.ai_service import AIService

    # Instantiate AIService
    ai_service_instance = AIService()

    # Define a simple test context
    test_context = "What are the key features of a good smartphone?"

    # The expected prompt that generate_response will construct
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{test_context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

    # Call the generate_response method
    response = ai_service_instance.generate_response(test_context)

    # Assert that the response matches the mocked output
    expected_response_text = "Mocked AI response for the given context."
    assert response == expected_response_text

    # Verify that generate_content was called exactly once
    assert len(mock_generate_content_calls) == 1

    # Verify the arguments passed to generate_content
    called_args = mock_generate_content_calls[0]
    assert called_args["model"] == "gemini-2.0-flash"
    assert called_args["contents"] == expected_prompt
