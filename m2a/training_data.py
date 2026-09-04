"""
M2A Synthetic Intent Training Data

Labeled examples for training the Logistic Regression intent classifier.
These cover natural language variations an AI agent might use when querying
a product endpoint without providing a structured intent header.

NOTE: For the time being, the training data is limited to a core synthetic corpus
for prototype scope (~105 examples across 5 classes). In production, this can be
expanded with real merchant traffic logs and query analytics.

Intent Labels:
    BUY     - Agent wants to purchase / transact
    STOCK   - Agent wants stock / availability info
    SPECS   - Agent wants technical specifications / dimensions / materials
    COMPARE - Agent wants comparative data (price, rating, features)
    BROWSE  - Agent wants a general overview / discovery
"""

TRAINING_DATA = [
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

# Convenience exports for the classifier
TEXTS = [text for text, label in TRAINING_DATA]
LABELS = [label for text, label in TRAINING_DATA]
