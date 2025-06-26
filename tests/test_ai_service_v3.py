import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
import os

# Set up logging to capture logs during tests
logging.basicConfig(level=logging.INFO)

# Ensure path includes app directory for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the service to be tested
from app.services.ai_service import AIService

# --- Fixtures ---

@pytest.fixture
def mock_get_settings():
    """Mocks app.utils.config.get_settings to return a mock settings object."""
    with patch('app.utils.config.get_settings') as mock:
        mock_settings = MagicMock()
        mock_settings.GOOGLE_API_KEY = "mock_api_key"
        mock.return_value = mock_settings
        yield mock

@pytest.fixture
def mock_genai_client():
    """Mocks google.genai.Client and its generate_content method."""
    with patch('google.genai.Client') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content = MagicMock() # Ensure it's a callable mock
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def mock_product_data_service():
    """Mocks app.services.product_data_service.ProductDataService."""
    with patch('app.services.product_data_service.ProductDataService') as mock_service_class:
        mock_service_instance = AsyncMock() # Since smart_search_products is async
        mock_service_class.return_value = mock_service_instance
        yield mock_service_instance

@pytest.fixture
def ai_service_instance(mock_get_settings, mock_genai_client, mock_product_data_service):
    """Provides an initialized AIService instance for tests."""
    return AIService()

# --- Test Cases ---

class TestAIService:

    # --- __init__ Tests ---

    def test_init_success(self, mock_get_settings, mock_genai_client, mock_product_data_service, caplog):
        """Test successful initialization of AIService."""
        with caplog.at_level(logging.INFO):
            service = AIService()
            mock_get_settings.assert_called_once()
            mock_genai_client.assert_called_once_with(api_key="mock_api_key")
            mock_product_data_service.assert_called_once()
            assert isinstance(service.client, MagicMock)
            assert isinstance(service.product_service, AsyncMock)
            assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_get_settings_failure(self, caplog):
        """Test initialization failure when get_settings raises an error."""
        with patch('app.utils.config.get_settings', side_effect=ValueError("Settings error")), \
             caplog.at_level(logging.ERROR), \
             pytest.raises(ValueError, match="Settings error"):
            AIService()
            assert "Error initializing AI service: Settings error" in caplog.text

    def test_init_genai_client_failure(self, mock_get_settings, caplog):
        """Test initialization failure when genai.Client raises an error."""
        with patch('google.genai.Client', side_effect=ConnectionError("API connection failed")), \
             caplog.at_level(logging.ERROR), \
             pytest.raises(ConnectionError, match="API connection failed"):
            AIService()
            assert "Error initializing AI service: API connection failed" in caplog.text

    # --- get_response Tests ---

    @pytest.mark.asyncio
    async def test_get_response_success_with_products(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response successfully generates a response with relevant products."""
        mock_product_data_service.smart_search_products.return_value = (
            [
                {"name": "Laptop XYZ", "price": 10000000, "brand": "Brand A", "category": "laptop", "specifications": {"rating": 4.5}, "description": "Powerful laptop for gaming and work."},
                {"name": "Laptop ABC", "price": 8000000, "brand": "Brand B", "category": "laptop", "specifications": {"rating": 4.0}, "description": "Lightweight and portable laptop for everyday use."}
            ],
            "Here are some laptops:"
        )
        mock_genai_client.models.generate_content.return_value.text = "AI response about laptops."

        question = "Rekomendasikan laptop bagus"
        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response(question)

            mock_product_data_service.smart_search_products.assert_called_once_with(
                keyword=question, category='laptop', max_price=None, limit=5
            )
            mock_genai_client.models.generate_content.assert_called_once()
            args, kwargs = mock_genai_client.models.generate_content.call_args
            prompt = kwargs['contents']
            
            assert "Question: Rekomendasikan laptop bagus" in prompt
            assert "Here are some laptops:" in prompt
            assert "Relevant Products:\n1. Laptop XYZ" in prompt
            assert "Price: Rp 10,000,000" in prompt
            assert "Rating: 4.5/5" in prompt
            assert "Description: Powerful laptop for gaming and work..." in prompt
            assert "Successfully generated AI response" in caplog.text
            assert response == "AI response about laptops."

    @pytest.mark.asyncio
    async def test_get_response_success_no_products(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response successfully generates a response when no products are found."""
        mock_product_data_service.smart_search_products.return_value = (
            [],
            "We couldn't find specific products for your query."
        )
        mock_genai_client.models.generate_content.return_value.text = "AI general response."

        question = "Apa saja produk terbaru?"
        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response(question)

            mock_product_data_service.smart_search_products.assert_called_once_with(
                keyword=question, category=None, max_price=None, limit=5
            )
            mock_genai_client.models.generate_content.assert_called_once()
            args, kwargs = mock_genai_client.models.generate_content.call_args
            prompt = kwargs['contents']
            
            assert "Question: Apa saja produk terbaru?" in prompt
            assert "We couldn't find specific products for your query." in prompt
            assert "No specific products found, but I can provide general recommendations." in prompt
            assert "Relevant Products:" not in prompt # Should not be present
            assert "Successfully generated AI response" in caplog.text
            assert response == "AI general response."

    @pytest.mark.parametrize("question, expected_category", [
        ("Cari laptop gaming", "laptop"),
        ("Rekomendasi notebook murah", "laptop"),
        ("HP yang bagus apa ya?", "smartphone"),
        ("Ponsel terbaru", "smartphone"),
        ("Tablet harga terjangkau", "tablet"),
        ("Headphone Bluetooth", "headphone"),
        ("Earphone terbaik", "headphone"),
        ("Kamera DSLR", "kamera"),
        ("Speaker portabel", "audio"),
        ("TV 4K", "tv"),
        ("Drone dengan kamera", "drone"),
        ("Jam tangan pintar", "jam"),
        ("Smartwatch murah", "jam"),
        ("Saya mau beli komputer", "laptop"),
        ("Saya cari audio system", "audio"),
    ])
    @pytest.mark.asyncio
    async def test_get_response_category_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category):
        """Test category detection based on various keywords."""
        mock_product_data_service.smart_search_products.return_value = ([], "")
        mock_genai_client.models.generate_content.return_value.text = "AI response."

        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once()
        args, kwargs = mock_product_data_service.smart_search_products.call_args
        assert kwargs['category'] == expected_category

    @pytest.mark.parametrize("question, expected_max_price", [
        ("Laptop budget 10 juta", 10000000),
        ("HP sekitar 5 juta", 5000000),
        ("Cari smartphone 2 juta", 2000000),
        ("Headphone yang murah", 5000000), # 'murah' keyword
        ("Cari produk budget mahasiswa", 5000000), # 'budget' keyword
        ("TV bagus", None), # No price mentioned
        ("Apa ada laptop sekitar 7,5 juta?", None), # Does not match 'X juta' pattern
        ("Harga laptop 10jt", 10000000), # Handles 'jt' if present but current regex is 'juta'
        ("Budget saya 5juta", 5000000) # Test case where 'juta' is attached
    ])
    @pytest.mark.asyncio
    async def test_get_response_price_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_max_price):
        """Test max_price detection based on various keywords and patterns."""
        mock_product_data_service.smart_search_products.return_value = ([], "")
        mock_genai_client.models.generate_content.return_value.text = "AI response."

        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once()
        args, kwargs = mock_product_data_service.smart_search_products.call_args
        assert kwargs['max_price'] == expected_max_price

    @pytest.mark.asyncio
    async def test_get_response_no_category_no_price(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """Test get_response when no category or price is detected."""
        mock_product_data_service.smart_search_products.return_value = ([], "")
        mock_genai_client.models.generate_content.return_value.text = "AI response."

        question = "Tolong berikan informasi umum."
        await ai_service_instance.get_response(question)
        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=None, max_price=None, limit=5
        )

    @pytest.mark.asyncio
    async def test_get_response_product_data_service_error(self, ai_service_instance, mock_product_data_service, caplog):
        """Test get_response gracefully handles errors from ProductDataService."""
        mock_product_data_service.smart_search_products.side_effect = Exception("Product search failed")
        
        question = "Cari produk A"
        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response(question)
            assert "Error generating AI response: Product search failed" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
            mock_product_data_service.smart_search_products.assert_called_once()
            # Ensure genai client is not called if product service fails early
            ai_service_instance.client.models.generate_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_response_genai_api_error(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response gracefully handles errors from Google AI API."""
        mock_product_data_service.smart_search_products.return_value = ([], "")
        mock_genai_client.models.generate_content.side_effect = Exception("Google AI API error")

        question = "Hello AI"
        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response(question)
            assert "Error generating AI response: Google AI API error" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
            mock_product_data_service.smart_search_products.assert_called_once()
            mock_genai_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_response_partial_product_data(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """Test context building with partially missing product data."""
        mock_product_data_service.smart_search_products.return_value = (
            [
                {"name": "Product X"}, # Missing price, brand, category, specs, description
                {"name": "Product Y", "price": 500000, "brand": "Brand C"}, # Missing category, specs, description
                {"name": "Product Z", "description": "Full desc here", "specifications": {"rating": 5.0}}
            ],
            "Found some products."
        )
        mock_genai_client.models.generate_content.return_value.text = "AI response."

        question = "Produk apa saja?"
        await ai_service_instance.get_response(question)
        
        args, kwargs = mock_genai_client.models.generate_content.call_args
        prompt = kwargs['contents']

        assert "1. Product X" in prompt
        assert "Price: Rp 0" in prompt # Default price
        assert "Brand: Unknown" in prompt # Default brand
        assert "Category: Unknown" in prompt # Default category
        assert "Rating: 0/5" in prompt # Default rating
        assert "Description: No description..." in prompt # Default description

        assert "2. Product Y" in prompt
        assert "Price: Rp 500,000" in prompt
        assert "Brand: Brand C" in prompt
        assert "Category: Unknown" in prompt
        assert "Rating: 0/5" in prompt
        assert "Description: No description..." in prompt

        assert "3. Product Z" in prompt
        assert "Description: Full desc here..." in prompt
        assert "Rating: 5.0/5" in prompt


    # --- generate_response (Legacy) Tests ---

    def test_generate_response_success(self, ai_service_instance, mock_genai_client, caplog):
        """Test generate_response successfully generates a response."""
        mock_genai_client.models.generate_content.return_value.text = "Legacy AI response."

        context = "Some product information for legacy API."
        with caplog.at_level(logging.INFO):
            response = ai_service_instance.generate_response(context)

            mock_genai_client.models.generate_content.assert_called_once_with(
                model="gemini-2.0-flash",
                contents=f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""
            )
            assert "Successfully generated AI response" in caplog.text
            assert response == "Legacy AI response."

    def test_generate_response_genai_api_error(self, ai_service_instance, mock_genai_client, caplog):
        """Test generate_response raises an error when Google AI API fails."""
        mock_genai_client.models.generate_content.side_effect = Exception("Legacy API error")

        context = "Context for error"
        with caplog.at_level(logging.ERROR), \
             pytest.raises(Exception, match="Legacy API error"):
            ai_service_instance.generate_response(context)
            assert "Error generating AI response: Legacy API error" in caplog.text