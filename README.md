# HackerDigest

CLI application that fetches top stories from Hacker News and generates bilingual summaries (Spanish/English) using a local Ollama model.

## Features

- Fetch top stories from Hacker News API
- Extract full article content using newspaper4k
- Generate bilingual summaries with local Ollama model
- Beautiful CLI output with Rich
- Export to Markdown format

## Architecture

```
hacker_digest/
├── domain/           # Entities and interfaces (Article, ports)
├── infrastructure/   # HN API client, Ollama client, Content Extractor
├── usecases/         # Business logic (SummarizeArticle)
├── interface/        # CLI output (Rich, Markdown)
└── main.py           # Entry point
```

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running on `localhost:11434`

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hacker-digest.git
cd hacker-digest

# Create virtual environment (recommended)
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

# Custom number of stories
python main.py --limit 5

# Different Ollama model
python main.py --model mistral

# Export to markdown file
python main.py --markdown

# Export with custom limit
python main.py --markdown --limit 20

# Custom output directory
python main.py --markdown --output-dir ./my-digests
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 10 | Number of stories to fetch |
| `--model` | llama3:8b | Ollama model to use |
| `--markdown` | false | Export output to markdown file |
| `--output-dir` | digests | Directory for markdown exports |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | localhost:11434 | Ollama API endpoint |

## Troubleshooting

### Ollama not running

```
Error: Connection error: [Errno 111] Connection refused
```

Make sure Ollama is running:
```bash
ollama serve
```

### Model not found

```
Error: model 'llama3:8b' not found
```

Pull the required model:
```bash
ollama pull llama3:8b
```

### Content extraction fails

Some websites block content extraction. The app will skip to the next story.

## License

MIT
