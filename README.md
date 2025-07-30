<p align="center">
  <img src="logo.png" alt="ObsidianConverter Logo" width="200"/>
</p>

<h1 align="center">ObsidianConverter</h1>

<p align="center">
  A powerful utility for converting plain text files into well-structured Obsidian notes with smart linking, tagging, and organization.
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_TR.md">Türkçe</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_ZH.md">中文</a>
</p>

## Features

- **Intelligent Content Parsing**: Leverages LLMs to identify natural content breaks and organize information
- **Automatic Note Linking**: Creates connections between related notes using semantic similarity
- **Recursive Directory Processing**: Processes all text files in a directory and its subdirectories
- **Obsidian-Optimized Output**: Creates files with proper frontmatter and formatting for Obsidian
- **Smart Tag Generation**: Suggests relevant tags based on note content
- **Content Categorization**: Organizes notes into logical folders based on content themes
- **Enhanced Obsidian Integration**: Support for callouts, dataview queries, and table of contents
- **Parallel Processing**: Process multiple files simultaneously for faster conversion
- **Configuration System**: Customize behavior through YAML configuration files
- **Statistics Tracking**: Detailed statistics on conversion process and note creation
- **Multiple LLM Support**: Works with Ollama, OpenAI, or Anthropic models
- **Interactive Mode**: Review, edit, and refine notes before saving
- **Docker Support**: Run with Docker and Docker Compose for easy setup

## Requirements

- Python 3.8+
- One of the following LLM providers:
  - [Ollama](https://ollama.ai/) (default, local LLM service)
  - OpenAI API key (for GPT models)
  - Anthropic API key (for Claude models)
- Required Python packages (see `requirements.txt`)
- Docker (optional, for containerized usage)

## Installation

### Method 1: Development Setup
1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment:
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
4. Install in development mode: `pip install -e .`

### Method 2: Regular Installation
1. Clone this repository
2. Run: `pip install .`

### Method 3: Docker Installation
1. Build the Docker image: `docker build -t obsidian-converter .`
2. Run with Docker: `docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter`
3. Or use Docker Compose: `docker-compose up`

See [README_DOCKER.md](README_DOCKER.md) for detailed Docker instructions.

### Prerequisites
- For Ollama: Ensure it's installed and running with the required model (default: "mistral")
  - Install the model with: `ollama pull mistral`
- For OpenAI: Set your API key via `--openai-key` argument or `OPENAI_API_KEY` environment variable
- For Anthropic: Set your API key via `--anthropic-key` argument or `ANTHROPIC_API_KEY` environment variable

## Usage

```bash
# Show help message
obsidian-converter --help

# Basic usage (processes all .txt files in txt/ directory)
obsidian-converter

# Process specific files
obsidian-converter files example.txt subdir/notes.txt

# Clean output directory
obsidian-converter clean

# List all generated notes
obsidian-converter list

# List notes from a specific category
obsidian-converter list --category technical

# Create a configuration file
obsidian-converter config --create --file my_config.yaml

# View current configuration
obsidian-converter config --file my_config.yaml

# Use a configuration file
obsidian-converter --config my_config.yaml

# Custom directories
obsidian-converter --input /path/to/input --output /path/to/output

# Enable parallel processing
obsidian-converter --parallel --workers 4

# Clean output directory before conversion
obsidian-converter --clean

# Using a specific model
obsidian-converter --model llama2

# Verbose logging
obsidian-converter --verbose

# Interactive review mode
obsidian-converter --interactive

# Specify editor for interactive mode
obsidian-converter --interactive --editor vim

# Use different LLM providers
obsidian-converter --provider ollama --model llama2
obsidian-converter --provider openai --model gpt-3.5-turbo --openai-key YOUR_API_KEY
obsidian-converter --provider anthropic --model claude-3-sonnet-20240229 --anthropic-key YOUR_API_KEY

# All options combined
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 \
  --similarity 0.4 --max-links 10 --clean --verbose --parallel --workers 8 --interactive
```

## Configuration

The tool can be configured through command-line arguments or with a YAML configuration file:

```bash
# Create a default configuration file
obsidian-converter config --create --file my_config.yaml
```

Example configuration file:

```yaml
# Core settings
input_dir: txt
output_dir: vault
model: mistral

# LLM provider settings
provider: ollama      # ollama, openai, or anthropic
openai_api_key: null  # Your OpenAI API key (or use env variable)
anthropic_api_key: null  # Your Anthropic API key (or use env variable)
llm_temperature: 0.7  # Temperature for LLM responses

# Processing settings
similarity_threshold: 0.3
max_links: 5
use_cache: true
cache_file: .llm_cache.json

# Performance settings
parallel_processing: true
max_workers: 4
chunk_size: 1000000  # 1MB chunks for large files

# Obsidian specific settings
obsidian_features:
  callouts: true
  dataview: true
  toc: true
  graph_metadata: true

# File patterns to include/exclude
include_patterns:
  - '*.txt'
  - '*.md'
exclude_patterns:
  - '*.tmp'
  - '~*'
```

You can use this configuration file with:

```bash
obsidian-converter --config my_config.yaml
```

## Advanced Features

### Statistics and Reporting

The tool generates statistics about the conversion process, including:

- Number of processed files and created notes
- Categories and tags distribution
- Word and character counts
- LLM performance metrics
- Processing time

A JSON report is automatically saved in the `.stats` directory within your output folder.

### Parallel Processing

For large document sets, enable parallel processing to speed up conversion:

```bash
obsidian-converter --parallel --workers 4
```

### Memory Optimization

Large files are automatically processed in chunks to reduce memory usage. You can customize the chunk size in the configuration file.

### Custom File Patterns

By default, the tool processes `.txt` files, but you can customize the patterns in the configuration file:

```yaml
include_patterns:
  - '*.txt'  # Text files
  - '*.md'   # Markdown files
  - 'notes_*.log'  # Log files with specific naming
```

### Interactive Mode

Review and edit each note before saving with interactive mode:

```bash
obsidian-converter --interactive
```

In interactive mode, you can:
- Edit notes in your preferred text editor
- Discard notes you don't want to keep
- Change note categories
- View full content before deciding
- Review metadata and suggested links

To specify a custom editor (instead of using your system's default):

```bash
obsidian-converter --interactive --editor vim
```

## Example Output

For a text file containing mixed notes, ObsidianConverter will produce multiple well-structured markdown files:

```markdown
---
title: Project Planning
date: 2023-06-15
tags: [planning, project-management, workflow]
category: Work
---

## Project Planning

Here's the content about project planning that was extracted...

## Related Notes
- [[Meeting Notes - Q2 Review]]
- [[Task Prioritization Methods]]
```

## How It Works

1. Reads all `.txt` files from the input directory and its subdirectories
2. Uses LLM to analyze and break down content into logical sections
3. Creates appropriate metadata (frontmatter) for each note
4. Establishes connections between related notes
5. Organizes notes into a clean folder structure
6. Generates the complete Obsidian vault

## License

MIT