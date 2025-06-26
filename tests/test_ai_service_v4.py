import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# --- MOCK CLASSES / OBJECTS ---
class MockSettings:
    """Mock class for application settings."""
    def __init__(self):
        self.GOOGLE_API_KEY = "MOCK_API_KEY_123"

# MOCK DATA - use raw dictionaries for products as ProductDataService would return dicts
MOCK_PRODUCTS_DATA = [
    {"name": "Laptop A", "price": 15000000, "brand": "BrandX", "category": "laptop", "specifications": {"rating": 4.5}, "description": "Powerful laptop for gaming and work."},
    {"name": "Smartphone B", "price": 8000000, "brand": "BrandY", "category": "smartphone", "specifications": {"rating": 4.2}, "description": "Excellent camera and long battery life."},
    {"name": "Headphones C", "price": 2500000, "brand": "BrandZ", "category": "headphone", "specifications": {"rating": 3.8}, "description": "Noise-cancelling over-ear headphones."},
    {"name": "TV D", "price": 12000000, "brand": "BrandA", "category": "tv", "specifications": {"rating": 4.0}, "description": "4K Smart TV with HDR support."}
]

MOCK_AI_RESPONSE_TEXT = "This is a mock AI response."
MOCK_FALLBACK_MESSAGE_PRODUCT_SERVICE = "No products match your criteria."

# --- Pytest fixtures ---
@pytest.fixture
def mock_settings():
    """Mocks app.utils.config.get_settings to return mock settings."""
    with patch('app.utils.config.get_settings', return_value=MockSettings()) as mock:
        yield mock

@pytest.fixture
def mock_genai_client():
    """Mocks google.genai.Client. Its models.generate_content method is set as an AsyncMock
    because `get_response` is async and awaits it.
    Note: For `generate_response` (synchronous), a separate patch might be needed
    if its behavior deviates from an awaited AsyncMock due to original code's sync nature."""
    mock_models = MagicMock()
    # `AsyncMock` is used because the real `generate_content` is async and `get_response` awaits it.
    mock_models.generate_content = AsyncMock(return_value=MagicMock(text=MOCK_AI_RESPONSE_TEXT))
    mock_client = MagicMock()
    mock_client.models = mock_models
    
    with patch('google.genai.Client', return_value=mock_client) as mock:
        yield mock_client # Yield the mock_client instance

@pytest.fixture
def mock_product_data_service():
    """Mocks app.services.product_data_service.ProductDataService."""
    mock_service = AsyncMock()
    # Configure smart_search_products to return a tuple of (list of dicts, string)
    mock_service.smart_search_products = AsyncMock(return_value=(MOCK_PRODUCTS_DATA, MOCK_FALLBACK_MESSAGE_PRODUCT_SERVICE))
    with patch('app.services.product_data_service.ProductDataService', return_value=mock_service) as mock:
        yield mock

@pytest.fixture
def mock_ai_service_logger():
    """Mocks the logger used in AIService to capture log calls."""
    with patch('app.services.ai_service.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service, mock_ai_service_logger):
    """Provides an AIService instance with all its dependencies mocked."""
    # Import AIService *after* patches are applied in fixtures to ensure mocks are active
    from app.services.ai_service import AIService
    service = AIService()
    return service

# --- TEST SUITE FOR AIService ---
class TestAIService:

    # --- Tests for __init__ method ---
    @pytest.mark.asyncio
    async def test_init_success(self, ai_service_instance, mock_settings, mock_genai_client, mock_product_data_service, mock_ai_service_logger):
        """Test AIService initialization succeeds and sets up client and product service."""
        assert isinstance(ai_service_instance.client, MagicMock)
        mock_genai_client.assert_called_once_with(api_key="MOCK_API_KEY_123")
        assert isinstance(ai_service_instance.product_service, AsyncMock)
        mock_product_data_service.assert_called_once()
        mock_ai_service_logger.info.assert_called_with("Successfully initialized AI service with Google AI client")

    @pytest.mark.asyncio
    async def test_init_get_settings_exception(self, mock_settings, mock_ai_service_logger):
        """Test AIService initialization fails if get_settings raises an exception."""
        mock_settings.side_effect = Exception("Config error")
        from app.services.ai_service import AIService # Import here to ensure patch is active for init
        with pytest.raises(Exception, match="Config error"):
            AIService()
        mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: Config error")

    @pytest.mark.asyncio
    async def test_init_genai_client_exception(self, mock_settings, mock_genai_client, mock_ai_service_logger):
        """Test AIService initialization fails if genai.Client initialization raises an exception."""
        mock_genai_client.side_effect = Exception("GenAI client error")
        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="GenAI client error"):
            AIService()
        mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: GenAI client error")

    @pytest.mark.asyncio
    async def test_init_product_service_exception(self, mock_settings, mock_genai_client, mock_product_data_service, mock_ai_service_logger):
        """Test AIService initialization fails if ProductDataService initialization raises an exception."""
        mock_product_data_service.side_effect = Exception("Product service error")
        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="Product service error"):
            AIService()
        mock_ai_service_logger.error.assert_called_once_with("Error initializing AI service: Product service error")

    # --- Tests for get_response (async) method ---
    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price", [
        ("Cari laptop gaming", "laptop", None),
        ("Rekomendasi HP terbaru", "smartphone", None),
        ("Tablet atau ipad untuk kerja?", "tablet", None),
        ("Headphone Bluetooth yang bagus", "headphone", None),
        ("Kamera DSLR entry level", "kamera", None),
        ("Speaker portabel yang mantap", "audio", None),
        ("TV 50 inch", "tv", None),
        ("Drone yang bisa terbang jauh", "drone", None),
        ("Jam tangan pintar yang murah", "jam", 5000000), # With 'murah' keyword
        ("Smartphone budget 3 juta", "smartphone", 3000000), # With 'juta' price
        ("Laptop dengan budget 10 juta", "laptop", 10000000),
        ("hp murah", "smartphone", 5000000), # With 'murah'
        ("produk apa saja?", None, None), # No category or price
        ("cari laptop", "laptop", None), # Simple category
        ("handphone 2 juta", "smartphone", 2000000), # price and category
        ("komputer murah", "laptop", 5000000), # different keyword for laptop + budget
        ("Ponsel 1 juta", "smartphone", 1000000), # another keyword for smartphone
        ("Berapa harga notebook 7 juta?", "laptop", 7000000),
        ("headset budget 500rb", "headphone", 5000000), # '500rb' is not detected by regex, but 'budget' keyword triggers default max_price
        ("beli headset", "headphone", None), # No budget/price keywords
        ("saya mau cari earphone", "headphone", None),
        ("camera mirrorless", "kamera", None),
        ("sound bar", "audio", None),
        ("televisi 6 juta", "tv", 6000000),
        ("quadcopter 2 juta", "drone", 2000000),
        ("smartwatch", "jam", None),
        ("", None, None), # Empty question
        ("What's up?", None, None) # Irrelevant question
    ])
    async def test_get_response_category_and_price_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category, expected_max_price):
        """Test get_response correctly detects category and max_price based on question keywords."""
        await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once()
        call_kwargs = mock_product_data_service.smart_search_products.call_args.kwargs
        assert call_kwargs['keyword'] == question
        assert call_kwargs['category'] == expected_category
        assert call_kwargs['max_price'] == expected_max_price
        assert call_kwargs['limit'] == 5 # Default limit

        mock_genai_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_response_success_with_products(self, ai_service_instance, mock_product_data_service, mock_genai_client, mock_ai_service_logger):
        """Test get_response success when products are found and context is built correctly."""
        question = "Best laptop for students"
        expected_response = MOCK_AI_RESPONSE_TEXT

        response = await ai_service_instance.get_response(question)

        assert response == expected_response
        mock_ai_service_logger.info.assert_any_call(f"Getting AI response for question: {question}")
        mock_product_data_service.smart_search_products.assert_called_once()

        # Verify the prompt content
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']
        assert f"Question: {question}" in prompt
        assert MOCK_FALLBACK_MESSAGE_PRODUCT_SERVICE in prompt
        assert "Relevant Products:" in prompt
        for product in MOCK_PRODUCTS_DATA:
            assert f"{product['name']}" in prompt
            assert f"Price: Rp {product['price']:,}" in prompt
            assert f"Brand: {product['brand']}" in prompt
            assert f"Category: {product['category']}" in prompt
            assert f"Rating: {product['specifications']['rating']}/5" in prompt
            assert f"Description: {product['description'][:200]}..." in prompt
        assert kwargs['model'] == "gemini-2.5-flash"
        mock_ai_service_logger.info.assert_any_call("Successfully generated AI response")


    @pytest.mark.asyncio
    async def test_get_response_success_no_products(self, ai_service_instance, mock_product_data_service, mock_genai_client, mock_ai_service_logger):
        """Test get_response success when no products are found and context reflects this."""
        mock_product_data_service.smart_search_products.return_value = ([], "No specific product found for your query.")
        question = "Tell me about cars"
        expected_response = MOCK_AI_RESPONSE_TEXT

        response = await ai_service_instance.get_response(question)

        assert response == expected_response
        mock_ai_service_logger.info.assert_any_call(f"Getting AI response for question: {question}")
        mock_product_data_service.smart_search_products.assert_called_once()

        # Verify the prompt content
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']
        assert f"Question: {question}" in prompt
        assert "No specific product found for your query." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # No products, so this section should not be there
        assert kwargs['model'] == "gemini-2.5-flash"
        mock_ai_service_logger.info.assert_any_call("Successfully generated AI response")

    @pytest.mark.asyncio
    async def test_get_response_product_service_exception(self, ai_service_instance, mock_product_data_service, mock_ai_service_logger):
        """Test get_response handles exception from product_service.smart_search_products gracefully."""
        mock_product_data_service.smart_search_products.side_effect = Exception("Product search failed")
        question = "What is the best product?"
        expected_fallback_message = "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

        response = await ai_service_instance.get_response(question)

        assert response == expected_fallback_message
        mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: Product search failed")
        mock_product_data_service.smart_search_products.assert_called_once()
        ai_service_instance.client.models.generate_content.assert_not_called() # AI client should not be called if product service fails

    @pytest.mark.asyncio
    async def test_get_response_genai_exception(self, ai_service_instance, mock_genai_client, mock_ai_service_logger):
        """Test get_response handles exception from client.models.generate_content gracefully."""
        mock_genai_client.models.generate_content.side_effect = Exception("AI generation failed")
        question = "General question"
        expected_fallback_message = "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

        response = await ai_service_instance.get_response(question)

        assert response == expected_fallback_message
        mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: AI generation failed")
        ai_service_instance.client.models.generate_content.assert_called_once() # AI client was called but failed

    @pytest.mark.asyncio
    async def test_get_response_product_with_missing_fields(self, ai_service_instance, mock_product_data_service, mock_genai_client, mock_ai_service_logger):
        """Test get_response context building with products having missing fields, ensuring defaults are used."""
        # Create products with some missing fields to test robustness of context building
        products_with_missing_data = [
            {"name": "Product A", "price": 1000000, "brand": "BrandX", "category": "category1", "specifications": {"rating": 4.0}, "description": "Description A full length."},
            {"name": "Product B", "price": 5000000, "category": "category2", "specifications": {}}, # Missing brand, rating, and description for Product B (rating default 0)
            {"brand": "BrandZ", "specifications": {"rating": 3.5}, "description": "Description C concise."}, # Missing name, price, category for Product C (name/price/cat defaults)
            {} # Empty product dictionary to test all defaults
        ]
        mock_product_data_service.smart_search_products.return_value = (products_with_missing_data, "Some message about mixed products.")

        question = "test missing product fields"
        await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']

        # Check Product A (complete)
        assert "1. Product A" in prompt
        assert "Price: Rp 1,000,000" in prompt
        assert "Brand: BrandX" in prompt
        assert "Category: category1" in prompt
        assert "Rating: 4.0/5" in prompt
        assert "Description: Description A full length..." in prompt # Should be truncated

        # Check Product B (missing brand, rating, description)
        assert "2. Product B" in prompt
        assert "Price: Rp 5,000,000" in prompt
        assert "Brand: Unknown" in prompt # Default
        assert "Category: category2" in prompt
        assert "Rating: 0/5" in prompt # Default (from get('rating', 0) on empty dict)
        assert "Description: No description..." in prompt # Default (truncated)

        # Check Product C (missing name, price, category, etc.)
        assert "3. Unknown" in prompt # Default name
        assert "Price: Rp 0" in prompt # Default price
        assert "Brand: BrandZ" in prompt
        assert "Category: Unknown" in prompt # Default
        assert "Rating: 3.5/5" in prompt
        assert "Description: Description C concise..." in prompt

        # Check Empty Product Dictionary
        assert "4. Unknown" in prompt
        assert "Price: Rp 0" in prompt
        assert "Brand: Unknown" in prompt
        assert "Category: Unknown" in prompt
        assert "Rating: 0/5" in prompt
        assert "Description: No description..." in prompt


    # --- Tests for generate_response (synchronous, legacy method) ---
    @pytest.mark.asyncio # Needed because the underlying mock is an AsyncMock
    async def test_generate_response_success(self, ai_service_instance, mock_genai_client, mock_ai_service_logger):
        """Test generate_response success (legacy method).
        NOTE: This test patches `generate_content` locally to simulate a synchronous return
        because the original `generate_response` method is synchronous but calls
        an underlying asynchronous Google AI client method (`generate_content`).
        This local patch prevents a TypeError that would occur if `generate_content` were
        truly awaited by an `AsyncMock` without the `generate_response` method being `async def`."""
        context = "This is a test context for the legacy method."
        expected_response = MOCK_AI_RESPONSE_TEXT

        # Temporarily patch models.generate_content to return a direct mock for this sync method
        with patch.object(ai_service_instance.client.models, 'generate_content', return_value=MagicMock(text=MOCK_AI_RESPONSE_TEXT)) as mock_generate_content_sync:
            response = ai_service_instance.generate_response(context) # Call synchronously

            assert response == expected_response
            mock_ai_service_logger.info.assert_any_call("Generating AI response")
            
            args, kwargs = mock_generate_content_sync.call_args # Use the locally patched mock
            # The prompt structure for generate_response is slightly different from get_response
            expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
            assert kwargs['contents'] == expected_prompt
            assert kwargs['model'] == "gemini-2.0-flash"
            mock_ai_service_logger.info.assert_any_call("Successfully generated AI response")


    @pytest.mark.asyncio # Still needed for error path too for the same reason as above
    async def test_generate_response_genai_exception(self, ai_service_instance, mock_genai_client, mock_ai_service_logger):
        """Test generate_response handles exception from client.models.generate_content and re-raises."""
        # Temporarily patch models.generate_content to raise for this sync method
        with patch.object(ai_service_instance.client.models, 'generate_content', side_effect=Exception("Legacy AI generation failed")) as mock_generate_content_sync:
            context = "Some context for legacy method."

            with pytest.raises(Exception, match="Legacy AI generation failed"):
                ai_service_instance.generate_response(context)

            mock_ai_service_logger.error.assert_called_once_with("Error generating AI response: Legacy AI generation failed")
            mock_generate_content_sync.assert_called_once() # Ensure the patched mock was called