"""
Text processing utilities
"""
import re
import hashlib
from datetime import datetime
from pathlib import Path


def slugify(title):
    """
    Convert a title to a URL-friendly slug
    
    Args:
        title: The title to convert
        
    Returns:
        A slug-friendly string
    """
    return re.sub(r'[^\w\-]', '-', title.strip().lower())[:60]


def create_md_filename(title, category=None):
    """
    Create a markdown filename with date prefix and slug
    
    Args:
        title: The title to use for the filename
        category: Optional category for subfolder organization
        
    Returns:
        A filename string (possibly with subfolder path)
    """
    date_str = datetime.now().strftime("%Y%m%d%H%M")
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    
    if category:
        # Create slugified category path
        category_slug = slugify(category)
        return str(Path(category_slug) / filename)
    
    return filename


def content_hash(content):
    """
    Create a hash of the content for caching
    
    Args:
        content: The text content to hash
        
    Returns:
        MD5 hash of the content
    """
    return hashlib.md5(content.encode()).hexdigest()


def extract_frontmatter_and_content(markdown_text):
    """
    Extract frontmatter and content from markdown
    
    Args:
        markdown_text: The full markdown text with frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, content)
    """
    # Split frontmatter from content
    if markdown_text.startswith("---"):
        parts = markdown_text.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            content = parts[2].strip()
            
            # Parse frontmatter into dict
            frontmatter = {}
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
            
            return frontmatter, content
    
    # No frontmatter found
    return {}, markdown_text