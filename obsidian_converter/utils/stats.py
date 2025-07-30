"""
Statistics tracking for ObsidianConverter
"""
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("obsidian_converter")

class ConversionStats:
    """Track and report statistics about the conversion process"""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
        # Counts
        self.processed_files = 0
        self.created_notes = 0
        self.failed_files = 0
        
        # Categorization
        self.categories: Dict[str, int] = {}
        
        # Tag statistics
        self.tags: Dict[str, int] = {}
        
        # Content statistics
        self.total_words = 0
        self.total_characters = 0
        
        # Performance metrics
        self.llm_time = 0.0
        self.llm_calls = 0
        self.llm_cache_hits = 0
        self.llm_cache_misses = 0
        
    def record_processed_file(self):
        """Increment processed files counter"""
        self.processed_files += 1
        
    def record_created_note(self, category: Optional[str] = None, tags: Optional[List[str]] = None,
                           word_count: int = 0, char_count: int = 0):
        """
        Record a successfully created note
        
        Args:
            category: The note's category
            tags: List of tags for the note
            word_count: Number of words in the note
            char_count: Number of characters in the note
        """
        self.created_notes += 1
        
        # Record category
        if category:
            self.categories[category] = self.categories.get(category, 0) + 1
        
        # Record tags
        if tags:
            for tag in tags:
                self.tags[tag] = self.tags.get(tag, 0) + 1
        
        # Record content statistics
        self.total_words += word_count
        self.total_characters += char_count
    
    def record_failed_file(self):
        """Increment failed files counter"""
        self.failed_files += 1
    
    def record_llm_call(self, duration: float, cache_hit: bool = False):
        """
        Record an LLM call
        
        Args:
            duration: Duration of the call in seconds
            cache_hit: Whether the call was served from cache
        """
        self.llm_calls += 1
        
        if cache_hit:
            self.llm_cache_hits += 1
        else:
            self.llm_cache_misses += 1
            self.llm_time += duration
    
    def finish(self):
        """Mark the end of processing"""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """Get the total processing duration in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def average_llm_time(self) -> float:
        """Get the average LLM call duration"""
        if self.llm_cache_misses > 0:
            return self.llm_time / self.llm_cache_misses
        return 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Get the LLM cache hit rate as a percentage"""
        if self.llm_calls > 0:
            return (self.llm_cache_hits / self.llm_calls) * 100
        return 0
    
    @property
    def most_common_category(self) -> Optional[str]:
        """Get the most common category"""
        if not self.categories:
            return None
        return max(self.categories.items(), key=lambda x: x[1])[0]
    
    @property
    def most_common_tags(self) -> List[str]:
        """Get the top 5 most common tags"""
        if not self.tags:
            return []
        sorted_tags = sorted(self.tags.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in sorted_tags[:5]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to a dictionary"""
        end = self.end_time or time.time()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': self.duration,
            'processed_files': self.processed_files,
            'created_notes': self.created_notes,
            'failed_files': self.failed_files,
            'categories': self.categories,
            'tags': self.tags,
            'content': {
                'total_words': self.total_words,
                'total_characters': self.total_characters,
                'average_words_per_note': self.total_words / max(1, self.created_notes)
            },
            'performance': {
                'llm_calls': self.llm_calls,
                'llm_cache_hits': self.llm_cache_hits,
                'llm_cache_hit_rate': self.cache_hit_rate,
                'average_llm_time': self.average_llm_time
            }
        }
    
    def save_report(self, output_dir: str) -> str:
        """
        Save statistics report to a JSON file
        
        Args:
            output_dir: Directory to save the report
            
        Returns:
            Path to the saved report
        """
        stats_dir = Path(output_dir) / ".stats"
        os.makedirs(stats_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = stats_dir / f"conversion_stats_{timestamp}.json"
        
        try:
            with open(report_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            
            logger.info(f"Statistics report saved to {report_path}")
            return str(report_path)
        except Exception as e:
            logger.error(f"Failed to save statistics report: {e}")
            return ""
    
    def print_summary(self):
        """Print a summary of the statistics"""
        duration_min = self.duration / 60
        
        summary = [
            f"Conversion completed in {duration_min:.2f} minutes",
            f"Processed {self.processed_files} files, created {self.created_notes} notes",
            f"Failed files: {self.failed_files}",
            f"Top categories: {', '.join([f'{cat} ({count})' for cat, count in sorted(self.categories.items(), key=lambda x: x[1], reverse=True)[:3]])}",
            f"Top tags: {', '.join(self.most_common_tags)}",
            f"Total content: {self.total_words} words, {self.total_characters} characters",
            f"LLM performance: {self.llm_calls} calls, {self.cache_hit_rate:.1f}% cache hit rate, {self.average_llm_time:.2f}s average time"
        ]
        
        print("\n=== Conversion Summary ===")
        for line in summary:
            print(line)
        print("==========================")