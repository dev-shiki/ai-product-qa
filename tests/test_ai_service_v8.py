import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ai_service import AIService
from app.utils.config import Settings  # Assuming Settings class exists in config

# Setup logging for tests
logger = logging.getLogger(__name__)

# Fixtures for common mocks
@pytest.fixture
def mock_settings():
    """Mocks get_settings to return a Settings object with a dummy API key."""
    settings = MagicMock(spec=Settings)
    settings.GOOGLE_API_KEY = "dummy_api_key_123"
    with patch('app.utils.config.get_settings', return_value=settings) as mock_get_settings:
        yield mock_get_settings

@pytest.fixture
def mock_product_data_service_class():
    """Mocks the ProductDataService class itself."""
    with patch('app.services.ai_service.ProductDataService') as mock_service_class:
        # Configure the mock instance that AIService.__init__ will create
        mock_instance = mock_service_class.return_value
        mock_instance.smart_search_products = AsyncMock() # Ensure smart_search_products is an AsyncMock
        yield mock_service_class

@pytest.fixture
def mock_genai_client_class():
    """Mocks google.genai.Client class and its methods."""
    with patch('google.genai.Client') as mock_client_class:
        # Configure the mock instance that AIService.__init__ will create
        mock_client_instance = mock_client_class.return_value
        # Mock the models attribute and its generate_content method
        mock_client_instance.models = MagicMock()
        mock_client_instance.models.generate_content = MagicMock()
        # The return value of generate_content needs a .text attribute
        mock_client_instance.models.generate_content.return_value.text = "Mocked AI response"
        yield mock_client_class

@pytest.fixture
def ai_service_instance(mock_settings, mock_product_data_service_class, mock_genai_client_class):
    """Provides an AIService instance with mocked dependencies."""
    return AIService()

# Test cases for AIService.__init__
class TestAIServiceInit:
    def test_init_success(self, mock_settings, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests successful initialization of AIService.
        Verifies client and product service are initialized and success log is present.
        """
        with caplog.at_level(logging.INFO):
            service = AIService()
            mock_settings.assert_called_once()
            mock_genai_client_class.assert_called_once_with(api_key=mock_settings.return_value.GOOGLE_API_KEY)
            mock_product_data_service_class.assert_called_once()
            assert "Successfully initialized AI service with Google AI client" in caplog.text
            assert service.client is mock_genai_client_class.return_value
            assert service.product_service is mock_product_data_service_class.return_value

    def test_init_get_settings_failure(self, mock_settings, caplog):
        """
        Tests AIService initialization when get_settings raises an exception.
        Verifies error is logged and re-raised.
        """
        mock_settings.side_effect = Exception("Config error: Missing API Key")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="Config error: Missing API Key"):
                AIService()
            assert "Error initializing AI service: Config error: Missing API Key" in caplog.text

    def test_init_genai_client_failure(self, mock_settings, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests AIService initialization when genai.Client raises an exception.
        Verifies error is logged and re-raised.
        """
        mock_genai_client_class.side_effect = Exception("GenAI client initialization failed")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="GenAI client initialization failed"):
                AIService()
            assert "Error initializing AI service: GenAI client initialization failed" in caplog.text

    def test_init_product_service_failure(self, mock_settings, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests AIService initialization when ProductDataService raises an exception.
        Verifies error is logged and re-raised.
        """
        mock_product_data_service_class.side_effect = Exception("ProductDataService initialization failed")
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="ProductDataService initialization failed"):
                AIService()
            assert "Error initializing AI service: ProductDataService initialization failed" in caplog.text


# Test cases for AIService.get_response
class TestAIServiceGetResponse:
    # Helper to create dummy product data
    def _create_product_data(self, num_products=1, category="Laptop"):
        products = []
        for i in range(num_products):
            products.append({
                "name": f"Product {i+1}",
                "price": 1000000 + i * 100000,
                "brand": f"Brand {i+1}",
                "category": category,
                "specifications": {"rating": 4.5},
                "description": f"Description for product {i+1}. This is a test description that will be truncated." * 5
            })
        return products

    @pytest.mark.asyncio
    async def test_get_response_success_with_products(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests successful AI response generation when products are found.
        Verifies product context, correct API call, and return value.
        """
        question = "rekomendasi laptop gaming harga 15 juta"
        expected_ai_response = "Here are some great laptop options for you..."

        # Configure the mock ProductDataService instance that AIService uses
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_product_service_instance.smart_search_products.return_value = (self._create_product_data(num_products=2, category="Laptop"), "Found some relevant laptops.")

        # Configure the mock genai client instance that AIService uses
        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response(question)

            mock_product_service_instance.smart_search_products.assert_awaited_once_with(
                keyword=question, category='laptop', max_price=15000000, limit=5
            )

            # Assert prompt content (check for key phrases)
            call_args = mock_genai_client_instance.models.generate_content.call_args[1]
            assert call_args['model'] == "gemini-2.5-flash"
            assert "You are a helpful product assistant." in call_args['contents']
            assert f"Question: {question}" in call_args['contents']
            assert "Relevant Products:" in call_args['contents']
            assert "1. Product 1" in call_args['contents']
            assert "2. Product 2" in call_args['contents']
            assert "Price: Rp 1,000,000" in call_args['contents']
            assert "Rating: 4.5/5" in call_args['contents']
            assert "Found some relevant laptops." in call_args['contents']
            assert "No specific products found" not in call_args['contents']

            assert response == expected_ai_response
            assert f"Getting AI response for question: {question}" in caplog.text
            assert "Successfully generated AI response" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_success_no_products(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests successful AI response generation when no products are found.
        Verifies correct context, API call, and return value.
        """
        question = "cari barang yang aneh"
        expected_ai_response = "I couldn't find any specific products for that query."

        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_product_service_instance.smart_search_products.return_value = ([], "No specific products found for your query.")

        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = await ai_service_instance.get_response(question)

            mock_product_service_instance.smart_search_products.assert_awaited_once_with(
                keyword=question, category=None, max_price=None, limit=5
            )

            call_args = mock_genai_client_instance.models.generate_content.call_args[1]
            assert "Relevant Products:" not in call_args['contents']
            assert "No specific products found, but I can provide general recommendations." in call_args['contents']
            assert "No specific products found for your query." in call_args['contents'] # From fallback message

            assert response == expected_ai_response
            assert "Successfully generated AI response" in caplog.text

    @pytest.mark.parametrize("question, expected_category, expected_max_price", [
        ("Cari laptop untuk gaming", "laptop", None),
        ("HP Samsung budget 3 juta", "smartphone", 3000000),
        ("tablet Apple", "tablet", None),
        ("headphone murah", "headphone", 5000000), # Test 'murah' for 5M budget
        ("kamera dibawah 10 juta", "kamera", 10000000),
        ("audio system", "audio", None),
        ("TV 50 inch", "tv", None),
        ("berapa harga drone?", "drone", None),
        ("smartwatch yang bagus", "jam", None),
        ("rekomendasi komputer kerja", "laptop", None), # Test synonym
        ("ponsel terbaru", "smartphone", None), # Test synonym
        ("earphone bluetooth", "headphone", None), # Test synonym
        ("handphone 2 juta", "smartphone", 2000000),
        ("budget hp 4.5 juta", "smartphone", 4500000),
        ("cari laptop budget", "laptop", 5000000), # Test 'budget' for 5M budget
        ("apakah ada monitor?", None, None), # No matching category or price
        ("saya mau beli sesuatu", None, None), # No specific keywords
        ("jam tangan", "jam", None), # Test 'jam' category
        ("harga hp", "smartphone", None), # No price, only category
        ("smartphone 7 juta", "smartphone", 7000000), # Exact match 'juta'
        ("saya butuh smartphone dengan anggaran 6 juta", "smartphone", 6000000), # More complex sentence
    ])
    @pytest.mark.asyncio
    async def test_get_response_category_price_detection(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, question, expected_category, expected_max_price):
        """
        Tests the category and price detection logic within get_response.
        Verifies smart_search_products is called with the correct parameters.
        """
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_product_service_instance.smart_search_products.return_value = ([], "No products.")

        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.return_value.text = "Mocked AI response"

        await ai_service_instance.get_response(question)

        mock_product_service_instance.smart_search_products.assert_awaited_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

    @pytest.mark.asyncio
    async def test_get_response_smart_search_products_exception(self, ai_service_instance, mock_product_data_service_class, caplog):
        """
        Tests get_response when smart_search_products raises an exception.
        Verifies error is logged and fallback message is returned.
        """
        question = "anything"
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_product_service_instance.smart_search_products.side_effect = Exception("Product search failed")

        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response(question)
            assert "Error generating AI response: Product search failed" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    @pytest.mark.asyncio
    async def test_get_response_genai_content_generation_exception(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class, caplog):
        """
        Tests get_response when client.models.generate_content raises an exception.
        Verifies error is logged and fallback message is returned.
        """
        question = "anything"
        mock_product_service_instance = mock_product_data_service_class.return_value
        mock_product_service_instance.smart_search_products.return_value = ([], "No products.")

        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.side_effect = Exception("GenAI generation failed")

        with caplog.at_level(logging.ERROR):
            response = await ai_service_instance.get_response(question)
            assert "Error generating AI response: GenAI generation failed" in caplog.text
            assert response == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    @pytest.mark.asyncio
    async def test_get_response_product_description_truncation(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """
        Tests that product descriptions in the context are truncated to 200 characters.
        """
        long_description = "A very very very long description that definitely exceeds two hundred characters. " * 20
        products = [{
            "name": "Product with long description",
            "price": 100, "brand": "BrandX", "category": "CategoryY",
            "specifications": {"rating": 5},
            "description": long_description
        }]
        mock_product_data_service_class.return_value.smart_search_products.return_value = (products, "Found one product.")
        mock_genai_client_class.return_value.models.generate_content.return_value.text = "Mocked AI response"

        await ai_service_instance.get_response("test question")

        call_args = mock_genai_client_class.return_value.models.generate_content.call_args[1]
        context = call_args['contents']

        # Check if the description is truncated and ends with "..."
        expected_truncated_desc = long_description[:200] + "..."
        assert expected_truncated_desc in context
        assert long_description not in context # Ensure full string isn't there

    @pytest.mark.asyncio
    async def test_get_response_empty_product_fields(self, ai_service_instance, mock_product_data_service_class, mock_genai_client_class):
        """
        Tests that default values are used for missing or empty product fields in context.
        """
        products = [{
            "name": "Product Missing Fields",
            "price": None, # Test None price
            "brand": "", # Test empty brand
            "category": "", # Test empty category
            "specifications": {}, # Test empty specifications
            "description": "" # Test empty description
        }]
        mock_product_data_service_class.return_value.smart_search_products.return_value = (products, "Found one product.")
        mock_genai_client_class.return_value.models.generate_content.return_value.text = "Mocked AI response"

        await ai_service_instance.get_response("test question")

        call_args = mock_genai_client_class.return_value.models.generate_content.call_args[1]
        context = call_args['contents']

        assert "1. Product Missing Fields" in context
        assert "Price: Rp 0" in context # Default for missing/None price
        assert "Brand: Unknown" in context # Default for missing/empty brand
        assert "Category: Unknown" in context # Default for missing/empty category
        assert "Rating: 0/5" in context # Default for missing/empty specifications.rating
        assert "Description: No description..." in context # Default for missing/empty description

# Test cases for AIService.generate_response (legacy method)
class TestAIServiceGenerateResponse:
    def test_generate_response_success(self, ai_service_instance, mock_genai_client_class, caplog):
        """
        Tests successful generation of response using the legacy method.
        Verifies correct API call and return value.
        """
        context = "This is some test context for the AI."
        expected_ai_response = "AI processed the context successfully."

        mock_genai_client_instance = mock_genai_client_class.return_value
        mock_genai_client_instance.models.generate_content.return_value.text = expected_ai_response

        with caplog.at_level(logging.INFO):
            response = ai_service_instance.generate_response(context)

            # Assert prompt content
            call_args = mock_genai_client_instance.models.generate_content.call_args[1]
            assert call_args['model'] == "gemini-2.0-flash"
            assert "You are a helpful product assistant." in call_args['contents']
            assert context in call_args['contents']
            # Ensure the specific prompt structure is present
            assert "\nPlease provide a clear and concise answer that helps the user understand the products and make an informed decision." in call_args['contents']

            assert response == expected_ai_response
            assert "Generating AI response" in caplog.text
            assert "Successfully generated AI response" in caplog.text

    def test_generate_response_genai_content_generation_exception(self, ai_service_instance, mock_genai_client_class, caplog):
        """
        Tests generate_response when client.models.generate_content raises an exception.
        Verifies error is logged and re-raised.
        """
        context = "Error scenario test for legacy method."
        mock_genai_client_class.return_value.models.generate_content.side_effect = Exception("GenAI legacy generation failed")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception, match="GenAI legacy generation failed"):
                ai_service_instance.generate_response(context)
            assert "Error generating AI response: GenAI legacy generation failed" in caplog.text