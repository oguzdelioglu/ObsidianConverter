#!/usr/bin/env python3
import json
import os
import re
import tiktoken
from datetime import datetime

def num_tokens_from_string(string, encoding_name="cl100k_base"):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def format_number(num):
    """Format number with commas as thousands separator"""
    return f"{num:,}"

def clean_string_for_display(text, max_length=100):
    """Clean and truncate a string for display purposes"""
    if not text:
        return ""
    # Replace newlines with spaces
    text = re.sub(r'\s+', ' ', text)
    # Truncate if too long
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

# Load the cache file
cache_file = ".llm_cache.json"

print(f"Loading cache from {cache_file}...")
if not os.path.exists(cache_file):
    print(f"Error: Cache file {cache_file} not found")
    exit(1)

with open(cache_file, "r", encoding="utf-8") as f:
    try:
        cache = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not parse {cache_file} as JSON")
        exit(1)

# Initialize counters
total_prompts = len(cache)
total_input_tokens = 0
total_output_tokens = 0
total_tokens = 0
longest_response = 0
longest_response_content = ""
longest_response_key = ""

# Calculate tokens for each cache entry
print("Calculating token usage...")
entries = []
for key, response in cache.items():
    # In this cache format, the value is directly the response string
    response_tokens = num_tokens_from_string(response)
    
    if response_tokens > longest_response:
        longest_response = response_tokens
        longest_response_content = response
        longest_response_key = key
    
    # Get a snippet of the response for preview
    response_preview = clean_string_for_display(response)
    
    total_output_tokens += response_tokens
    
    entries.append({
        "key": key,
        "response_preview": response_preview,
        "output_tokens": response_tokens,
        "response": response
    })

# Sort entries by total tokens (highest first)
entries.sort(key=lambda x: x["output_tokens"], reverse=True)
total_tokens = total_output_tokens

# Create the log file
log_file = "details.log"
print(f"Writing results to {log_file}...")

with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"# ObsidianConverter LLM Token Usage Report\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write(f"## Summary\n")
    f.write(f"Total cached responses: {total_prompts}\n")
    f.write(f"Total output tokens: {format_number(total_output_tokens)}\n\n")
    
    # Calculate cost estimate based on different models
    ollama_cost = 0  # Free for local compute
    gpt35_output_cost = total_output_tokens * 0.000002  # $0.002 per 1K tokens
    gpt4_output_cost = total_output_tokens * 0.00006  # $0.06 per 1K tokens
    gpt4o_mini_output_cost = total_output_tokens * 0.0006 / 1000  # $0.0006 per 1K tokens
    claude_output_cost = total_output_tokens * 0.00003  # $0.03 per 1K tokens (approximate)
    
    f.write(f"## Estimated Costs (Output Only)\n")
    f.write(f"- Ollama (local): Free (compute costs only)\n")
    f.write(f"- OpenAI GPT-3.5: ${gpt35_output_cost:.2f} (at $0.002 per 1K tokens)\n")
    f.write(f"- OpenAI GPT-4: ${gpt4_output_cost:.2f} (at $0.06 per 1K tokens)\n")
    f.write(f"- OpenAI GPT-4o-mini: ${gpt4o_mini_output_cost:.2f} (at $0.0006 per 1K tokens)\n")
    f.write(f"- Anthropic Claude: ${claude_output_cost:.2f} (at $0.03 per 1K tokens)\n\n")
    
    f.write(f"## Token Distribution by Response Size\n")
    
    # Calculate response size distribution
    size_ranges = {
        "small (< 500 tokens)": 0,
        "medium (500-1000 tokens)": 0, 
        "large (1000-1500 tokens)": 0,
        "very large (>1500 tokens)": 0
    }
    
    for entry in entries:
        tokens = entry["output_tokens"]
        if tokens < 500:
            size_ranges["small (< 500 tokens)"] += 1
        elif tokens < 1000:
            size_ranges["medium (500-1000 tokens)"] += 1
        elif tokens < 1500:
            size_ranges["large (1000-1500 tokens)"] += 1
        else:
            size_ranges["very large (>1500 tokens)"] += 1
    
    for size_range, count in size_ranges.items():
        percentage = (count / total_prompts) * 100
        f.write(f"- {size_range}: {count} responses ({percentage:.1f}%)\n")
    
    f.write(f"\n## Response Statistics\n")
    f.write(f"- Longest response: {format_number(longest_response)} tokens\n")
    f.write(f"- Average response: {format_number(total_output_tokens // total_prompts)} tokens\n\n")
    
    f.write(f"## Longest Response Sample (First 300 characters)\n")
    f.write(f"```\n{longest_response_content[:300]}...\n```\n\n")
    
    f.write(f"## Top 10 Token-Heavy Responses\n")
    f.write(f"| # | Tokens | Response Preview |\n")
    f.write(f"|---|--------|------------------|\n")
    
    for i, entry in enumerate(entries[:10]):
        preview = clean_string_for_display(entry["response"], 60)
        f.write(f"| {i+1} | {entry['output_tokens']} | {preview} |\n")
    
    # Content categories analysis - looking for patterns in responses
    f.write(f"\n## Content Analysis\n")
    
    # Check for notes with common indicators
    has_frontmatter = 0
    has_code_blocks = 0
    has_links = 0
    has_headings = 0
    
    for entry in entries:
        response = entry["response"]
        if "---\ntitle:" in response:
            has_frontmatter += 1
        if "```" in response:
            has_code_blocks += 1
        if "[[" in response or "](https://" in response:
            has_links += 1
        if re.search(r"^#+\s+", response, re.MULTILINE):
            has_headings += 1
    
    f.write(f"- Responses with frontmatter: {has_frontmatter} ({has_frontmatter/total_prompts*100:.1f}%)\n")
    f.write(f"- Responses with code blocks: {has_code_blocks} ({has_code_blocks/total_prompts*100:.1f}%)\n")
    f.write(f"- Responses with links: {has_links} ({has_links/total_prompts*100:.1f}%)\n")
    f.write(f"- Responses with headings: {has_headings} ({has_headings/total_prompts*100:.1f}%)\n")

# Write a CSV with detailed info for further analysis
csv_file = "token_details.csv"
with open(csv_file, "w", encoding="utf-8") as f:
    f.write("ID,Tokens,PreviewText\n")
    for i, entry in enumerate(entries):
        preview = entry["response_preview"].replace('"', '""')  # Escape double quotes for CSV
        f.write(f"{i+1},{entry['output_tokens']},\"{preview}\"\n")

print(f"Analysis complete!")
print(f"Total LLM usage: {format_number(total_output_tokens)} output tokens")
print(f"Detailed report written to {log_file}")
print(f"CSV data written to {csv_file}")