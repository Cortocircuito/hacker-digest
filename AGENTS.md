# HackerDigest

## Setup and Verification

- Python 3.10+; runtime dependencies are in `requirements.txt`, test dependencies in `requirements-dev.txt`.
- Create and activate `venv` before commands, then run `python -m pip install -r requirements-dev.txt`.
- Run all tests with `python -m pytest`; run one module with `python -m pytest tests/test_algolia_client.py`.
- Run `python -m compileall -q domain infrastructure interface usecases main.py` after Python changes. There is no configured formatter, linter, type checker, CI workflow, or task runner.
- Tests must mock HTTP and Newspaper4k calls. They require neither live Hacker News nor a running Ollama service.

## Boundaries

- `main.py` is the composition root and CLI argument parser.
- `domain/` defines `Article` and Protocol ports. `usecases/` may import only `domain/`; adapters belong in `infrastructure/`; Rich and Markdown rendering belongs in `interface/cli.py`.
- Providers implement `HackerNewsPort.get_top_stories(limit)`: use `HNClient` for the current `topstories` ranking and `AlgoliaClient` only for `--date` queries. Algolia dates are UTC and results are ranked by their current score, not a reconstructed historical HN front page.

## Runtime Contracts

- `HNClient`, `AlgoliaClient`, and `OllamaClient` own `httpx.AsyncClient` instances. Use them as async context managers or call `await close()`.
- The default local model is `gemma2:2b` at `http://localhost:11434`. `ensure_model()` matches exact tags; an untagged request may match only `<model>:latest`.
- `NewspaperExtractor` is synchronous internally: keep blocking work in `asyncio.to_thread`, enforce both the coroutine and Newspaper4k request timeout, and send at most `MAX_CHARS` (3,000) characters to Ollama.
- `SummarizeArticle` preserves article order, caps extraction concurrency at three, and deliberately summarizes sequentially. Extraction failures pass `None`; summary failures return `[Error generating summary]`. Keep operational failures logged with article context.

## CLI Output

- `--limit` must be positive. Defaults are 10 for Rich and 30 for `--markdown`; an explicit limit always wins.
- `--date YYYY-MM-DD` accepts past or current UTC dates and selects Algolia. Reject future dates before connecting to services.
- Markdown writes UTF-8 files under `--output-dir` (default `digests/`), including full-article and Hacker News discussion links. Current exports use `hacker-digest-YYYY-MM-DD.md`; historical exports also include the generation date.
