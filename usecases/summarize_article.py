from domain.entities import Article
from domain.services import ArticleContentPort, HackerNewsPort, SummarizerPort


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

    async def execute(self, limit: int = 10) -> list[tuple[Article, str]]:
        articles = await self._hn_client.get_top_stories(limit)
        results: list[tuple[Article, str]] = []
        for article in articles:
            try:
                content = None
                if article.url:
                    content = await self._content_extractor.extract_content(article.url)
                summary = await self._summarizer.summarize(article, content)
                results.append((article, summary))
            except Exception:
                results.append((article, "[Error generating summary]"))
        return results
