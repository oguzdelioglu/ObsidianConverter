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
            "temperature": self.config.llm_temperature,
            "timeout": self.config.llm_timeout
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
        
        # Make sure we use one of the main categories
        main_categories = ["Technology", "Finance", "Personal", "Projects", "Knowledge", "Reference"]
        
        if not category or category not in main_categories:
            # Try more sophisticated matching
            if category:
                # Try exact case insensitive matching first
                category_lower = category.lower()
                found_match = False
                for main_cat in main_categories:
                    if main_cat.lower() == category_lower:
                        category = main_cat
                        found_match = True
                        break
                        
                # If no exact match, try partial matching
                if not found_match:
                    for main_cat in main_categories:
                        if main_cat.lower() in category_lower or category_lower in main_cat.lower():
                            category = main_cat
                            found_match = True
                            break
                    
                    # If still no match, use semantic mapping
                    if not found_match:
                        # Map common categories to main categories
                        tech_categories = ["web", "programming", "code", "development", "software", "app", "computer", "server", "network", "database", "api", "cyber", "devops", "algorithm", "digital"]
                        finance_categories = ["money", "financial", "economy", "business", "invest", "crypto", "blockchain", "banking", "budget", "tax", "trading", "accounting", "economic", "market"]
                        personal_categories = ["health", "life", "diary", "journal", "self", "habit", "routine", "emotion", "feeling", "relationship", "family", "fitness", "wellness", "mental"]
                        project_categories = ["project", "task", "work", "plan", "management", "team", "milestone", "startup", "product", "implementation", "delivery", "meeting", "workflow", "operation"]
                        knowledge_categories = ["learn", "study", "concept", "theory", "education", "training", "science", "research", "academic", "topic", "subject", "field", "discipline", "method"]
                        reference_categories = ["reference", "guide", "manual", "documentation", "instruction", "template", "list", "directory", "collection", "resource", "document", "account", "credential"]
                        
                        # Check for keyword matches
                        for word in re.findall(r'\w+', category_lower):
                            if word in tech_categories:
                                category = "Technology"
                                found_match = True
                                break
                            elif word in finance_categories:
                                category = "Finance"
                                found_match = True
                                break
                            elif word in personal_categories:
                                category = "Personal"
                                found_match = True
                                break
                            elif word in project_categories:
                                category = "Projects"
                                found_match = True
                                break
                            elif word in knowledge_categories:
                                category = "Knowledge"
                                found_match = True
                                break
                            elif word in reference_categories:
                                category = "Reference"
                                found_match = True
                                break
                                
                        # If still no match, check for common subcategories
                        if not found_match:
                            # Technology subcategories
                            if any(x in category_lower for x in ["android", "ios", "mobile", "web", "seo", "wordpress", "coding", "program", "dev", "github", "git", "security", "data", "ui", "ux"]):
                                category = "Technology"
                            # Finance subcategories
                            elif any(x in category_lower for x in ["token", "coin", "nft", "defi", "exchange", "wallet", "transaction", "payment", "income", "revenue"]):
                                category = "Finance"
                            # Personal subcategories
                            elif any(x in category_lower for x in ["productivity", "meditation", "mindful", "exercise", "diet", "sleep", "stress", "therapy"]):
                                category = "Personal"
                            # Projects subcategories
                            elif any(x in category_lower for x in ["business", "marketing", "sales", "client", "customer", "growth", "strategy"]):
                                category = "Projects"
                            # Knowledge subcategories
                            elif any(x in category_lower for x in ["tutorial", "guide", "course", "lesson", "definition", "example", "literature", "history"]):
                                category = "Knowledge"
                            # Reference subcategories
                            elif any(x in category_lower for x in ["specification", "standard", "protocol", "formula", "checklist", "password", "contact"]):
                                category = "Reference"
                            else:
                                # Default to Knowledge if no match is found
                                logger.warning(f"Category '{category}' not in main categories, using 'Knowledge' instead")
                                category = "Knowledge"
                        
            else:
                # If category is None or empty, use Knowledge as default
                logger.warning(f"No category specified, using 'Knowledge' instead")
                category = "Knowledge"
        
        # Check if content is long enough to add a table of contents
        # Add TOC if there are multiple headers in the content
        if len(content_without_frontmatter.split()) > 150:  # Lower threshold to include more TOCs
            # Count headers in content
            header_matches = re.findall(r'^#+\s+.+$', content_without_frontmatter, re.MULTILINE)
            if len(header_matches) > 1:  # Lower threshold to include more TOCs
                # Split the content at the first occurrence of ##
                parts = re.split(r'(^##\s+.*$)', content_without_frontmatter, 1, re.MULTILINE)
                if len(parts) >= 3:
                    # Add TOC between frontmatter and first heading
                    toc = "\n## Table of Contents\n\n"
                    toc += "```toc\nstyle: bullet\nmin_depth: 2\nmax_depth: 3\ntitle: In This Note\n```\n\n"
                    content = content.replace(content_without_frontmatter, parts[0] + toc + parts[1] + parts[2])
                    
        # Find similar notes
        suggestions = self.suggest_links(content_without_frontmatter)
        
        # Enhanced related notes section
        if len(suggestions) > 0 or (tags and len(tags) > 0):
            content += "\n\n## Connections\n"
            
            # Add backlinks section
            content += "\n### Related Notes\n"
            
            if suggestions:
                # Use a callout block for related notes
                content += "> [!info] Related content\n>\n"
                for sug_title, sug_filename in suggestions[:8]:  # Limit to top 8 suggestions
                    # Get the basename without extension for the link display
                    link_name = Path(sug_filename).stem
                    content += f"> - [[{link_name}]] - {sug_title}\n"
            else:
                content += "_No related notes found yet._\n"
                
            # Add tags section with dataview
            content += "\n### Notes with Similar Tags\n"
            
            if tags and isinstance(tags, list) and len(tags) > 0:
                # Properly format tags for dataview query
                formatted_tags = ' OR '.join([f'"{tag}"' for tag in tags[:3]])
                content += "```dataview\n"
                content += "LIST\n"
                content += f"FROM #({formatted_tags})\n"
                content += f"WHERE file.name != this.file.name\n"
                content += "SORT file.mtime DESC\n"
                content += "LIMIT 7\n"
                content += "```\n"
            else:
                content += "_Add tags to see related notes here._\n"
                
            # Add category browser
            content += f"\n### More in {category}\n"
            content += "```dataview\n"
            content += "LIST\n"
            content += f"FROM \"{category}\"\n"
            content += f"WHERE file.name != this.file.name\n"
            content += "SORT file.name ASC\n"
            content += "LIMIT 10\n"
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
            
        # Validate and fix content before adding to existing notes
        try:
            fixed_content = self._validate_and_fix_content(content)
        except Exception as e:
            logger.warning(f"Error validating content: {e}")
            fixed_content = content
        
        # Write the fixed content if needed
        if fixed_content != content:
            logger.debug(f"Fixed content issues in {md_filename}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            content = fixed_content
            
            # Re-extract content without frontmatter after fixing
            if "---" in content:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content_without_frontmatter = parts[2].strip()
        
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
        
        try:
            # Extract key phrases and concepts from content for enhanced matching
            content_lower = content.lower()
            key_phrases = set()
            key_concepts = set()
            
            # Look for common patterns that might indicate key phrases
            # Extract phrases in quotes
            quote_phrases = re.findall(r'["\'](.*?)["\']', content)
            key_phrases.update(quote_phrases)
            
            # Extract phrases in brackets/parentheses
            bracket_phrases = re.findall(r'\[(.*?)\]|\((.*?)\)', content)
            for phrase_tuple in bracket_phrases:
                for phrase in phrase_tuple:
                    if phrase and len(phrase) > 3:
                        key_phrases.add(phrase)
            
            # Extract bolded or italicized text
            emphasis_phrases = re.findall(r'\*\*(.*?)\*\*|\*(.*?)\*', content)
            for phrase_tuple in emphasis_phrases:
                for phrase in phrase_tuple:
                    if phrase and len(phrase) > 3:
                        key_phrases.add(phrase)
            
            # Extract header text (very important for similarity)
            headers = re.findall(r'^#+\s+(.*?)$', content, re.MULTILINE)
            key_phrases.update(headers)
            
            # Extract potential concepts and technical terms
            # Technology terms
            tech_terms = re.findall(r'\b(python|javascript|typescript|java|c\+\+|ruby|go|rust|react|angular|vue|node\.?js|docker|kubernetes|aws|azure|gcp|sql|nosql|mongodb|redis|api|rest|graphql|blockchain|crypto|ai|ml)\b', content_lower)
            key_concepts.update(tech_terms)
            
            # Financial terms
            finance_terms = re.findall(r'\b(invest(ing|ment)?|trad(ing|e)|stock(s)?|crypto(currency)?|bitcoin|ethereum|bank(ing)?|budget|accounting|financ(e|ial)|econom(y|ic)|market)\b', content_lower)
            key_concepts.update([t[0] for t in finance_terms if t[0]])
            
            # General concepts (common nouns that might be important)
            concept_pattern = r'\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)\b'
            potential_concepts = re.findall(concept_pattern, content)
            key_concepts.update(potential_concepts)
            
            # Add content with extra weight for key phrases and concepts
            weighted_content = content
            
            # Add key phrases with high weight (3x)
            for phrase in key_phrases:
                if len(phrase) > 3:  # Only use meaningful phrases
                    weighted_content += f" {phrase} {phrase} {phrase}"  # Repeat for extra weight
            
            # Add key concepts with medium weight (2x)
            for concept in key_concepts:
                if len(concept) > 3:  # Only use meaningful concepts
                    weighted_content += f" {concept} {concept}"  # Repeat for extra weight
            
            # Use enhanced vectorizer for better results
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=15000,  # Allow more features
                ngram_range=(1, 3),  # Include trigrams for better context
                min_df=1,
                max_df=0.95
            )
            
            # Calculate similarity with weighted content
            all_texts = existing_contents + [weighted_content]
            vectors = vectorizer.fit_transform(all_texts)
            
            similarity = cosine_similarity(vectors[-1], vectors[:-1])
            
            # Use more aggressive similarity threshold to get more links
            effective_threshold = max(self.similarity_threshold * 0.8, 0.15)  # Lower threshold to get more links
            
            # Get top matches plus all that are above threshold
            max_suggestions = min(20, max(8, self.max_links))  # At least 8, at most 20
            similar_indices = similarity.argsort()[0][-max_suggestions:][::-1]
            
            # Find potential direct concept matches
            direct_matches = []
            for concept in key_concepts:
                if len(concept) > 3:
                    concept_lower = concept.lower()
                    for i, title in enumerate(existing_titles):
                        if concept_lower in title.lower():
                            direct_matches.append(i)
            
            # Combine direct matches with similarity matches
            all_match_indices = list(set(similar_indices.tolist() + direct_matches))
            
            # Return list of (title, filename) tuples for similar notes
            results = []
            for i in all_match_indices:
                if i < len(existing_titles) and (i in direct_matches or similarity[0][i] > effective_threshold):
                    results.append((existing_titles[i], existing_filenames[i]))
            
            # Limit to max_suggestions
            return results[:max_suggestions]
                    
        except Exception as e:
            logger.warning(f"Error computing note similarities: {e}")
            return []
    
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
    
    def create_home_page(self):
        """
        Creates a Home.md page as an index for the Obsidian vault
        
        Returns:
            The path to the created home page file
        """
        logger.info("Creating Home.md index page for Obsidian vault")
        
        # Get all categories in use
        categories = set()
        for filename, (title, _) in self.existing_notes.items():
            category = os.path.dirname(filename)
            if category:
                categories.add(category)
        
        # Create content
        content = """---
title: "Obsidian Vault Home"
tags: ["index", "dashboard", "home-page"]
date: """ + datetime.now().strftime("%Y-%m-%d") + """
alias: ["Home", "Index", "Dashboard"]
---

# Obsidian Vault Home

Welcome to your knowledge base! This page serves as the central hub to navigate your notes.

## Main Categories
"""
        
        # Add links to main categories
        main_categories = ["Technology", "Finance", "Personal", "Projects", "Knowledge", "Reference"]
        for category in main_categories:
            if category.lower() in [cat.lower() for cat in categories]:
                content += f"- [[{category}/{category}|{category} Notes]]\n"
            else:
                # Include as a potential category even if no notes exist yet
                content += f"- {category}\n"
        
        content += "\n## Recent Notes\n"
        content += "```dataview\nLIST FROM \"\" \nSORT file.mtime DESC\nWHERE file.name != \"Home\"\nLIMIT 10\n```\n\n"
        
        content += "## Most Linked Notes\n"
        content += "```dataview\nTABLE length(file.inlinks) as \"Incoming Links\" \nSORT length(file.inlinks) DESC\nWHERE file.name != \"Home\"\nLIMIT 5\n```\n\n"
        
        content += "## Tags Overview\n"
        content += "```dataview\nLIST\nGROUP BY tags\nLIMIT 20\n```\n\n"
        
        # Save the home page
        home_path = os.path.join(self.output_dir, "Home.md")
        with open(home_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return home_path

    def _process_file_worker(self, file_path):
        """
        Worker function for parallel processing
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Tuple of (number of notes created, file path)
        """
        try:
            created = self.process_file(file_path)
            return len(created), file_path
        except Exception as e:
            logger.error(f"Error processing item {file_path}: {e}")
            return 0, file_path
            
    def _validate_and_fix_content(self, content):
        """
        Validate and fix common issues in note content
        
        Args:
            content: The note content to validate and fix
            
        Returns:
            Fixed content
        """
        # Fix duplicate headers
        # Find the first heading level (# or ## or ###)
        heading_match = re.search(r'^(#+)\s+(.*?)$', content, re.MULTILINE)
        if heading_match:
            heading_level = heading_match.group(1)
            heading_text = heading_match.group(2)
            
            # Check for duplicate headings with the same text
            duplicate_pattern = f"^{heading_level}\\s+{re.escape(heading_text)}$"
            matches = re.findall(duplicate_pattern, content, re.MULTILINE)
            
            if len(matches) > 1:
                # Keep only the first occurrence
                seen_count = [0]
                def replace_func(m):
                    seen_count[0] += 1
                    return m.group(0) if seen_count[0] <= 1 else ""
                content = re.sub(duplicate_pattern, replace_func, content, flags=re.MULTILINE)
        
        # Fix unclosed code blocks
        code_block_starts = re.findall(r'```[a-zA-Z0-9]*', content)
        code_block_ends = re.findall(r'```\s*$', content, re.MULTILINE)
        
        if len(code_block_starts) > len(code_block_ends):
            # Add missing closing code blocks
            content += "\n```\n"
        
        # Remove any trailing code blocks at the end of the file
        content = re.sub(r'\n```\s*$', '', content)
        
        # Remove any standalone code blocks (not part of a section)
        content = re.sub(r'\n```markdown\s*\n+```\s*\n', '\n', content)
        content = re.sub(r'\n```\s*\n+```\s*\n', '\n', content)
        
        # Remove LLM self-explanations or meta-commentary
        content = re.sub(r'\nFor the given content.*', '', content)
        content = re.sub(r'\nI have analyzed the.*', '', content)
        content = re.sub(r'\nBased on the content.*', '', content)
        
        # Remove unnecessary bracketed text that looks like LLM explanations
        content = re.sub(r'\[This note (?:provides|describes|explains|covers|discusses|outlines).*?\]', '', content)
        content = re.sub(r'\nThis note provides.*', '', content)
        content = re.sub(r'\nThe content is about.*', '', content)
        content = re.sub(r'\nI\'ve organized the.*', '', content)
        
        # Fix duplicate headers
        content = re.sub(r'(## [^\n]+)\n+# \1', r'\1', content)
        content = re.sub(r'(# [^\n]+)\n+## \1', r'\1', content)
        
        # Fix missing Related Concepts section
        if "## Related Concepts" not in content and "# Related Concepts" not in content:
            # Add a minimal Related Concepts section
            content += "\n\n## Related Concepts\n"
            
            # Try to extract category from frontmatter
            category = None
            category_match = re.search(r'category:\s*(\w+)', content)
            if category_match:
                category = category_match.group(1)
            
            # Add relevant links based on category
            if category == "Technology":
                content += "- [[Programming]] - Programming concepts and techniques\n"
                content += "- [[Software Development]] - Software development methodologies\n"
                content += "- [[Computer Science]] - Fundamental computer science concepts\n"
            elif category == "Finance":
                content += "- [[Investment]] - Investment strategies and concepts\n"
                content += "- [[Economics]] - Economic principles and theories\n"
                content += "- [[Financial Planning]] - Personal and business financial planning\n"
            elif category == "Personal":
                content += "- [[Self Improvement]] - Personal development strategies\n"
                content += "- [[Productivity]] - Methods to enhance productivity\n"
                content += "- [[Health]] - Health and wellness information\n"
            elif category == "Projects":
                content += "- [[Project Management]] - Project management methodologies\n"
                content += "- [[Team Collaboration]] - Strategies for team collaboration\n"
                content += "- [[Business Strategy]] - Business planning and strategy\n"
            elif category == "Knowledge":
                content += "- [[Learning]] - Learning methods and approaches\n"
                content += "- [[Research]] - Research methodologies and findings\n"
                content += "- [[Education]] - Educational concepts and resources\n"
            else:  # Reference or default
                content += "- [[Knowledge]] - General knowledge base\n"
                content += "- [[Reference]] - Reference materials\n"
                content += "- [[Resources]] - Useful resources and tools\n"
        
        # Fix frontmatter issues
        if content.startswith("---"):
            # Extract frontmatter
            frontmatter_match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                
                # Check for required fields
                required_fields = {
                    "title": r'^title:',
                    "date": r'^date:',
                    "tags": r'^tags:',
                    "category": r'^category:',
                    "created": r'^created:',
                    "modified": r'^modified:',
                    "alias": r'^alias:'
                }
                
                fixed_frontmatter = frontmatter
                
                for field, pattern in required_fields.items():
                    if not re.search(pattern, frontmatter, re.MULTILINE):
                        # Add missing field
                        if field == "title":
                            # Extract title from first heading
                            title_match = re.search(r'^#+\s+(.*?)$', content, re.MULTILINE)
                            title = title_match.group(1) if title_match else "Untitled Note"
                            fixed_frontmatter += f'\ntitle: "{title}"'
                        elif field == "date":
                            fixed_frontmatter += f'\ndate: {datetime.now().strftime("%Y-%m-%d")}'
                        elif field == "tags":
                            fixed_frontmatter += '\ntags: []'
                        elif field == "category":
                            fixed_frontmatter += '\ncategory: Knowledge'
                        elif field == "created":
                            fixed_frontmatter += f'\ncreated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                        elif field == "modified":
                            fixed_frontmatter += f'\nmodified: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                        elif field == "alias":
                            # Extract title
                            title_match = re.search(r'title:\s*"?(.*?)"?$', fixed_frontmatter, re.MULTILINE)
                            if title_match:
                                title = title_match.group(1).strip('"\'')
                                fixed_frontmatter += f'\nalias: [{title}]'
                            else:
                                fixed_frontmatter += '\nalias: []'
                
                # Replace frontmatter if changes were made
                if fixed_frontmatter != frontmatter:
                    content = content.replace(f"---\n{frontmatter}\n---", f"---\n{fixed_frontmatter}\n---")
        
        # Fix formatting issues
        # Ensure proper spacing between sections
        content = re.sub(r'(\n#+\s+.*?\n)(?!\n)', r'\1\n', content)
        
        # Fix multiple consecutive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure content doesn't end with excessive newlines
        content = content.rstrip() + "\n"
        
        return content
        
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
            
            # Execute processing in parallel
            results = execute_in_parallel(
                self._process_file_worker, 
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
        
        # Create Home.md index page if notes were generated
        if total_notes > 0:
            logger.info("Creating Home.md index page")
            self.create_home_page()
            total_notes += 1  # Count Home.md as an additional note
        
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