"""
Core ObsidianConverter functionality
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from obsidian_converter.llm import ContentProcessor
from obsidian_converter.utils.text import create_md_filename

logger = logging.getLogger("obsidian_converter")


class ObsidianConverter:
    """Main converter class for transforming text files to Obsidian notes"""
    
    def __init__(self, input_dir, output_dir, model="mistral", 
                 similarity_threshold=0.3, max_links=5, use_cache=True):
        """
        Initialize the converter
        
        Args:
            input_dir: Input directory containing text files
            output_dir: Output directory for Obsidian vault
            model: Ollama model to use
            similarity_threshold: Threshold for note linking
            max_links: Maximum number of links between notes
            use_cache: Whether to use caching for LLM responses
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.model = model
        self.similarity_threshold = similarity_threshold
        self.max_links = max_links
        self.use_cache = use_cache
        
        # Initialize the content processor
        self.processor = ContentProcessor(model=model, use_cache=use_cache)
        
        # Store existing notes for linking
        self.existing_notes = {}  # filename => (title, content)
    
    def generate_frontmatter(self, title, tags=None, category=None):
        """
        Generate markdown frontmatter for Obsidian
        
        Args:
            title: Note title
            tags: List of tags
            category: Note category
            
        Returns:
            Formatted frontmatter string
        """
        if tags is None:
            tags = []
        
        tags_str = ", ".join([f'"{tag}"' for tag in tags]) if tags else ""
        category_line = f"category: {category}\n" if category else ""
        
        return f"""---
title: "{title}"
date: {datetime.today().date()}
tags: [{tags_str}]
{category_line}---

"""
    
    def write_note(self, title, content, category=None, tags=None):
        """
        Write a note to the Obsidian vault with proper linking
        
        Args:
            title: Note title
            content: Note content
            category: Optional category for organization
            tags: Optional list of tags
            
        Returns:
            The created filename
        """
        md_filename = create_md_filename(title, category)
        filepath = os.path.join(self.output_dir, md_filename)
        
        # Extract markdown content without frontmatter
        content_without_frontmatter = content
        if "---" in content:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content_without_frontmatter = parts[2].strip()
        
        # Find similar notes
        suggestions = self.suggest_links(content_without_frontmatter)
        
        # Add related notes section if there are suggestions
        if suggestions:
            content += "\n\n## Related Notes\n"
            for sug_title, sug_filename in suggestions:
                # Get the basename without extension for the link display
                link_name = Path(sug_filename).stem
                content += f"- [[{sug_title}|{link_name}]]\n"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write the note
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Add to existing notes for future linking
        self.existing_notes[md_filename] = (title, content_without_frontmatter)
        
        return md_filename
    
    def suggest_links(self, content):
        """
        Find related notes based on content similarity
        
        Args:
            content: The note content to find relations for
            
        Returns:
            List of (title, filename) tuples for similar notes
        """
        if not self.existing_notes:
            return []
        
        # Extract just the content parts from existing notes
        existing_titles = []
        existing_contents = []
        existing_filenames = []
        
        for filename, (title, note_content) in self.existing_notes.items():
            existing_titles.append(title)
            existing_contents.append(note_content)
            existing_filenames.append(filename)
        
        # Skip if no existing notes
        if not existing_contents:
            return []
        
        # Calculate similarity
        all_texts = existing_contents + [content]
        vectorizer = TfidfVectorizer().fit_transform(all_texts)
        
        similarity = cosine_similarity(vectorizer[-1], vectorizer[:-1])
        similar_indices = similarity.argsort()[0][-self.max_links:][::-1]
        
        # Return list of (title, filename) tuples for similar notes
        return [(existing_titles[i], existing_filenames[i]) 
                for i in similar_indices 
                if similarity[0][i] > self.similarity_threshold]
    
    def process_file(self, file_path):
        """
        Process a single text file and create markdown notes
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of created files
        """
        logger.info(f"Processing file: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract sections from content
            sections = self.processor.process_content(content, file_path)
            
            created_files = []
            for title, body, category, tags in sections:
                if not title:
                    continue
                
                # Generate frontmatter if not present in body
                if not body.startswith("---"):
                    frontmatter = self.generate_frontmatter(title, tags, category)
                    full_md = f"{frontmatter}{body}"
                else:
                    full_md = body
                
                # Write the note to file
                filename = self.write_note(title, full_md, category, tags)
                created_files.append(filename)
            
            return created_files
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []
    
    def find_text_files(self):
        """
        Find all text files in input directory and subdirectories
        
        Returns:
            List of file paths
        """
        text_files = []
        
        # Handle if input_dir is actually a file
        if os.path.isfile(self.input_dir):
            if self.input_dir.endswith('.txt'):
                return [self.input_dir]
            else:
                logger.warning(f"Input is not a directory or text file: {self.input_dir}")
                return []
        
        # Walk through directory
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith(".txt"):
                    full_path = os.path.join(root, file)
                    text_files.append(full_path)
        
        return text_files
    
    def run(self):
        """
        Run the conversion process for all files
        
        Returns:
            Number of notes created
        """
        logger.info(f"Starting conversion from {self.input_dir} to {self.output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Find all text files
        text_files = self.find_text_files()
        logger.info(f"Found {len(text_files)} text files to process")
        
        # Process files with progress bar
        total_notes = 0
        for file_path in tqdm(text_files, desc="Processing files"):
            created_files = self.process_file(file_path)
            total_notes += len(created_files)
        
        # Save cache when done
        self.processor._save_cache()
        
        logger.info(f"Conversion complete. Created {total_notes} notes from {len(text_files)} files.")
        return total_notes