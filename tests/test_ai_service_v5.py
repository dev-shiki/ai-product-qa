import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Suppress logging during tests to prevent clutter unless specifically tested
logging.disable(logging.CRITICAL)

# Import the class to be tested
# Adjust the import path based on the target test file location (test_services/)
from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Mocks the get_settings function to provide a mock API key."""
    mock = MagicMock()
    mock.GOOGLE_API_KEY = "test_api_key_123"
    # Patch the get_settings function in the module where it's used
    with patch('app.utils.config.get_settings', return_value=mock) as _mock_settings:
        yield _mock_settings

@pytest.fixture
def mock_genai_client():
    """
    Mocks google.genai.Client and its models.generate_content method.
    The patch is applied at the point where `genai.Client` is imported and used in `AIService`.
    """
    mock_client_instance = MagicMock()
    # Configure the mock response for generate_content
    mock_response = MagicMock()
    mock_response.text = "Mocked AI response text."
    mock_client_instance.models.generate_content.return_value = mock_response
    
    # Patch genai.Client class itself so AIService.__init__ receives our mock
    # The patch target needs to be where genai.Client is looked up by AIService, which is its own module
    with patch('app.services.ai_service.genai.Client', return_value=mock_client_instance) as _mock_client_class:
        yield _mock_client_class # Yield the mock for the Client class

@pytest.fixture
def mock_product_service():
    """
    Mocks ProductDataService and its async smart_search_products method.
    The patch is applied at the point where `ProductDataService` is imported and used in `AIService`.
    """
    mock_service_instance = AsyncMock() # AsyncMock for the instance
    # Default return value for smart_search_products
    mock_service_instance.smart_search_products.return_value = ([], "No specific products found.")
    
    # Patch ProductDataService class itself so AIService.__init__ receives our mock
    # The patch target needs to be where ProductDataService is looked up by AIService, its own module
    with patch('app.services.ai_service.ProductDataService', return_value=mock_service_instance) as _mock_product_service_class:
        yield _mock_product_service_class # Yield the mock for the ProductDataService class

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_service):
    """
    Provides an initialized AIService instance for tests.
    The required mocks are already active due to their respective fixture scopes.
    """
    return AIService()

# --- Tests for __init__ method ---

def test_ai_service_init_success(mock_settings, mock_genai_client, mock_product_service, caplog):
    """
    Test that AIService initializes successfully, verifying all dependencies are correctly set up
    and an info log is recorded.
    """
    with caplog.at_level(logging.INFO):
        service = AIService()
        
        # Verify that get_settings was called
        mock_settings.assert_called_once()
        
        # Verify genai.Client was initialized with the correct API key
        mock_genai_client.assert_called_once_with(api_key="test_api_key_123")
        assert service.client == mock_genai_client.return_value # Check that service.client is the mocked instance
        
        # Verify ProductDataService was initialized
        mock_product_service.assert_called_once()
        assert service.product_service == mock_product_service.return_value # Check that service.product_service is the mocked instance

        # Verify info log message
        assert "Successfully initialized AI service with Google AI client" in caplog.text

def test_ai_service_init_failure(mock_settings, caplog):
    """
    Test that AIService initialization raises an exception and logs an error
    if genai.Client instantiation fails (e.g., due to missing API key, network issue).
    """
    # Simulate an error during genai.Client initialization
    mock_settings.return_value.GOOGLE_API_KEY = None # Simulate missing key or other init error
    with patch('app.services.ai_service.genai.Client', side_effect=Exception("Google AI client initialization failed")):
        with pytest.raises(Exception, match="Google AI client initialization failed"):
            with caplog.at_level(logging.ERROR):
                AIService()
        
        # Verify error log message
        assert "Error initializing AI service: Google AI client initialization failed" in caplog.text

# --- Tests for get_response method ---

@pytest.mark.asyncio
async def test_get_response_success_with_products(ai_service_instance, mock_product_service, mock_genai_client, caplog):
    """
    Test the `get_response` method when `smart_search_products` finds relevant products,
    and the AI successfully generates a response based on the enriched context.
    Checks prompt content, mock calls, and logging.
    """
    question = "Laptop gaming harga 15 juta"
    
    # Configure mock product service to return products with a long description for slicing test
    long_description = "This is a powerful gaming machine designed for high-performance tasks and immersive gaming experiences. It features a cutting-edge processor, dedicated graphics card, ample RAM, and a high-refresh-rate display, making it ideal for competitive gamers and content creators alike. It also boasts an advanced cooling system to prevent overheating during intense sessions. The build quality is premium, ensuring durability and a sleek aesthetic. This laptop offers exceptional value for its price point and is highly recommended by reviewers."
    mock_products = [
        {'name': 'Gaming Laptop X', 'price': 14_000_000, 'brand': 'BrandA', 'category': 'laptop', 'specifications': {'rating': 4.5}, 'description': long_description},
        {'name': 'Gaming Laptop Y', 'price': 16_000_000, 'brand': 'BrandB', 'category': 'laptop', 'specifications': {'rating': 4.0}, 'description': 'High performance laptop with good specs.'}
    ]
    mock_product_service.return_value.smart_search_products.return_value = (mock_products, "Here are some gaming laptops matching your criteria.")

    # Configure mock genai client response
    expected_ai_response = "Berdasarkan pertanyaan Anda, Gaming Laptop X dan Y mungkin cocok untuk Anda. Gaming Laptop X memiliki rating 4.5/5 dan harga Rp 14.000.000."
    mock_genai_client.return_value.models.generate_content.return_value.text = expected_ai_response

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

        assert response == expected_ai_response
        
        # Verify smart_search_products was called with correct parameters
        mock_product_service.return_value.smart_search_products.assert_called_once_with(
            keyword=question, category='laptop', max_price=15_000_000, limit=5
        )
        
        # Verify generate_content was called
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        
        # Check parts of the prompt sent to genai.Client
        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]['contents']
        assert f"Question: {question}" in prompt
        assert "Here are some gaming laptops matching your criteria." in prompt
        assert "Relevant Products:\n" in prompt
        assert "1. Gaming Laptop X" in prompt
        assert "Price: Rp 14,000,000" in prompt
        assert "Brand: BrandA" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.5/5" in prompt
        # Check description slicing and ellipsis ([:200]...)
        assert long_description[:200] + "..." in prompt
        assert "2. Gaming Laptop Y" in prompt
        assert "model=gemini-2.5-flash" in str(kwargs) or "model='gemini-2.5-flash'" in str(args[0]) # Verify model name

        # Verify log messages
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text


@pytest.mark.asyncio
async def test_get_response_success_no_products(ai_service_instance, mock_product_service, mock_genai_client, caplog):
    """
    Test the `get_response` method when `smart_search_products` finds no products,
    and the AI generates a general response. Checks prompt content, mock calls, and logging.
    """
    question = "Rekomendasi produk yang tidak ada di inventori"
    
    # Configure mock product service to return no products
    mock_product_service.return_value.smart_search_products.return_value = ([], "Tidak ada produk yang cocok dengan pencarian Anda.")

    expected_ai_response = "Mohon maaf, saat ini tidak ada produk yang sesuai dengan kriteria Anda. Apakah ada hal lain yang bisa saya bantu?"
    mock_genai_client.return_value.models.generate_content.return_value.text = expected_ai_response

    with caplog.at_level(logging.INFO):
        response = await ai_service_instance.get_response(question)

        assert response == expected_ai_response
        
        # Verify smart_search_products was called with correct parameters (no category/price detected for this question)
        mock_product_service.return_value.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        # Verify generate_content was called
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        
        # Check parts of the prompt sent to genai.Client
        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]['contents']
        assert f"Question: {question}" in prompt
        assert "Tidak ada produk yang cocok dengan pencarian Anda." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # Should not be in prompt if no products

        # Verify log messages
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("question, expected_category, expected_max_price", [
    # Category detection (case-insensitive and aliases)
    ("cari laptop gaming", "laptop", None),
    ("beli hp baru", "smartphone", None),
    ("mau tablet yang bagus", "tablet", None),
    ("headphone murah", "headphone", 5_000_000), # headphone + budget
    ("rekomendasi kamera", "kamera", None),
    ("speaker aktif", "audio", None),
    ("tv pintar", "tv", None),
    ("drone", "drone", None),
    ("smartwatch", "jam", None),
    ("komputer desktop", "laptop", None), # 'komputer' maps to 'laptop'
    ("earphone bluetooth", "headphone", None), # alias
    ("saya mau beli telepon", "smartphone", None), # alias

    # Price detection - 'juta' keyword
    ("laptop harga 10 juta", "laptop", 10_000_000),
    ("smartphone 5 juta", "smartphone", 5_000_000),
    ("kamera dibawah 2 juta", "kamera", 2_000_000),
    ("cari tv 7 juta an", "tv", 7_000_000),
    ("budget 3.5 juta untuk hp", "smartphone", 3_500_000), # Test with decimal and 'juta'
    ("laptop 20jt", "laptop", 20_000_000), # Test with 'jt' alias

    # Price detection - 'budget' or 'murah' keywords (default 5 juta if no 'juta' specified)
    ("cari laptop budget", "laptop", 5_000_000), # category + budget
    ("hp murah", "smartphone", 5_000_000), # category + murah
    ("produk apa saja yang murah", None, 5_000_000), # only murah, no category

    # No category or price detected
    ("apa rekomendasi produk terbaru", None, None),
    ("hallo", None, None),
    ("bagaimana cuaca hari ini?", None, None), # Irrelevant question
    ("cari smartphone dibawah 3 juta", "smartphone", None), # No 'juta' keyword
])
async def test_get_response_category_price_detection(ai_service_instance, mock_product_service, mock_genai_client, 
                                                    question, expected_category, expected_max_price):
    """
    Test that the `get_response` method correctly extracts category and max_price
    from various user questions, passing them to `smart_search_products`.
    """
    # Set default mock responses for successful flow
    mock_product_service.return_value.smart_search_products.return_value = ([], "Fallback message.")
    mock_genai_client.return_value.models.generate_content.return_value.text = "AI Response."

    await ai_service_instance.get_response(question)

    # Verify smart_search_products was called with the correctly detected parameters
    mock_product_service.return_value.smart_search_products.assert_called_once_with(
        keyword=question, 
        category=expected_category, 
        max_price=expected_max_price, 
        limit=5
    )

@pytest.mark.asyncio
async def test_get_response_smart_search_products_failure(ai_service_instance, mock_product_service, caplog):
    """
    Test `get_response` error handling when `smart_search_products` raises an exception.
    It should log the error and return a specific fallback message, without calling the AI.
    """
    question = "Pertanyaan yang menyebabkan error pencarian produk"
    mock_product_service.return_value.smart_search_products.side_effect = Exception("Simulated product search service error")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)

        # Verify the fallback error message is returned
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        
        # Verify the error was logged
        assert "Error generating AI response: Simulated product search service error" in caplog.text
        
        # Verify that smart_search_products was called but generate_content was NOT
        mock_product_service.return_value.smart_search_products.assert_called_once()
        ai_service_instance.client.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_get_response_genai_client_failure(ai_service_instance, mock_product_service, mock_genai_client, caplog):
    """
    Test `get_response` error handling when `genai.Client.models.generate_content` raises an exception.
    It should log the error and return a specific fallback message.
    """
    question = "Pertanyaan untuk AI yang error"
    
    # Ensure product search succeeds so we reach the AI call
    mock_product_service.return_value.smart_search_products.return_value = ([], "Products found ok.")
    
    # Simulate an error during AI content generation
    mock_genai_client.return_value.models.generate_content.side_effect = Exception("Simulated GenAI content generation error")

    with caplog.at_level(logging.ERROR):
        response = await ai_service_instance.get_response(question)

        # Verify the fallback error message is returned
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        
        # Verify the error was logged
        assert "Error generating AI response: Simulated GenAI content generation error" in caplog.text
        
        # Verify both smart_search_products and generate_content were called
        mock_product_service.return_value.smart_search_products.assert_called_once()
        mock_genai_client.return_value.models.generate_content.assert_called_once()

# --- Tests for generate_response (legacy method) ---

def test_generate_response_success(ai_service_instance, mock_genai_client, caplog):
    """
    Test the legacy `generate_response` method success path.
    Checks prompt content, model used, mock calls, and logging.
    """
    context = "This is some pre-formatted product context for the legacy AI method."
    expected_ai_response = "Legacy AI response based on the provided context."
    mock_genai_client.return_value.models.generate_content.return_value.text = expected_ai_response

    with caplog.at_level(logging.INFO):
        response = ai_service_instance.generate_response(context)

        assert response == expected_ai_response
        
        # Verify generate_content was called
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        
        # Check prompt content and model for the legacy method
        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]['contents']
        assert context in prompt
        assert "model='gemini-2.0-flash'" in str(kwargs) or "model='gemini-2.0-flash'" in str(args[0]) # Verify specifically 'gemini-2.0-flash' model

        # Verify log messages
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text


def test_generate_response_genai_client_failure(ai_service_instance, mock_genai_client, caplog):
    """
    Test the legacy `generate_response` method error handling when
    `genai.Client.models.generate_content` raises an exception.
    It should re-raise the exception after logging it.
    """
    context = "Context that causes legacy AI to fail."
    mock_genai_client.return_value.models.generate_content.side_effect = Exception("Legacy GenAI API call failed")

    with pytest.raises(Exception, match="Legacy GenAI API call failed"):
        with caplog.at_level(logging.ERROR):
            ai_service_instance.generate_response(context)
    
    # Verify the error was logged
    assert "Error generating AI response: Legacy GenAI API call failed" in caplog.text
    
    # Verify generate_content was called
    mock_genai_client.return_value.models.generate_content.assert_called_once()