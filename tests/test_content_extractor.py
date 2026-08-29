import pytest
import time
from unittest.mock import MagicMock, patch

from infrastructure.content_extractor import NewspaperExtractor


@pytest.mark.asyncio
async def test_content_extractor_timeout():
    def slow_fetch(url):
        time.sleep(0.1)
        return MagicMock(text="content")

    with patch.object(NewspaperExtractor, "_fetch_article", side_effect=slow_fetch):
        extractor = NewspaperExtractor(timeout=0.01)
        result = await extractor.extract_content("https://example.com")
        assert result is None


@pytest.mark.asyncio
async def test_content_extractor_empty_url():
    extractor = NewspaperExtractor()
    result = await extractor.extract_content("")
    assert result is None


@pytest.mark.asyncio
async def test_content_extractor_success():
    mock_article = MagicMock()
    mock_article.text = "Test content"

    with patch.object(NewspaperExtractor, "_fetch_article", return_value=mock_article):
        extractor = NewspaperExtractor()
        result = await extractor.extract_content("https://example.com")
        assert result == "Test content"


def test_content_extractor_passes_timeout_to_newspaper():
    with patch("infrastructure.content_extractor.newspaper.Article") as article_class:
        extractor = NewspaperExtractor(timeout=12)
        extractor._fetch_article("https://example.com")

    article_class.assert_called_once_with("https://example.com", request_timeout=12)
