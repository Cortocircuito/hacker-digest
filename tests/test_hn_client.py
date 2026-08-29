import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.hn_client import HNClient


@pytest.mark.asyncio
async def test_hn_client_context_manager():
    async with HNClient() as client:
        assert client._client is not None
        http_client = client._client

    assert http_client.is_closed


@pytest.mark.asyncio
async def test_hn_client_get_article_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": 123,
        "title": "Test Title",
        "url": "https://example.com",
        "by": "testuser",
        "score": 50,
        "time": 1234567890,
        "descendants": 10,
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        async with HNClient() as client:
            article = await client.get_article(123)
            assert article.id == 123
            assert article.title == "Test Title"
            assert article.url == "https://example.com"


@pytest.mark.asyncio
async def test_hn_client_get_article_invalid_data():
    mock_response = MagicMock()
    mock_response.json.return_value = None
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        async with HNClient() as client:
            with pytest.raises(ValueError, match="Invalid article data"):
                await client.get_article(123)


@pytest.mark.asyncio
async def test_hn_client_rejects_invalid_top_stories_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {"ids": [1, 2]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        async with HNClient() as client:
            with pytest.raises(ValueError, match="Invalid top stories response"):
                await client.get_top_stories()
