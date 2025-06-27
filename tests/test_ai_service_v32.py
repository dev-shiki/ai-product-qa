import pytest
from app.services.ai_service import generate_response

def test_generate_response_basic():
    # Helper classes to simulate the mock behavior without importing external mock libraries.
    # This is done to adhere to the "JANGAN menambahkan import statement" constraint
    # while still providing isolated unit testing.

    class MockContentResponse:
        """Simulates the response object returned by generate_content."""
        def __init__(self, text_content):
            self.text = text_content

    class MockModelsAttribute:
        """Simulates the `models` attribute of the genai.Client, containing `generate_content`."""
        def __init__(self, mock_return_text):
            self._mock_return_text = mock_return_text
            self._call_count = 0
            self._last_call_args = None
            self._last_call_kwargs = None

        def generate_content(self, *args, **kwargs):
            self._call_count += 1
            self._last_call_args = args
            self._last_call_kwargs = kwargs
            return MockContentResponse(self._mock_return_text)

        def assert_called_once(self):
            """Verifies that generate_content was called exactly once."""
            assert self._call_count == 1, f"Expected 1 call, but got {self._call_count}"

        def assert_called_once_with(self, *args, **kwargs):
            """Verifies that generate_content was called once with specific arguments."""
            self.assert_called_once()
            # For simplicity, compare relevant keyword arguments
            assert self._last_call_kwargs.get('model') == kwargs.get('model')
            assert self._last_call_kwargs.get('contents') == kwargs.get('contents')
            # If there are positional arguments, compare them as well
            if args:
                assert self._last_call_args == args

    class MockAIClient:
        """Simulates the genai.Client, providing the `models` attribute."""
        def __init__(self, mock_return_text):
            self.models = MockModelsAttribute(mock_return_text)

    # Instantiate AIService.
    # Note: For this test, we assume AIService's __init__ (which calls get_settings() and
    # genai.Client()) can complete without error in the test environment (e.g.,
    # GOOGLE_API_KEY is set). In a more comprehensive unit test setup, the dependencies
    # of __init__ would also be mocked, usually with pytest fixtures or patchers.
    service = AIService()

    # Create our custom mock for the AI client and replace the service's client with it.
    # This ensures that generate_response calls our mock instead of the real API.
    mock_return_text = "Ini adalah respons AI untuk pengujian berdasarkan konteks yang diberikan."
    mock_client_instance = MockAIClient(mock_return_text)
    service.client = mock_client_instance

    test_context = "Saya ingin membeli laptop baru, budget 10 juta."
    
    # Call the function under test
    response = service.generate_response(test_context)

    # Assertions
    assert isinstance(response, str)
    assert response == mock_return_text
    
    # Verify that the AI model's generate_content method was called exactly once
    mock_client_instance.models.assert_called_once()
    
    # Construct the expected prompt that generate_response sends to the AI model
    expected_prompt_start = """You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

"""
    expected_prompt_end = """
Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    expected_contents = f"{expected_prompt_start}{test_context}{expected_prompt_end}"

    # Verify the arguments passed to generate_content
    mock_client_instance.models.assert_called_once_with(
        model="gemini-2.0-flash", 
        contents=expected_contents
    )
