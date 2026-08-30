import asyncio
import logging
import warnings

warnings.filterwarnings(
    "ignore",
    message="nltk is not installed.*",
    category=UserWarning,
)
import newspaper

from domain.services import ArticleContentPort

logger = logging.getLogger(__name__)

MAX_CHARS = 3000


class NewspaperExtractor(ArticleContentPort):
    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout

    async def extract_content(self, url: str) -> str | None:
        if not url:
            return None

        try:
            article = await asyncio.wait_for(
                asyncio.to_thread(self._fetch_article, url),
                timeout=self._timeout,
            )
            if article and article.text:
                return article.text[:MAX_CHARS]
            return None
        except asyncio.TimeoutError:
            logger.warning("Timeout extracting content from %s", url)
            return None
        except Exception as e:
            logger.warning("Failed to extract content from %s: %s", url, e)
            return None

    def _fetch_article(self, url: str) -> newspaper.Article:
        article = newspaper.Article(url, request_timeout=self._timeout)
        article.download()
        article.parse()
        return article
