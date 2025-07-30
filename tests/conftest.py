"""
Pytest configuration for ObsidianConverter tests
"""
import os
import pytest
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory that's removed after the test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing"""
    file_path = os.path.join(temp_dir, "sample.txt")
    with open(file_path, "w") as f:
        f.write("""# Sample Document

## First Section
This is the first section of the document.
- Item 1
- Item 2

## Second Section
This is the second section with some additional content.
""")
    return file_path


@pytest.fixture
def mock_llm_response():
    """Return a mock LLM response for testing"""
    return """---
title: "First Section"
tags: ["sample", "document", "section"]
date: 2023-01-01
category: Notes
---

## First Section

This is the first section of the document.
- Item 1
- Item 2

---
title: "Second Section"
tags: ["sample", "additional", "content"]
date: 2023-01-01
category: Notes
---

## Second Section

This is the second section with some additional content.
"""