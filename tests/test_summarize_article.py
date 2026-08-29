import pytest
from unittest.mock import AsyncMock

from usecases.summarize_article import SummarizeArticle
from domain.entities import Article


@pytest.mark.asyncio
async def test_summarize_article_success():
    mock_hn_client = AsyncMock()
    mock_summarizer = AsyncMock()
    mock_content_extractor = AsyncMock()

    article = Article(
        id=1,
        title="Test",
        url="https://example.com",
        by="user",
        score=100,
        time=1234567890,
        descendants=10,
    )
    mock_hn_client.get_top_stories.return_value = [article]
    mock_content_extractor.extract_content.return_value = "content"
    mock_summarizer.summarize.return_value = "summary"

    use_case = SummarizeArticle(mock_hn_client, mock_summarizer, mock_content_extractor)
    results = await use_case.execute(limit=1)

    assert len(results) == 1
    assert results[0][0] == article
    assert results[0][1] == "summary"


@pytest.mark.asyncio
async def test_summarize_article_error_handling():
    mock_hn_client = AsyncMock()
    mock_summarizer = AsyncMock()
    mock_content_extractor = AsyncMock()

    article = Article(
        id=1,
        title="Test",
        url="https://example.com",
        by="user",
        score=100,
        time=1234567890,
        descendants=10,
    )
    mock_hn_client.get_top_stories.return_value = [article]
    mock_summarizer.summarize.side_effect = Exception("API Error")

    use_case = SummarizeArticle(mock_hn_client, mock_summarizer, mock_content_extractor)
    results = await use_case.execute(limit=1)

    assert len(results) == 1
    assert results[0][1] == "[Error generating summary]"
