import pytest
import unittest.mock as mock
import asyncio
import logging
from unittest.mock import AsyncMock

# Set up logging for tests to capture output if needed
# This ensures that any logs from the tested code are visible
@pytest.fixture(autouse=True)
def caplog_fixture(caplog):
    """Fixture to capture logs during tests."""
    caplog.set_level(logging.INFO)

@pytest.fixture
def mock_settings():
    """Mocks the app.utils.config.get_settings function."""
    with mock.patch('app.utils.config.get_settings') as mock_get_settings:
        mock_settings_instance = mock.Mock()
        mock_settings_instance.GOOGLE_API_KEY = "test_api_key_123"
        mock_get_settings.return_value = mock_settings_instance
        yield mock_get_settings

@pytest.fixture
def mock_genai_client():
    """Mocks google.genai.Client and its methods."""
    with mock.patch('google.genai.Client') as MockClient:
        # Configure the mock instance that genai.Client() returns
        mock_client_instance = MockClient.return_value
        
        # Configure the nested mocks for models.generate_content
        mock_generate_content_return_value = mock.Mock()
        mock_generate_content_return_value.text = "Mock AI Generated Response"
        mock_client_instance.models.generate_content.return_value = mock_generate_content_return_value
        
        yield MockClient

@pytest.fixture
def mock_product_data_service():
    """Mocks app.services.product_data_service.ProductDataService."""
    with mock.patch('app.services.product_data_service.ProductDataService') as MockProductDataService:
        # Configure the mock instance that ProductDataService() returns
        mock_service_instance = MockProductDataService.return_value
        
        # Configure the async mock for smart_search_products
        mock_service_instance.smart_search_products = AsyncMock(
            return_value=([], "No specific products found for your query.")
        )
        yield MockProductDataService

@pytest.fixture
def ai_service(mock_settings, mock_genai_client, mock_product_data_service):
    """Fixture to provide an AIService instance with mocked dependencies."""
    # Import AIService here to ensure mocks are applied before import
    from app.services.ai_service import AIService
    service = AIService()
    return service

class TestAIService:

    # --- __init__ method tests ---
    def test_init_success(self, ai_service, mock_settings, mock_genai_client, mock_product_data_service, caplog):
        """
        Test successful initialization of AIService.
        Ensures Client and ProductDataService are instantiated and an info log is recorded.
        """
        assert ai_service.client is not None
        assert ai_service.product_service is not None
        mock_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key="test_api_key_123")
        mock_product_data_service.assert_called_once()
        assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_raises_exception_on_settings_error(self, mock_settings, caplog):
        """
        Test that __init__ raises an exception if get_settings fails.
        Ensures an error log is recorded.
        """
        mock_settings.side_effect = Exception("Failed to load settings")
        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="Failed to load settings"):
            AIService()
        assert "Error initializing AI service: Failed to load settings" in caplog.text

    def test_init_raises_exception_on_genai_client_error(self, mock_settings, mock_genai_client, caplog):
        """
        Test that __init__ raises an exception if genai.Client initialization fails.
        Ensures an error log is recorded.
        """
        mock_genai_client.side_effect = Exception("GenAI client error")
        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="GenAI client error"):
            AIService()
        assert "Error initializing AI service: GenAI client error" in caplog.text

    def test_init_raises_exception_on_product_service_error(self, mock_settings, mock_genai_client, mock_product_data_service, caplog):
        """
        Test that __init__ raises an exception if ProductDataService initialization fails.
        Ensures an error log is recorded.
        """
        mock_product_data_service.side_effect = Exception("Product service error")
        from app.services.ai_service import AIService
        with pytest.raises(Exception, match="Product service error"):
            AIService()
        assert "Error initializing AI service: Product service error" in caplog.text

    # --- get_response method tests ---
    @pytest.mark.asyncio
    async def test_get_response_success_no_products(self, ai_service, mock_product_data_service, mock_genai_client, caplog):
        """
        Test get_response when smart_search_products returns no relevant products.
        """
        question = "What is a good smartphone?"
        mock_product_data_service.return_value.smart_search_products.return_value = (
            [], "No specific products found for 'smartphone'."
        )
        mock_genai_client.return_value.models.generate_content.return_value.text = "AI response about general smartphones."

        response = await ai_service.get_response(question)

        assert response == "AI response about general smartphones."
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once_with(
            keyword=question, category='smartphone', max_price=None, limit=5
        )
        
        # Check prompt content
        args, _ = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]
        assert "Question: What is a good smartphone?" in prompt
        assert "No specific products found for 'smartphone'." in prompt
        assert "No specific products found, but I can provide general recommendations." in prompt
        assert "Relevant Products:" not in prompt # Ensure no products section
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_success_with_products(self, ai_service, mock_product_data_service, mock_genai_client, caplog):
        """
        Test get_response when smart_search_products returns relevant products.
        Ensures product details are correctly formatted in the prompt.
        """
        question = "Recommend a laptop under 15 juta."
        mock_products = [
            {
                'name': 'Laptop X',
                'price': 12500000,
                'brand': 'BrandA',
                'category': 'laptop',
                'specifications': {'rating': 4.5},
                'description': 'This is a long description for Laptop X that should be truncated by the service logic.'
            },
            {
                'name': 'Laptop Y',
                'price': 14000000,
                'brand': 'BrandB',
                'category': 'laptop',
                'specifications': {'rating': 4.0},
                'description': 'Another description for Laptop Y.'
            }
        ]
        mock_product_data_service.return_value.smart_search_products.return_value = (
            mock_products, "Here are some laptops matching your criteria."
        )
        mock_genai_client.return_value.models.generate_content.return_value.text = "AI response about specific laptops."

        response = await ai_service.get_response(question)

        assert response == "AI response about specific laptops."
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once_with(
            keyword=question, category='laptop', max_price=15000000, limit=5
        )
        
        args, _ = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]

        assert "Question: Recommend a laptop under 15 juta." in prompt
        assert "Here are some laptops matching your criteria." in prompt
        assert "Relevant Products:\n" in prompt
        assert "1. Laptop X\n   Price: Rp 12,500,000\n   Brand: BrandA\n   Category: laptop\n   Rating: 4.5/5\n   Description: This is a long description for Laptop X that should be truncated by the service logic" in prompt
        assert "...laptop service logic." in prompt # Check truncation
        assert "2. Laptop Y\n   Price: Rp 14,000,000\n   Brand: BrandB\n   Category: laptop\n   Rating: 4.0/5\n   Description: Another description for Laptop Y" in prompt
        assert "Successfully generated AI response" in caplog.text

    @pytest.mark.parametrize("question, expected_category", [
        ("Cari laptop gaming", "laptop"),
        ("hp terbaik", "smartphone"),
        ("tablet murah", "tablet"),
        ("headphone nirkabel", "headphone"),
        ("kamera digital", "kamera"),
        ("speaker bluetooth", "audio"),
        ("televisi 4k", "tv"),
        ("drone murah", "drone"),
        ("smartwatch terbaru", "jam"),
        ("komputer kerja", "laptop"), # Alternative keyword
        ("iphone", "smartphone"), # Alternative keyword
        ("ipad air", "tablet"), # Alternative keyword
        ("earphone bagus", "headphone"), # Alternative keyword
        ("camera mirrorless", "kamera"), # Alternative keyword
        ("audio system", "audio"), # Alternative keyword
        ("Jam tangan sporty", "jam"), # Alternative keyword
        ("I need a new phone", "smartphone"), # English keyword
        ("What's a good notebook for students?", "laptop"), # English keyword
    ])
    @pytest.mark.asyncio
    async def test_get_response_category_detection(self, ai_service, mock_product_data_service, mock_genai_client, question, expected_category):
        """Test accurate category detection based on various keywords."""
        await ai_service.get_response(question)
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once()
        args, kwargs = mock_product_data_service.return_value.smart_search_products.call_args
        assert kwargs['category'] == expected_category

    @pytest.mark.parametrize("question, expected_price", [
        ("laptop 10 juta", 10000000),
        ("handphone di bawah 5 juta", 5000000),
        ("tablet 2.5 juta", 2500000), # Test decimal-like parsing
        ("mencari hp sekitar 3 juta rupiah", 3000000),
        ("budget hp 4 juta", 4000000), # Budget + juta
    ])
    @pytest.mark.asyncio
    async def test_get_response_price_detection_juta(self, ai_service, mock_product_data_service, mock_genai_client, question, expected_price):
        """Test accurate price detection for 'X juta' format."""
        await ai_service.get_response(question)
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once()
        args, kwargs = mock_product_data_service.return_value.smart_search_products.call_args
        assert kwargs['max_price'] == expected_price

    @pytest.mark.parametrize("question, expected_price", [
        ("cari laptop dengan budget", 5000000),
        ("rekomendasi hp murah", 5000000),
        ("tablet harga terjangkau", None), # Should not detect 5M if only 'terjangkau'
        ("saya punya budget", 5000000),
    ])
    @pytest.mark.asyncio
    async def test_get_response_price_detection_budget_murah(self, ai_service, mock_product_data_service, mock_genai_client, question, expected_price):
        """Test price detection for 'budget' or 'murah' keywords, defaulting to 5M."""
        await ai_service.get_response(question)
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once()
        args, kwargs = mock_product_data_service.return_value.smart_search_products.call_args
        assert kwargs['max_price'] == expected_price

    @pytest.mark.asyncio
    async def test_get_response_mixed_detection(self, ai_service, mock_product_data_service, mock_genai_client):
        """Test question with both category and price detection."""
        question = "Rekomendasi smartphone budget 7 juta"
        await ai_service.get_response(question)
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once()
        args, kwargs = mock_product_data_service.return_value.smart_search_products.call_args
        assert kwargs['category'] == 'smartphone'
        assert kwargs['max_price'] == 7000000

    @pytest.mark.asyncio
    async def test_get_response_no_category_no_price(self, ai_service, mock_product_data_service, mock_genai_client):
        """Test get_response with a general question that has no category or price."""
        question = "Tell me about electronics"
        await ai_service.get_response(question)
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once()
        args, kwargs = mock_product_data_service.return_value.smart_search_products.call_args
        assert kwargs['category'] is None
        assert kwargs['max_price'] is None

    @pytest.mark.asyncio
    async def test_get_response_smart_search_products_exception(self, ai_service, mock_product_data_service, caplog):
        """
        Test get_response error handling when smart_search_products raises an exception.
        Should return a fallback message.
        """
        mock_product_data_service.return_value.smart_search_products.side_effect = Exception("Product search failed")
        
        response = await ai_service.get_response("Any question")
        
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: Product search failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_genai_error(self, ai_service, mock_genai_client, caplog):
        """
        Test get_response error handling when generate_content raises an exception.
        Should return a fallback message.
        """
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("GenAI API error")
        
        response = await ai_service.get_response("Any question")
        
        assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        assert "Error generating AI response: GenAI API error" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_empty_question(self, ai_service, mock_product_data_service, mock_genai_client):
        """Test get_response with an empty question string."""
        question = ""
        await ai_service.get_response(question)
        
        mock_product_data_service.return_value.smart_search_products.assert_awaited_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )
        
        args, _ = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]
        assert "Question: \n\n" in prompt # Ensure empty question is in prompt

    @pytest.mark.asyncio
    async def test_get_response_product_missing_fields(self, ai_service, mock_product_data_service, mock_genai_client):
        """
        Test get_response with products that have missing or incomplete fields
        to ensure default values are used and no KeyError occurs.
        """
        mock_products = [
            {
                'name': 'Incomplete Product',
                'price': None, # Missing price
                # Missing brand, category, specifications, description
            }
        ]
        mock_product_data_service.return_value.smart_search_products.return_value = (
            mock_products, "Fallback for incomplete products."
        )

        response = await ai_service.get_response("Test incomplete product")

        args, _ = mock_genai_client.return_value.models.generate_content.call_args
        prompt = args[0]
        assert "1. Incomplete Product\n   Price: Rp 0\n   Brand: Unknown\n   Category: Unknown\n   Rating: 0/5\n   Description: No description" in prompt
        assert response == "Mock AI Generated Response" # Ensure it still returns a response

    # --- generate_response method tests ---
    def test_generate_response_success(self, ai_service, mock_genai_client, caplog):
        """
        Test successful generation of AI response using the legacy method.
        """
        context = "This is a test context for the legacy method."
        mock_genai_client.return_value.models.generate_content.return_value.text = "Legacy AI Response."

        response = ai_service.generate_response(context)

        assert response == "Legacy AI Response."
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        
        # Check prompt content
        args, _ = mock_genai_client.return_value.models.generate_content.call_args
        model_name = args[0]
        contents = args[1]
        
        assert model_name == "gemini-2.0-flash"
        assert "You are a helpful product assistant." in contents
        assert context in contents
        assert "Successfully generated AI response" in caplog.text

    def test_generate_response_genai_error(self, ai_service, mock_genai_client, caplog):
        """
        Test error handling in generate_response when genai.Client fails.
        Should re-raise the exception.
        """
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("Legacy GenAI API error")

        with pytest.raises(Exception, match="Legacy GenAI API error"):
            ai_service.generate_response("Some context")
        
        assert "Error generating AI response: Legacy GenAI API error" in caplog.text