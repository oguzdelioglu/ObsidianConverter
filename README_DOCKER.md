# Docker Usage Instructions

ObsidianConverter can be run in Docker for easier deployment and isolation. This guide explains how to use the Docker image and Docker Compose setup.

## Using Docker

### Build the Docker image

```bash
docker build -t obsidian-converter .
```

### Run with Docker

Basic usage:

```bash
# Create directories for input/output
mkdir -p txt vault

# Run the container
docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output obsidian-converter
```

With API keys for cloud LLM providers:

```bash
docker run -v $(pwd)/txt:/data/input -v $(pwd)/vault:/data/output \
  -e OPENAI_API_KEY=your_openai_key \
  obsidian-converter --provider openai --model gpt-4
```

## Using Docker Compose

The included `docker-compose.yml` file sets up both Ollama and ObsidianConverter services:

```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Configuration with Docker Compose

To use a custom configuration file:

1. Create a configuration file:

```bash
obsidian-converter config --create --file my_config.yaml
```

2. Mount the configuration file:

```yaml
# Modify docker-compose.yml
services:
  converter:
    volumes:
      - ./my_config.yaml:/app/my_config.yaml
    command: --config my_config.yaml --verbose
```

### Environment Variables

The following environment variables can be set in the Docker container:

- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `OBSIDIAN_INPUT_DIR`: Override the input directory (default: `/data/input`)
- `OBSIDIAN_OUTPUT_DIR`: Override the output directory (default: `/data/output`)

## Advanced Docker Usage

### Using with Different Ollama Models

Update the Docker Compose file to pull a specific model before running:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    # ... other settings ...
    command: sh -c "ollama pull llama2 && ollama serve"
```

### Running Tests in Docker

```bash
docker build -t obsidian-converter-test -f Dockerfile.test .
docker run obsidian-converter-test
```