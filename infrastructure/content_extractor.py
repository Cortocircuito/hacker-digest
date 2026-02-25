import asyncio

import newspaper

from domain.services import ArticleContentPort

MAX_CHARS = 3000


class NewspaperExtractor(ArticleContentPort):
    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout

    async def extract_content(self, url: str) -> str | None:
        if not url:
            return None

        try:
            article = await asyncio.to_thread(self._fetch_article, url)
            if article and article.text:
                return article.text[:MAX_CHARS]
            return None
        except Exception:
            return None

    def _fetch_article(self, url: str) -> newspaper.Article:
        paper = newspaper.build(url, memoize_articles=False)
        if paper.articles:
            article = paper.articles[0]
            article.download()
            article.parse()
            return article
        raise ValueError("No articles found")
