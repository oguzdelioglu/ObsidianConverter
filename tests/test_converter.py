"""
Tests for the core ObsidianConverter functionality
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from obsidian_converter.converter import ObsidianConverter
from obsidian_converter.config import ObsidianConverterConfig


class TestObsidianConverter(unittest.TestCase):
    """Test the ObsidianConverter class"""
    
    def setUp(self):
        """Set up for tests"""
        self.temp_input_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()
        
        # Create a test config
        self.config = ObsidianConverterConfig()
        self.config.input_dir = self.temp_input_dir
        self.config.output_dir = self.temp_output_dir
        self.config.use_cache = False  # Don't use cache for tests
        
        # Create test files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directories and their contents
        for directory in [self.temp_input_dir, self.temp_output_dir]:
            for root, _, files in os.walk(directory, topdown=False):
                for file in files:
                    os.unlink(os.path.join(root, file))
                os.rmdir(root)
    
    def create_test_files(self):
        """Create test files for conversion"""
        # Create a simple test file
        test_file1 = os.path.join(self.temp_input_dir, "test1.txt")
        with open(test_file1, "w") as f:
            f.write("# Test Document\n\n## Section 1\nThis is some content.\n\n## Section 2\nMore content here.")
        
        # Create a subdirectory with another test file
        subdir = os.path.join(self.temp_input_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        test_file2 = os.path.join(subdir, "test2.txt")
        with open(test_file2, "w") as f:
            f.write("# Another Document\n\n## Subsection\nSome more test content.")
    
    @patch('obsidian_converter.llm.ContentProcessor')
    def test_find_text_files(self, mock_processor):
        """Test finding text files in directories"""
        converter = ObsidianConverter(config=self.config)
        
        # Should find both test files
        files = converter.find_text_files()
        self.assertEqual(len(files), 2)
        
        # Check both expected files are found
        file_basenames = [os.path.basename(f) for f in files]
        self.assertIn("test1.txt", file_basenames)
        self.assertIn("test2.txt", file_basenames)
    
    @patch('obsidian_converter.llm.ContentProcessor')
    def test_file_pattern_filtering(self, mock_processor):
        """Test file pattern filtering"""
        # Create a non-txt file that should be excluded
        excluded_file = os.path.join(self.temp_input_dir, "excluded.log")
        with open(excluded_file, "w") as f:
            f.write("This should be excluded")
        
        # Configure patterns
        self.config.include_patterns = ["*.txt"]
        self.config.exclude_patterns = ["*2.txt"]  # Exclude test2.txt
        
        converter = ObsidianConverter(config=self.config)
        files = converter.find_text_files()
        
        # Should find only test1.txt
        self.assertEqual(len(files), 1)
        self.assertEqual(os.path.basename(files[0]), "test1.txt")
    
    @patch('obsidian_converter.llm.ContentProcessor')
    def test_generate_frontmatter(self, mock_processor):
        """Test frontmatter generation"""
        converter = ObsidianConverter(config=self.config)
        
        frontmatter = converter.generate_frontmatter("Test Title", ["tag1", "tag2"], "Category")
        
        # Check frontmatter structure
        self.assertIn('title: "Test Title"', frontmatter)
        self.assertIn('tags: ["tag1", "tag2"]', frontmatter)
        self.assertIn('category: Category', frontmatter)
        self.assertIn('created:', frontmatter)
        self.assertIn('modified:', frontmatter)
    
    @patch('obsidian_converter.converter.ObsidianConverter.process_file')
    @patch('obsidian_converter.llm.ContentProcessor')
    def test_run_sequential(self, mock_processor, mock_process_file):
        """Test running the converter in sequential mode"""
        # Configure to use sequential mode
        self.config.parallel_processing = False
        
        # Set up mock return value
        mock_process_file.return_value = ["note1.md", "note2.md"]
        
        converter = ObsidianConverter(config=self.config)
        notes_count = converter.run()
        
        # Should have processed 2 files, each generating 2 notes
        self.assertEqual(mock_process_file.call_count, 2)
        self.assertEqual(notes_count, 4)
    
    @patch('obsidian_converter.llm.ContentProcessor')
    def test_suggest_links(self, mock_processor):
        """Test suggesting links between notes"""
        converter = ObsidianConverter(config=self.config)
        
        # Add some test notes
        converter.existing_notes = {
            "note1.md": ("Title 1", "This is about programming and python"),
            "note2.md": ("Title 2", "This is about cooking recipes"),
            "note3.md": ("Title 3", "More about python programming")
        }
        
        # Test finding related notes
        links = converter.suggest_links("I'm learning python programming")
        self.assertEqual(len(links), 2)  # Should find note1 and note3
        
        # Titles should be in the results
        titles = [title for title, _ in links]
        self.assertIn("Title 1", titles)
        self.assertIn("Title 3", titles)
        
        # Test with unrelated content
        unrelated_links = converter.suggest_links("This is about astronomy")
        self.assertEqual(len(unrelated_links), 0)


if __name__ == "__main__":
    unittest.main()