"""
Performance utilities for processing large files and parallel execution
"""
import os
import time
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Callable, TypeVar, Iterable, Dict, Any, Tuple, Iterator

logger = logging.getLogger("obsidian_converter")

T = TypeVar('T')
R = TypeVar('R')

def chunked_read(file_path: str, chunk_size: int = 1000000) -> Iterator[str]:
    """
    Read a large file in chunks to avoid memory issues
    
    Args:
        file_path: Path to the file
        chunk_size: Size of each chunk in bytes
        
    Yields:
        File content chunks
    """
    file_size = os.path.getsize(file_path)
    
    if file_size <= chunk_size:
        # File is small enough to read entirely
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            yield f.read()
    else:
        # Read file in chunks
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk = f.read(chunk_size)
            while chunk:
                yield chunk
                chunk = f.read(chunk_size)

def execute_in_parallel(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int = None,
    desc: str = "Processing"
) -> List[R]:
    """
    Execute a function on multiple items in parallel
    
    Args:
        func: Function to execute
        items: Items to process
        max_workers: Maximum number of worker processes
        desc: Description for logging
        
    Returns:
        List of results
    """
    if max_workers is None:
        # Use CPU count but at least 2 and at most 8 workers
        max_workers = min(max(multiprocessing.cpu_count(), 2), 8)
    
    results = []
    item_count = 0
    try:
        # Try to get length if possible
        item_count = len(list(items))
    except:
        pass
    
    if item_count:
        logger.info(f"{desc} {item_count} items with {max_workers} workers")
    else:
        logger.info(f"{desc} items with {max_workers} workers")
    
    start_time = time.time()
    
    # Using ProcessPoolExecutor for true parallelism
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(func, item): item for item in items}
        
        completed = 0
        # Process results as they complete
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                # Log progress
                if item_count and completed % max(1, item_count // 10) == 0:
                    progress = (completed / item_count) * 100
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    logger.info(f"Progress: {progress:.1f}% ({completed}/{item_count}), {rate:.2f} items/sec")
                    
            except Exception as e:
                logger.error(f"Error processing item {item}: {e}")
    
    # Log completion
    elapsed = time.time() - start_time
    logger.info(f"Completed {desc.lower()} {completed} items in {elapsed:.2f} seconds")
    
    return results

def split_text_by_size(text: str, max_size: int = 10000) -> List[str]:
    """
    Split large text into smaller chunks for processing
    
    Args:
        text: The text to split
        max_size: Maximum size in characters
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    current_pos = 0
    text_len = len(text)
    
    while current_pos < text_len:
        # Try to find a natural break
        chunk_end = min(current_pos + max_size, text_len)
        
        # If not at the end, find a good break point
        if chunk_end < text_len:
            # Find the next paragraph or sentence break
            paragraph_break = text.rfind('\n\n', current_pos, chunk_end)
            sentence_break = text.rfind('. ', current_pos, chunk_end)
            
            if paragraph_break > current_pos + max_size // 2:
                # Good paragraph break
                chunk_end = paragraph_break + 2
            elif sentence_break > current_pos + max_size // 2:
                # Good sentence break
                chunk_end = sentence_break + 2
            else:
                # No good break found, fall back to word boundary
                word_break = text.rfind(' ', current_pos + max_size // 2, chunk_end)
                if word_break > current_pos:
                    chunk_end = word_break + 1
        
        chunks.append(text[current_pos:chunk_end])
        current_pos = chunk_end
    
    return chunks