import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import asyncio

# --- Fixtures ---

@pytest.fixture
def mock_settings():
    """Mock get_settings to return a dummy API key."""
    mock_obj = MagicMock()
    mock_obj.GOOGLE_API_KEY = "dummy_api_key_123"
    with patch('app.utils.config.get_settings', return_value=mock_obj) as mock:
        yield mock

@pytest.fixture
def mock_genai_client():
    """Mock google.genai.Client and its models.generate_content method."""
    mock_content_response = MagicMock()
    mock_content_response.text = "AI Generated Response"

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_content_response

    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models

    with patch('google.genai.Client', return_value=mock_client_instance) as mock_client_cls:
        yield mock_client_cls

@pytest.fixture
def mock_product_data_service():
    """Mock ProductDataService and its smart_search_products method."""
    mock_product_service_instance = MagicMock()
    mock_product_service_instance.smart_search_products = AsyncMock(
        return_value=(
            [
                {
                    'name': 'Laptop Pro 1',
                    'price': 15000000,
                    'brand': 'BrandX',
                    'category': 'laptop',
                    'specifications': {'rating': 4.5},
                    'description': 'Powerful laptop for all your needs.'
                },
                {
                    'name': 'Laptop Eco 2',
                    'price': 12000000,
                    'brand': 'BrandY',
                    'category': 'laptop',
                    'specifications': {'rating': 4.0},
                    'description': 'Affordable laptop with good performance.'
                }
            ],
            "Here are some relevant products based on your query."
        )
    )
    with patch('app.services.product_data_service.ProductDataService', return_value=mock_product_service_instance) as mock:
        yield mock

@pytest.fixture
def ai_service_instance(mock_settings, mock_genai_client, mock_product_data_service):
    """Fixture for a correctly initialized AIService instance."""
    return AIService()

@pytest.fixture(autouse=True)
def mock_logging():
    """Mocks the logger to capture calls for assertion."""
    with patch('app.services.ai_service.logger') as mock_logger:
        yield mock_logger

# --- Test Cases ---

class TestAIServiceInitialization:
    def test_init_success(self, mock_settings, mock_genai_client, mock_product_data_service, mock_logging):
        """
        Test successful initialization of AIService.
        Verifies that settings, genai.Client, and ProductDataService are correctly initialized
        and success log is recorded.
        """
        service = AIService()

        mock_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key="dummy_api_key_123")
        mock_product_data_service.assert_called_once()
        assert service.client == mock_genai_client.return_value
        assert service.product_service == mock_product_data_service.return_value
        mock_logging.info.assert_called_once_with("Successfully initialized AI service with Google AI client")
        mock_logging.error.assert_not_called()

    def test_init_get_settings_failure(self, mock_settings, mock_logging):
        """
        Test initialization failure when get_settings raises an exception.
        Verifies that an exception is raised and an error log is recorded.
        """
        mock_settings.side_effect = Exception("Config error")

        with pytest.raises(Exception, match="Config error"):
            AIService()

        mock_settings.assert_called_once()
        mock_logging.error.assert_called_once_with("Error initializing AI service: Config error")
        mock_logging.info.assert_not_called()

    def test_init_genai_client_failure(self, mock_settings, mock_genai_client, mock_logging):
        """
        Test initialization failure when genai.Client initialization fails.
        Verifies that an exception is raised and an error log is recorded.
        """
        mock_genai_client.side_effect = Exception("GenAI client error")

        with pytest.raises(Exception, match="GenAI client error"):
            AIService()

        mock_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key="dummy_api_key_123")
        mock_logging.error.assert_called_once_with("Error initializing AI service: GenAI client error")
        mock_logging.info.assert_not_called()

    def test_init_product_service_failure(self, mock_settings, mock_genai_client, mock_product_data_service, mock_logging):
        """
        Test initialization failure when ProductDataService initialization fails.
        Verifies that an exception is raised and an error log is recorded.
        """
        mock_product_data_service.side_effect = Exception("Product service error")

        with pytest.raises(Exception, match="Product service error"):
            AIService()

        mock_settings.assert_called_once()
        mock_genai_client.assert_called_once_with(api_key="dummy_api_key_123")
        mock_product_data_service.assert_called_once()
        mock_logging.error.assert_called_once_with("Error initializing AI service: Product service error")
        mock_logging.info.assert_not_called()


class TestAIServiceGetResponse:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("question, expected_category, expected_max_price, expected_product_return", [
        ("Cari laptop yang bagus", "laptop", None, "laptop_data"),
        ("HP murah dibawah 5 juta", "smartphone", 5000000, "empty_data"),
        ("Smartphone budget 3 juta", "smartphone", 3000000, "empty_data"),
        ("Headphones", "headphone", None, "empty_data"),
        ("Saya mau kamera 10 juta", "kamera", 10000000, "empty_data"),
        ("speaker harga 2 juta", "audio", 2000000, "empty_data"),
        ("Televisi murah", "tv", 5000000, "empty_data"),
        ("Drone dengan anggaran", "drone", 5000000, "empty_data"),
        ("Smartwatch", "jam", None, "empty_data"),
        ("Produk umum apa saja?", None, None, "empty_data"), # No category, no price
        ("Cari notebook 15 juta", "laptop", 15000000, "laptop_data"), # Test notebook keyword
        ("Ada ipad sekitar 7 juta?", "tablet", 7000000, "empty_data"), # Test ipad keyword
        ("Cari headset gaming", "headphone", None, "empty_data"), # Test headset keyword
        ("Telepon 8 juta", "smartphone", 8000000, "empty_data"), # Test telepon keyword
        ("Komputer", "laptop", None, "laptop_data"), # Test komputer keyword
        ("Ponsel", "smartphone", None, "empty_data"), # Test ponsel keyword
        ("Handphone", "smartphone", None, "empty_data"), # Test handphone keyword
        ("budget murah", None, 5000000, "empty_data"), # Only budget, no category
        ("apakah ada yang murah", None, 5000000, "empty_data"), # Only murah, no category
    ])
    async def test_get_response_success_with_various_inputs(self, ai_service_instance, mock_product_data_service, mock_genai_client, mock_logging,
                                                            question, expected_category, expected_max_price, expected_product_return):
        """
        Test successful get_response with various question inputs covering category and price extraction.
        Verifies correct calls to product service and AI client, and proper prompt construction.
        """
        laptop_data = [
            {
                'name': 'Super Laptop',
                'price': 20000000,
                'brand': 'TechCo',
                'category': 'laptop',
                'specifications': {'rating': 4.8},
                'description': 'High-performance laptop for professionals.'
            }
        ]
        empty_data = []

        if expected_product_return == "laptop_data":
            mock_product_data_service.return_value.smart_search_products.return_value = (
                laptop_data,
                "Found some great laptops for you."
            )
        else:
            mock_product_data_service.return_value.smart_search_products.return_value = (
                empty_data,
                "No specific products found for this query."
            )

        response_text = await ai_service_instance.get_response(question)

        mock_logging.info.assert_any_call(f"Getting AI response for question: {question}")
        mock_product_data_service.return_value.smart_search_products.assert_called_once_with(
            keyword=question, category=expected_category, max_price=expected_max_price, limit=5
        )

        mock_genai_client.return_value.models.generate_content.assert_called_once()
        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        actual_model = kwargs.get('model')
        actual_contents = kwargs.get('contents')

        assert actual_model == "gemini-2.5-flash"
        assert f"Question: {question}" in actual_contents
        assert "You are a helpful product assistant." in actual_contents
        assert "Please provide a clear and concise answer" in actual_contents
        
        if expected_product_return == "laptop_data":
            assert "Relevant Products:" in actual_contents
            assert "1. Super Laptop" in actual_contents
        else:
            assert "No specific products found, but I can provide general recommendations." in actual_contents
            assert "Relevant Products:" not in actual_contents # Ensure this section is not present for empty results

        assert "AI Generated Response" == response_text
        mock_logging.info.assert_any_call("Successfully generated AI response")
        mock_logging.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_response_product_service_raises_exception(self, ai_service_instance, mock_product_data_service, mock_genai_client, mock_logging):
        """
        Test get_response when smart_search_products raises an exception.
        Verifies that a fallback message is returned and an error log is recorded,
        and AI content generation is not attempted.
        """
        mock_product_data_service.return_value.smart_search_products.side_effect = Exception("DB error")
        question = "Laptop 5 juta"

        response_text = await ai_service_instance.get_response(question)

        mock_logging.info.assert_any_call(f"Getting AI response for question: {question}")
        mock_product_data_service.return_value.smart_search_products.assert_called_once()
        mock_logging.error.assert_called_once_with("Error generating AI response: DB error")
        assert response_text == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."
        mock_genai_client.return_value.models.generate_content.assert_not_called() # Crucial: AI call should not happen

    @pytest.mark.asyncio
    async def test_get_response_genai_client_raises_exception(self, ai_service_instance, mock_genai_client, mock_logging):
        """
        Test get_response when genai.Client.models.generate_content raises an exception.
        Verifies that a fallback message is returned and an error log is recorded.
        """
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("AI API limit reached")
        question = "Smartphone gaming"

        response_text = await ai_service_instance.get_response(question)

        mock_logging.info.assert_any_call(f"Getting AI response for question: {question}")
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        mock_logging.error.assert_called_once_with("Error generating AI response: AI API limit reached")
        assert response_text == "Maaf, saya sedang mengalami kesulitan untuk memberikan rekomendasi. Silakan coba lagi nanti."

    @pytest.mark.asyncio
    async def test_get_response_product_details_formatting(self, ai_service_instance, mock_product_data_service, mock_genai_client):
        """
        Test that product details are correctly formatted in the prompt, including price formatting,
        rating, description truncation, and handling of missing product keys.
        """
        mock_product_data_service.return_value.smart_search_products.return_value = (
            [
                {
                    'name': 'Test Product X',
                    'price': 12345678,
                    'brand': 'TestBrand',
                    'category': 'TestCategory',
                    'specifications': {'rating': 4.7},
                    'description': 'This is a long description that needs to be truncated for the prompt to keep it concise and readable. It contains more than 200 characters, so truncation should definitely occur with an ellipsis at the end, ensuring only the relevant part is included.'
                }
            ],
            "Here's a test product."
        )
        question = "Test question about product details"
        await ai_service_instance.get_response(question)

        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        prompt_content = kwargs.get('contents')

        assert "Relevant Products:\n1. Test Product X" in prompt_content
        assert "Price: Rp 12,345,678" in prompt_content
        assert "Brand: TestBrand" in prompt_content
        assert "Category: TestCategory" in prompt_content
        assert "Rating: 4.7/5" in prompt_content
        # Check for truncated description + ellipsis
        expected_truncated_desc = "Description: This is a long description that needs to be truncated for the prompt to keep it concise and readable. It contains more than 200 characters, so truncation should definitely occur with an ellipsis at the end, ensuring only the relevant part is inclu..."
        assert expected_truncated_desc in prompt_content
        
        # Test product with missing keys
        mock_product_data_service.return_value.smart_search_products.return_value = (
            [
                {
                    'name': 'Partial Product',
                    'price': 1000000,
                    # Missing brand, category, specifications, description intentionally
                }
            ],
            "Test partial product."
        )
        await ai_service_instance.get_response("Partial product query")
        args, kwargs = mock_genai_client.return_value.models.generate_content.call_args
        prompt_content = kwargs.get('contents')

        assert "1. Partial Product" in prompt_content
        assert "Price: Rp 1,000,000" in prompt_content
        assert "Brand: Unknown" in prompt_content
        assert "Category: Unknown" in prompt_content
        assert "Rating: 0/5" in prompt_content
        assert "Description: No description..." in prompt_content


class TestAIServiceGenerateResponse:
    def test_generate_response_success(self, ai_service_instance, mock_genai_client, mock_logging):
        """
        Test successful generation of AI response using the legacy generate_response method.
        Verifies correct model, prompt content, and success log.
        """
        context = "This is a test context for the AI model."
        response = ai_service_instance.generate_response(context)

        mock_logging.info.assert_any_call("Generating AI response")
        expected_prompt = f"""You are a helpful product assistant. Based on the following context, provide a helpful and informative response:

{context}

Please provide a clear and concise answer that helps the user understand the products and make an informed decision."""

        mock_genai_client.return_value.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash",
            contents=expected_prompt
        )
        assert response == "AI Generated Response"
        mock_logging.info.assert_any_call("Successfully generated AI response")
        mock_logging.error.assert_not_called()

    def test_generate_response_failure(self, ai_service_instance, mock_genai_client, mock_logging):
        """
        Test generation failure when genai.Client.models.generate_content raises an exception
        in the legacy generate_response method.
        Verifies that the exception is re-raised and an error log is recorded.
        """
        mock_genai_client.return_value.models.generate_content.side_effect = Exception("Legacy AI API error")
        context = "Error context for legacy method."

        with pytest.raises(Exception, match="Legacy AI API error"):
            ai_service_instance.generate_response(context)

        mock_logging.info.assert_any_call("Generating AI response")
        mock_genai_client.return_value.models.generate_content.assert_called_once()
        mock_logging.error.assert_called_once_with("Error generating AI response: Legacy AI API error")