import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import logging

# Import the service to be tested
from app.services.ai_service import AIService

# Import modules that will be mocked
from app.utils.config import get_settings
from app.services.product_data_service import ProductDataService
import google.genai as genai

# Helper for mock product data to simulate responses from ProductDataService
_MOCK_PRODUCT_DATA = [
    {
        "name": "Laptop Pro X",
        "price": 15000000,
        "brand": "TechCorp",
        "category": "laptop",
        "specifications": {"rating": 4.5, "processor": "i7", "storage": "512GB SSD"},
        "description": "Powerful laptop for professionals. Features a stunning display and long battery life. Ideal for heavy tasks and gaming. Comes with 16GB RAM and 512GB SSD. This description is intentionally long to test the truncation logic in the AI service context building, ensuring it correctly handles descriptions exceeding the specified character limit of 200 characters before appending ellipsis."
    },
    {
        "name": "Smartphone Z Ultra",
        "price": 8000000,
        "brand": "MobileCo",
        "category": "smartphone",
        "specifications": {"rating": 4.2, "camera": "48MP", "screen_size": "6.5 inches"},
        "description": "Innovative smartphone with advanced camera features and sleek design. Perfect for photography enthusiasts. Includes 128GB storage and a vibrant AMOLED display."
    },
    {
        "name": "Wireless Headphone Elite",
        "price": 2500000,
        "brand": "SoundWave",
        "category": "headphone",
        "specifications": {"rating": 4.8, "noise_cancellation": True},
        "description": "Premium wireless headphones with industry-leading noise cancellation. Enjoy immersive audio experience on the go. Long-lasting battery and comfortable fit for extended listening sessions."
    }
]

@pytest.fixture(autouse=True)
def mock_dependencies(mocker):
    """
    Fixture to mock common external dependencies for AIService.
    This fixture is auto-used for all tests in this file to ensure a clean state
    and isolated testing.
    """
    # 1. Mock app.utils.config.get_settings
    mock_settings = MagicMock()
    mock_settings.GOOGLE_API_KEY = "test_api_key_123_abc"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)

    # 2. Mock google.genai.Client
    mock_genai_client = MagicMock()
    # Configure the mock such that client.models.generate_content returns a mock object
    # that has a .text attribute, simulating the GenAI response structure.
    mock_genai_client.models.generate_content.return_value = MagicMock(text="Default Mocked AI response text.")
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # 3. Mock app.services.product_data_service.ProductDataService
    # Use AsyncMock because smart_search_products is an async method.
    mock_product_data_service = AsyncMock()
    # Set a default return value for smart_search_products, which can be overridden in tests.
    # Default is no products found.
    mock_product_data_service.smart_search_products.return_value = (
        [], "No specific products found by default."
    )
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_product_data_service)
    
    # Return mocks for specific assertions in tests
    return {
        "settings": mock_settings,
        "genai_client": mock_genai_client,
        "product_service": mock_product_data_service
    }

@pytest.fixture
def ai_service(mock_dependencies):
    """
    Fixture to provide an instance of AIService.
    It implicitly relies on `mock_dependencies` to ensure external services are mocked
    before AIService is initialized.
    """
    return AIService()

# --- Test AIService.__init__ ---

def test_ai_service_init_success(ai_service, mock_dependencies, caplog):
    """
    Tests successful initialization of AIService.
    Verifies that `self.client` and `self.product_service` are correctly set
    and an informational log message is recorded.
    """
    with caplog.at_level(logging.INFO):
        # Re-initialize to ensure the __init__ logic is executed within caplog's scope
        service = AIService() 
        assert service.client == mock_dependencies["genai_client"]
        assert service.product_service == mock_dependencies["product_service"]
        assert "Successfully initialized AI service with Google AI client" in caplog.text

def test_ai_service_init_failure_genai_client(mocker, caplog):
    """
    Tests AIService initialization failure when `google.genai.Client` raises an exception.
    Ensures an error is logged and the initialization exception is re-raised.
    """
    mocker.patch('google.genai.Client', side_effect=Exception("GenAI client failed to initialize"))
    
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="GenAI client failed to initialize"):
            AIService()
    assert "Error initializing AI service: GenAI client failed to initialize" in caplog.text

def test_ai_service_init_failure_get_settings(mocker, caplog):
    """
    Tests AIService initialization failure when `app.utils.config.get_settings` raises an exception.
    Ensures an error is logged and the initialization exception is re-raised.
    """
    mocker.patch('app.utils.config.get_settings', side_effect=Exception("Settings could not be loaded"))
    
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Settings could not be loaded"):
            AIService()
    assert "Error initializing AI service: Settings could not be loaded" in caplog.text

# --- Test AIService.get_response (async method) ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service, mock_dependencies, caplog):
    """
    Tests `get_response` successfully returns an AI response when relevant products are found.
    Verifies correct arguments passed to product service, accurate prompt construction
    including product context, and proper AI client interaction.
    """
    # Configure product service to return a product
    mock_dependencies["product_service"].smart_search_products.return_value = (
        [_MOCK_PRODUCT_DATA[0]], "We found a great laptop for you based on your criteria."
    )
    # Configure AI client to return a specific response
    mock_dependencies["genai_client"].models.generate_content.return_value = MagicMock(text="AI response about Laptop Pro X details.")

    question = "Can you recommend a laptop for gaming under 20 juta?"
    
    with caplog.at_level(logging.INFO):
        response = await ai_service.get_response(question)

    assert response == "AI response about Laptop Pro X details."
    
    # Verify `smart_search_products` was called with correct parameters
    mock_dependencies["product_service"].smart_search_products.assert_called_once_with(
        keyword=question, category="laptop", max_price=20000000, limit=5
    )
    
    # Verify `generate_content` was called and check its arguments (model and prompt)
    mock_dependencies["genai_client"].models.generate_content.assert_called_once()
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert kwargs['model'] == "gemini-2.5-flash" # Verify specific model used for get_response
    assert f"Question: {question}" in prompt
    assert "We found a great laptop for you based on your criteria." in prompt
    assert "Relevant Products:\n1. Laptop Pro X" in prompt
    assert "Price: Rp 15,000,000" in prompt
    assert "Brand: TechCorp" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 4.5/5" in prompt
    # Check truncated description
    expected_truncated_description = _MOCK_PRODUCT_DATA[0]["description"][:200] + "..."
    assert f"Description: {expected_truncated_description}" in prompt
    
    # Verify logging
    assert f"Getting AI response for question: {question}" in caplog.text
    assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service, mock_dependencies, caplog):
    """
    Tests `get_response` when no specific products are found by the product service.
    Verifies the context includes the "No specific products found" message.
    """
    mock_dependencies["product_service"].smart_search_products.return_value = (
        [], "We couldn't find specific products matching your request."
    )
    mock_dependencies["genai_client"].models.generate_content.return_value = MagicMock(text="General AI response about tech trends.")

    question = "Tell me about general tech trends without product recommendations."
    
    with caplog.at_level(logging.INFO):
        response = await ai_service.get_response(question)

    assert response == "General AI response about tech trends."
    
    mock_dependencies["product_service"].smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert kwargs['model'] == "gemini-2.5-flash"
    assert f"Question: {question}" in prompt
    assert "We couldn't find specific products matching your request." in prompt
    assert "No specific products found, but I can provide general recommendations." in prompt
    assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("recommend a smartphone", "smartphone", None),
    ("laptop murah", "laptop", 5000000), # Test 'murah' for default budget
    ("tablet 10 juta", "tablet", 10000000),
    ("hp budget 3 juta", "smartphone", 3000000),
    ("kamera bagus", "kamera", None),
    ("headphone under 2 juta", "headphone", 2000000),
    ("notebook 7 juta", "laptop", 7000000),
    ("telepon pintar", "smartphone", None),
    ("ponsel canggih", "smartphone", None),
    ("komputer gaming", "laptop", None),
    ("earphone terbaik", "headphone", None),
    ("ipad pro", "tablet", None),
    ("budget kamera 5 juta", "kamera", 5000000),
    ("I need an audio speaker", "audio", None),
    ("Smartwatch for fitness", "jam", None),
    ("drone untuk pemula", "drone", None),
    ("TV paling jernih", "tv", None),
    ("hp", "smartphone", None), # Single keyword
    ("i need a smartphone with a budget", "smartphone", 5000000), # Budget keyword mixed
    ("what is the best phone for 5juta", "smartphone", 5000000), # No space in '5juta'
    ("what is the best phone for 5 juta", "smartphone", 5000000), # Space in '5 juta'
    ("apa rekomendasi laptop 15 juta", "laptop", 15000000),
    ("no category no price", None, None), # No matches
    (" ", None, None), # Whitespace question
    ("", None, None), # Empty question
    ("a phone under 1.5 million", "smartphone", None), # 'million' isn't handled by 'juta' regex
    ("budget for a new phone", "smartphone", 5000000), # Only "budget" keyword, no number
    ("find me a laptop for 20 juta rupiah", "laptop", 20000000), # Additional words after 'juta'
])
async def test_get_response_question_parsing(ai_service, mock_dependencies, question, expected_category, expected_max_price):
    """
    Tests various question inputs for correct category and max_price extraction logic.
    Verifies the arguments passed to `smart_search_products` match expectations.
    """
    # The actual AI response content is not relevant for this test, only the parsing logic.
    await ai_service.get_response(question)
    mock_dependencies["product_service"].smart_search_products.assert_called_once()
    args, kwargs = mock_dependencies["product_service"].smart_search_products.call_args
    assert kwargs['category'] == expected_category
    assert kwargs['max_price'] == expected_max_price
    # Reset mock for next iteration of parametrize, ensuring each test case is isolated
    mock_dependencies["product_service"].smart_search_products.reset_mock()


@pytest.mark.asyncio
async def test_get_response_error_genai_client(ai_service, mock_dependencies, caplog):
    """
    Tests `get_response` when the GenAI client's `generate_content` method raises an exception.
    Verifies that a specific fallback error message is returned and an error is logged.
    """
    mock_dependencies["genai_client"].models.generate_content.side_effect = Exception("Google AI service internal error")

    question = "What should I buy?"
    with caplog.at_level(logging.ERROR):
        response = await ai_service.get_response(question)

    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Google AI service internal error" in caplog.text

@pytest.mark.asyncio
async def test_get_response_error_product_service(ai_service, mock_dependencies, caplog):
    """
    Tests `get_response` when the product service's `smart_search_products` method raises an exception.
    Verifies that a specific fallback error message is returned and an error is logged.
    """
    mock_dependencies["product_service"].smart_search_products.side_effect = Exception("Product database lookup failed")

    question = "Find me anything."
    with caplog.at_level(logging.ERROR):
        response = await ai_service.get_response(question)

    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    assert "Error generating AI response: Product database lookup failed" in caplog.text

@pytest.mark.asyncio
async def test_get_response_product_description_truncation(ai_service, mock_dependencies):
    """
    Tests that product description in the context is correctly truncated to 200 characters
    and appended with '...'.
    """
    mock_product = _MOCK_PRODUCT_DATA[0].copy()
    # The default description in _MOCK_PRODUCT_DATA is already long enough to test truncation
    mock_dependencies["product_service"].smart_search_products.return_value = (
        [mock_product], "Testing description truncation."
    )

    await ai_service.get_response("test description")
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    original_description = _MOCK_PRODUCT_DATA[0]["description"]
    expected_truncated_desc = original_description[:200] + "..."
    assert f"Description: {expected_truncated_desc}" in prompt
    # Ensure the full, untruncated description is NOT in the prompt
    assert original_description not in prompt 

@pytest.mark.asyncio
async def test_get_response_product_missing_keys(ai_service, mock_dependencies):
    """
    Tests `get_response` gracefully handles product dictionaries with missing optional keys
    by using default values in the context string.
    """
    malformed_product = {
        "name": "Product Without All Data",
        "price": 1000000,
        # 'brand', 'category', 'specifications', 'description' are intentionally missing
    }
    mock_dependencies["product_service"].smart_search_products.return_value = (
        [malformed_product], "Malformed product data test."
    )

    await ai_service.get_response("test malformed product")
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert "Brand: Unknown" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt
    assert "Description: No description..." in prompt # Default description is "No description", then truncated with "..."

@pytest.mark.asyncio
async def test_get_response_product_empty_description(ai_service, mock_dependencies):
    """
    Tests `get_response` handles product dictionaries with an empty description string.
    It should still append "..." to the empty string.
    """
    empty_desc_product = {
        "name": "Empty Desc Product",
        "price": 1000000,
        "brand": "TestBrand",
        "category": "TestCat",
        "specifications": {"rating": 3.0},
        "description": "", # Empty description
    }
    mock_dependencies["product_service"].smart_search_products.return_value = (
        [empty_desc_product], "Empty description test."
    )

    await ai_service.get_response("test empty description")
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert "Description: ..." in prompt # An empty string `''[:200]` is `''`, then it becomes `...`

# --- Test AIService.generate_response (legacy method) ---

def test_generate_response_success(ai_service, mock_dependencies, caplog):
    """
    Tests `generate_response` successfully returns an AI response using the legacy method.
    Verifies correct prompt construction and AI client interaction, including the model name.
    """
    mock_dependencies["genai_client"].models.generate_content.return_value = MagicMock(text="Legacy AI response text.")

    context = "This is a custom context for the legacy AI method, focusing on general information."
    
    with caplog.at_level(logging.INFO):
        response = ai_service.generate_response(context)

    assert response == "Legacy AI response text."
    
    # Verify `generate_content` call and check its arguments (model and prompt)
    mock_dependencies["genai_client"].models.generate_content.assert_called_once()
    args, kwargs = mock_dependencies["genai_client"].models.generate_content.call_args
    prompt = kwargs['contents']
    
    assert kwargs['model'] == "gemini-2.0-flash" # Specific model for legacy method
    assert context in prompt
    assert "You are a helpful product assistant." in prompt
    assert "Please provide a clear and concise answer that helps the user understand the products and make an informed decision." in prompt
    assert "Successfully generated AI response" in caplog.text

def test_generate_response_error_genai_client(ai_service, mock_dependencies, caplog):
    """
    Tests `generate_response` when the GenAI client raises an exception during content generation.
    Ensures the exception is re-raised and an error is logged, as this method does not
    have a graceful fallback message.
    """
    mock_dependencies["genai_client"].models.generate_content.side_effect = Exception("Legacy AI generation error occurred")

    context = "Error scenario for legacy method."
    
    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Legacy AI generation error occurred"):
            ai_service.generate_response(context)
    
    assert "Error generating AI response: Legacy AI generation error occurred" in caplog.text