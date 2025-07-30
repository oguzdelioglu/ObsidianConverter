"""
LLM integration for content processing
"""
import os
import re
import json
import logging
import traceback
from datetime import datetime

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
        # Set default timeout if not provided
        if 'timeout' not in kwargs and provider == 'ollama':
            kwargs['timeout'] = 300  # 5 minutes default timeout for Ollama
            
        try:
            self.llm = LLMProviderFactory.create_provider(provider, model, **kwargs)
            logger.info(f"Initialized {provider} LLM provider with model {model}")
        except Exception as e:
            logger.error(f"Failed to initialize {provider} LLM provider: {e}")
            logger.warning(f"Falling back to Ollama provider with model mistral")
            self.provider_name = "ollama"
            self.model = "mistral"
            # Ensure timeout is set for fallback provider
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 300
            self.llm = LLMProviderFactory.create_provider("ollama", "mistral", **kwargs)
        
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
            1. Create meaningful titles that accurately reflect the content - without timestamps or date prefixes
            2. Organize content with appropriate heading levels (H2, H3, etc.)
            3. Use bullet points or numbered lists for series of related items
            4. Preserve code blocks with correct language identifiers
            5. Split very long notes into multiple related notes if appropriate

            ### Metadata Generation:
            1. Generate 3-5 relevant tags that describe key concepts (no # prefix in frontmatter)
            2. USE EXCLUSIVELY ONE OF THESE PRIMARY CATEGORIES for folder organization (this is critical):
               - Technology (tech, software, programming, development, IT, coding, web, computer, network, server, database)
               - Finance (money, investing, cryptocurrency, banking, economy, trading, market, accounting, budget)
               - Personal (life, health, goals, habits, fitness, wellbeing, relationships, journal, diary)
               - Projects (work, business, initiatives, planning, tasks, milestones, development, implementation)
               - Knowledge (concepts, theories, learning, education, research, science, studies, information)
               - Reference (guides, manuals, instructions, documentation, resources, lists, collections)
            3. DO NOT CREATE ANY OTHER CATEGORIES - you MUST select from the above list ONLY
            4. Use specific, descriptive tags for sub-categorization instead of creating sub-folders
            5. Always use kebab-case for tags (e.g., "project-management" not "project management")
            6. Include today's date in YYYY-MM-DD format

            ### Link Management (CRITICAL - CREATE MANY LINKS):
            1. Create EXPLICIT links to other potential notes using [[Topic]] syntax
            2. For EACH main concept, term, technology, person, or idea mentioned, CREATE A LINK using [[Term]] format
            3. Create AT LEAST 5-10 LINKS in each note - this is VERY IMPORTANT
            4. Link to both general concepts AND specific topics (e.g., [[Programming]], [[Python]], [[Database]], [[SQL]])
            5. Use descriptive link text with pipe syntax when helpful: [[actual-note-title|Descriptive Link Text]]
            6. ALWAYS include a "Related Concepts" section at the end with 3-7 explicit links to related topics
            7. For technical content, link to relevant technologies, frameworks, and concepts
            8. For financial content, link to relevant financial terms, concepts, and instruments
            9. For knowledge content, link to related fields, theories, and concepts

            ## Obsidian Formatting Features to Use:
            - Internal links: [[note-name]] to reference related concepts
            - Bold: **text** for emphasis of important points
            - Italics: *text* for definitions or specialized terms
            - Callouts: > [!note] for important information
            - Code blocks: ```language\\ncode\\n``` for any code or commands
            - Tables: Use markdown tables for structured information

            ## Output Format:
            For each section, you MUST STRICTLY follow this exact format:

            ```
            ---
            title: "Clear Descriptive Title"
            tags: ["primary-topic", "specific-concept", "technical-area", "relevant-keyword", "domain-specific-tag"]
            date: 2025-07-30
            category: Technology|Finance|Personal|Projects|Knowledge|Reference
            alias: ["Alternative Name", "Another Reference"]
            ---

            # Clear Descriptive Title

            [Well-formatted content with appropriate markdown structure and MANY explicit links to related concepts using [[Term]] format. Include at least 5-10 links throughout the content. Make sure all code blocks are properly closed with triple backticks.]

            ## Key Points
            - First important point with [[relevant link]]
            - Second important point with [[another link]]
            - Third important point with [[third link]]

            ## Related Concepts
            - [[Concept-One]] - Brief description of relationship
            - [[Concept-Two]] - Brief description of relationship
            - [[Concept-Three]] - Brief description of relationship
            - [[Concept-Four]] - Brief description of relationship
            - [[Concept-Five]] - Brief description of relationship
            ```

            CRITICAL REQUIREMENTS:
            1. Your output MUST contain the full frontmatter block with YAML format exactly as shown above
            2. The category MUST be one of the six allowed categories
            3. Include AT LEAST 5 specific, relevant tags in each note
            4. DO NOT repeat the title as a heading - use a single # heading with the title
            5. Include AT LEAST 5-10 internal links using [[Term]] format throughout the content
            6. ALWAYS include a "Related Concepts" section with 3-7 explicit links
            7. Ensure all code blocks are properly closed with triple backticks
            8. Add a "Key Points" section to summarize important information

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
            try:
                result = self.llm.invoke(prompt)
            except Exception as e:
                logger.error(f"Error invoking LLM for {context_path}: {str(e)}")
                # Create a minimal fallback response
                result = f"""---
title: "{os.path.basename(context_path) if context_path else 'Untitled Note'}"
tags: ["auto-generated", "error-recovery"]
date: {datetime.now().strftime('%Y-%m-%d')}
category: Knowledge
---

# {os.path.basename(context_path) if context_path else 'Untitled Note'}

{content[:500]}... (content truncated due to processing error)

## Error Information
Processing error occurred: {str(e)}

## Key Points
- This note was auto-generated due to an error in LLM processing
- The original content may need manual review
- Consider retrying with a different model or breaking the content into smaller chunks

## Related Concepts
- [[Knowledge Management]]
- [[Error Handling]]
- [[Content Processing]]
"""
            
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
        allowed_categories = ["Technology", "Finance", "Personal", "Projects", "Knowledge", "Reference"]
        
        # Track if we found any matches
        found_matches = False
        
        # Use regex to find each markdown section with frontmatter
        pattern = r'---\s*\n(.*?)\n---\s*\n(.*?)(?=\n---|\Z)'
        matches = list(re.finditer(pattern, llm_output, re.DOTALL))
        
        # Process standard frontmatter matches
        for match in matches:
            found_matches = True
            try:
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
                
                # Improved category handling
                if category_match:
                    category = category_match.group(1).strip().strip('"\'')
                    # Validate against allowed categories
                    if category not in allowed_categories:
                        # Try case insensitive matching
                        category_lower = category.lower()
                        found = False
                        for allowed in allowed_categories:
                            if allowed.lower() == category_lower:
                                category = allowed
                                found = True
                                break
                        
                        # If still not found, generate from title
                        if not found:
                            category = self._generate_category_from_title(title)
                else:
                    category = self._generate_category_from_title(title)
                
                # Create proper formatted content
                formatted_content = f"## {title}\n\n{content}"
                sections.append((title, formatted_content, category, tags))
            except Exception as e:
                logger.warning(f"Error extracting section: {str(e)}")
                # Continue to next match
        
        # Multiple fallback methods if no sections were extracted
        if not sections:
            logger.warning(f"Failed to extract sections from {context_path}, trying multiple fallback methods")
            
            # Attempt 1: Try relaxed frontmatter pattern
            try:
                relaxed_pattern = r'---\s*(.*?)---\s*(.*?)(?=---|$)'
                relaxed_matches = re.finditer(relaxed_pattern, llm_output, re.DOTALL)
                for match in relaxed_matches:
                    fm = match.group(1).strip()
                    body = match.group(2).strip()
                    
                    # Try to extract title
                    title_match = re.search(r'title:[ \t]*["\']?(.*?)["\']?[\n\r]', fm, re.MULTILINE)
                    title = title_match.group(1).strip() if title_match else "Untitled Note"
                    
                    # Try to extract category
                    category = self._generate_category_from_title(title)
                    
                    # Try to extract tags
                    tags = []
                    tags_match = re.search(r'tags:[ \t]*\[(.*?)\]', fm, re.DOTALL)
                    if tags_match:
                        raw_tags = tags_match.group(1).strip()
                        tag_matches = re.findall(r'"([^"]+)"|\'([^\']+)\'|([^,\s]+)', raw_tags)
                        for tag_match in tag_matches:
                            tag = next((t for t in tag_match if t), "").strip()
                            if tag:
                                tags.append(tag)
                    
                    if not tags:
                        tags = self._generate_tags_from_content(title, body)
                    
                    formatted_content = f"## {title}\n\n{body}"
                    sections.append((title, formatted_content, category, tags))
            except Exception as e:
                logger.debug(f"Relaxed frontmatter extraction failed: {str(e)}")
            
            # Attempt 2: Use heading-based extraction if still empty
            if not sections:
                try:
                    # Use simple split by H2 headings as fallback
                    h2_sections = re.split(r'## (.*?)\n', llm_output)
                    if len(h2_sections) > 1:
                        for i in range(1, len(h2_sections), 2):
                            if i+1 < len(h2_sections):
                                title = h2_sections[i].strip()
                                body = h2_sections[i+1].strip()
                                
                                # Generate category and tags
                                category = self._generate_category_from_title(title)
                                tags = self._generate_tags_from_content(title, body)
                                
                                formatted_content = f"## {title}\n\n{body}"
                                sections.append((title, formatted_content, category, tags))
                except Exception as e:
                    logger.debug(f"Heading-based extraction failed: {str(e)}")
            
            # Final attempt: Treat the entire content as a single note
            if not sections:
                try:
                    # Try to find a title or use the first line/sentence
                    title_match = re.search(r'^#+\s+(.*?)$', llm_output, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        # Use first non-empty line as title
                        first_lines = [line.strip() for line in llm_output.split('\n') if line.strip()]
                        if first_lines:
                            # Limit title length
                            title = first_lines[0][:50]
                            if len(first_lines[0]) > 50:
                                title += "..."
                        else:
                            title = os.path.basename(context_path) if context_path else "Untitled Note"
                    
                    # Generate metadata
                    category = self._generate_category_from_title(title)
                    tags = self._generate_tags_from_content(title, llm_output)
                    
                    formatted_content = f"## {title}\n\n{llm_output}"
                    sections.append((title, formatted_content, category, tags))
                except Exception as e:
                    logger.warning(f"All section extraction methods failed: {str(e)}")
                    # Create minimal fallback note
                    title = os.path.basename(context_path) if context_path else "Untitled Note"
                    category = "Knowledge"
                    tags = []
                    formatted_content = f"## {title}\n\n{llm_output}"
                    sections.append((title, formatted_content, category, tags))
        
            # If no matches found with the standard pattern, try a more relaxed pattern
            if not found_matches:
                logger.warning(f"No sections found with standard pattern for {context_path}, trying relaxed pattern")
                # Try a more relaxed frontmatter pattern
                relaxed_pattern = r'---\s*(.*?)---\s*(.*?)(?=\n---|\Z)'
                matches = re.finditer(relaxed_pattern, llm_output, re.DOTALL)
                
                for match in matches:
                    found_matches = True
                    try:
                        frontmatter = match.group(1)
                        content = match.group(2).strip()
                        
                        # Extract metadata with more relaxed patterns
                        title_match = re.search(r'title:?\s*"?(.*?)"?[\n\r]', frontmatter, re.MULTILINE | re.IGNORECASE)
                        tags_match = re.search(r'tags:?\s*\[(.*?)\]', frontmatter, re.DOTALL | re.IGNORECASE)
                        category_match = re.search(r'category:?\s*(.*?)[\n\r]', frontmatter, re.MULTILINE | re.IGNORECASE)
                        
                        title = title_match.group(1).strip().strip('"\'') if title_match else "Untitled Note"
                        
                        # Parse tags
                        tags = []
                        if tags_match:
                            raw_tags = tags_match.group(1).strip()
                            tag_pattern = r'"([^"]+)"|\'([^\']+)\'|([^,\s]+)'
                            tag_matches = re.findall(tag_pattern, raw_tags)
                            for tag_match in tag_matches:
                                tag = next((t for t in tag_match if t), "").strip()
                                if tag:
                                    tags.append(tag)
                        
                        # Get category
                        category = None
                        if category_match:
                            category = category_match.group(1).strip().strip('"\'')
                        
                        if not category or category not in allowed_categories:
                            category = self._generate_category_from_title(title)
                        
                        sections.append((title, content, category, tags))
                    except Exception as e:
                        logger.warning(f"Error extracting section with relaxed pattern: {str(e)}")
            
            # If still no matches, try heading-based extraction
            if not found_matches:
                logger.warning(f"No sections found with frontmatter patterns for {context_path}, trying heading-based extraction")
                # Try to extract based on headings
                h1_sections = re.split(r'\n#\s+', llm_output)
                
                if len(h1_sections) > 1:  # First element is content before first h1, might be empty
                    for i, section in enumerate(h1_sections[1:], 1):  # Skip the first element
                        try:
                            # Extract title from the first line
                            title_end = section.find('\n')
                            if title_end > 0:
                                title = section[:title_end].strip()
                                body = section[title_end:].strip()
                                
                                # Generate metadata
                                category = self._generate_category_from_title(title)
                                tags = self._generate_tags_from_content(title, body)
                                
                                formatted_content = f"# {title}\n\n{body}"
                                sections.append((title, formatted_content, category, tags))
                                found_matches = True
                        except Exception as e:
                            logger.debug(f"Error in heading-based extraction: {str(e)}")
                
                # If still no matches, try h2 headings
                if not found_matches:
                    h2_sections = re.split(r'\n##\s+', llm_output)
                    if len(h2_sections) > 1:
                        for i, section in enumerate(h2_sections[1:], 1):
                            try:
                                title_end = section.find('\n')
                                if title_end > 0:
                                    title = section[:title_end].strip()
                                    body = section[title_end:].strip()
                                    
                                    category = self._generate_category_from_title(title)
                                    tags = self._generate_tags_from_content(title, body)
                                    
                                    formatted_content = f"## {title}\n\n{body}"
                                    sections.append((title, formatted_content, category, tags))
                                    found_matches = True
                            except Exception as e:
                                logger.debug(f"Error in h2 heading-based extraction: {str(e)}")
            
            # Final fallback: treat the entire content as a single note
            if not found_matches:
                logger.warning(f"All pattern-based extraction methods failed for {context_path}, using whole content as single note")
                try:
                    # Try to find a title or use the first line/sentence
                    title_match = re.search(r'^#+\s+(.*?)$', llm_output, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        # Use first non-empty line as title
                        first_lines = [line.strip() for line in llm_output.split('\n') if line.strip()]
                        if first_lines:
                            # Limit title length
                            title = first_lines[0][:50]
                            if len(first_lines[0]) > 50:
                                title += "..."
                        else:
                            title = os.path.basename(context_path) if context_path else "Untitled Note"
                    
                    # Generate metadata
                    category = self._generate_category_from_title(title)
                    tags = self._generate_tags_from_content(title, llm_output)
                    
                    sections.append((title, llm_output, category, tags))
                except Exception as e:
                    logger.error(f"Final fallback extraction failed: {str(e)}")
                    # Create absolute minimal note
                    title = os.path.basename(context_path) if context_path else "Untitled Note"
                    sections.append((title, llm_output, "Knowledge", []))
                
        # Post-process: ensure all sections have a valid category
        for i, (title, content, category, tags) in enumerate(sections):
            if not category or category not in allowed_categories:
                new_category = self._generate_category_from_title(title)
                sections[i] = (title, content, new_category, tags)
                
        return sections
    
    def _generate_category_from_title(self, title):
        """
        Generate a category based on the title

        Args:
            title: The note title

        Returns:
            A suggested category name from the restricted set of main categories
        """
        title_lower = title.lower()
        
        # ONLY use these main categories for organization
        main_categories = {
            "Technology": ["tech", "software", "programming", "code", "app", "website", "internet", "computer", 
                        "digital", "online", "web", "development", "algorithm", "database", "server", "api", 
                        "framework", "library", "tool", "script", "system", "network", "coding", "developer",
                        "it", "application", "browser", "cybersecurity", "cloud", "mobile", "hardware",
                        "security", "automation", "data", "interface", "platform", "api", "blockchain",
                        "devops", "android", "ios", "seo", "wordpress", "domain", "seo", "github", "git"],
                        
            "Finance": ["money", "financial", "invest", "stock", "market", "crypto", "cryptocurrency", "bitcoin", 
                      "ethereum", "banking", "economy", "fund", "income", "expense", "budget", "accounting", 
                      "transaction", "payment", "wallet", "bank", "trading", "tax", "finance", "solana",
                      "binance", "exchange", "token", "coin", "blockchain", "defi", "nft", "mining",
                      "staking", "investment", "profit", "revenue", "asset", "liability", "capital",
                      "loan", "interest", "mortgage", "insurance", "wealth", "portfolio"],
                      
            "Personal": ["health", "life", "diary", "journal", "personal", "habit", "routine", "goal", 
                       "achievement", "hobby", "fitness", "meditation", "reflection", "self", "emotion", 
                       "feeling", "mood", "relationship", "experience", "memory", "dream", "wellness",
                       "family", "friend", "social", "mental", "physical", "spiritual", "diet", 
                       "exercise", "mindfulness", "productivity", "sleep", "stress", "therapy", 
                       "psychology", "motivation", "happiness", "travel", "adventure", "food", "recipe"],
                       
            "Projects": ["project", "business", "work", "task", "initiative", "startup", "venture", 
                       "plan", "idea", "proposal", "collaboration", "team", "schedule", "timeline", 
                       "milestone", "deliverable", "objective", "goal", "product", "service",
                       "management", "planning", "roadmap", "strategy", "implementation", "client",
                       "customer", "marketing", "sales", "brand", "launch", "growth", "metric",
                       "kpi", "agile", "sprint", "backlog", "requirement", "scope", "budget",
                       "deadline", "progress", "status", "meeting", "workflow", "operations"],
                       
            "Knowledge": ["learn", "study", "concept", "theory", "principle", "method", "process", "discipline", 
                        "subject", "topic", "field", "course", "education", "training", "skill", "lesson", 
                        "tutorial", "guide", "manual", "explanation", "definition", "book", "article", "paper",
                        "science", "math", "history", "philosophy", "language", "grammar", "vocabulary",
                        "literature", "research", "analysis", "methodology", "technique", "framework",
                        "model", "hypothesis", "experiment", "observation", "discovery", "invention",
                        "innovation", "insight", "wisdom", "understanding", "information", "fact",
                        "networking", "protocol", "server", "linux", "command"],
                        
            "Reference": ["reference", "guide", "manual", "documentation", "instruction", "specification", 
                         "standard", "protocol", "formula", "recipe", "template", "checklist", "directory", 
                         "index", "catalog", "dictionary", "glossary", "cheatsheet", "resource", "link",
                         "list", "collection", "compilation", "archive", "repository", "database", 
                         "record", "document", "file", "backup", "code", "credential", "password",
                         "contact", "address", "phone", "email", "url", "website", "account",
                         "identifier", "serial", "key", "license", "certificate", "authorization"]
        }
        
        # Search for keywords in title
        for category, keywords in main_categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        # If no keywords match, assign to Knowledge by default
        return "Knowledge"
    
    def _generate_tags_from_content(self, title, content):
        """
        Generate tags based on the content
        
        Args:
            title: The note title
            content: The note content
            
        Returns:
            A list of generated tags
        """
        tags = []
        
        # Extract meaningful words from title
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', title.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'about', 'have', 'has', 'had', 
                     'not', 'what', 'when', 'where', 'who', 'how', 'which', 'there', 'their', 'they',
                     'been', 'were', 'would', 'could', 'should', 'will', 'then', 'than', 'them', 'these'}
        title_tags = [word for word in words if word not in stop_words]
        tags.extend(title_tags)
        
        # Add tags from common patterns in content
        if re.search(r'```[a-zA-Z]*\n', content):
            code_lang = re.search(r'```([a-zA-Z0-9]+)', content)
            if code_lang and code_lang.group(1):
                tags.append(f'{code_lang.group(1)}-code')
            tags.append('code-snippet')
            
        # Extract programming languages and technologies
        tech_patterns = {
            'python': r'\bpython\b',
            'javascript': r'\b(javascript|js)\b',
            'typescript': r'\b(typescript|ts)\b',
            'java': r'\bjava\b',
            'c-sharp': r'\b(c#|c-sharp|csharp)\b',
            'cpp': r'\b(c\+\+|cpp)\b',
            'php': r'\bphp\b',
            'ruby': r'\bruby\b',
            'go': r'\bgo\b',
            'rust': r'\brust\b',
            'swift': r'\bswift\b',
            'kotlin': r'\bkotlin\b',
            'react': r'\breact\b',
            'angular': r'\bangular\b',
            'vue': r'\bvue\b',
            'node': r'\bnode\.?js\b',
            'docker': r'\bdocker\b',
            'kubernetes': r'\b(kubernetes|k8s)\b',
            'aws': r'\baws\b',
            'azure': r'\bazure\b',
            'gcp': r'\b(gcp|google cloud)\b',
            'database': r'\b(database|db)\b',
            'sql': r'\bsql\b',
            'nosql': r'\bnosql\b',
            'mongodb': r'\bmongodb\b',
            'redis': r'\bredis\b',
            'api': r'\bapi\b',
            'rest': r'\brest\b',
            'graphql': r'\bgraphql\b',
            'blockchain': r'\bblockchain\b',
            'crypto': r'\b(crypto|cryptocurrency)\b',
            'ai': r'\b(ai|artificial intelligence)\b',
            'ml': r'\b(ml|machine learning)\b',
            'dl': r'\b(dl|deep learning)\b'
        }
        
        for tag, pattern in tech_patterns.items():
            if re.search(pattern, content.lower()):
                tags.append(tag)
                
        # Extract financial terms
        finance_patterns = {
            'investing': r'\binvest(ing|ment)?\b',
            'trading': r'\btrad(ing|e)\b',
            'stocks': r'\bstock(s)?\b',
            'crypto': r'\b(crypto|cryptocurrency|bitcoin|ethereum|token)\b',
            'banking': r'\bbank(ing)?\b',
            'budget': r'\bbudget\b',
            'accounting': r'\baccounting\b',
            'finance': r'\bfinanc(e|ial)\b',
            'economy': r'\beconom(y|ic)\b',
            'market': r'\bmarket\b'
        }
        
        for tag, pattern in finance_patterns.items():
            if re.search(pattern, content.lower()):
                tags.append(tag)
                
        # Extract content format indicators
        if re.search(r'https?://[^\s]+', content):
            tags.append('links')
            
            # Check for specific sites
            if re.search(r'github\.com', content.lower()):
                tags.append('github')
            if re.search(r'stackoverflow\.com', content.lower()):
                tags.append('stackoverflow')
            if re.search(r'youtube\.com|youtu\.be', content.lower()):
                tags.append('youtube')
            
        if re.search(r'\d{4}-\d{2}-\d{2}', content):
            tags.append('dated')
            
        if len(re.findall(r'^\s*-\s+', content, re.MULTILINE)) > 3:
            tags.append('list')
            
        if len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE)) > 3:
            tags.append('numbered-list')
            
        if re.search(r'\|\s*-+\s*\|', content):
            tags.append('table')
            
        if re.search(r'!\[\s*\]\(', content):
            tags.append('images')
        
        # Look for domain-specific content
        domains = {
            'tutorial': r'\b(tutorial|how[-\s]to|guide)\b',
            'reference': r'\b(reference|cheatsheet|documentation)\b',
            'concept': r'\b(concept|theory|principle)\b',
            'tool': r'\b(tool|utility|application)\b',
            'project': r'\b(project|implementation)\b',
            'research': r'\b(research|study|analysis)\b',
            'note': r'\b(note|summary|overview)\b'
        }
        
        for tag, pattern in domains.items():
            if re.search(pattern, content.lower()):
                tags.append(tag)
        
        # Convert tags to kebab-case and ensure uniqueness
        processed_tags = []
        for tag in tags:
            # Convert to lowercase and replace spaces/underscores with hyphens
            kebab_tag = tag.lower().replace(' ', '-').replace('_', '-')
            # Remove any non-alphanumeric characters except hyphens
            kebab_tag = re.sub(r'[^a-z0-9-]', '', kebab_tag)
            # Ensure no consecutive hyphens
            kebab_tag = re.sub(r'-+', '-', kebab_tag)
            # Remove leading/trailing hyphens
            kebab_tag = kebab_tag.strip('-')
            
            if kebab_tag and len(kebab_tag) > 1:  # Ensure tag is not empty and not just a single character
                processed_tags.append(kebab_tag)
        
        # Remove duplicates while preserving order
        unique_tags = []
        for tag in processed_tags:
            if tag not in unique_tags:
                unique_tags.append(tag)
        
        # Ensure we have at least 3 tags, add generic ones if needed
        if len(unique_tags) < 3:
            category = self._generate_category_from_title(title)
            if category.lower() not in unique_tags:
                unique_tags.append(category.lower())
            
            if 'note' not in unique_tags:
                unique_tags.append('note')
                
            if 'reference' not in unique_tags and category == 'Reference':
                unique_tags.append('reference')
                
            if 'knowledge' not in unique_tags and category == 'Knowledge':
                unique_tags.append('knowledge')
        
        # Limit to 10 tags, prioritizing more specific ones (usually longer)
        return sorted(unique_tags, key=len, reverse=True)[:10]