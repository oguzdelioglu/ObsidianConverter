# ObsidianConverter

A powerful utility for converting plain text files into well-structured Obsidian notes with smart linking, tagging, and organization.

## Features

- **Intelligent Content Parsing**: Leverages LLMs to identify natural content breaks and organize information
- **Automatic Note Linking**: Creates connections between related notes using semantic similarity
- **Recursive Directory Processing**: Processes all text files in a directory and its subdirectories
- **Obsidian-Optimized Output**: Creates files with proper frontmatter and formatting for Obsidian
- **Smart Tag Generation**: Suggests relevant tags based on note content
- **Content Categorization**: Organizes notes into logical folders based on content themes

## Requirements

- Python 3.8+
- Ollama (local LLM service)
- Required Python packages (see `requirements.txt`)

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

### Prerequisites
- Ensure [Ollama](https://ollama.ai/) is installed and running with the required model (default: "mistral")
- If needed, install the model with: `ollama pull mistral`

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

# Custom directories
obsidian-converter --input /path/to/input --output /path/to/output

# Clean output directory before conversion
obsidian-converter --clean

# Using a specific model
obsidian-converter --model llama2

# Verbose logging
obsidian-converter --verbose

# All options
obsidian-converter --input /path/to/input --output /path/to/output --model llama2 --similarity 0.4 --max-links 10 --clean --verbose
```

## Configuration

The tool can be configured through command-line arguments or by editing the constants at the top of the script:

- `INPUT_DIR`: Directory containing text files to process
- `OUTPUT_DIR`: Directory where Obsidian vault will be created
- `MODEL`: The Ollama model to use for content processing

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