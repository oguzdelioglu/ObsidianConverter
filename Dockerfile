FROM python:3.10-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install optional dependencies for all LLM providers
RUN pip install --no-cache-dir openai anthropic

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create directories for input/output
RUN mkdir -p /data/input /data/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OBSIDIAN_INPUT_DIR=/data/input
ENV OBSIDIAN_OUTPUT_DIR=/data/output

# Default command
ENTRYPOINT ["obsidian-converter"]
CMD ["--help"]