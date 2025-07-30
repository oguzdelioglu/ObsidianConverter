"""
Core ObsidianConverter functionality
"""
import os
import re
import time
import logging
import fnmatch
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from obsidian_converter.llm import ContentProcessor
from obsidian_converter.config import ObsidianConverterConfig
from obsidian_converter.utils.text import create_md_filename, content_hash
from obsidian_converter.utils.performance import chunked_read, execute_in_parallel, split_text_by_size
from obsidian_converter.utils.stats import ConversionStats
from obsidian_converter.interactive import InteractiveReviewer

logger = logging.getLogger("obsidian_converter")


class ObsidianConverter:
    """Main converter class for transforming text files to Obsidian notes"""
    
    def __init__(self, input_dir=None, output_dir=None, model=None, 
                 similarity_threshold=None, max_links=None, use_cache=None,
                 interactive=False, config_path=None, config=None):
        """
        Initialize the converter
        
        Args:
            input_dir: Input directory containing text files
            output_dir: Output directory for Obsidian vault
            model: Ollama model to use
            similarity_threshold: Threshold for note linking
            max_links: Maximum number of links between notes
            use_cache: Whether to use caching for LLM responses
            interactive: Whether to enable interactive review mode
            config_path: Path to config file (overrides other arguments if provided)
            config: Pre-loaded config object
        """
        # Load config
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.config = ObsidianConverterConfig.from_file(config_path)
        else:
            self.config = ObsidianConverterConfig()
        
        # Override config with provided arguments
        if input_dir is not None:
            self.config.input_dir = input_dir
        if output_dir is not None:
            self.config.output_dir = output_dir
        if model is not None:
            self.config.model = model
        if similarity_threshold is not None:
            self.config.similarity_threshold = similarity_threshold
        if max_links is not None:
            self.config.max_links = max_links
        if use_cache is not None:
            self.config.use_cache = use_cache
            
        # Initialize properties from config for backward compatibility
        self.input_dir = self.config.input_dir
        self.output_dir = self.config.output_dir
        self.model = self.config.model
        self.similarity_threshold = self.config.similarity_threshold
        self.max_links = self.config.max_links
        self.use_cache = self.config.use_cache
        
        # Interactive mode
        self.interactive = interactive
        if interactive:
            self.reviewer = InteractiveReviewer()
        
        # Initialize the content processor with provider settings
        llm_kwargs = {
            "temperature": self.config.llm_temperature
        }
        
        # Add API keys if available
        if self.config.provider == "openai" and self.config.openai_api_key:
            llm_kwargs["api_key"] = self.config.openai_api_key
        elif self.config.provider == "anthropic" and self.config.anthropic_api_key:
            llm_kwargs["api_key"] = self.config.anthropic_api_key
            
        self.processor = ContentProcessor(
            model=self.model,
            provider=self.config.provider,
            use_cache=self.use_cache,
            cache_file=self.config.cache_file,
            **llm_kwargs
        )
        
        # Store existing notes for linking
        self.existing_notes = {}  # filename => (title, content)
        
        # Initialize statistics
        self.stats = ConversionStats()
    
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
        
        # Format tags with proper quoting
        tags_str = ", ".join([f'"{tag}"' for tag in tags]) if tags else ""
        
        # Add category and other Obsidian metadata
        category_line = f"category: {category}\n" if category else ""
        created_date = datetime.today().date()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add Obsidian-specific metadata for better compatibility
        return f"""---
title: "{title}"
date: {created_date}
tags: [{tags_str}]
{category_line}created: {current_time}
modified: {current_time}
alias: [{title}]
---

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
        # Extract markdown content without frontmatter
        content_without_frontmatter = content
        if "---" in content:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content_without_frontmatter = parts[2].strip()
        
        # Check if content is long enough to add a table of contents
        # Add TOC if there are multiple headers in the content
        if len(content_without_frontmatter.split()) > 200:
            # Count headers in content
            header_matches = re.findall(r'^#+\s+.+$', content_without_frontmatter, re.MULTILINE)
            if len(header_matches) > 2:
                # Split the content at the first occurrence of ##
                parts = re.split(r'(^##\s+.*$)', content_without_frontmatter, 1, re.MULTILINE)
                if len(parts) >= 3:
                    # Add TOC between frontmatter and first heading
                    toc = "\n## Table of Contents\n\n"
                    toc += "```toc\nstyle: bullet | number | inline (default: bullet)\nmin_depth: 1\nmax_depth: 3\ntitle: In This Note\nallow_inconsistent_headings: false\n```\n\n"
                    content = content.replace(content_without_frontmatter, parts[0] + toc + parts[1] + parts[2])
        
        # Find similar notes
        suggestions = self.suggest_links(content_without_frontmatter)
        
        # Add related notes section if there are suggestions
        if suggestions:
            content += "\n\n## Related Notes\n"
            # Use a callout block for related notes
            content += "> [!info] Related content you may find interesting\n>\n"
            for sug_title, sug_filename in suggestions:
                # Get the basename without extension for the link display
                link_name = Path(sug_filename).stem
                content += f"> - [[{sug_title}|{link_name}]]\n"
            
            # Add dataview query for finding similar notes by tags
            if tags and isinstance(tags, list) and len(tags) > 0:
                content += "\n\n## Other Notes with Similar Tags\n"
                content += "```dataview\n"
                content += "LIST\n"
                content += f"FROM #{' OR #'.join(tags[:3])}\n"
                content += f"WHERE file.name != this.file.name\n"
                content += "SORT file.mtime DESC\n"
                content += "LIMIT 5\n"
                content += "```\n"
        
        # Interactive review if enabled
        save_note = True
        if self.interactive:
            try:
                content, save_note, category = self.reviewer.review_note(title, content, category)
                if not save_note:
                    logger.info(f"Note '{title}' discarded by user")
                    return None
                
                # Re-extract content without frontmatter after possible edits
                if "---" in content:
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        content_without_frontmatter = parts[2].strip()
                
                # Category may have changed during review
                if category is None:
                    md_filename = create_md_filename(title)
                else:
                    md_filename = create_md_filename(title, category)
            except KeyboardInterrupt:
                logger.info("Interactive review interrupted by user")
                return None
            except Exception as e:
                logger.warning(f"Error during interactive review: {e}, continuing with original content")
                md_filename = create_md_filename(title, category)
        else:
            # Normal mode, no interaction
            md_filename = create_md_filename(title, category)
        
        filepath = os.path.join(self.output_dir, md_filename)
        
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
        self.stats.record_processed_file()
        
        try:
            # For large files, read in chunks to avoid memory issues
            try:
                file_size = os.path.getsize(file_path)
                
                if file_size > self.config.chunk_size:
                    logger.info(f"Large file detected ({file_size/1024/1024:.1f} MB), processing in chunks")
                    content = ""
                    for chunk in chunked_read(file_path, chunk_size=self.config.chunk_size):
                        content += chunk
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
            except UnicodeDecodeError:
                # Try different encoding if UTF-8 fails
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            
            # For very large content, split it into manageable pieces
            if len(content) > self.config.chunk_size:
                text_chunks = split_text_by_size(content, max_size=self.config.chunk_size)
                logger.info(f"Split content into {len(text_chunks)} chunks for processing")
                
                # Process each chunk
                all_sections = []
                for i, chunk in enumerate(text_chunks):
                    logger.debug(f"Processing content chunk {i+1}/{len(text_chunks)}")
                    chunk_sections = self.processor.process_content(chunk, f"{file_path} (chunk {i+1})")
                    all_sections.extend(chunk_sections)
                
                sections = all_sections
            else:
                # Normal processing
                llm_start = time.time()
                sections = self.processor.process_content(content, file_path)
                llm_time = time.time() - llm_start
                
                # Record LLM call statistics
                cache_hit = hasattr(self.processor, 'cache') and content_hash(content) in self.processor.cache
                self.stats.record_llm_call(llm_time, cache_hit=cache_hit)
            
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
                
                # Record note statistics
                word_count = len(body.split())
                char_count = len(body)
                self.stats.record_created_note(category=category, tags=tags, 
                                             word_count=word_count, char_count=char_count)
            
            return created_files
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.stats.record_failed_file()
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
            if any(fnmatch.fnmatch(self.input_dir.lower(), pattern.lower()) for pattern in self.config.include_patterns):
                return [self.input_dir]
            else:
                logger.warning(f"Input is not a directory or supported file type: {self.input_dir}")
                return []
                
        if not os.path.exists(self.input_dir):
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return []
        
        # Walk through directory
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file should be included based on patterns
                include_file = False
                for pattern in self.config.include_patterns:
                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                        include_file = True
                        break
                
                # Check if file should be excluded
                for pattern in self.config.exclude_patterns:
                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                        include_file = False
                        break
                
                if include_file:
                    text_files.append(file_path)
        
        logger.info(f"Found {len(text_files)} files matching patterns: {', '.join(self.config.include_patterns)}")
        
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
        
        # Process files
        if self.config.parallel_processing and len(text_files) > 1:
            # Parallel processing
            logger.info(f"Using parallel processing with {self.config.max_workers} workers")
            
            # Define a worker function that processes a single file
            def process_file_worker(file_path):
                try:
                    created = self.process_file(file_path)
                    return len(created), file_path
                except Exception as e:
                    logger.error(f"Error in worker processing {file_path}: {e}")
                    return 0, file_path
            
            # Execute processing in parallel
            results = execute_in_parallel(
                process_file_worker, 
                text_files, 
                max_workers=self.config.max_workers,
                desc="Processing files"
            )
            
            # Collect results
            total_notes = sum(count for count, _ in results)
        else:
            # Sequential processing with progress bar
            total_notes = 0
            for file_path in tqdm(text_files, desc="Processing files"):
                created_files = self.process_file(file_path)
                total_notes += len(created_files)
        
        # Save cache when done
        self.processor._save_cache()
        
        # Finalize statistics
        self.stats.finish()
        
        # Generate statistics report
        stats_file = self.stats.save_report(self.output_dir)
        
        # Print summary
        self.stats.print_summary()
        
        logger.info(f"Conversion complete. Created {total_notes} notes from {len(text_files)} files.")
        return total_notes