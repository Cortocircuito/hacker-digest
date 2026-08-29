import asyncio
import logging
from collections.abc import Callable

from domain.entities import Article
from domain.services import ArticleContentPort, HackerNewsPort, SummarizerPort

logger = logging.getLogger(__name__)

MAX_CONCURRENT_EXTRACTIONS = 3
ProgressCallback = Callable[[str, int, int], None]


class SummarizeArticle:
    def __init__(
        self,
        hn_client: HackerNewsPort,
        summarizer: SummarizerPort,
        content_extractor: ArticleContentPort,
    ) -> None:
        self._hn_client = hn_client
        self._summarizer = summarizer
        self._content_extractor = content_extractor

    async def execute(
        self,
        limit: int = 10,
        progress_callback: ProgressCallback | None = None,
    ) -> list[tuple[Article, str]]:
        articles = await self._hn_client.get_top_stories(limit)
        total = len(articles)
        if progress_callback:
            progress_callback("Extracting", 0, total)

        extracted = 0

        def report_extraction() -> None:
            nonlocal extracted
            extracted += 1
            if progress_callback:
                progress_callback("Extracting", extracted, total)

        extraction_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTIONS)
        contents = await asyncio.gather(
            *(
                self._extract_content(
                    article,
                    extraction_semaphore,
                    report_extraction if progress_callback else None,
                )
                for article in articles
            )
        )

        if progress_callback:
            progress_callback("Summarizing", 0, total)

        results: list[tuple[Article, str]] = []
        for completed, (article, content) in enumerate(
            zip(articles, contents), start=1
        ):
            try:
                summary = await self._summarizer.summarize(article, content)
                results.append((article, summary))
            except Exception as e:
                logger.error(
                    "Failed to summarize article %d '%s': %s",
                    article.id,
                    article.title,
                    e,
                )
                results.append((article, "[Error generating summary]"))
            if progress_callback:
                progress_callback("Summarizing", completed, total)
        return results

    async def _extract_content(
        self,
        article: Article,
        semaphore: asyncio.Semaphore,
        on_complete: Callable[[], None] | None,
    ) -> str | None:
        try:
            if not article.url:
                return None
            async with semaphore:
                return await self._content_extractor.extract_content(article.url)
        except Exception:
            logger.warning(
                "Failed to extract content for article %d '%s'",
                article.id,
                article.title,
                exc_info=True,
            )
            return None
        finally:
            if on_complete:
                on_complete()
