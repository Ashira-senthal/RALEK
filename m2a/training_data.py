"""
M2A Synthetic Intent Training Data

Labeled examples for training the Logistic Regression intent classifier.
These cover natural language variations an AI agent might use when querying
a product endpoint without providing a structured intent header.

The base dataset of ~105 hand-curated examples is augmented at import time
using nlpaug (keyboard proximity, random character mutation, OCR-style confusion)
to generate ~500+ typo variants. This makes the classifier robust against
real-world spelling mistakes without needing a large external dataset.

Intent Labels:
    BUY     - Agent wants to purchase / transact
    STOCK   - Agent wants stock / availability info
    SPECS   - Agent wants technical specifications / dimensions / materials
    COMPARE - Agent wants comparative data (price, rating, features)
    BROWSE  - Agent wants a general overview / discovery
"""

import random

# -------------------------------------------------------------------------
# Base training corpus — hand-curated, high-quality, domain-specific
# -------------------------------------------------------------------------

BASE_TRAINING_DATA = [
    # -------------------------------------------------------------------------
    # BUY — Purchase intent
    # -------------------------------------------------------------------------
    ("I want to buy this", "BUY"),
    ("I'd like to purchase this item", "BUY"),
    ("how do I buy this", "BUY"),
    ("I want to order this now", "BUY"),
    ("add to cart", "BUY"),
    ("proceed to checkout", "BUY"),
    ("how can I pay for this", "BUY"),
    ("I want to complete a purchase", "BUY"),
    ("get payment link", "BUY"),
    ("buy now", "BUY"),
    ("place an order", "BUY"),
    ("I'm ready to pay", "BUY"),
    ("generate a payment link for this product", "BUY"),
    ("I want to transact", "BUY"),
    ("initiate purchase", "BUY"),
    ("proceed with payment", "BUY"),
    ("I want to check out this product", "BUY"),
    ("complete order", "BUY"),
    ("confirm purchase", "BUY"),
    ("I'd like to acquire this", "BUY"),
    ("how to order", "BUY"),
    ("give me a checkout link", "BUY"),

    # -------------------------------------------------------------------------
    # STOCK — Availability / inventory intent
    # -------------------------------------------------------------------------
    ("is this in stock", "STOCK"),
    ("is this available", "STOCK"),
    ("how many units are left", "STOCK"),
    ("do you have this in stock", "STOCK"),
    ("what is the stock count", "STOCK"),
    ("is this available in size L", "STOCK"),
    ("do you have this in blue", "STOCK"),
    ("is this available in large", "STOCK"),
    ("availability check", "STOCK"),
    ("check stock", "STOCK"),
    ("is this out of stock", "STOCK"),
    ("stock status", "STOCK"),
    ("inventory level", "STOCK"),
    ("how many are available", "STOCK"),
    ("can I still get this in XL", "STOCK"),
    ("remaining units", "STOCK"),
    ("is the size medium available", "STOCK"),
    ("do you have any left", "STOCK"),
    ("availability in crimson red", "STOCK"),
    ("is this backordered", "STOCK"),
    ("when will it be restocked", "STOCK"),

    # -------------------------------------------------------------------------
    # SPECS — Technical specifications intent
    # -------------------------------------------------------------------------
    ("what are the dimensions", "SPECS"),
    ("what is the weight", "SPECS"),
    ("what materials is this made of", "SPECS"),
    ("give me the technical specifications", "SPECS"),
    ("what are the specs", "SPECS"),
    ("how heavy is this", "SPECS"),
    ("what is it made of", "SPECS"),
    ("material composition", "SPECS"),
    ("product dimensions", "SPECS"),
    ("weight and dimensions", "SPECS"),
    ("is this carbon fiber", "SPECS"),
    ("what size is this item", "SPECS"),
    ("technical details", "SPECS"),
    ("physical specifications", "SPECS"),
    ("what is the build material", "SPECS"),
    ("how long is it", "SPECS"),
    ("size chart", "SPECS"),
    ("what colors does this come in", "SPECS"),
    ("available sizes", "SPECS"),
    ("product measurements", "SPECS"),
    ("what are the exact measurements", "SPECS"),
    ("what is the weight of this item", "SPECS"),
    ("how much does this weigh", "SPECS"),
    ("weight of this product", "SPECS"),
    ("tell me the weight", "SPECS"),
    ("how many grams is this", "SPECS"),
    ("what is the total weight", "SPECS"),

    # -------------------------------------------------------------------------
    # COMPARE — Comparative / evaluation intent
    # -------------------------------------------------------------------------
    ("compare this with other products", "COMPARE"),
    ("how does this compare", "COMPARE"),
    ("what is the price vs alternatives", "COMPARE"),
    ("how is the rating", "COMPARE"),
    ("compare price and quality", "COMPARE"),
    ("is this worth the price", "COMPARE"),
    ("what is the review score", "COMPARE"),
    ("how many reviews does this have", "COMPARE"),
    ("compare features", "COMPARE"),
    ("price comparison", "COMPARE"),
    ("value for money", "COMPARE"),
    ("how does the rating compare", "COMPARE"),
    ("customer rating", "COMPARE"),
    ("review summary", "COMPARE"),
    ("is this highly rated", "COMPARE"),
    ("benchmark against similar items", "COMPARE"),
    ("what do customers think", "COMPARE"),
    ("quality to price ratio", "COMPARE"),
    ("how many stars", "COMPARE"),
    ("is this good value", "COMPARE"),

    # -------------------------------------------------------------------------
    # BROWSE — General discovery / overview intent
    # -------------------------------------------------------------------------
    ("tell me about this product", "BROWSE"),
    ("give me an overview", "BROWSE"),
    ("what is this", "BROWSE"),
    ("describe this item", "BROWSE"),
    ("product summary", "BROWSE"),
    ("what does this do", "BROWSE"),
    ("general information", "BROWSE"),
    ("show me this product", "BROWSE"),
    ("product details", "BROWSE"),
    ("what category is this", "BROWSE"),
    ("give me a description", "BROWSE"),
    ("what brand is this", "BROWSE"),
    ("is this a good product", "BROWSE"),
    ("what is included in the box", "BROWSE"),
    ("overview of this item", "BROWSE"),
    ("tell me more", "BROWSE"),
    ("product info", "BROWSE"),
    ("what can you tell me about this", "BROWSE"),
    ("show me details", "BROWSE"),
    ("give me everything about this product", "BROWSE"),
    ("all information about this", "BROWSE"),
]


# -------------------------------------------------------------------------
# Typo augmentation via nlpaug
# -------------------------------------------------------------------------

def _augment_training_data(base_data, augments_per_example=4, seed=42):
    """Generate typo-augmented training examples using nlpaug.

    Uses three augmentation strategies:
      1. KeyboardAug  — QWERTY proximity typos (e.g., 'buy' → 'biy')
      2. RandomCharAug — random char insert/delete/swap (e.g., 'purchase' → 'pruchase')
      3. OcrAug       — OCR-style confusion (e.g., '0' ↔ 'O', 'l' ↔ '1')

    Args:
        base_data: list of (text, label) tuples.
        augments_per_example: number of augmented variants per original example.
        seed: random seed for reproducibility.

    Returns:
        Combined list of original + augmented (text, label) tuples.
    """
    try:
        import nlpaug.augmenter.char as nac
    except ImportError:
        # nlpaug not installed — fall back to base data only.
        # This ensures the module still works without nlpaug (e.g. in CI).
        print("[M2A WARNING] nlpaug not installed — using base training data only.")
        return base_data

    random.seed(seed)

    augmenters = [
        nac.KeyboardAug(
            aug_char_min=1, aug_char_max=2,
            aug_word_min=1, aug_word_max=2,
            include_special_char=False,
            include_numeric=False,
        ),
        nac.RandomCharAug(
            action="substitute",
            aug_char_min=1, aug_char_max=2,
            aug_word_min=1, aug_word_max=1,
        ),
        nac.OcrAug(
            aug_char_min=1, aug_char_max=2,
            aug_word_min=1, aug_word_max=1,
        ),
    ]

    augmented = list(base_data)  # Start with all originals
    seen = {text.lower() for text, _ in base_data}

    for text, label in base_data:
        generated = 0
        attempts = 0
        max_attempts = augments_per_example * 3  # Avoid infinite loops

        while generated < augments_per_example and attempts < max_attempts:
            attempts += 1
            aug = random.choice(augmenters)
            try:
                variants = aug.augment(text, n=1)
                if isinstance(variants, list):
                    variant = variants[0]
                else:
                    variant = variants

                # Skip duplicates and unchanged text
                if variant.lower() not in seen and variant.lower() != text.lower():
                    augmented.append((variant, label))
                    seen.add(variant.lower())
                    generated += 1
            except Exception:
                continue

    return augmented


# -------------------------------------------------------------------------
# Build the final augmented dataset at import time
# -------------------------------------------------------------------------

TRAINING_DATA = _augment_training_data(BASE_TRAINING_DATA, augments_per_example=6, seed=42)

# Convenience exports for the classifier
TEXTS = [text for text, label in TRAINING_DATA]
LABELS = [label for text, label in TRAINING_DATA]
