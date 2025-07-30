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
total_prompts = 0
total_input_tokens = 0
total_output_tokens = 0
total_tokens = 0
longest_prompt = 0
longest_response = 0
longest_prompt_key = ""
longest_response_key = ""

# Calculate tokens for each cache entry
print("Calculating token usage...")
entries = []
for key, value in cache.items():
    # Handle the case where the value is directly the response string
    if isinstance(value, str):
        prompt = "Unknown (cached response only)"
        response = value
        prompt_tokens = 0  # We don't have the original prompt
    else:
        # Handle the case where value is a dictionary with prompt and response
        prompt = value.get("prompt", "")
        response = value.get("response", "")
    
    prompt_tokens = num_tokens_from_string(prompt) if prompt != "Unknown (cached response only)" else 0
    response_tokens = num_tokens_from_string(response)
    
    if prompt_tokens > longest_prompt:
        longest_prompt = prompt_tokens
        longest_prompt_key = key
        
    if response_tokens > longest_response:
        longest_response = response_tokens
        longest_response_key = key
    
    # Extract the first 50 characters of the prompt for identification
    if prompt != "Unknown (cached response only)":
        prompt_preview = prompt[:50].replace('\n', ' ') + "..."
    else:
        prompt_preview = "Unknown (cached response only)"
    
    total_prompts += 1
    total_input_tokens += prompt_tokens
    total_output_tokens += response_tokens
    
    entries.append({
        "prompt_preview": prompt_preview,
        "input_tokens": prompt_tokens,
        "output_tokens": response_tokens,
        "total_tokens": prompt_tokens + response_tokens
    })

# Sort entries by total tokens (highest first)
entries.sort(key=lambda x: x["total_tokens"], reverse=True)
total_tokens = total_input_tokens + total_output_tokens

# Create the log file
log_file = "details.log"
print(f"Writing results to {log_file}...")

with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"# ObsidianConverter LLM Token Usage Report\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write(f"## Summary\n")
    f.write(f"Total cached prompts/responses: {total_prompts}\n")
    f.write(f"Total input tokens: {format_number(total_input_tokens)}\n")
    f.write(f"Total output tokens: {format_number(total_output_tokens)}\n")
    f.write(f"Total combined tokens: {format_number(total_tokens)}\n\n")
    
    # Only calculate cost if we have input tokens (i.e., if prompts were stored)
    if total_input_tokens > 0:
        # Cost estimates (using OpenAI GPT-4 rates as reference)
        input_cost = total_input_tokens * 0.00003  # $0.03 per 1K tokens
        output_cost = total_output_tokens * 0.00006  # $0.06 per 1K tokens
        gpt4o_mini_input_cost = total_input_tokens * 0.00015 / 1000  # $0.00015 per 1K tokens
        gpt4o_mini_output_cost = total_output_tokens * 0.0006 / 1000  # $0.0006 per 1K tokens
        total_cost = input_cost + output_cost
        gpt4o_mini_total_cost = gpt4o_mini_input_cost + gpt4o_mini_output_cost
        
        f.write(f"## Estimated Costs (based on GPT-4 pricing)\n")
        f.write(f"Input cost: ${input_cost:.2f} (at $0.03 per 1K tokens)\n")
        f.write(f"Output cost: ${output_cost:.2f} (at $0.06 per 1K tokens)\n")
        f.write(f"Total cost: ${total_cost:.2f}\n\n")
        
        f.write(f"## Estimated Costs (based on GPT-4o-mini pricing)\n")
        f.write(f"Input cost: ${gpt4o_mini_input_cost:.2f} (at $0.00015 per 1K tokens)\n")
        f.write(f"Output cost: ${gpt4o_mini_output_cost:.2f} (at $0.0006 per 1K tokens)\n")
        f.write(f"Total cost: ${gpt4o_mini_total_cost:.2f}\n\n")
    else:
        # For cache with only responses, estimate cost based on Ollama model (local)
        f.write(f"## Estimated Costs\n")
        f.write(f"Note: The cache only contains responses, not prompts. Cost calculations would be incomplete.\n")
        f.write(f"For reference, if using a local model like Ollama, costs would be primarily compute resources.\n")
        f.write(f"If using OpenAI GPT-4, output costs alone would be approximately ${total_output_tokens * 0.00006:.2f}.\n")
        f.write(f"If using OpenAI GPT-4o-mini, output costs alone would be approximately ${total_output_tokens * 0.0006 / 1000:.2f}.\n\n")
    
    f.write(f"## Response Statistics\n")
    f.write(f"Longest response: {format_number(longest_response)} tokens\n\n")
    
    if total_input_tokens > 0:
        f.write(f"Longest prompt: {format_number(longest_prompt)} tokens\n\n")
        f.write(f"## Token Distribution\n")
        f.write(f"Input tokens: {total_input_tokens} ({total_input_tokens/total_tokens*100:.1f}%)\n")
        f.write(f"Output tokens: {total_output_tokens} ({total_output_tokens/total_tokens*100:.1f}%)\n")
        f.write(f"Input/Output ratio: {total_input_tokens/total_output_tokens if total_output_tokens > 0 else 0:.2f}\n\n")
    
    f.write(f"## Top 10 Token-Heavy Responses\n")
    if total_input_tokens > 0:
        f.write(f"{'Prompt Preview':<55} {'Input':<10} {'Output':<10} {'Total':<10}\n")
        f.write(f"{'-'*55} {'-'*10} {'-'*10} {'-'*10}\n")
    else:
        f.write(f"{'Response Preview':<55} {'Output Tokens':<15}\n")
        f.write(f"{'-'*55} {'-'*15}\n")
    
    for i, entry in enumerate(entries[:10]):
        if total_input_tokens > 0:
            f.write(f"{entry['prompt_preview']:<55} {entry['input_tokens']:<10} {entry['output_tokens']:<10} {entry['total_tokens']:<10}\n")
        else:
            response_preview = entry['prompt_preview'][:50] if entry['prompt_preview'] != "Unknown (cached response only)" else "Response " + str(i+1)
            f.write(f"{response_preview:<55} {entry['output_tokens']:<15}\n")
    
print(f"Analysis complete!")
print(f"Total LLM usage: {format_number(total_input_tokens)} input tokens, {format_number(total_output_tokens)} output tokens")
print(f"Detailed report written to {log_file}")