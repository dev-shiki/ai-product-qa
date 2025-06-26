import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch

# Note: The `autouse=True` fixture `setup_common_mocks` will run for every test.
# It patches `get_settings`, `google.genai.Client`, `ProductDataService`, and the `logger`.
# If a specific test needs to modify one of these mocks (e.g., to simulate an error),
# it should re-patch or set a side_effect on the mock provided by the fixture.

@pytest.fixture(autouse=True)
def setup_common_mocks(mocker):
    """
    Sets up common mocks for `get_settings`, `google.genai.Client`, `ProductDataService`,
    and the module-level `logger` used by `AIService`.
    These mocks are automatically applied to all tests.
    """
    # Mock get_settings
    mock_settings_obj = MagicMock()
    mock_settings_obj.GOOGLE_API_KEY = "test_api_key_123"
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings_obj)

    # Mock google.genai.Client
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content = MagicMock(
        return_value=MagicMock(text="Mocked AI Response from genai.Client")
    )
    mocker.patch('google.genai.Client', return_value=mock_genai_client)

    # Mock ProductDataService
    mock_product_service = MagicMock()
    mock_product_service.smart_search_products = AsyncMock(
        return_value=(
            [], "No specific products found from default search."
        )
    )
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_product_service)

    # Mock the module-level logger
    # This patches the logger instance that AIService imports and uses.
    mock_logger = mocker.patch('app.services.ai_service.logger')

    # Return the mocked instances for individual tests to access if needed
    return {
        "settings": mock_settings_obj,
        "genai_client": mock_genai_client,
        "product_service": mock_product_service,
        "logger": mock_logger
    }

@pytest.fixture
def ai_service_instance(setup_common_mocks):
    """
    Provides an initialized AIService instance for tests.
    It relies on `setup_common_mocks` for its dependencies.
    """
    from app.services.ai_service import AIService
    return AIService()

@pytest.fixture
def sample_products():
    """Provides sample product data for testing context building."""
    return [
        {
            'name': 'Laptop Gaming Pro',
            'price': 15000000,
            'brand': 'BrandX',
            'category': 'laptop',
            'specifications': {'rating': 4.5},
            'description': 'A high-performance gaming laptop with RTX 3080, 32GB RAM, and 1TB SSD. Perfect for demanding games and creative tasks. It features a stunning 144Hz display and a backlit keyboard and a very long description to test truncation functionality.'
        },
        {
            'name': 'Smartphone Elite',
            'price': 7500000,
            'brand': 'BrandY',
            'category': 'smartphone',
            'specifications': {'rating': 4.2},
            'description': 'An excellent smartphone with a 108MP camera, 5000mAh battery, and a vibrant AMOLED display. Ideal for photography enthusiasts and heavy users. Comes with fast charging support.'
        },
        {
            'name': 'Headphones X9',
            'price': 2000000,
            'brand': 'AudioPro',
            'category': 'headphone',
            'specifications': {'rating': 4.8},
            'description': 'Premium noise-cancelling headphones with exceptional sound quality and comfort. Long battery life and a sleek design make them perfect for travel or daily commutes.'
        }
    ]

# --- Test Cases for AIService Initialization ---

def test_ai_service_init_success(ai_service_instance, setup_common_mocks):
    """
    Tests that AIService initializes successfully, setting up client and product service,
    and logging the success message.
    """
    assert ai_service_instance.client is not None
    assert ai_service_instance.product_service is not None
    # Verify that get_settings was called and its return value used for API key
    setup_common_mocks["genai_client"].assert_called_once_with(api_key="test_api_key_123")
    setup_common_mocks["product_service"].assert_called_once()
    setup_common_mocks["logger"].info.assert_called_with("Successfully initialized AI service with Google AI client")

def test_ai_service_init_failure_get_settings(mocker):
    """
    Tests AIService initialization failure when `get_settings` raises an error.
    Ensures the error is logged and re-raised.
    """
    mocker.patch('app.utils.config.get_settings', side_effect=ValueError("Test config error"))
    mock_logger = mocker.patch('app.services.ai_service.logger') # Re-patch logger for this specific test
    from app.services.ai_service import AIService
    with pytest.raises(ValueError, match="Test config error"):
        AIService()
    mock_logger.error.assert_called_with("Error initializing AI service: Test config error")

def test_ai_service_init_failure_genai_client(mocker):
    """
    Tests AIService initialization failure when `genai.Client` instantiation raises an error.
    Ensures the error is logged and re-raised.
    """
    mocker.patch('app.utils.config.get_settings', return_value=MagicMock(GOOGLE_API_KEY="dummy_key")) # Ensure settings is fine
    mocker.patch('google.genai.Client', side_effect=Exception("GenAI client init error"))
    mock_logger = mocker.patch('app.services.ai_service.logger') # Re-patch logger for this specific test
    from app.services.ai_service import AIService
    with pytest.raises(Exception, match="GenAI client init error"):
        AIService()
    mock_logger.error.assert_called_with("Error initializing AI service: GenAI client init error")

# --- Test Cases for AIService.get_response ---

@pytest.mark.asyncio
async def test_get_response_basic_question_with_products(ai_service_instance, setup_common_mocks, sample_products):
    """
    Tests `get_response` with a simple question where `smart_search_products` returns products.
    Verifies method calls, return value, and context building in the AI prompt.
    """
    mock_product_service = setup_common_mocks["product_service"]
    mock_genai_client = setup_common_mocks["genai_client"]
    mock_logger = setup_common_mocks["logger"]

    mock_product_service.smart_search_products.return_value = (
        sample_products, "Here are some top recommendations based on your query:"
    )
    mock_genai_client.models.generate_content.return_value = MagicMock(text="AI response about the recommended products.")

    question = "recommend some products for me"
    response = await ai_service_instance.get_response(question)

    # Assertions on method calls
    mock_product_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    mock_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_logger.info.assert_any_call("Successfully generated AI response")
    assert response == "AI response about the recommended products."

    # Verify prompt content passed to generate_content
    prompt_call_args = mock_genai_client.models.generate_content.call_args.kwargs['contents']
    assert f"Question: {question}" in prompt_call_args
    assert "Here are some top recommendations based on your query:" in prompt_call_args
    assert "Relevant Products:\n" in prompt_call_args
    assert "1. Laptop Gaming Pro" in prompt_call_args
    assert "Price: Rp 15,000,000" in prompt_call_args
    assert "Brand: BrandX" in prompt_call_args
    assert "Category: laptop" in prompt_call_args
    assert "Rating: 4.5/5" in prompt_call_args
    # Check for description truncation and ellipsis
    # The actual length of the example description is > 200, so it should be truncated.
    expected_truncated_desc = sample_products[0]['description'][:200]
    assert f"Description: {expected_truncated_desc}..." in prompt_call_args
    assert "2. Smartphone Elite" in prompt_call_args
    assert "3. Headphones X9" in prompt_call_args
    assert "No specific products found, but I can provide general recommendations." not in prompt_call_args

@pytest.mark.asyncio
async def test_get_response_no_products_found(ai_service_instance, setup_common_mocks):
    """
    Tests `get_response` when `smart_search_products` returns no products.
    Verifies `no products found` context is built correctly.
    """
    mock_product_service = setup_common_mocks["product_service"]
    mock_genai_client = setup_common_mocks["genai_client"]

    mock_product_service.smart_search_products.return_value = (
        [], "No specific products found for your very specific query."
    )
    mock_genai_client.models.generate_content.return_value = MagicMock(text="AI response with general advice.")

    question = "looking for a unicorn product"
    response = await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    assert response == "AI response with general advice."

    # Verify prompt content when no products are found
    prompt_call_args = mock_genai_client.models.generate_content.call_args.kwargs['contents']
    assert "No specific products found, but I can provide general recommendations." in prompt_call_args
    assert "Relevant Products:" not in prompt_call_args # Ensure product list section is absent

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    ("rekomendasi laptop", "laptop", None),
    ("cari smartphone", "smartphone", None),
    ("headphone murah", "headphone", 5000000),
    ("tv budget 5 juta", "tv", 5000000),
    ("kamera pro dibawah 10 juta", "kamera", 10000000),
    ("notebook gaming", "laptop", None), # synonym for laptop
    ("hp terbaik", "smartphone", None), # synonym for smartphone
    ("tablet untuk kerja", "tablet", None),
    ("earphone gaming", "headphone", None), # synonym for headphone
    ("speaker bagus", "audio", None),
    ("drone untuk pemula 3 juta", "drone", 3000000),
    ("smartwatch murah", "jam", 5000000), # synonym for jam + budget
    ("komputer 20 juta", "laptop", 20000000), # synonym for laptop + price
    ("ponsel murah", "smartphone", 5000000), # synonym for smartphone + budget
    ("ipad 7 juta", "tablet", 7000000), # synonym for tablet + price
    ("televisi dibawah 15 juta", "tv", 15000000),
    ("camera mirrorless", "kamera", None), # synonym for kamera
    ("audio system", "audio", None),
    ("quadcopter", "drone", None), # synonym for drone
    ("jam tangan pintar", "jam", None), # synonym for jam
    ("produk 50 juta", None, 50000000), # Only price, no category
    ("apa rekomendasi produk dengan budget", None, 5000000), # Only budget, no specific amount
    ("cari yang murah", None, 5000000), # Only "murah" keyword
    ("pertanyaan tanpa kategori atau harga", None, None), # No keywords
    ("laptop dan smartphone", "laptop", None), # Tests category priority (laptop comes first in mapping)
    ("saya ingin membeli hp baru", "smartphone", None) # Test 'hp' keyword
])
async def test_get_response_category_and_price_detection(ai_service_instance, setup_common_mocks,
                                                         question, expected_category, expected_max_price):
    """
    Tests various scenarios for question parsing, verifying correct category and max_price
    are passed to `smart_search_products`.
    """
    mock_product_service = setup_common_mocks["product_service"]
    
    await ai_service_instance.get_response(question)

    mock_product_service.smart_search_products.assert_called_once_with(
        keyword=question, category=expected_category, max_price=expected_max_price, limit=5
    )
    # The AI client is also always called after product search
    setup_common_mocks["genai_client"].models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_get_response_product_service_raises_exception(ai_service_instance, setup_common_mocks):
    """
    Tests `get_response` when `ProductDataService.smart_search_products` raises an exception.
    Ensures a graceful fallback message is returned and error is logged.
    """
    mock_product_service = setup_common_mocks["product_service"]
    mock_logger = setup_common_mocks["logger"]

    mock_product_service.smart_search_products.side_effect = Exception("Product search API error")

    question = "I need a product recommendation"
    response = await ai_service_instance.get_response(question)

    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_logger.error.assert_called_once_with("Error generating AI response: Product search API error")
    # Ensure genai.Client.models.generate_content was NOT called
    setup_common_mocks["genai_client"].models.generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_get_response_genai_client_raises_exception(ai_service_instance, setup_common_mocks):
    """
    Tests `get_response` when `genai.Client.models.generate_content` raises an exception.
    Ensures a graceful fallback message is returned and error is logged.
    """
    mock_genai_client = setup_common_mocks["genai_client"]
    mock_logger = setup_common_mocks["logger"]

    mock_genai_client.models.generate_content.side_effect = Exception("AI generation failed unexpectedly")

    question = "Tell me about products"
    response = await ai_service_instance.get_response(question)

    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    mock_logger.error.assert_called_once_with("Error generating AI response: AI generation failed unexpectedly")
    # Ensure ProductDataService.smart_search_products was called (it succeeds first)
    setup_common_mocks["product_service"].smart_search_products.assert_called_once()

# --- Test Cases for AIService.generate_response (Legacy Method) ---

def test_generate_response_success(ai_service_instance, setup_common_mocks):
    """
    Tests successful execution of the `generate_response` (legacy) method.
    Verifies correct model and context are passed to the AI client and success is logged.
    """
    mock_genai_client = setup_common_mocks["genai_client"]
    mock_logger = setup_common_mocks["logger"]

    context_text = "This is a custom context provided for the legacy AI response."
    expected_ai_response = "Here is the AI response based on your custom context."
    mock_genai_client.models.generate_content.return_value = MagicMock(text=expected_ai_response)

    response = ai_service_instance.generate_response(context_text)

    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args.kwargs
    assert call_args['model'] == "gemini-2.0-flash"
    assert context_text in call_args['contents']
    assert "You are a helpful product assistant." in call_args['contents']
    assert "Please provide a clear and concise answer that helps the user understand the products and make an informed decision." in call_args['contents']
    assert response == expected_ai_response
    mock_logger.info.assert_any_call("Generating AI response")
    mock_logger.info.assert_any_call("Successfully generated AI response")

def test_generate_response_raises_exception(ai_service_instance, setup_common_mocks):
    """
    Tests `generate_response` when `genai.Client.models.generate_content` raises an exception.
    Ensures the exception is re-raised and error is logged.
    """
    mock_genai_client = setup_common_mocks["genai_client"]
    mock_logger = setup_common_mocks["logger"]

    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI generation error")

    context_text = "Some legacy context"
    with pytest.raises(Exception, match="Legacy AI generation error"):
        ai_service_instance.generate_response(context_text)

    mock_genai_client.models.generate_content.assert_called_once()
    mock_logger.error.assert_called_once_with("Error generating AI response: Legacy AI generation error")