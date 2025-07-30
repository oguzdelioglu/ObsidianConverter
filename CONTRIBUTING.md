# Contributing to ObsidianConverter

Thank you for considering contributing to ObsidianConverter! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. A clear, descriptive title
2. A detailed description of the bug
3. Steps to reproduce the bug
4. Expected behavior
5. Actual behavior
6. Your environment (OS, Python version, etc.)
7. Any relevant logs or error messages

### Suggesting Features

We welcome feature suggestions! Please create an issue with:

1. A clear, descriptive title
2. A detailed description of the proposed feature
3. Any relevant examples or use cases
4. Why this feature would be useful to the project

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request

## Development Setup

1. Clone your fork of the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment:
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
4. Install in development mode: `pip install -e .`
5. Install development dependencies: `pip install -e ".[dev]"`

## Testing

Run tests with pytest:

```bash
pytest
```

## Code Style

We follow PEP 8 style guidelines. Please ensure your code adheres to these standards.

## Documentation

Please update documentation when making changes:

- Update docstrings for any modified functions/classes
- Update README.md if necessary
- Update other documentation files as needed

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).