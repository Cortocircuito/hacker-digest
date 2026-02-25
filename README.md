# HackerDigest

CLI application that fetches top stories from Hacker News and generates bilingual summaries (Spanish/English) using a local Ollama model.

## Features

- Fetch top stories from Hacker News API
- Extract full article content using newspaper4k
- Generate bilingual summaries with local Ollama model
- Beautiful CLI output with Rich

## Architecture

```
hacker_digest/
├── domain/           # Entities and interfaces
├── infrastructure/   # HN API, Ollama, Content Extractor
├── usecases/         # Business logic
├── interface/        # CLI
└── main.py           # Entry point
```

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running

## Installation

```bash
# Clone the repository
cd hacker_digest

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Pull Ollama model (if not already done)
ollama pull llama3:8b
```

## Usage

```bash
# Run with defaults (10 stories, llama3:8b)
python main.py

# Custom limit
python main.py --limit 5

# Different model
python main.py --model mistral
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 10 | Number of stories to fetch |
| `--model` | llama3:8b | Ollama model to use |

## Examples

```bash
# Fetch 3 stories with mistral
python main.py --limit 3 --model mistral
```

## License

MIT
