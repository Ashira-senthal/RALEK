#!/usr/bin/env python3
import requests
import json
import time
import tiktoken
from html.parser import HTMLParser

BASE_URL = "http://localhost:5000"
enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(enc.encode(text))

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.result.append(text)
    def get_text(self):
        return ' '.join(self.result)

def simulate_llm_processing(prompt_text, target_keyword):
    """Simulates an LLM 'reading' context to find an answer."""
    start_time = time.time()
    # Fake processing time proportional to token length (e.g., 0.5ms per token context reading)
    tokens = count_tokens(prompt_text)
    processing_delay = tokens * 0.0005 
    time.sleep(processing_delay)
    
    found = target_keyword.lower() in prompt_text.lower()
    duration = time.time() - start_time
    return tokens, duration, found

def print_box(title):
    print("\n" + "="*70)
    print(f" 🤖 {title}")
    print("="*70)

def main():
    print_box("SCENARIO: AI Agent wants to find out if 'AuraX Pro' is in stock.")
    product_url = f"{BASE_URL}/product/prod_001"
    
    # ---------------------------------------------------------
    # 1. TRADITIONAL APPROACH (Without Middleware)
    # ---------------------------------------------------------
    print("\n❌ TRADITIONAL AGENT (No Middleware)")
    print("Action: Fetching standard URL like a human browser...")
    
    # Fetch HTML
    http_start = time.time()
    resp_html = requests.get(product_url, headers={"User-Agent": "Mozilla/5.0"})
    http_end = time.time()
    
    html_text = resp_html.text
    html_size = len(html_text.encode('utf-8')) / 1024
    
    # "Agent" parses HTML
    extractor = HTMLTextExtractor()
    extractor.feed(html_text)
    extracted_text = extractor.get_text()
    
    # "Agent" processes context
    print(f"Network Latency: {(http_end - http_start)*1000:.1f}ms")
    print(f"Payload Received: {html_size:.2f} KB of HTML")
    print("Agent is reading the DOM context to find stock info...")
    
    tokens_html, process_time_html, _ = simulate_llm_processing(extracted_text, "stock")
    
    print(f"Context size: {tokens_html} tokens consumed.")
    print(f"LLM Processing Time: {process_time_html:.2f} seconds.")
    print(f"Total Token Cost (Input @ $5/1M): ${(tokens_html / 1000000) * 5:.5f}")


    # ---------------------------------------------------------
    # 2. M2A APPROACH (With Middleware)
    # ---------------------------------------------------------
    print_box("✅ M2A AGENT (With Middleware)")
    print("Action: Fetching URL with Agent Headers and Natural Language query...")
    
    # Fetch JSON via content negotiation
    http_start = time.time()
    headers = {
        "Signature-Agent": "1",
        "Accept": "application/vnd.m2a+json"
    }
    # Pass natural language intent
    resp_json = requests.get(f"{product_url}?query=is this in stock?", headers=headers)
    http_end = time.time()
    
    json_text = resp_json.text
    json_size = len(json_text.encode('utf-8')) / 1024
    
    print(f"Network Latency: {(http_end - http_start)*1000:.1f}ms")
    print(f"Payload Received: {json_size:.2f} KB of Pruned JSON")
    print(f"Server classified intent as: {resp_json.json()['intent']['classified_as']}")
    print("Agent is reading the JSON context...")
    
    # "Agent" processes context
    tokens_json, process_time_json, _ = simulate_llm_processing(json_text, "stock")
    
    print(f"Context size: {tokens_json} tokens consumed.")
    print(f"LLM Processing Time: {process_time_json:.2f} seconds.")
    print(f"Total Token Cost (Input @ $5/1M): ${(tokens_json / 1000000) * 5:.5f}")


    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------
    print_box("📊 PERFORMANCE COMPARISON")
    token_reduction = (1 - (tokens_json / tokens_html)) * 100
    speed_increase = process_time_html / process_time_json
    
    print(f"Tokens Saved:      {tokens_html - tokens_json} tokens per request (-{token_reduction:.1f}%)")
    print(f"Speed Multiplier:  {speed_increase:.1f}x faster LLM processing")
    print(f"Bandwidth Saved:   {html_size - json_size:.2f} KB per request")
    print("\nCONCLUSION: The M2A middleware completely eliminates the HTML DOM noise,")
    print("allowing the AI to execute actions faster, cheaper, and more reliably.")

if __name__ == "__main__":
    main()
