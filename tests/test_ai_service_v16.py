import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from app.services.ai_service import AIService

# --- Dummy Classes/Mocks for External Dependencies ---
# These are used as specs for MagicMock to ensure attribute access correctness.
# In a real project, you might import these actual classes if they exist and are accessible.
class MockSettings:
    """A dummy class to represent the structure of settings returned by get_settings."""
    GOOGLE_API_KEY: str = "dummy_api_key_123"

class MockGenaiClient:
    """A dummy class to represent the structure of google.genai.Client."""
    def __init__(self, api_key: str):
        pass
    models = MagicMock()

class MockProductDataService:
    """A dummy class to represent the structure of ProductDataService."""
    async def smart_search_products(self, keyword: str, category: str, max_price: int, limit: int):
        pass

# --- Pytest Fixtures ---
@pytest.fixture
def mock_settings():
    """Fixture to mock app.utils.config.get_settings()."""
    mock_settings_obj = MagicMock(spec=MockSettings)
    mock_settings_obj.GOOGLE_API_KEY = "test_google_api_key"
    with patch('app.utils.config.get_settings', return_value=mock_settings_obj):
        yield mock_settings_obj

@pytest.fixture
def mock_genai_client():
    """Fixture to mock google.genai.Client."""
    mock_client = MagicMock(spec=MockGenaiClient)
    # Default return value for successful AI response generation
    mock_client.models.generate_content.return_value.text = "AI response from Gemini model"
    with patch('google.genai.Client', return_value=mock_client):
        yield mock_client

@pytest.fixture
def mock_product_data_service():
    """Fixture to mock app.services.product_data_service.ProductDataService."""
    # Use AsyncMock as smart_search_products is an async method
    mock_service = AsyncMock(spec=MockProductDataService)
    # Default return value for smart_search_products (no products, generic fallback)
    mock_service.smart_search_products.return_value = ([], "No specific product context found for this query.")
    with patch('app.services.product_data_service.ProductDataService', return_value=mock_service):
        yield mock_service

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service):
    """Fixture to provide an AIService instance with all its dependencies mocked."""
    # AIService's __init__ will use the patched get_settings, genai.Client, and ProductDataService
    return AIService()

# --- Test Cases for AIService.__init__ ---
class TestAIServiceInit:
    def test_init_success(self, mock_settings, mock_genai_client, mock_product_data_service, caplog):
        """
        Test successful initialization of AIService.
        Verifies correct calls to external services and log messages.
        """
        caplog.set_level(logging.INFO)
        service = AIService()

        # Assert that genai.Client and ProductDataService were instantiated with correct arguments
        mock_genai_client.assert_called_once_with(api_key="test_google_api_key")
        mock_product_data_service.assert_called_once()

        # Assert log message
        assert "Successfully initialized AI service with Google AI client" in caplog.text

        # Assert that the instance attributes are correctly set to the mocked objects
        assert isinstance(service.client, MagicMock)
        assert isinstance(service.product_service, AsyncMock)

    def test_init_failure(self, mock_settings, caplog):
        """
        Test initialization failure when an exception occurs during genai.Client instantiation.
        Verifies error logging and exception re-raising.
        """
        caplog.set_level(logging.ERROR)
        # Simulate an exception during genai.Client initialization
        with patch('google.genai.Client', side_effect=Exception("Google AI Client Init Error")):
            with pytest.raises(Exception, match="Google AI Client Init Error"):
                AIService()
            # Assert log message for error
            assert "Error initializing AI service: Google AI Client Init Error" in caplog.text

# --- Test Cases for AIService.get_response (async method) ---
class TestAIServiceGetResponse:

    @pytest.mark.asyncio
    async def test_get_response_general_question_no_category_price(
        self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog
    ):
        """
        Test get_response with a general question that doesn't contain category
        or price keywords. Ensures correct default parameters are passed to
        smart_search_products and context is built correctly for no products.
        """
        caplog.set_level(logging.INFO)
        question = "Tell me about some interesting products."
        # Configure smart_search_products to return no products
        mock_product_data_service.smart_search_products.return_value = (
            [], 
            "No specific product context found for this general query."
        )

        response = await ai_service_instance.get_response(question)

        # Verify smart_search_products was called with default None for category/price
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )

        # Verify genai.Client.models.generate_content was called
        mock_genai_client.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']

        # Assert prompt content
        assert f"Question: {question}" in prompt
        assert "No specific product context found for this general query." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # Should not include product list
        assert "AI response from Gemini model" == response
        
        # Assert log messages
        assert f"Getting AI response for question: {question}" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category", [
        ("Cari laptop gaming", "laptop"),
        ("HP Samsung terbaru", "smartphone"),
        ("handphone murah", "smartphone"),
        ("Tablet murah", "tablet"),
        ("Headset Bluetooth", "headphone"),
        ("earphone terbaik", "headphone"),
        ("Kamera DSLR", "kamera"),
        ("fotografi", "kamera"),
        ("Speaker portabel", "audio"),
        ("sound system", "audio"),
        ("Televisi pintar", "tv"),
        ("Drone DJI", "drone"),
        ("Jam tangan pintar", "jam"),
        ("smartwatch rekomendasi", "jam"),
        ("Apapun", None), # Test case for no category match
        ("sepeda listrik", None), # Another test for no category match
    ])
    async def test_get_response_with_category_detection(
        self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category
    ):
        """Test get_response correctly detects various categories from questions."""
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=None, limit=5
        )
        mock_product_data_service.smart_search_products.reset_mock() # Reset for next param

    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_max_price", [
        ("Laptop harga 10 juta", 10000000),
        ("Smartphone budget 5 juta", 5000000),
        ("Cari hp murah", 5000000), # Test 'murah' keyword
        ("Tablet di bawah 2 juta", 2000000), # Test only 'juta' keyword
        ("Ada TV 15 juta", 15000000),
        ("Produk tanpa budget", None), # Test case for no price match
    ])
    async def test_get_response_with_price_detection(
        self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_max_price
    ):
        """Test get_response correctly detects various price ranges from questions."""
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=expected_max_price, limit=5
        )
        mock_product_data_service.smart_search_products.reset_mock() # Reset for next param

    @pytest.mark.asyncio
    async def test_get_response_with_category_and_price(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """Test get_response when both category and price are detected in the question."""
        question = "Cari laptop gaming budget 20 juta"
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category='laptop', max_price=20000000, limit=5
        )

    @pytest.mark.asyncio
    async def test_get_response_with_products_found(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """
        Test get_response when smart_search_products returns relevant products.
        Verifies that product details are correctly formatted into the AI prompt context.
        """
        question = "Rekomendasi laptop harga 10 juta"
        mock_products = [
            {
                "name": "Super Laptop X1",
                "price": 10000000,
                "brand": "TechBrand",
                "category": "laptop",
                "specifications": {"rating": 4.5},
                "description": "Powerful laptop for gaming and work and productivity. This is a very long description to test the truncation logic to ensure it works correctly and doesn't break the context generation. It should be truncated to 200 characters plus ellipsis."
            },
            {
                "name": "Budget Laptop Y2",
                "price": 8000000,
                "brand": "EcoTech",
                "category": "laptop",
                "specifications": {"rating": 3.8},
                "description": "Affordable laptop for daily use, good for students and light tasks."
            }
        ]
        mock_fallback_message = "We found a couple of great laptops that match your criteria!"
        mock_product_data_service.smart_search_products.return_value = (mock_products, mock_fallback_message)

        response = await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']

        # Assert prompt contains all expected product details and formatting
        assert f"Question: {question}" in prompt
        assert mock_fallback_message in prompt
        assert "Relevant Products:\n" in prompt
        assert "1. Super Laptop X1" in prompt
        assert "Price: Rp 10,000,000" in prompt # Check price formatting
        assert "Brand: TechBrand" in prompt
        assert "Category: laptop" in prompt
        assert "Rating: 4.5/5" in prompt
        # Check description truncation (first 200 chars + "...")
        expected_desc_truncated = "Powerful laptop for gaming and work and productivity. This is a very long description to test the truncation logic to ensure it works correctly and doesn't break the context generation. It should be truncated to 200 characters plus ellipsis..."
        assert f"Description: {expected_desc_truncated}" in prompt
        
        assert "2. Budget Laptop Y2" in prompt
        assert "AI response from Gemini model" == response

    @pytest.mark.asyncio
    async def test_get_response_product_details_missing_fields(
        self, ai_service_instance, mock_product_data_service, mock_genai_client
    ):
        """
        Test context generation when product dictionaries have missing or None values.
        Ensures defaults ('Unknown', 0, 'No description') are used.
        """
        question = "Products with missing details"
        mock_products = [
            { # All fields missing or None
                "name": None,
                "price": None,
                "brand": None,
                "category": None,
                "specifications": {}, # 'rating' key missing inside 'specifications'
                "description": None
            },
            { # Some fields provided
                "name": "Partial Product",
                "price": 100000,
                "description": "Short description"
            }
        ]
        mock_product_data_service.smart_search_products.return_value = (
            mock_products, "Some products found with missing details."
        )

        await ai_service_instance.get_response(question)
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']

        # Check for defaults for the first product
        assert "1. Unknown" in prompt
        assert "Price: Rp 0" in prompt
        assert "Brand: Unknown" in prompt
        assert "Category: Unknown" in prompt
        assert "Rating: 0/5" in prompt
        assert "Description: No description..." in prompt

        # Check for provided values for the second product
        assert "2. Partial Product" in prompt
        assert "Price: Rp 100,000" in prompt
        assert "Description: Short description..." in prompt # Still truncated even if short

    @pytest.mark.asyncio
    async def test_get_response_product_data_service_raises_exception(
        self, ai_service_instance, mock_product_data_service, caplog
    ):
        """
        Test get_response when ProductDataService.smart_search_products raises an exception.
        Verifies error logging and fallback message return.
        """
        caplog.set_level(logging.ERROR)
        question = "Question causing product service error"
        mock_product_data_service.smart_search_products.side_effect = Exception("Product database connection failed")

        response = await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        assert "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti." == response
        assert "Error generating AI response: Product database connection failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_genai_client_raises_exception(
        self, ai_service_instance, mock_genai_client, caplog
    ):
        """
        Test get_response when genai.Client.models.generate_content raises an exception.
        Verifies error logging and fallback message return.
        """
        caplog.set_level(logging.ERROR)
        question = "Question causing AI generation error"
        # Ensure product service returns something so we reach the genai client call
        ai_service_instance.product_service.smart_search_products.return_value = (
            [], "No specific product context."
        )
        mock_genai_client.models.generate_content.side_effect = Exception("Google AI API call failed")

        response = await ai_service_instance.get_response(question)

        mock_genai_client.models.generate_content.assert_called_once()
        assert "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti." == response
        assert "Error generating AI response: Google AI API call failed" in caplog.text

# --- Test Cases for AIService.generate_response (legacy method) ---
class TestAIServiceGenerateResponse:
    def test_generate_response_success(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test successful execution of the legacy generate_response method.
        Verifies correct model usage and prompt content.
        """
        caplog.set_level(logging.INFO)
        context = "This is a test context for the legacy AI response generation method."
        mock_genai_client.models.generate_content.return_value.text = "Legacy AI response from Gemini 2.0 Flash"

        response = ai_service_instance.generate_response(context) # Note: This method is not async

        # Verify genai.Client.models.generate_content was called with specific model and prompt
        mock_genai_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents=f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
        )
        assert "Legacy AI response from Gemini 2.0 Flash" == response
        
        # Assert log messages
        assert "Generating AI response" in caplog.text
        assert "Successfully generated AI response" in caplog.text

    def test_generate_response_failure(self, ai_service_instance, mock_genai_client, caplog):
        """
        Test generate_response when genai.Client.models.generate_content raises an exception.
        Verifies error logging and exception re-raising.
        """
        caplog.set_level(logging.ERROR)
        context = "Error test context for legacy method."
        mock_genai_client.models.generate_content.side_effect = Exception("Legacy GenAI API error")

        with pytest.raises(Exception, match="Legacy GenAI API error"):
            ai_service_instance.generate_response(context) # Note: This method is not async

        mock_genai_client.models.generate_content.assert_called_once()
        assert "Error generating AI response: Legacy GenAI API error" in caplog.text