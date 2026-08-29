import asyncio
from unittest.mock import AsyncMock, call

import pytest

from domain.entities import Article
from usecases.summarize_article import SummarizeArticle


def _articles(count: int) -> list[Article]:
    return [
        Article(
            id=index,
            title=f"Article {index}",
            url=f"https://example.com/{index}",
            by="user",
            score=100,
            time=1234567890,
            descendants=10,
        )
        for index in range(1, count + 1)
    ]


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


@pytest.mark.asyncio
async def test_summarize_article_limits_extraction_and_preserves_order():
    class TrackingExtractor:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0

        async def extract_content(self, url: str) -> str:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            try:
                await asyncio.sleep(0.01)
                return url
            finally:
                self.active -= 1

    articles = _articles(5)
    mock_hn_client = AsyncMock()
    mock_hn_client.get_top_stories.return_value = articles
    extractor = TrackingExtractor()
    mock_summarizer = AsyncMock()
    mock_summarizer.summarize.side_effect = (
        lambda article, content: f"{article.id}: {content}"
    )
    progress: list[tuple[str, int, int]] = []

    use_case = SummarizeArticle(mock_hn_client, mock_summarizer, extractor)
    results = await use_case.execute(
        progress_callback=lambda phase, done, total: progress.append(
            (phase, done, total)
        )
    )

    assert extractor.max_active == 3
    assert [article.id for article, _ in results] == [1, 2, 3, 4, 5]
    assert [summary for _, summary in results] == [
        "1: https://example.com/1",
        "2: https://example.com/2",
        "3: https://example.com/3",
        "4: https://example.com/4",
        "5: https://example.com/5",
    ]
    extracting = [event for event in progress if event[0] == "Extracting"]
    summarizing = [event for event in progress if event[0] == "Summarizing"]
    assert extracting == [
        ("Extracting", 0, 5),
        ("Extracting", 1, 5),
        ("Extracting", 2, 5),
        ("Extracting", 3, 5),
        ("Extracting", 4, 5),
        ("Extracting", 5, 5),
    ]
    assert summarizing == [
        ("Summarizing", 0, 5),
        ("Summarizing", 1, 5),
        ("Summarizing", 2, 5),
        ("Summarizing", 3, 5),
        ("Summarizing", 4, 5),
        ("Summarizing", 5, 5),
    ]


@pytest.mark.asyncio
async def test_summarize_article_runs_ollama_sequentially():
    class TrackingSummarizer:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0

        async def summarize(self, article: Article, content: str | None = None) -> str:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            try:
                await asyncio.sleep(0.01)
                return article.title
            finally:
                self.active -= 1

    articles = _articles(3)
    mock_hn_client = AsyncMock()
    mock_hn_client.get_top_stories.return_value = articles
    mock_content_extractor = AsyncMock()
    mock_content_extractor.extract_content.return_value = "content"
    summarizer = TrackingSummarizer()

    use_case = SummarizeArticle(mock_hn_client, summarizer, mock_content_extractor)
    await use_case.execute()

    assert summarizer.max_active == 1


@pytest.mark.asyncio
async def test_summarize_article_continues_after_extraction_failure():
    class FailingExtractor:
        async def extract_content(self, url: str) -> str:
            if url.endswith("/1"):
                raise RuntimeError("Blocked by publisher")
            return "article content"

    articles = _articles(2)
    mock_hn_client = AsyncMock()
    mock_hn_client.get_top_stories.return_value = articles
    mock_summarizer = AsyncMock()
    mock_summarizer.summarize.return_value = "summary"

    use_case = SummarizeArticle(mock_hn_client, mock_summarizer, FailingExtractor())
    results = await use_case.execute()

    assert [article for article, _ in results] == articles
    assert mock_summarizer.summarize.await_args_list == [
        call(articles[0], None),
        call(articles[1], "article content"),
    ]
