"""
Tests for utility functions in ObsidianConverter
"""
import os
import tempfile
import unittest
from pathlib import Path

from obsidian_converter.utils.text import slugify, content_hash
from obsidian_converter.utils.performance import split_text_by_size, chunked_read


class TestTextUtils(unittest.TestCase):
    """Test text utility functions"""
    
    def test_slugify(self):
        """Test the slugify function"""
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("This is a Test!"), "this-is-a-test-")
        self.assertEqual(slugify("  Spaces  "), "spaces")
        
        # Test long strings get truncated
        long_string = "a" * 100
        self.assertEqual(len(slugify(long_string)), 60)
    
    def test_content_hash(self):
        """Test the content_hash function"""
        # Same content should produce same hash
        content1 = "This is some content"
        content2 = "This is some content"
        self.assertEqual(content_hash(content1), content_hash(content2))
        
        # Different content should produce different hash
        content3 = "This is different content"
        self.assertNotEqual(content_hash(content1), content_hash(content3))


class TestPerformanceUtils(unittest.TestCase):
    """Test performance utility functions"""
    
    def test_split_text_by_size(self):
        """Test text splitting function"""
        # Short text shouldn't be split
        short_text = "This is a short text"
        self.assertEqual(split_text_by_size(short_text, 100), [short_text])
        
        # Longer text should be split
        long_text = "This is a longer text. " * 20  # ~400 chars
        chunks = split_text_by_size(long_text, 100)
        self.assertTrue(len(chunks) > 1)
        self.assertTrue(all(len(chunk) <= 100 for chunk in chunks))
        
        # Combined chunks should equal original (except for potential whitespace differences)
        self.assertEqual("".join(chunks).strip(), long_text.strip())
    
    def test_chunked_read(self):
        """Test chunked file reading"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            # Write some content
            content = "Line 1\nLine 2\nLine 3\n" * 100
            temp.write(content)
            temp_path = temp.name
        
        try:
            # Read in chunks
            chunks = list(chunked_read(temp_path, chunk_size=100))
            # Should have multiple chunks
            self.assertTrue(len(chunks) > 1)
            
            # Combined chunks should equal original content
            self.assertEqual("".join(chunks), content)
            
            # Test with very large chunk size (should read entire file)
            big_chunks = list(chunked_read(temp_path, chunk_size=1000000))
            self.assertEqual(len(big_chunks), 1)
            self.assertEqual(big_chunks[0], content)
        finally:
            # Clean up
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()