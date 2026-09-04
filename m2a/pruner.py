"""
M2A Semantic Pruning Engine

This module is responsible for taking a heavy, rich e-commerce product dictionary
and stripping it down to only the fields relevant to the agent's specific intent.

By pruning irrelevant data (e.g., stripping reviews and heavy descriptions when 
the agent only wants to check stock), we drastically reduce the token payload 
sent to the agent, solving the core economic problem of agentic commerce.

It also uses `tiktoken` to calculate the exact token savings for audit and demonstration purposes.
"""

import copy
import json
import tiktoken

# Load the tokenizer used by GPT-4 and Claude 3 (cl100k_base)
try:
    _tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    _tokenizer = None


# Define which fields are necessary for which intent.
# The pruning engine will ONLY return these fields for the given intent.
INTENT_FIELD_MAP = {
    "BUY": [
        "id", "name", "price", "currency", "stock_count", "sku", 
        "shipping_info", "return_policy"
    ],
    "STOCK": [
        "id", "name", "stock_count", "sizes", "colors"
    ],
    "SPECS": [
        "id", "name", "dimensions", "materials", "sizes", "colors"
    ],
    "COMPARE": [
        "id", "name", "price", "currency", "rating", "reviews_count", 
        "trust_badges"
    ],
    "BROWSE": [
        "id", "name", "price", "currency", "description", "category", 
        "brand", "rating"
    ],
    # AMBIGUOUS returns minimal identifying info so the agent knows what product 
    # it is looking at while it decides its next action.
    "AMBIGUOUS": [
        "id", "name", "price", "currency"
    ]
}


def _count_tokens(data: dict) -> int:
    """Helper to count the number of tokens in a JSON-serialized dictionary."""
    if not _tokenizer:
        return 0
    # Convert to JSON string (compact) to simulate network payload
    text = json.dumps(data, separators=(',', ':'))
    return len(_tokenizer.encode(text))


def prune_product_data(product: dict, intent: str) -> dict:
    """
    Prunes a product dictionary based on the agent's intent.

    Args:
        product: The full product dictionary from the catalog.
        intent: The classified intent (BUY, STOCK, SPECS, COMPARE, BROWSE, AMBIGUOUS).

    Returns:
        A new dictionary containing only the relevant fields, plus a '_meta' block 
        detailing the token savings.
    """
    if not product:
        return {}

    # Get the allowed fields for this intent. Fallback to minimal fields if intent is unknown.
    allowed_fields = INTENT_FIELD_MAP.get(intent, INTENT_FIELD_MAP["AMBIGUOUS"])
    
    # Measure original token weight
    original_tokens = _count_tokens(product)
    
    # Build the pruned product dictionary
    pruned_product = {}
    pruned_away_fields = []
    
    for key, value in product.items():
        if key in allowed_fields:
            # Deepcopy to prevent mutating original nested structures
            pruned_product[key] = copy.deepcopy(value)
        else:
            pruned_away_fields.append(key)
            
    # Measure new token weight
    pruned_tokens = _count_tokens(pruned_product)
    
    # Calculate savings
    savings_pct = 0.0
    if original_tokens > 0:
        savings_pct = round(((original_tokens - pruned_tokens) / original_tokens) * 100, 2)
        
    # Attach diagnostic metadata
    pruned_product["_meta"] = {
        "applied_intent": intent,
        "original_tokens": original_tokens,
        "pruned_tokens": pruned_tokens,
        "savings_percentage": savings_pct,
        "fields_removed": len(pruned_away_fields)
    }
    
    return pruned_product
