#!/usr/bin/env python3
import requests
import json
import time
import tiktoken
import sys

BASE_URL = "http://localhost:5000"
enc = tiktoken.get_encoding("cl100k_base")

def print_header(title):
    print("\n" + "="*60)
    print(f" 🚀 {title}")
    print("="*60)

def count_tokens(text):
    return len(enc.encode(text))

def run_test_scenario(name, endpoint, headers, expected_intent=None):
    print(f"\n--- Scenario: {name} ---")
    print(f"URL: {BASE_URL}{endpoint}")
    print(f"Headers: {json.dumps(headers)}")
    
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Is app.py running?")
        sys.exit(1)
        
    duration = time.time() - start
    
    print(f"Status Code: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Vary Header: {resp.headers.get('Vary')}")
    print(f"Response Time: {duration*1000:.2f}ms")
    
    text = resp.text
    tokens = count_tokens(text)
    size_kb = len(text.encode('utf-8')) / 1024
    print(f"Payload Size: {size_kb:.2f} KB ({tokens} tokens)")
    
    if "application/vnd.m2a+json" in resp.headers.get("Content-Type", ""):
        data = resp.json()
        print(f"Parsed JSON keys: {list(data.keys())}")
        if "intent" in data:
            print(f"Detected Intent: {data['intent'].get('classified_as')}")
            if expected_intent and data['intent'].get('classified_as') != expected_intent:
                print(f"⚠️  WARNING: Expected {expected_intent} but got {data['intent'].get('classified_as')}")
        if "payment" in data:
            print(f"Payment Link: {data['payment'].get('payment_link_url', 'Error generating link')}")
        if "token_savings" in data:
            print(f"Server-reported Savings: {data['token_savings']}")
    else:
        print("Response Snippet:")
        print(text[:200].replace('\n', ' ') + "...")
        
    return tokens

def main():
    print_header("M2A Dual-Reality Server Test Harness")
    
    # 1. Human Request
    human_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    human_tokens = run_test_scenario(
        "Human Browser (Product Page)", 
        "/product/prod_001", 
        human_headers
    )
    
    # 2. Agent BUY Request
    agent_buy_headers = {
        "User-Agent": "OpenAI/GPT-4",
        "Accept": "application/vnd.m2a+json",
        "Signature-Agent": "1"
    }
    agent_buy_tokens = run_test_scenario(
        "Agent - BUY Intent (Explicit)", 
        "/product/prod_001?intent=BUY", 
        agent_buy_headers,
        expected_intent="BUY"
    )
    
    # 3. Agent STOCK Request
    agent_stock_tokens = run_test_scenario(
        "Agent - STOCK Intent (Natural Language)", 
        "/product/prod_001?query=Do you have this in stock?", 
        agent_buy_headers,
        expected_intent="STOCK"
    )

    # 4. Agent SPECS Request
    agent_specs_tokens = run_test_scenario(
        "Agent - SPECS Intent (Natural Language)", 
        "/product/prod_001?query=how heavy are these?", 
        agent_buy_headers,
        expected_intent="SPECS"
    )
    
    # Summary
    print_header("Token Payload Comparison")
    print(f"Human HTML Payload: {human_tokens} tokens")
    print(f"Agent BUY Payload:  {agent_buy_tokens} tokens (saved {(1 - agent_buy_tokens/human_tokens)*100:.1f}%)")
    print(f"Agent STOCK Payload: {agent_stock_tokens} tokens (saved {(1 - agent_stock_tokens/human_tokens)*100:.1f}%)")
    print(f"Agent SPECS Payload: {agent_specs_tokens} tokens (saved {(1 - agent_specs_tokens/human_tokens)*100:.1f}%)")
    print("\n✅ Harness execution complete.")

if __name__ == "__main__":
    main()
