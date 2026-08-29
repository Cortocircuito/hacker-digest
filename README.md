# HackerDigest

HackerDigest is an asynchronous CLI that fetches Hacker News top stories and generates concise Spanish/English summaries with a local Ollama model.

## Features

- Fetches top stories from the Hacker News Firebase API.
- Extracts linked article content with Newspaper4k before summarizing.
- Generates bilingual summaries with a local Ollama model.
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
# Show the top 10 stories
python main.py

# Fetch a custom number of stories
python main.py --limit 20

# Use a different local model
python main.py --model mistral

# Write a Markdown digest; defaults to 30 stories
python main.py --markdown

# Choose a destination directory and story limit
python main.py --markdown --limit 20 --output-dir my-digests
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--limit` | `10` | Positive number of stories to fetch. Markdown mode uses `30` when omitted. |
| `--model` | `gemma2:2b` | Local Ollama model to use. |
| `--markdown` | `false` | Write the digest to a dated Markdown file. |
| `--output-dir` | `digests` | Directory for Markdown exports. |

## Development

Install development dependencies and run the checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall -q domain infrastructure interface usecases main.py
```

Tests use mocked HTTP and extractor calls, so they do not require a running Ollama instance or live Hacker News requests.

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

## License

MIT
