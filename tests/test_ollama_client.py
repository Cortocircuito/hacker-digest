import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.ollama_client import OllamaClient
from domain.entities import Article


@pytest.mark.asyncio
async def test_ollama_client_context_manager():
    async with OllamaClient() as client:
        assert client._client is not None
        http_client = client._client

    assert http_client.is_closed


@pytest.mark.asyncio
async def test_ollama_client_summarize_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": "ESPAÑOL:\nResumen de prueba.\n\nENGLISH:\nTest summary."
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        async with OllamaClient() as client:
            article = Article(
                id=1,
                title="Test",
                url="https://example.com",
                by="user",
                score=100,
                time=1234567890,
                descendants=10,
            )
            summary = await client.summarize(article)
            assert "ESPAÑOL" in summary
            assert "ENGLISH" in summary


@pytest.mark.asyncio
async def test_ollama_client_ensure_model_exists():
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "gemma2:2b"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        async with OllamaClient() as client:
            await client.ensure_model()


@pytest.mark.asyncio
async def test_ollama_client_ensure_model_accepts_implicit_latest_tag():
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "mistral:latest"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get, \
         patch("infrastructure.ollama_client.subprocess.run") as mock_subprocess:
        mock_get.return_value = mock_response
        async with OllamaClient(model="mistral") as client:
            await client.ensure_model()

    mock_subprocess.assert_not_called()


@pytest.mark.asyncio
async def test_ollama_client_ensure_model_rejects_different_tag():
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "gemma2:9b"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get, \
         patch("infrastructure.ollama_client.subprocess.run") as mock_subprocess:
        mock_get.return_value = mock_response
        async with OllamaClient(model="gemma2:2b") as client:
            await client.ensure_model()

    mock_subprocess.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_client_ensure_model_not_exists():
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get, \
         patch("infrastructure.ollama_client.subprocess.run") as mock_subprocess:
        mock_get.return_value = mock_response
        async with OllamaClient() as client:
            await client.ensure_model()
            mock_subprocess.assert_called_once()
