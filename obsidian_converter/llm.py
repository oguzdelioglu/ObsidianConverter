"""
LLM integration for content processing
"""
import os
import re
import json
import logging

from obsidian_converter.llm_providers.provider_factory import LLMProviderFactory
from obsidian_converter.llm_providers.base import BaseLLMProvider

from obsidian_converter.utils.text import content_hash

logger = logging.getLogger("obsidian_converter")


class ContentProcessor:
    """
    Process content with LLM to extract sections and enhance metadata
    """
    def __init__(self, model="mistral", provider="ollama", use_cache=True, cache_file=".llm_cache.json", **kwargs):
        """
        Initialize the content processor
        
        Args:
            model: The LLM model to use
            provider: The LLM provider to use (ollama, openai, anthropic)
            use_cache: Whether to use caching for LLM responses
            cache_file: Path to the cache file
            **kwargs: Additional provider-specific arguments
        """
        self.model = model
        self.provider_name = provider
        self.use_cache = use_cache
        self.cache_file = cache_file
        self.cache = {}
        
        # Initialize the LLM provider
        try:
            self.llm = LLMProviderFactory.create_provider(provider, model, **kwargs)
            logger.info(f"Initialized {provider} LLM provider with model {model}")
        except Exception as e:
            logger.error(f"Failed to initialize {provider} LLM provider: {e}")
            logger.warning(f"Falling back to Ollama provider with model mistral")
            self.provider_name = "ollama"
            self.model = "mistral"
            self.llm = LLMProviderFactory.create_provider("ollama", "mistral")
        
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
    
    def _get_prompt(self, content, context_path=""):
        """
        Create the LLM prompt for content analysis
        
        Args:
            content: The text content to analyze
            context_path: Optional file path for context
            
        Returns:
            A string prompt for the LLM
        """
        # Extract file name for additional context if available
        file_context = ""
        if context_path:
            try:
                file_name = os.path.basename(context_path)
                file_name_without_ext = os.path.splitext(file_name)[0]
                file_context = f"\nThe content is from a file named: '{file_name_without_ext}', which may provide context about the topic."
            except:
                pass
            
        return f"""
# Obsidian Note Creation Task

You are an expert knowledge organizer who specializes in creating well-structured Obsidian notes. Your task is to analyze text content and convert it into logically organized Obsidian markdown notes.

## Context{file_context}

## Instructions

### Content Analysis:
1. Carefully analyze the content to identify distinct topics or sections
2. Each logical topic should become a separate note with its own frontmatter
3. Identify natural boundaries between concepts or subjects
4. Preserve all important information from the original content
5. Maintain code blocks, lists, and other formatting

### Note Structure:
1. Create meaningful titles that accurately reflect the content
2. Organize content with appropriate heading levels (H2, H3, etc.)
3. Use bullet points or numbered lists for series of related items
4. Preserve code blocks with correct language identifiers
5. Split very long notes into multiple related notes if appropriate

### Metadata Generation:
1. Generate 3-7 relevant tags that describe key concepts (no # prefix in frontmatter)
2. Assign each note to a logical category folder
3. Choose specific, descriptive tags (avoid overly generic tags)
4. Use multi-word tags for complex concepts (e.g., "project-management" not "project")
5. Include today's date in YYYY-MM-DD format

## Obsidian Formatting Features to Use:
- Internal links: [[note-name]] to reference related concepts
- Bold: **text** for emphasis of important points
- Italics: *text* for definitions or specialized terms
- Callouts: > [!note] for important information
- Code blocks: ```language\\ncode\\n``` for any code or commands
- Tables: Use markdown tables for structured information

## Output Format:
For each section, create:

```
---
title: "Clear Descriptive Title"
tags: ["primary-topic", "specific-concept", "technical-area"]
date: YYYY-MM-DD
category: CategoryName
---

## Clear Descriptive Title

[Well-formatted content with appropriate markdown structure]
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
            prompt = self._get_prompt(content, context_path)
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
            title_match = re.search(r'title:\s*"?(.*?)"?$', frontmatter, re.MULTILINE)
            tags_match = re.search(r'tags:\s*\[(.*?)\]', frontmatter, re.DOTALL)
            category_match = re.search(r'category:\s*(.*?)$', frontmatter, re.MULTILINE)
            
            title = title_match.group(1).strip().strip('"\'') if title_match else "Untitled Note"
            
            # Enhanced tag extraction
            tags = []
            if tags_match:
                # Handle different tag formats: ["tag1", "tag2"] or [tag1, tag2] or ["tag1","tag2"]
                raw_tags = tags_match.group(1).strip()
                # Remove quotes from tags
                tag_pattern = r'"([^"]+)"|\'([^\']+)\'|([^,\s]+)'
                tag_matches = re.findall(tag_pattern, raw_tags)
                for tag_match in tag_matches:
                    # Each match is a tuple with the captured groups, only one will have a value
                    tag = next((t for t in tag_match if t), "").strip()
                    if tag:
                        tags.append(tag)
            
            category = category_match.group(1).strip().strip('"\'') if category_match else None
            
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
                        
                        # Generate category based on content
                        category = self._generate_category_from_title(title)
                        # Generate basic tags
                        tags = self._generate_tags_from_content(title, body)
                        
                        sections.append((title, f"## {title}\n\n{body}", category, tags))
        
        # Post-process: ensure all sections have a category
        for i, (title, content, category, tags) in enumerate(sections):
            if not category:
                sections[i] = (title, content, self._generate_category_from_title(title), tags)
                
        return sections
    
    def _generate_category_from_title(self, title):
        """
        Generate a category based on the title
        
        Args:
            title: The note title
            
        Returns:
            A suggested category name
        """
        title_lower = title.lower()
        
        # Common categories based on keywords
        category_mapping = {
            'project': 'Projects',
            'task': 'Tasks',
            'meeting': 'Meetings',
            'note': 'Notes',
            'idea': 'Ideas',
            'research': 'Research',
            'code': 'CodeSnippets',
            'snippet': 'CodeSnippets',
            'document': 'Documentation',
            'guide': 'Guides',
            'tutorial': 'Tutorials',
            'reference': 'References',
            'book': 'Books',
            'article': 'Articles',
            'paper': 'Papers',
            'study': 'Studies',
            'concept': 'Concepts',
            'theory': 'Theories',
            'finance': 'Finance',
            'personal': 'Personal',
            'work': 'Work',
            'journal': 'Journal',
            'review': 'Reviews',
            'technical': 'Technical',
            'design': 'Design'
        }
        
        # Check if title contains any key terms
        for keyword, category in category_mapping.items():
            if keyword in title_lower:
                return category
                
        # Default categories based on first word or general content
        if title_lower.startswith('how to'):
            return 'Guides'
        elif title_lower.startswith('why'):
            return 'Explanations'
        elif title_lower.startswith('what is'):
            return 'Definitions'
        
        # Default category
        return 'General'
    
    def _generate_tags_from_content(self, title, content):
        """
        Generate tags based on the content
        
        Args:
            title: The note title
            content: The note content
            
        Returns:
            A list of generated tags
        """
        # Extract meaningful words from title
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', title.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'about'}
        tags = [word for word in words if word not in stop_words]
        
        # Add tags from common patterns in content
        if re.search(r'```[a-zA-Z]*\n', content):
            tags.append('code-snippet')
            
        if re.search(r'https?://[^\s]+', content):
            tags.append('links')
            
        if re.search(r'\d{4}-\d{2}-\d{2}', content):
            tags.append('dated')
            
        if len(re.findall(r'^\s*-\s+', content, re.MULTILINE)) > 3:
            tags.append('list')
            
        # Limit to 5 tags
        return list(set(tags))[:5]