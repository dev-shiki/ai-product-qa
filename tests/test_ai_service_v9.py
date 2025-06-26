import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import logging

# Fixture for mocking app.utils.config.get_settings
@pytest.fixture
def mock_get_settings():
    """Mocks app.utils.config.get_settings to return a mock settings object with an API key."""
    with patch('app.utils.config.get_settings') as mock_settings:
        mock_settings.return_value = MagicMock(GOOGLE_API_KEY="test_api_key_123")
        yield mock_settings

# Fixture for mocking google.genai.Client class
@pytest.fixture
def mock_genai_client_cls():
    """Mocks google.genai.Client class and its instance, setting up a default async return value for generate_content."""
    with patch('google.genai.Client') as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content = AsyncMock()
        # Set a default successful response for genai calls
        mock_instance.models.generate_content.return_value.text = "Mocked AI Response from Gemini"
        mock_client_cls.return_value = mock_instance
        yield mock_client_cls

# Fixture for mocking app.services.product_data_service.ProductDataService class
@pytest.fixture
def mock_product_service_cls():
    """Mocks ProductDataService class and its instance, setting up a default async return value for smart_search_products."""
    with patch('app.services.product_data_service.ProductDataService') as mock_prod_service_cls:
        mock_instance = MagicMock()
        mock_instance.smart_search_products = AsyncMock()
        # Set a default return value for smart_search_products (no products, general message)
        mock_instance.smart_search_products.return_value = ([], "General products information.")
        mock_prod_service_cls.return_value = mock_instance
        yield mock_prod_service_cls

# Fixture for mocking the logger used within AIService
@pytest.fixture
def mock_ai_service_logger():
    """Mocks the specific logger instance used within the AIService module."""
    with patch('app.services.ai_service.logger') as mock_log:
        yield mock_log

# Fixture to provide an initialized AIService instance with all dependencies mocked
@pytest.fixture
def ai_service_instance(mock_get_settings, mock_genai_client_cls, mock_product_service_cls, mock_ai_service_logger):
    """Provides a pre-initialized AIService instance with its external dependencies mocked."""
    # Import the class here to ensure mocks are active when it's initialized
    from app.services.ai_service import AIService
    service = AIService()
    return service


# --- Test Cases for AIService.__init__ ---

def test_ai_service_init_success(mock_get_settings, mock_genai_client_cls, mock_product_service_cls, mock_ai_service_logger):
    """
    Test that AIService successfully initializes by calling get_settings, genai.Client,
    and ProductDataService, and logs the success message.
    """
    from app.services.ai_service import AIService
    service = AIService()

    mock_get_settings.assert_called_once()
    mock_genai_client_cls.assert_called_once_with(api_key="test_api_key_123")
    mock_product_service_cls.assert_called_once()
    mock_ai_service_logger.info.assert_called_once_with("Successfully initialized AI service with Google AI client")
    assert isinstance(service.client, MagicMock)
    assert isinstance(service.product_service, MagicMock)

def test_ai_service_init_get_settings_failure(mock_get_settings, mock_ai_service_logger):
    """
    Test that AIService initialization raises an exception if get_settings fails
    and logs the error.
    """
    mock_get_settings.side_effect = Exception("Config loading error")
    from app.services.ai_service import AIService
    with pytest.raises(Exception, match="Config loading error"):
        AIService()
    mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: Config loading error")

def test_ai_service_init_genai_client_failure(mock_get_settings, mock_genai_client_cls, mock_ai_service_logger):
    """
    Test that AIService initialization raises an exception if genai.Client fails to initialize
    and logs the error.
    """
    mock_genai_client_cls.side_effect = Exception("GenAI client init failed")
    from app.services.ai_service import AIService
    with pytest.raises(Exception, match="GenAI client init failed"):
        AIService()
    mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: GenAI client init failed")

def test_ai_service_init_product_data_service_failure(mock_get_settings, mock_genai_client_cls, mock_product_service_cls, mock_ai_service_logger):
    """
    Test that AIService initialization raises an exception if ProductDataService fails to initialize
    and logs the error.
    """
    mock_product_service_cls.side_effect = Exception("Product service init failed")
    from app.services.ai_service import AIService
    with pytest.raises(Exception, match="Product service init failed"):
        AIService()
    mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: Product service init failed")


# --- Test Cases for AIService.get_response (async) ---

@pytest.mark.asyncio
async def test_get_response_no_category_price_no_products(ai_service_instance, mock_product_service_cls, mock_ai_service_logger):
    """
    Test get_response when the question does not yield a specific category or price,
    and smart_search_products returns no relevant products.
    Ensures correct parameters for smart_search_products and prompt content for genai.
    """
    question = "Can you recommend something general for my home?"
    mock_product_service_cls.return_value.smart_search_products.return_value = ([], "General product information provided.")
    
    response = await ai_service_instance.get_response(question)

    mock_ai_service_logger.info.assert_any_call(f"Getting AI response for question: {question}")
    mock_product_service_cls.return_value.smart_search_products.assert_called_once_with(
        keyword=question, category=None, max_price=None, limit=5
    )
    prompt_content = ai_service_instance.client.models.generate_content.call_args[1]['contents']
    assert "General product information provided." in prompt_content
    assert "No specific products found, but I can provide general recommendations." in prompt_content
    ai_service_instance.client.models.generate_content.assert_called_once()
    assert response == "Mocked AI Response from Gemini"
    mock_ai_service_logger.info.assert_any_call("Successfully generated AI response")

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_price", [
    # Category detection tests
    ("I need a new laptop.", "laptop", None),
    ("Cari notebook yang bagus.", "laptop", None),
    ("Komputer baru dong", "laptop", None),
    ("What smartphone is good?", "smartphone", None),
    ("Rekomendasi hp", "smartphone", None),
    ("Cari handphone", "smartphone", None),
    ("telepon bagus", "smartphone", None),
    ("ponsel terbaru", "smartphone", None),
    ("tablet untuk kerja", "tablet", None),
    ("ipad pro", "tablet", None),
    ("headphone bluetooth", "headphone", None),
    ("earphone gaming", "headphone", None),
    ("headset untuk call", "headphone", None),
    ("kamera dslr", "kamera", None),
    ("camera mirrorless", "kamera", None),
    ("speaker aktif", "audio", None),
    ("soundbar terbaru", "audio", None),
    ("tv 4k", "tv", None),
    ("televisi pintar", "tv", None),
    ("drone dji", "drone", None),
    ("quadcopter", "drone", None),
    ("jam tangan pintar", "jam", None),
    ("smartwatch terbaik", "jam", None),

    # Price detection tests
    ("Cari hp 3 juta.", "smartphone", 3000000),
    ("Laptop harga 7.5 juta", "laptop", 7500000),
    ("TV di bawah 10 juta", "tv", 10000000),
    ("Smartphone budget", "smartphone", 5000000), # Test implicit budget with category
    ("cari laptop murah", "laptop", 5000000), # Test implicit murah with category
    ("budget saya 5 juta", None, 5000000), # Test implicit budget without specific category in query (falls to general)
    ("yang murah saja", None, 5000000), # Test 'murah' without category
    ("apakah ada yang 2 juta?", None, 2000000), # Generic price question
    ("apakah ada jam tangan 1 juta?", "jam", 1000000),

    # Combined category and price detection
    ("Cari laptop gaming 15 juta", "laptop", 15000000),
    ("Rekomendasi smartphone murah", "smartphone", 5000000),
])
async def test_get_response_category_price_detection(ai_service_instance, mock_product_service_cls, question, expected_category, expected_price):
    """
    Test that get_response correctly detects categories and prices from various user questions
    and passes them to smart_search_products.
    """
    await ai_service_instance.get_response(question)
    mock_product_service_cls.return_value.smart_search_products.assert_called_once_with(
        keyword=question, category=expected_category, max_price=expected_price, limit=5
    )

@pytest.mark.asyncio
async def test_get_response_with_products_context_building(ai_service_instance, mock_product_service_cls):
    """
    Test that product context is correctly built within the prompt when products are found.
    Ensures correct formatting, price formatting, and description truncation with ellipsis.
    """
    question = "Show me good laptops."
    long_desc = "This is a very very long description for a test product to ensure that the truncation logic in the AI service works correctly. It should be cut off at 200 characters and followed by an ellipsis. This ensures the prompt doesn't become too large and that the output format is consistent." * 5 # Make it really long
    mock_products = [
        {"name": "Laptop Pro X", "price": 18500000, "brand": "TechCorp", "category": "laptop", "specifications": {"rating": 4.7}, "description": "Powerful laptop for professionals."},
        {"name": "Laptop Lite Y", "price": 7200000, "brand": "Gizmo", "category": "laptop", "specifications": {"rating": 4.2}, "description": long_desc}
    ]
    mock_product_service_cls.return_value.smart_search_products.return_value = (mock_products, "Found these laptops for you.")

    await ai_service_instance.get_response(question)

    prompt_content = ai_service_instance.client.models.generate_content.call_args[1]['contents']
    assert "Relevant Products:\n" in prompt_content
    assert "Found these laptops for you." in prompt_content # Fallback message included

    # Check for Laptop Pro X details
    assert "1. Laptop Pro X" in prompt_content
    assert "Price: Rp 18,500,000" in prompt_content
    assert "Brand: TechCorp" in prompt_content
    assert "Category: laptop" in prompt_content
    assert "Rating: 4.7/5" in prompt_content
    assert "Description: Powerful laptop for professionals..." in prompt_content # Short description still gets '...'

    # Check for Laptop Lite Y details (long description truncation)
    assert "2. Laptop Lite Y" in prompt_content
    assert "Price: Rp 7,200,000" in prompt_content
    assert "Brand: Gizmo" in prompt_content
    assert "Category: laptop" in prompt_content
    assert "Rating: 4.2/5" in prompt_content
    # Verify the truncated part of the long description is in the prompt
    assert long_desc[:200] in prompt_content
    # Verify that the ellipsis is present after truncation (and for all descriptions)
    assert prompt_content.count("...") == len(mock_products)

@pytest.mark.asyncio
async def test_get_response_product_data_missing_keys(ai_service_instance, mock_product_service_cls):
    """
    Test get_response handles product data from smart_search_products having missing keys,
    ensuring default values like 'Unknown', 0, 'No description' are used in the context.
    """
    question = "Show me some products with incomplete data."
    mock_products = [
        {"name": "Product A"}, # Missing price, brand, category, spec, description
        {"name": "Product B", "price": 100000, "brand": "BrandX", "specifications": {}}, # Missing category, rating, description
        {"description": "Just a description"} # Missing name, price, brand, category, spec
    ]
    mock_product_service_cls.return_value.smart_search_products.return_value = (mock_products, "Incomplete products info.")

    await ai_service_instance.get_response(question)

    prompt_content = ai_service_instance.client.models.generate_content.call_args[1]['contents']

    # Product A: All defaults
    assert "1. Product A" in prompt_content
    assert "Price: Rp 0" in prompt_content
    assert "Brand: Unknown" in prompt_content
    assert "Category: Unknown" in prompt_content
    assert "Rating: 0/5" in prompt_content
    assert "Description: No description..." in prompt_content

    # Product B: Some defaults
    assert "2. Product B" in prompt_content
    assert "Price: Rp 100,000" in prompt_content
    assert "Brand: BrandX" in prompt_content
    assert "Category: Unknown" in prompt_content
    assert "Rating: 0/5" in prompt_content
    assert "Description: No description..." in prompt_content

    # Product C: Missing name, other defaults
    assert "3. Unknown" in prompt_content # Name is missing
    assert "Price: Rp 0" in prompt_content
    assert "Brand: Unknown" in prompt_content
    assert "Category: Unknown" in prompt_content
    assert "Rating: 0/5" in prompt_content
    assert "Description: Just a description..." in prompt_content


@pytest.mark.asyncio
async def test_get_response_product_service_raises_exception(ai_service_instance, mock_product_service_cls, mock_ai_service_logger):
    """
    Test get_response handles an exception raised by smart_search_products
    and returns the predefined error message without calling genai.
    """
    question = "Query that causes product search error"
    mock_product_service_cls.return_value.smart_search_products.side_effect = Exception("Product search API failed")
    
    response = await ai_service_instance.get_response(question)

    mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: Product search API failed")
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
    ai_service_instance.client.models.generate_content.assert_not_called() # Ensure genai call is skipped

@pytest.mark.asyncio
async def test_get_response_genai_client_raises_exception(ai_service_instance, mock_product_service_cls, mock_ai_service_logger):
    """
    Test get_response handles an exception raised by genai.Client.models.generate_content
    and returns the predefined error message.
    """
    question = "Query that causes AI generation error"
    # Ensure smart_search_products succeeds so genai call is attempted
    mock_product_service_cls.return_value.smart_search_products.return_value = ([], "No products.")
    ai_service_instance.client.models.generate_content.side_effect = Exception("GenAI generation API failed")
    
    response = await ai_service_instance.get_response(question)

    mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: GenAI generation API failed")
    assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."


# --- Test Cases for AIService.generate_response (legacy method) ---

def test_generate_response_success(ai_service_instance, mock_ai_service_logger):
    """
    Test that the legacy generate_response method works successfully,
    calling genai with the correct model and prompt, and returning the response text.
    """
    context_data = "This is a detailed context for a product recommendation. User wants a cheap laptop."
    ai_service_instance.client.models.generate_content.return_value.text = "Legacy AI: Based on the context, here is a helpful response."

    response = ai_service_instance.generate_response(context_data)

    mock_ai_service_logger.info.assert_any_call("Generating AI response")
    expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context_data}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
    ai_service_instance.client.models.generate_content.assert_called_once_with(
        model="gemini-2.0-flash", # Specific model for legacy method
        contents=expected_prompt
    )
    assert response == "Legacy AI: Based on the context, here is a helpful response."
    mock_ai_service_logger.info.assert_any_call("Successfully generated AI response")

def test_generate_response_genai_client_raises_exception(ai_service_instance, mock_ai_service_logger):
    """
    Test that the legacy generate_response method re-raises an exception
    from genai.Client and logs the error.
    """
    context_data = "Error context for legacy generation test."
    ai_service_instance.client.models.generate_content.side_effect = Exception("Legacy GenAI API failed")

    with pytest.raises(Exception, match="Legacy GenAI API failed"):
        ai_service_instance.generate_response(context_data)

    mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: Legacy GenAI API failed")