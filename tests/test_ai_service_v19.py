import pytest
from unittest.mock import AsyncMock, Mock
import logging
from app.services.ai_service import AIService
from app.services.product_data_service import ProductDataService  # Import for mocking path
from google import genai  # Import for mocking path
from app.utils.config import get_settings  # Import for mocking path

# Configure logging for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def mock_settings():
    """Mocks the get_settings function."""
    mock_obj = Mock()
    mock_obj.GOOGLE_API_KEY = "test_api_key"
    return mock_obj


@pytest.fixture
def mock_genai_client(mocker):
    """Mocks genai.Client and its models.generate_content method."""
    mock_client_instance = Mock()
    mock_client_instance.models = Mock()
    mock_client_instance.models.generate_content = Mock()
    mocker.patch('google.genai.Client', return_value=mock_client_instance)
    return mock_client_instance


@pytest.fixture
def mock_product_data_service(mocker):
    """Mocks ProductDataService and its smart_search_products method."""
    mock_service_instance = AsyncMock()  # AsyncMock for async methods
    mock_service_instance.smart_search_products = AsyncMock()
    mocker.patch('app.services.product_data_service.ProductDataService', return_value=mock_service_instance)
    return mock_service_instance


@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service, mocker):
    """Provides an initialized AIService instance for tests."""
    # Patch get_settings before AIService is initialized
    mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
    return AIService()


class TestAIService:

    def test_init_success(self, mock_settings, mock_genai_client, mock_product_data_service, mocker, caplog):
        """Test successful initialization of AIService."""
        mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
        
        with caplog.at_level(logging.INFO):
            service = AIService()
            
            mock_settings.GOOGLE_API_KEY.assert_called_once()
            mock_genai_client.assert_called_once_with(api_key="test_api_key")
            mock_product_data_service.assert_called_once()
            
            assert isinstance(service.client, Mock)
            assert isinstance(service.product_service, AsyncMock)
            assert "Successfully initialized AI service with Google AI client" in caplog.text

    def test_init_get_settings_failure(self, mocker, caplog):
        """Test initialization failure due to get_settings error."""
        mocker.patch('app.utils.config.get_settings', side_effect=Exception("Config error"))
        
        with pytest.raises(Exception, match="Config error"), caplog.at_level(logging.ERROR):
            AIService()
            assert "Error initializing AI service: Config error" in caplog.text

    def test_init_genai_client_failure(self, mock_settings, mocker, caplog):
        """Test initialization failure due to genai.Client error."""
        mocker.patch('app.utils.config.get_settings', return_value=mock_settings)
        mocker.patch('google.genai.Client', side_effect=Exception("GenAI client error"))
        
        with pytest.raises(Exception, match="GenAI client error"), caplog.at_level(logging.ERROR):
            AIService()
            assert "Error initializing AI service: GenAI client error" in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price", [
        ("Cari laptop murah", "laptop", 5000000),
        ("Rekomendasi smartphone budget 7 juta", "smartphone", 7000000),
        ("Tablet terbaru", "tablet", None),
        ("Headphone gaming", "headphone", None),
        ("Kamera DSLR bagus", "kamera", None),
        ("Saya butuh audio yang bagus", "audio", None),
        ("TV 4K", "tv", None),
        ("Drone yang stabil", "drone", None),
        ("Smartwatch terbaik harga 2 juta", "jam", 2000000),
        ("Produk tanpa kategori", None, None),
        ("Cari smartphone", "smartphone", None),
        ("Saya ingin hp 10 juta", "smartphone", 10000000),
        ("Tolong carikan ponsel dengan budget rendah", "smartphone", 5000000),
        ("Apa rekomendasi komputer untuk desain?", "laptop", None),
        ("Sepeda listrik", None, None), # Not in category_mapping
    ])
    async def test_get_response_category_price_detection(self, ai_service_instance, mock_product_data_service, mock_genai_client, question, expected_category, expected_max_price):
        """Test get_response with various category and price detection scenarios."""
        mock_product_data_service.smart_search_products.return_value = (
            [], "No specific products found for your query."
        )
        mock_genai_client.models.generate_content.return_value.text = "AI Response."

        await ai_service_instance.get_response(question)

        mock_product_data_service.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )
        assert mock_genai_client.models.generate_content.called

    @pytest.mark.asyncio
    async def test_get_response_with_products_found(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response when products are found."""
        products = [
            {'name': 'Laptop X', 'price': 15000000, 'brand': 'BrandA', 'category': 'laptop', 'specifications': {'rating': 4.5}, 'description': 'Powerful laptop for gaming and work.'},
            {'name': 'Smartphone Y', 'price': 7500000, 'brand': 'BrandB', 'category': 'smartphone', 'specifications': {'rating': 4.0}, 'description': 'Excellent camera and battery life.'},
            {'name': 'Short Desc Product', 'price': 1000000, 'brand': 'BrandC', 'category': 'misc', 'specifications': {'rating': 3.0}, 'description': 'A very short description that is less than 200 characters.'}
        ]
        fallback_msg = "Here are some relevant products."

        mock_product_data_service.smart_search_products.return_value = (products, fallback_msg)
        mock_genai_client.models.generate_content.return_value.text = "AI generated response about products."

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response("Tell me about laptops.")

            mock_product_data_service.smart_search_products.assert_called_once_with(
                keyword="Tell me about laptops.", category="laptop", max_price=None, limit=5
            )
            mock_genai_client.models.generate_content.assert_called_once()
            
            # Check prompt content
            call_args, _ = mock_genai_client.models.generate_content.call_args
            prompt = call_args[1]['contents']
            
            assert "Question: Tell me about laptops." in prompt
            assert fallback_msg in prompt
            assert "Relevant Products:" in prompt
            assert "1. Laptop X" in prompt
            assert "Price: Rp 15,000,000" in prompt
            assert "Description: Powerful laptop for gaming and work..." in prompt
            assert "Description: A very short description that is less than 200 characters..." in prompt # Test short description
            assert "Successfully generated AI response" in caplog.text
            assert response == "AI generated response about products."

    @pytest.mark.asyncio
    async def test_get_response_no_products_found(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response when no products are found."""
        fallback_msg = "No specific products found for your query."
        mock_product_data_service.smart_search_products.return_value = ([], fallback_msg)
        mock_genai_client.models.generate_content.return_value.text = "General AI response."

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response("General query.")

            mock_product_data_service.smart_search_products.assert_called_once()
            mock_genai_client.models.generate_content.assert_called_once()
            
            call_args, _ = mock_genai_client.models.generate_content.call_args
            prompt = call_args[1]['contents']
            
            assert "No specific products found, but I can provide general recommendations." in prompt
            assert response == "General AI response."
            assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_missing_product_fields(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """Test get_response handles missing product fields gracefully."""
        products = [
            {'name': 'Product A', 'brand': 'BrandX', 'category': 'electronics'},
            {'price': 5000000, 'specifications': {'rating': 4.0}, 'description': 'Good product'},
            {} # Completely empty product
        ]
        fallback_msg = "Some products found."

        mock_product_data_service.smart_search_products.return_value = (products, fallback_msg)
        mock_genai_client.models.generate_content.return_value.text = "AI response about products."

        response = await ai_service_instance.get_response("Query for products.")
        
        call_args, _ = mock_genai_client.models.generate_content.call_args
        prompt = call_args[1]['contents']

        assert "1. Product A" in prompt
        assert "Price: Rp 0" in prompt # Default price
        assert "Brand: BrandX" in prompt
        assert "Category: electronics" in prompt
        assert "Rating: 0/5" in prompt # Default rating
        assert "Description: No description..." in prompt # Default description

        assert "2. Unknown" in prompt # Default name
        assert "Price: Rp 5,000,000" in prompt
        assert "Brand: Unknown" in prompt
        assert "Category: Unknown" in prompt
        assert "Rating: 4.0/5" in prompt
        assert "Description: Good product..." in prompt
        
        assert "3. Unknown" in prompt # Default name
        assert "Price: Rp 0" in prompt
        assert "Brand: Unknown" in prompt
        assert "Category: Unknown" in prompt
        assert "Rating: 0/5" in prompt
        assert "Description: No description..." in prompt

        assert response == "AI response about products."


    @pytest.mark.asyncio
    async def test_get_response_smart_search_products_exception(self, ai_service_instance, mock_product_data_service, caplog):
        """Test get_response handles exception from smart_search_products."""
        mock_product_data_service.smart_search_products.side_effect = Exception("Product search failed")

        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response("Any question")
            
            mock_product_data_service.smart_search_products.assert_called_once()
            assert "Error generating AI response: Product search failed" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    @pytest.mark.asyncio
    async def test_get_response_genai_content_exception(self, ai_service_instance, mock_product_data_service, mock_genai_client, caplog):
        """Test get_response handles exception from genai.Client.models.generate_content."""
        mock_product_data_service.smart_search_products.return_value = ([], "Fallback message.")
        mock_genai_client.models.generate_content.side_effect = Exception("AI model error")

        with caplog.at_level(logging.DEBUG): # Use DEBUG to capture more logs if needed
            response = await ai_service_instance.get_response("Test AI error")
            
            mock_product_data_service.smart_search_products.assert_called_once()
            mock_genai_client.models.generate_content.assert_called_once()
            assert "Error generating AI response: AI model error" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    def test_generate_response_success(self, ai_service_instance, mock_genai_client, caplog):
        """Test successful generation of AI response using the legacy method."""
        mock_genai_client.models.generate_content.return_value.text = "Legacy AI output."
        context_input = "This is a test context for legacy method."

        with caplog.at_level(logging.INFO):
            response = ai_service_instance.generate_response(context_input)
            
            mock_genai_client.models.generate_content.assert_called_once()
            
            call_args, _ = mock_genai_client.models.generate_content.call_args
            assert call_args[0] == "gemini-2.0-flash"
            assert call_args[1]['contents'].startswith("You are a helpful product assistant. Based on the following context")
            assert context_input in call_args[1]['contents']
            
            assert response == "Legacy AI output."
            assert "Generating AI response" in caplog.text
            assert "Successfully generated AI response" in caplog.text

    def test_generate_response_genai_content_exception(self, ai_service_instance, mock_genai_client, caplog):
        """Test generate_response handles exception from genai.Client.models.generate_content and re-raises."""
        mock_genai_client.models.generate_content.side_effect = Exception("Legacy AI model error")
        context_input = "This is a test context for legacy method."

        with pytest.raises(Exception, match="Legacy AI model error"), caplog.at_level(logging.ERROR):
            ai_service_instance.generate_response(context_input)
            
            mock_genai_client.models.generate_content.assert_called_once()
            assert "Error generating AI response: Legacy AI model error" in caplog.text