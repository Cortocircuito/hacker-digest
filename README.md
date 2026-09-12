# HackerDigest

HackerDigest is an asynchronous CLI that retrieves Hacker News stories, extracts linked article content, and generates concise Spanish/English summaries with a local Ollama model.

## Features

- Fetches the current top stories from the Hacker News Firebase API.
- Retrieves stories submitted on a selected UTC day through the Hacker News Algolia Search API.
- Extracts linked article content with Newspaper4k before summarizing.
- Generates bilingual summaries with a local Ollama model.
- Extracts up to three articles concurrently while keeping Ollama summaries sequential for modest hardware.
- Renders results in a Rich-powered terminal UI.
- Exports a daily digest in Markdown.
- Continues when an article cannot be extracted or summarized.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running at `http://localhost:11434`

## Installation

```bash
git clone https://github.com/Cortocircuito/hacker-digest.git
cd hacker-digest

python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

python -m pip install -r requirements.txt
```

The default model is `gemma2:2b`. HackerDigest checks for it and pulls it automatically when absent. You can also pull it manually:

```bash
ollama pull gemma2:2b
```

## Usage

```bash
# Show the current top 10 stories from Hacker News
python main.py

# Fetch a custom number of stories
python main.py --limit 20

# Use a different local model
python main.py --model mistral

# Write a Markdown digest; defaults to 30 stories
python main.py --markdown

# Choose a destination directory and story limit
python main.py --markdown --limit 20 --output-dir my-digests

# Query stories submitted on a UTC date in the Rich terminal UI
python main.py --date 2026-09-10

# Export a historical date to Markdown
python main.py --date 2026-09-10 --markdown

# Show all options
python main.py --help
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--limit` | `10` | Positive number of stories to fetch. Markdown mode uses `30` when omitted. |
| `--model` | `gemma2:2b` | Local Ollama model to use. |
| `--markdown` | `false` | Write the digest to a dated Markdown file. |
| `--output-dir` | `digests` | Directory for Markdown exports. |
| `--date` | Current top stories | Query stories submitted on this UTC date (`YYYY-MM-DD`) through Algolia. Future dates are rejected. |

Without `--date`, HackerDigest uses Hacker News' current `topstories` ranking. With
`--date`, it uses Algolia's index, fetches all stories submitted during that UTC day,
and ranks them by their current score. Date queries do not recreate the Hacker News
front page or score at the end of that day.

Markdown exports include the article URL when available and a link to its Hacker News
discussion. Historical exports use a filename such as
`hacker-digest-2026-09-10-generated-2026-09-12.md`; current exports retain the
`hacker-digest-YYYY-MM-DD.md` name.

## Development

Install development dependencies in the activated virtual environment and run the
checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall -q domain infrastructure interface usecases main.py
```

Run one test module with `python -m pytest tests/test_algolia_client.py`. Tests mock
HTTP and Newspaper4k calls, so they do not require a running Ollama instance or live
Hacker News requests.

## Troubleshooting

### Ollama is unavailable

Start the Ollama server:

```bash
ollama serve
```

### Content extraction fails

Some sites block automated extraction or respond too slowly. HackerDigest logs the failure and generates a title-based summary instead.

### Invalid limit

`--limit` must be a positive integer:

```bash
python main.py --limit 10
```

### Invalid date

`--date` accepts `YYYY-MM-DD` in UTC and rejects future dates:

```bash
python main.py --date 2026-09-10
```

## License

MIT
