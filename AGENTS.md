# HackerDigest

## Overview

HackerDigest is an async Python CLI that fetches Hacker News top stories, extracts linked article content, and produces concise Spanish/English summaries with a local Ollama model.

## Architecture

```
domain/
  entities.py            # Article domain entity
  services.py            # Protocol ports
infrastructure/
  hn_client.py           # Hacker News Firebase API adapter
  ollama_client.py       # Ollama API adapter and model availability check
  content_extractor.py   # Newspaper4k content extractor
usecases/
  summarize_article.py   # Orchestrates retrieval, extraction, and summaries
interface/
  cli.py                 # Rich terminal and Markdown output
tests/                   # pytest tests
main.py                  # Composition root and argument parsing
```

Keep dependencies directed inward: domain and use cases must not import infrastructure or interface modules. Keep ports small and use `Protocol` for adapters.

## Domain Contracts

```python
@dataclass
class Article:
    id: int
    title: str
    url: str | None
    by: str
    score: int
    time: int
    descendants: int
```

```python
class HackerNewsPort(Protocol):
    async def get_top_stories(self, limit: int = 10) -> list[Article]: ...

class ArticleContentPort(Protocol):
    async def extract_content(self, url: str) -> str | None: ...

class SummarizerPort(Protocol):
    async def summarize(self, article: Article, content: str | None = None) -> str: ...
```

## Runtime Behavior

- The default Ollama model is `gemma2:2b`.
- Ollama must be installed and running locally at `http://localhost:11434`.
- `OllamaClient.ensure_model()` accepts an exact model tag and accepts `<model>:latest` when the requested model has no tag. Do not treat arbitrary tags as interchangeable.
- `HNClient` and `OllamaClient` own async HTTP clients and must be used as async context managers, or explicitly closed with `await close()`.
- `NewspaperExtractor` limits both its async wait and the underlying Newspaper4k request through `request_timeout`.
- Extraction failures are non-fatal: the summarizer receives `None` and falls back to the title. Summary failures produce `[Error generating summary]` for that article.
- Log operational failures with context; do not silently swallow exceptions.

## CLI

```bash
python main.py
python main.py --limit 20
python main.py --model mistral
python main.py --markdown --output-dir digests
```

`--limit` must be a positive integer. Markdown mode defaults to 30 stories when `--limit` is omitted.

## Dependencies And Verification

Runtime dependencies are in `requirements.txt`. Test dependencies are in `requirements-dev.txt`.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall -q domain infrastructure interface usecases main.py
```

The test suite uses `pytest-asyncio` with `asyncio_mode = auto` from `pytest.ini`. Tests should use mocked HTTP or extractor calls; do not require a running Ollama service or live Hacker News requests.

## Engineering Guidelines

- Use strict type hints and keep code compatible with Python 3.10+.
- Prefer small, direct changes over new abstractions.
- Preserve article ordering when introducing concurrency.
- Validate external API payloads before constructing domain entities.
- Avoid blocking the event loop. Run unavoidable blocking work in a thread and ensure its library-level network timeout is configured.
- Do not add caching, Redis, databases, or new export formats unless the task requires them.
