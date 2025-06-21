import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import AIService

@patch("app.services.ai_service.get_settings")
@patch("app.services.ai_service.genai.Client")
@patch("app.services.ai_service.ProductDataService")
@pytest.mark.asyncio
async def test_get_response(mock_product_service, mock_client, mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_client.return_value.models.generate_content.return_value.text = "AI answer"
    mock_product_service.return_value.search_products = AsyncMock(return_value=[{"name": "Produk A", "price": 10000, "brand": "BrandX", "category": "Elektronik", "specifications": {"rating": 5}, "description": "desc"}])
    ai = AIService()
    result = await ai.get_response("Apa laptop terbaik?")
    assert "AI answer" in result

@patch("app.services.ai_service.get_settings")
@patch("app.services.ai_service.genai.Client")
@patch("app.services.ai_service.ProductDataService")
def test_generate_response(mock_product_service, mock_client, mock_settings):
    mock_settings.return_value.GOOGLE_API_KEY = "dummy-key"
    mock_client.return_value.models.generate_content.return_value.text = "AI answer"
    ai = AIService()
    result = ai.generate_response("context")
    assert result == "AI answer" 