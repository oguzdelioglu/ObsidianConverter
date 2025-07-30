"""
Command line interface for ObsidianConverter
"""
import os
import re
import sys
import argparse
import logging
import shutil
from pathlib import Path

from obsidian_converter import __version__
from obsidian_converter.converter import ObsidianConverter
from obsidian_converter.config import ObsidianConverterConfig


# Default settings
DEFAULT_INPUT_DIR = "txt"
DEFAULT_OUTPUT_DIR = "vault"
DEFAULT_MODEL = "mistral"
DEFAULT_SIMILARITY_THRESHOLD = 0.3
DEFAULT_MAX_LINKS = 5
DEFAULT_CACHE_FILE = ".llm_cache.json"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("obsidian_converter")


def show_help():
    """Show detailed help information"""
    help_text = f"""
ObsidianConverter {__version__}
==============================

A tool to convert plain text files into well-structured Obsidian notes

Usage:
  obsidian-converter [options] [command]

Options:
  -h, --help                Show this help message and exit
  -V, --version             Show version and exit
  -i, --input DIR           Input directory containing text files (default: {DEFAULT_INPUT_DIR})
  -o, --output DIR          Output directory for Obsidian vault (default: {DEFAULT_OUTPUT_DIR})
  -m, --model MODEL         Ollama model to use (default: {DEFAULT_MODEL})
  -s, --similarity FLOAT    Similarity threshold for linking notes (default: {DEFAULT_SIMILARITY_THRESHOLD})
  --max-links INT           Maximum number of links between notes (default: {DEFAULT_MAX_LINKS})
  --no-cache                Disable caching of LLM responses
  -v, --verbose             Enable verbose logging
  --clean                   Clean output directory before conversion

Commands:
  convert                   Process all text files (default)
  files [FILE...]           Process specific text files
  clean                     Remove output directory and start fresh

Examples:
  obsidian-converter
    - Process all .txt files in 'txt' directory to 'vault' directory

  obsidian-converter --input documents --output obsidian-notes
    - Process all .txt files from 'documents' directory to 'obsidian-notes'

  obsidian-converter files example.txt notes/meeting.txt
    - Process only the specified text files

  obsidian-converter --model llama2 --clean
    - Use a different model and clean output before conversion
"""
    print(help_text)
    sys.exit(0)


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        description="Convert text files to Obsidian markdown notes",
        add_help=False  # We'll handle help manually for more detailed output
    )
    
    # Basic options
    parser.add_argument("-h", "--help", action="store_true",
                        help="Show detailed help message and exit")
    
    parser.add_argument("-V", "--version", action="store_true",
                        help="Show version and exit")
    
    parser.add_argument("--input", "-i", default=DEFAULT_INPUT_DIR,
                        help=f"Input directory containing text files (default: {DEFAULT_INPUT_DIR})")
    
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory for Obsidian vault (default: {DEFAULT_OUTPUT_DIR})")
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Default command (convert)
    convert_parser = subparsers.add_parser("convert", help="Convert all text files")
    
    # Files command
    files_parser = subparsers.add_parser("files", help="Convert specific text files")
    files_parser.add_argument("file_paths", nargs="+", help="Text files to convert")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean output directory")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List generated notes")
    list_parser.add_argument("--category", help="Filter by category")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Create or view configuration")
    config_parser.add_argument("--create", action="store_true", 
                              help="Create a default configuration file")
    config_parser.add_argument("--file", default="config.yaml", 
                              help="Path to config file (default: config.yaml)")
    
    # Advanced options
    parser.add_argument("--config", "-c", 
                       help="Path to configuration file")
    
    parser.add_argument("--provider", "-p", default="ollama",
                        choices=["ollama", "openai", "anthropic"],
                        help="LLM provider to use (default: ollama)")
                        
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"LLM model to use (default: {DEFAULT_MODEL})")
                        
    parser.add_argument("--openai-key",
                        help="OpenAI API key (can also use OPENAI_API_KEY env variable)")
                        
    parser.add_argument("--anthropic-key",
                        help="Anthropic API key (can also use ANTHROPIC_API_KEY env variable)")
    
    parser.add_argument("--similarity", "-s", type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
                        help=f"Similarity threshold for linking notes (default: {DEFAULT_SIMILARITY_THRESHOLD})")
    
    parser.add_argument("--max-links", type=int, default=DEFAULT_MAX_LINKS,
                        help=f"Maximum number of links between notes (default: {DEFAULT_MAX_LINKS})")
    
    parser.add_argument("--parallel", action="store_true", 
                        help="Enable parallel processing")
                        
    parser.add_argument("--workers", type=int,
                        help="Number of parallel workers (defaults to CPU count)")
    
    parser.add_argument("--no-cache", action="store_true", 
                        help="Disable caching of LLM responses")
    
    parser.add_argument("--interactive", "-it", action="store_true",
                        help="Enable interactive review mode")
                        
    parser.add_argument("--editor", 
                        help="Specify text editor for interactive mode (default: system EDITOR)")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    
    parser.add_argument("--clean", action="store_true",
                        help="Clean output directory before conversion")
    
    # For backward compatibility, allow files to be specified without the 'files' command
    parser.add_argument("files", nargs="*", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Show help if requested
    if args.help:
        show_help()
    
    # Show version if requested
    if args.version:
        print(f"ObsidianConverter version {__version__}")
        sys.exit(0)
    
    # If no command is specified but files are provided, use "files" command
    if not args.command and args.files:
        args.command = "files"
        args.file_paths = args.files
    
    # If no command and no files, default to "convert"
    if not args.command:
        args.command = "convert"
    
    return args


def clean_output_directory(directory):
    """
    Clean the output directory
    
    Args:
        directory: Path to the directory to clean
    """
    if os.path.exists(directory):
        logger.info(f"Cleaning output directory: {directory}")
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info(f"Output directory cleaned: {directory}")
        except Exception as e:
            logger.error(f"Error cleaning output directory: {e}")
    else:
        logger.info(f"Output directory doesn't exist, creating: {directory}")
        os.makedirs(directory, exist_ok=True)


def main():
    """
    Main CLI entry point
    """
    args = parse_arguments()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Clean command handling
    if args.command == "clean":
        clean_output_directory(args.output)
        print(f"Output directory cleaned: {args.output}")
        return 0
    
    # Config command handling
    if args.command == "config":
        if args.create:
            config_path = args.file
            if ObsidianConverterConfig.create_default_config(config_path):
                print(f"Created default configuration file: {config_path}")
                print("Edit this file to customize your conversion settings.")
                return 0
            else:
                logger.error(f"Failed to create configuration file: {config_path}")
                return 1
        else:
            # View or validate config
            config_path = args.file
            if os.path.exists(config_path):
                config = ObsidianConverterConfig.from_file(config_path)
                print("\nCurrent Configuration:")
                print("-" * 30)
                for key, value in config.__dict__.items():
                    if key.startswith('_'):
                        continue
                    print(f"{key}: {value}")
                return 0
            else:
                print(f"Configuration file not found: {config_path}")
                print("Use --create to create a default configuration file")
                return 1
    
    # List command handling
    if args.command == "list":
        output_dir = Path(args.output)
        if not output_dir.exists():
            logger.error(f"Output directory doesn't exist: {args.output}")
            return 1
            
        # Find all markdown files
        if args.category:
            category_dir = output_dir / args.category
            if not category_dir.exists():
                logger.error(f"Category directory doesn't exist: {category_dir}")
                return 1
            md_files = list(category_dir.glob("**/*.md"))
        else:
            md_files = list(output_dir.glob("**/*.md"))
        
        # Extract titles and categories from files
        notes = []
        for md_file in md_files:
            relative_path = md_file.relative_to(output_dir)
            category = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
            
            # Extract title from frontmatter
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                title = "Untitled"
                if content.startswith("---"):
                    frontmatter_end = content.find("---", 3)
                    if frontmatter_end != -1:
                        frontmatter = content[3:frontmatter_end]
                        title_match = re.search(r'title:\s*"?(.*?)"?$', frontmatter, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1)
                
                notes.append((title, category, str(relative_path)))
            except Exception as e:
                logger.error(f"Error reading file {md_file}: {e}")
        
        # Display results
        if not notes:
            print(f"No notes found in {args.output}" + 
                  (f" under category '{args.category}'" if args.category else ""))
            return 0
            
        print(f"\nFound {len(notes)} notes in {args.output}:")
        print("\n{:<40} {:<20} {:<40}".format("TITLE", "CATEGORY", "PATH"))
        print("-" * 100)
        
        for title, category, path in sorted(notes, key=lambda x: x[1]):
            print("{:<40} {:<20} {:<40}".format(
                title[:37] + "..." if len(title) > 40 else title,
                category,
                path
            ))
            
        return 0
    
    # Clean output directory if requested
    if args.clean:
        clean_output_directory(args.output)
    
    # Load config if specified
    config = None
    if args.config:
        if not os.path.exists(args.config):
            logger.error(f"Configuration file not found: {args.config}")
            return 1
        logger.info(f"Loading configuration from: {args.config}")
        config = ObsidianConverterConfig.from_file(args.config)
    
    # If config is loaded, override with command line arguments
    if config is not None:
        if args.provider:
            config.provider = args.provider
        if args.model:
            config.model = args.model
        if args.openai_key:
            config.openai_api_key = args.openai_key
        if args.anthropic_key:
            config.anthropic_api_key = args.anthropic_key
    
    # Create converter with config
    converter = ObsidianConverter(
        input_dir=args.input,
        output_dir=args.output,
        model=args.model,
        similarity_threshold=args.similarity,
        max_links=args.max_links,
        use_cache=not args.no_cache,
        interactive=args.interactive,
        config=config
    )
    
    # If no config loaded, set provider options directly
    if config is None and args.provider:
        converter.config.provider = args.provider
        if args.openai_key:
            converter.config.openai_api_key = args.openai_key
        if args.anthropic_key:
            converter.config.anthropic_api_key = args.anthropic_key
    
    # Set editor for interactive mode if specified
    if args.interactive and args.editor:
        if hasattr(converter, 'reviewer'):
            converter.reviewer.editor = args.editor
    
    # Apply additional arguments
    if args.parallel:
        converter.config.parallel_processing = True
    if args.workers:
        converter.config.max_workers = args.workers
    
    # Process specific files
    if args.command == "files":
        total_notes = 0
        for file in args.file_paths:
            # First check if file exists as is
            if os.path.exists(file):
                file_path = file
            # Then check if it's relative to input dir
            elif os.path.exists(os.path.join(args.input, file)):
                file_path = os.path.join(args.input, file)
            else:
                logger.error(f"File not found: {file}")
                continue
                
            logger.info(f"Processing specific file: {file_path}")
            created = converter.process_file(file_path)
            total_notes += len(created)
        
        logger.info(f"Conversion complete. Created {total_notes} notes from {len(args.file_paths)} files.")
    else:
        # Run the full conversion
        total_notes = converter.run()
    
    print(f"\nConverted {total_notes} notes into your Obsidian vault: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())