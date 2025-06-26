import pytest
from unittest.mock import Mock, patch, AsyncMock
import logging
import sys
import os

# Adjusting sys.path to allow imports from the 'app' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.ai_service import AIService
from app.utils.config import Settings # Assuming Settings class is defined in app.utils.config

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Mocks the get_settings function to return a mock Settings object."""
    settings = Mock(spec=Settings)
    settings.GOOGLE_API_KEY = "test_api_key_123"
    return settings

@pytest.fixture
def mock_genai_client():
    """
    Mocks the google.genai.Client instance.
    The `generate_content` method is an AsyncMock for `get_response` (awaited)
    and also configured to work for `generate_response` (not awaited).
    """
    mock_client = Mock()
    mock_client.models = Mock() # Ensure models attribute exists
    
    # Configure the generate_content method to be an AsyncMock.
    # The return_value will be the awaited result for AsyncMock.
    mock_generate_content_result = Mock()
    mock_generate_content_result.text = "Mocked AI response text for awaited call."
    
    # The AsyncMock instance itself needs a `.text` attribute for the
    # `generate_response` method, which does not await.
    mock_genai_method = AsyncMock(return_value=mock_generate_content_result)
    mock_genai_method.text = "Mocked AI response text for sync access."

    mock_client.models.generate_content = mock_genai_method
    return mock_client

@pytest.fixture
def mock_product_data_service():
    """Mocks the ProductDataService instance."""
    mock_service = Mock()
    mock_service.smart_search_products = AsyncMock() # smart_search_products is an async method
    # Default return for product search: no products
    mock_service.smart_search_products.return_value = ([], "No specific products found.")
    return mock_service

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service):
    """
    Provides an AIService instance with its dependencies (settings, genai client,
    and product service) mocked.
    """
    with patch('app.utils.config.get_settings', return_value=mock_settings), \
         patch('google.genai.Client', return_value=mock_genai_client), \
         patch('app.services.product_data_service.ProductDataService', return_value=mock_product_data_service):
        service = AIService()
        yield service # Use yield to allow for potential cleanup or specific patching in tests

# --- Tests for AIService Initialization ---

def test_aiservice_init_success(ai_service_instance, mock_genai_client, mock_product_data_service, caplog):
    """
    Tests successful initialization of AIService.
    Verifies that client and product_service are set and a log message is emitted.
    """
    with caplog.at_level(logging.INFO):
        assert isinstance(ai_service_instance.client, Mock)
        assert ai_service_instance.client == mock_genai_client
        assert isinstance(ai_service_instance.product_service, Mock)
        assert ai_service_instance.product_service == mock_product_data_service
        assert "Successfully initialized AI service with Google AI client" in caplog.text
    # Ensure client and product service are indeed the mocked objects and their constructors were called
    mock_genai_client.assert_called_once()
    mock_product_data_service.assert_called_once()


def test_aiservice_init_get_settings_failure(caplog):
    """
    Tests AIService initialization failure when get_settings raises an exception.
    Ensures an exception is re-raised and an error log is created.
    """
    with patch('app.utils.config.get_settings', side_effect=Exception("Config error")), \
         caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Config error"):
            AIService()
        assert "Error initializing AI service: Config error" in caplog.text

def test_aiservice_init_genai_client_failure(mock_settings, caplog):
    """
    Tests AIService initialization failure when google.genai.Client constructor
    raises an exception. Ensures an exception is re-raised and an error log is created.
    """
    with patch('app.utils.config.get_settings', return_value=mock_settings), \
         patch('google.genai.Client', side_effect=Exception("Client init error")), \
         caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Client init error"):
            AIService()
        assert "Error initializing AI service: Client init error" in caplog.text

def test_aiservice_init_product_service_failure(mock_settings, mock_genai_client, caplog):
    """
    Tests AIService initialization failure when ProductDataService constructor
    raises an exception. Ensures an exception is re-raised and an error log is created.
    """
    with patch('app.utils.config.get_settings', return_value=mock_settings), \
         patch('google.genai.Client', return_value=mock_genai_client), \
         patch('app.services.product_data_service.ProductDataService', side_effect=Exception("Product service init error")), \
         caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Product service init error"):
            AIService()
        assert "Error initializing AI service: Product service init error" in caplog.text


# --- Tests for get_response method ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
    """
    Tests get_response when product search returns relevant products.
    Verifies correct context building and AI response.
    """
    question = "Cari laptop gaming di bawah 10 juta"
    mock_products = [
        {"name": "Awesome Laptop", "price": 9500000, "brand": "BrandX", "category": "laptop", "specifications": {"rating": 4.5}, "description": "High performance gaming laptop for pros."},
        {"name": "Budget Laptop", "price": 7000000, "brand": "BrandY", "category": "laptop", "specifications": {"rating": 4.0}, "description": "Affordable gaming laptop for casual gamers who want value."}
    ]
    mock_fallback_message = "Found some great laptops for you!"

    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    mock_genai_client.models.generate_content.return_value.text = "Based on your interest, Awesome Laptop and Budget Laptop are good options."

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

        assert response == "Based on your interest, Awesome Laptop and Budget Laptop are good options."
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category="laptop", max_price=10000000, limit=5
        )
        mock_genai_client.models.generate_content.assert_called_once()
        call_args, _ = mock_genai_client.models.generate_content.call_args
        prompt = call_args[0]['contents']

        assert "Question: Cari laptop gaming di bawah 10 juta" in prompt
        assert "Found some great laptops for you!" in prompt
        assert "Relevant Products:" in prompt
        assert "1. Awesome Laptop" in prompt
        assert "Price: Rp 9,500,000" in prompt
        assert "Brand: BrandX" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.5/5" in prompt
        assert "Description: High performance gaming laptop for pros..." in prompt # Checks truncation
        assert "2. Budget Laptop" in prompt
        assert "Successfully generated AI response" in caplog.text
        assert "gemini-2.5-flash" in call_args[0]['model']


@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
    """
    Tests get_response when product search returns no relevant products.
    Verifies correct context building (without products) and AI response.
    """
    question = "Can you recommend a very specific item I just made up?"
    mock_product_data_service.smart_search_products.return_value = ([], "Could not find products matching your exact query.")
    mock_genai_client.models.generate_content.return_value.text = "I'm sorry, I couldn't find specific products for that. Can I help with general info?"

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

        assert response == "I'm sorry, I couldn't find specific products for that. Can I help with general info?"
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        mock_genai_client.models.generate_content.assert_called_once()
        call_args, _ = mock_genai_client.models.generate_content.call_args
        prompt = call_args[0]['contents']

        assert "Question: Can you recommend a very specific item I just made up?" in prompt
        assert "Could not find products matching your exact query." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # Ensure this is not present
        assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
async def test_get_response_ai_generation_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Tests get_response when the AI client fails to generate a response.
    Verifies that a friendly fallback message is returned and an error is logged.
    """
    question = "Tell me something."
    mock_genai_client.models.generate_content.side_effect = Exception("AI API error")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)

        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        mock_genai_client.models.generate_content.assert_called_once()
        assert "Error generating AI response: AI API error" in caplog.text

@pytest.mark.asyncio
async def test_get_response_product_data_service_failure(ai_service_instance, mock_product_data_service, caplog):
    """
    Tests get_response when the product data service fails.
    Verifies that a friendly fallback message is returned and an error is logged.
    """
    question = "Cari laptop."
    mock_product_data_service.smart_search_products.side_effect = Exception("Product service internal error")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)

        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        mock_product_data_service.smart_search_products.assert_called_once()
        assert "Error generating AI response: Product service internal error" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, expected_category, expected_max_price",
    [
        ("Cari laptop gaming 10 juta", "laptop", 10_000_000),
        ("Smartphone murah", "smartphone", 5_000_000), # Detects 'smartphone' and 'murah' for price
        ("Tablet di bawah 5 juta", "tablet", 5_000_000), # Detects 'tablet' and '5 juta' for price
        ("earphone bluetooth", "headphone", None),
        ("Kamera DSLR bagus", "kamera", None),
        ("TV Samsung 20 juta", "tv", 20_000_000),
        ("Jam tangan pintar", "jam", None),
        ("Ponsel dengan budget 7 juta", "smartphone", 7_000_000),
        ("Headset gaming", "headphone", None),
        ("Cari produk audio", "audio", None),
        ("Apa rekomendasi terbaik?", None, None), # No category, no price
        ("Saya mau beli HP dengan 3 juta", "smartphone", 3_000_000),
        ("drone budget 10 juta", "drone", 10_000_000),
        ("notebook 8 juta", "laptop", 8_000_000),
        ("ipad pro", "tablet", None),
        ("handphone 2 juta", "smartphone", 2_000_000),
        ("TV yang murah", "tv", 5_000_000), # Test 'murah' with category
        ("budget murah untuk audio", "audio", 5_000_000), # Test 'budget' with category
        ("telepon seluler", "smartphone", None), # Test synonym
        ("komputer baru", "laptop", None), # Test synonym
        ("fotografi gear", "kamera", None), # Test synonym
        ("speaker bluetooth", "audio", None), # Test synonym
        ("ponsel android 4 juta", "smartphone", 4_000_000), # Combined
        ("smartwatch 1 juta", "jam", 1_000_000), # Combined
        ("Produk", None, None), # Very general, no category or price
        ("laptop budget", "laptop", 5_000_000), # Category + "budget"
        ("Headphone murah banget", "headphone", 5_000_000), # Category + "murah"
        ("Cari smartphone", "smartphone", None), # Just category
        ("Harga 2 juta", None, 2_000_000), # Just price (no category)
        ("Sebuah kamera", "kamera", None), # Basic category detection
        ("TV", "tv", None), # Minimal category detection
    ]
)
async def test_get_response_category_and_price_detection(
    ai_service_instance, mock_product_data_service, mock_genai_client,
    question, expected_category, expected_max_price
):
    """
    Tests that get_response correctly extracts category and max_price from various questions.
    """
    await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once()
    call_args, _ = mock_product_data_service.smart_search_products.call_args

    assert call_args[1]['category'] == expected_category
    assert call_args[1]['max_price'] == expected_max_price
    assert call_args[1]['keyword'] == question # Ensure keyword is always passed


@pytest.mark.asyncio
async def test_get_response_empty_question(ai_service_instance, mock_product_data_service, mock_genai_client):
    """
    Tests get_response with an empty question string.
    Ensures smart_search_products is called with keyword="", category=None, max_price=None.
    """
    question = ""
    await ai_service_instance.get_response(question)

    mock_product_data_service.smart_search_products.assert_called_once_with(
        keyword="", category=None, max_price=None, limit=5
    )
    mock_genai_client.models.generate_content.assert_called_once()
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']
    assert "Question: \n\nNo specific products found, but I can provide general recommendations." in prompt
    assert "gemini-2.5-flash" in call_args[0]['model']

@pytest.mark.asyncio
async def test_get_response_product_context_missing_keys(ai_service_instance, mock_product_data_service, mock_genai_client):
    """
    Tests that product context building handles missing keys gracefully by using default values.
    """
    question = "Products with missing info"
    mock_products = [
        # Missing 'name', 'brand', 'category', 'specifications' (and thus rating)
        {"price": 1000000, "description": "A very basic product description."},
        # Missing 'price', 'description', has empty 'specifications'
        {"name": "Product B", "brand": "BrandB", "category": "tablet", "specifications": {}},
        # All fields present, but rating is missing within specifications
        {"name": "Product C", "price": 5000000, "brand": "BrandC", "category": "laptop", "specifications": {"display": "13 inch"}, "description": "Another product description."},
    ]
    mock_fallback_message = "Some products with incomplete data."
    mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)
    mock_genai_client.models.generate_content.return_value.text = "Response about products with missing info."

    response = await ai_service_instance.get_response(question)

    assert response == "Response about products with missing info."
    mock_genai_client.models.generate_content.assert_called_once()
    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']

    assert "1. Unknown" in prompt
    assert "Price: Rp 1,000,000" in prompt
    assert "Brand: Unknown" in prompt
    assert "Category: Unknown" in prompt
    assert "Rating: 0/5" in prompt
    assert "Description: A very basic product description...." in prompt # Default description truncation

    assert "2. Product B" in prompt
    assert "Price: Rp 0" in prompt # Default for missing price
    assert "Brand: BrandB" in prompt
    assert "Category: tablet" in prompt
    assert "Rating: 0/5" in prompt # Default for missing rating
    assert "Description: No description..." in prompt # Default for missing description

    assert "3. Product C" in prompt
    assert "Price: Rp 5,000,000" in prompt
    assert "Brand: BrandC" in prompt
    assert "Category: laptop" in prompt
    assert "Rating: 0/5" in prompt # Default for rating if key is missing in specifications
    assert "Description: Another product description...." in prompt


@pytest.mark.asyncio
async def test_get_response_product_description_truncation(ai_service_instance, mock_product_data_service, mock_genai_client):
    """
    Tests that product descriptions are truncated to 200 characters with '...' correctly.
    """
    question = "Long description product"
    long_description = "A" * 250
    mock_products = [
        {"name": "Product with Long Desc", "price": 100, "brand": "Test", "category": "test", "specifications": {"rating": 5}, "description": long_description},
    ]
    mock_product_data_service.smart_search_products.return_value = (mock_products, "Found one.")
    mock_genai_client.models.generate_content.return_value.text = "Truncated description response."

    await ai_service_instance.get_response(question)

    call_args, _ = mock_genai_client.models.generate_content.call_args
    prompt = call_args[0]['contents']

    expected_truncated_desc = long_description[:200] + "..."
    assert f"Description: {expected_truncated_desc}\n\n" in prompt
    assert len(prompt) > 200 # Ensure the full prompt is still long
    assert prompt.count("...") > 0 # Check for truncation ellipsis


# --- Tests for generate_response method (legacy) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog):
    """
    Tests successful execution of the legacy generate_response method.
    Verifies the correct AI model and content are used.
    Note: This method does not 'await' the genai client call. The test accounts for this
    by ensuring the mock returns an object with a '.text' attribute directly.
    """
    context = "This is a test context for legacy generation."
    expected_response_text = "Legacy AI response."

    # Configure the mock_genai_client fixture's generate_content method for this specific test
    # to return the expected text directly, as it's not awaited in generate_response.
    # The fixture already sets `mock_genai_method.text = "..."` on the AwaitableMock.
    mock_genai_client.models.generate_content.text = expected_response_text
    
    with caplog.at_level(logging.INFO):
        response = ai_service_instance.generate_response(context)

        assert response == expected_response_text
        mock_genai_client.models.generate_content.assert_called_once()
        call_args, _ = mock_genai_client.models.generate_content.call_args
        assert call_args[0]['model'] == "gemini-2.0-flash"
        expected_prompt_part = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
        assert expected_prompt_part in call_args[0]['contents']
        assert "Successfully generated AI response" in caplog.text

def test_generate_response_ai_generation_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Tests generate_response when the AI client fails to generate a response.
    Ensures an exception is re-raised and an error is logged.
    """
    context = "Failing context."
    
    # Configure the mock_genai_client fixture's generate_content method to raise an exception
    # directly when called (as it's not awaited here).
    mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI API error")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception, match="Legacy AI API error"):
            ai_service_instance.generate_response(context)
        mock_genai_client.models.generate_content.assert_called_once()
        assert "Error generating AI response: Legacy AI API error" in caplog.text