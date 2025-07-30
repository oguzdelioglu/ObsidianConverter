"""
LLM integration for content processing
"""
import os
import re
import json
import logging
from langchain_ollama import OllamaLLM

from obsidian_converter.utils.text import content_hash

logger = logging.getLogger("obsidian_converter")


class ContentProcessor:
    """
    Process content with LLM to extract sections and enhance metadata
    """
    def __init__(self, model="mistral", use_cache=True, cache_file=".llm_cache.json"):
        """
        Initialize the content processor
        
        Args:
            model: The Ollama model to use
            use_cache: Whether to use caching for LLM responses
            cache_file: Path to the cache file
        """
        self.model = model
        self.llm = OllamaLLM(model=model)
        self.use_cache = use_cache
        self.cache_file = cache_file
        self.cache = {}
        
        if self.use_cache:
            self._load_cache()
    
    def _load_cache(self):
        """Load cached LLM responses from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached LLM responses")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self):
        """Save cached LLM responses to file"""
        if self.use_cache:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.cache, f)
                logger.info(f"Saved {len(self.cache)} LLM responses to cache")
            except Exception as e:
                logger.warning(f"Failed to save cache: {e}")
    
    def _get_prompt(self, content):
        """
        Create the LLM prompt for content analysis
        
        Args:
            content: The text content to analyze
            
        Returns:
            A string prompt for the LLM
        """
        return f"""
# Content Analysis Task

Analyze the following unstructured text content and organize it into separate Obsidian markdown notes.

## Instructions:
1. Identify logical sections that should be separate notes
2. For each section, create proper Obsidian frontmatter with:
   - A descriptive title
   - Relevant tags (without # prefix in the frontmatter)
   - Category for organizing in folders
   - Today's date
3. Format each note using Obsidian markdown syntax
4. Each section should start with proper frontmatter followed by a level 2 heading

## Output Format:
For each section, create:

```
---
title: [Descriptive Title]
tags: [tag1, tag2, tag3]
date: YYYY-MM-DD
category: [Main Category]
---

## [Same Title as Above]

[Content with proper markdown formatting]
```

## Content to Analyze:
{content}
"""
    
    def process_content(self, content, context_path=""):
        """
        Process content with LLM and extract sections
        
        Args:
            content: The text content to process
            context_path: Path to the source file for context/logging
            
        Returns:
            List of tuples (title, body, category, tags)
        """
        content_key = content_hash(content)
        
        # Try to use cached response
        if self.use_cache and content_key in self.cache:
            logger.info(f"Using cached LLM response for content")
            result = self.cache[content_key]
        else:
            # Process with LLM
            logger.info(f"Processing content with LLM: {context_path}")
            prompt = self._get_prompt(content)
            result = self.llm.invoke(prompt)
            
            # Cache the response
            if self.use_cache:
                self.cache[content_key] = result
                # Save cache periodically
                if len(self.cache) % 10 == 0:
                    self._save_cache()
        
        # Extract sections from the result
        return self._extract_sections(result, context_path)
    
    def _extract_sections(self, llm_output, context_path=""):
        """
        Extract note sections from LLM output
        
        Args:
            llm_output: The LLM output text
            context_path: Path to the source file for context/logging
            
        Returns:
            List of tuples (title, body, category, tags)
        """
        sections = []
        
        # Use regex to find each markdown section with frontmatter
        pattern = r'---\s*\n(.*?)\n---\s*\n(.*?)(?=\n---|\Z)'
        matches = re.finditer(pattern, llm_output, re.DOTALL)
        
        for match in matches:
            frontmatter = match.group(1)
            content = match.group(2).strip()
            
            # Extract metadata from frontmatter
            title_match = re.search(r'title:\s*(.*)', frontmatter)
            tags_match = re.search(r'tags:\s*\[(.*?)\]', frontmatter)
            category_match = re.search(r'category:\s*(.*)', frontmatter)
            
            title = title_match.group(1).strip() if title_match else "Untitled Note"
            tags = [tag.strip() for tag in tags_match.group(1).split(',')] if tags_match else []
            category = category_match.group(1).strip() if category_match else None
            
            sections.append((title, content, category, tags))
        
        # Fallback if no sections were extracted
        if not sections:
            logger.warning(f"Failed to extract sections from {context_path}, using fallback method")
            # Use simple split by H2 headings as fallback
            h2_sections = re.split(r'## (.*?)\n', llm_output)
            if len(h2_sections) > 1:
                for i in range(1, len(h2_sections), 2):
                    if i+1 < len(h2_sections):
                        title = h2_sections[i].strip()
                        body = h2_sections[i+1].strip()
                        sections.append((title, f"## {title}\n\n{body}", None, []))
        
        return sections