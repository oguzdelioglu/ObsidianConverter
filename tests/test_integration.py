"""
Integration tests for ObsidianConverter
"""
import os
import tempfile
import unittest
import shutil
from pathlib import Path

from obsidian_converter.converter import ObsidianConverter
from obsidian_converter.config import ObsidianConverterConfig


class TestIntegration(unittest.TestCase):
    """Integration tests for full conversion process"""
    
    def setUp(self):
        """Set up for tests"""
        self.temp_input_dir = tempfile.mkdtemp()
        self.temp_output_dir = tempfile.mkdtemp()
        
        # Create a test config
        self.config = ObsidianConverterConfig()
        self.config.input_dir = self.temp_input_dir
        self.config.output_dir = self.temp_output_dir
        self.config.use_cache = False  # Don't use cache for tests
        self.config.model = "mistral"  # Use mistral model (or whatever is available)
        
        # For integration tests, we'll typically need to check if Ollama is running
        # This can be done via a simple API call before running tests
        self.ollama_available = self.check_ollama_available()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directories
        for directory in [self.temp_input_dir, self.temp_output_dir]:
            shutil.rmtree(directory, ignore_errors=True)
    
    def check_ollama_available(self):
        """Check if Ollama service is available"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @unittest.skipIf(not os.environ.get("RUN_INTEGRATION_TESTS"), "Skipping integration tests")
    def test_basic_conversion_flow(self):
        """Test the basic conversion flow with a simple input file"""
        if not self.ollama_available:
            self.skipTest("Ollama service not available")
        
        # Create a simple test file
        test_file = os.path.join(self.temp_input_dir, "integration_test.txt")
        with open(test_file, "w") as f:
            f.write("""# Meeting Notes

## Project Update
We discussed the timeline for the project completion.
Key points:
- Milestone 1 is complete
- Milestone 2 needs more work
- Final delivery date is unchanged

## Action Items
- John will update the documentation
- Mary will complete the testing
- Sam will prepare the presentation
""")
        
        # Run the converter
        converter = ObsidianConverter(config=self.config)
        notes_count = converter.run()
        
        # Should have created at least one note
        self.assertGreater(notes_count, 0)
        
        # Check if output directory contains markdown files
        md_files = list(Path(self.temp_output_dir).glob("**/*.md"))
        self.assertGreater(len(md_files), 0)
        
        # Check content of created files
        for md_file in md_files:
            with open(md_file, "r") as f:
                content = f.read()
                # Should contain frontmatter
                self.assertIn("---", content)
                self.assertIn("title:", content)
                self.assertIn("tags:", content)
                self.assertIn("date:", content)
    
    @unittest.skipIf(not os.environ.get("RUN_INTEGRATION_TESTS"), "Skipping integration tests")
    def test_category_organization(self):
        """Test that notes are organized into categories"""
        if not self.ollama_available:
            self.skipTest("Ollama service not available")
        
        # Create a test file with clearly categorized content
        test_file = os.path.join(self.temp_input_dir, "categories_test.txt")
        with open(test_file, "w") as f:
            f.write("""# Mixed Content Document

## Project Management Notes
This section contains project management information.
- Timeline planning
- Resource allocation
- Milestone tracking

## Technical Design Notes
This section contains technical design details.
- Architecture overview
- Component design
- API specifications
""")
        
        # Run the converter
        converter = ObsidianConverter(config=self.config)
        converter.run()
        
        # Check if categories were created
        directories = [d for d in os.listdir(self.temp_output_dir) 
                      if os.path.isdir(os.path.join(self.temp_output_dir, d))]
        
        # Should have created at least one category directory
        self.assertGreater(len(directories), 0)
        
        # Check files within categories
        for directory in directories:
            dir_path = os.path.join(self.temp_output_dir, directory)
            files = os.listdir(dir_path)
            self.assertGreater(len(files), 0)
            
            # Check that files in this directory are markdown
            for file in files:
                self.assertTrue(file.endswith(".md"))


if __name__ == "__main__":
    unittest.main()