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

            ### Link Management:
            1. Create EXPLICIT links to other potential notes using [[Topic]] syntax
            2. For each main concept mentioned, create a link to that concept the FIRST time it appears
            3. Avoid overlinking - only link important concepts, not every term
            4. Use descriptive link text with pipe syntax when helpful: [[actual-note-title|Descriptive Link Text]]
            5. Consider creating bidirectional links between closely related concepts

            ## Obsidian Formatting Features to Use:
            - Internal links: [[note-name]] to reference related concepts
            - Bold: **text** for emphasis of important points
            - Italics: *text* for definitions or specialized terms
            - Callouts: > [!note] for important information
            - Code blocks: ```language\\ncode\\n``` for any code or commands
            - Tables: Use markdown tables for structured information

            ## Output Format:
            For each section, STRICTLY follow this exact format:

            ```
            ---
            title: "Clear Descriptive Title"
            tags: ["primary-topic", "specific-concept", "technical-area"]
            date: 2025-07-30
            category: Technology|Finance|Personal|Projects|Knowledge|Reference
            alias: ["Alternative Name", "Another Reference"]
            ---

            ## Clear Descriptive Title

            [Well-formatted content with appropriate markdown structure and explicit links to related concepts]

            ## Related Concepts
            - [[Concept-One]] - Brief description of relationship
            - [[Concept-Two]] - Brief description of relationship
            ```

            IMPORTANT: Your output MUST contain the full frontmatter block with YAML format exactly as shown above.
            The category MUST be one of the six allowed categories.
            Use real content in place of the placeholders.

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
        allowed_categories = ["Technology", "Finance", "Personal", "Projects", "Knowledge", "Reference"]
        
        # Use regex to find each markdown section with frontmatter
        pattern = r'---\s*\n(.*?)\n---\s*\n(.*?)(?=\n---|\Z)'
        matches = re.finditer(pattern, llm_output, re.DOTALL)
        
        for match in matches:
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
                continue
        
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