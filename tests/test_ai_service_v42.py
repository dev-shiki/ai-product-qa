import pytest
from app.services.ai_service import generate_response

# Assuming 'MagicMock' from 'unittest.mock' and 'sys' module are available in the test environment
# without needing explicit import statements within this function body.
# This approach dynamically patches the modules that AIService depends on during its initialization
# and method calls, allowing the actual AIService class and its methods to be tested.

def test_generate_response_basic():
    # Save original module attributes to restore them after the test.
    # This is crucial for test isolation when patching global module states.
    original_get_settings = None
    original_genai = None
    original_logger = None

    try:
        # To access and patch the imports made within 'app/services/ai_service.py',
        # we need to get a reference to that module's namespace.
        # This implicitly assumes 'app.services.ai_service' is either already loaded
        # or can be accessed via `sys.modules`.
        # We also need the `AIService` class itself to instantiate it.
        # The line `from app.services.ai_service import AIService` is assumed to be
        # pre-existing in the test file where this function will be placed ("sudah disediakan").
        from app.services.ai_service import AIService

        # 1. Mock `get_settings` (from `app.utils.config`) that AIService.__init__ uses.
        #    It's imported as `get_settings` within `ai_service.py`, so we patch it in that module's scope.
        original_get_settings = sys.modules['app.services.ai_service'].get_settings
        mock_settings_obj = MagicMock()
        mock_settings_obj.GOOGLE_API_KEY = "mock_api_key_for_test"
        sys.modules['app.services.ai_service'].get_settings = MagicMock(return_value=mock_settings_obj)

        # 2. Mock `google.genai.Client` that AIService.__init__ and generate_response use.
        #    It's imported as `genai` within `ai_service.py`, so we patch `ai_service.genai`.
        original_genai = sys.modules['app.services.ai_service'].genai
        
        # Mock the instance returned by `genai.Client()`
        mock_client_instance = MagicMock()
        # Configure the return value for the generate_content method
        mock_client_instance.models.generate_content.return_value.text = "Mocked AI response for the test context."
        
        # Mock the `genai` module itself and set its `Client` attribute's return value
        mock_genai_module = MagicMock()
        mock_genai_module.Client.return_value = mock_client_instance
        sys.modules['app.services.ai_service'].genai = mock_genai_module

        # 3. Mock the logger to prevent actual logging and allow checking log calls if needed.
        original_logger = sys.modules['app.services.ai_service'].logger
        sys.modules['app.services.ai_service'].logger = MagicMock()

        # Now, instantiate AIService. It will use the mocked dependencies for its initialization.
        service_instance = AIService()

        # Define a simple test context to pass to the function.
        test_context = "User is asking about the general features of a new electronic gadget."

        # Call the target function: generate_response
        response = service_instance.generate_response(test_context)

        # Assertions to verify the behavior and expected interactions.
        # 1. Check if the response contains the mocked text.
        assert "Mocked AI response" in response, "The response should contain the mocked AI output."
        
        # 2. Verify that `generate_content` was called exactly once.
        mock_client_instance.models.generate_content.assert_called_once()
        
        # 3. Verify the arguments passed to `generate_content`.
        call_args, call_kwargs = mock_client_instance.models.generate_content.call_args
        assert call_kwargs['model'] == "gemini-2.0-flash", "AI model should be 'gemini-2.0-flash'."
        
        # Check if the prompt includes the test context and other standard parts.
        prompt_contents = call_kwargs['contents']
        assert "helpful product assistant" in prompt_contents, "Prompt should identify as a helpful assistant."
        assert f"Context:\n\n{test_context}" in prompt_contents, "Prompt should include the provided test context."
        assert "make an informed decision" in prompt_contents, "Prompt should guide the AI's response style."

    finally:
        # Restore original module attributes. This is crucial for preventing side effects
        # on other tests that might run in the same test session.
        if original_get_settings is not None:
            sys.modules['app.services.ai_service'].get_settings = original_get_settings
        if original_genai is not None:
            sys.modules['app.services.ai_service'].genai = original_genai
        if original_logger is not None:
            sys.modules['app.services.ai_service'].logger = original_logger
