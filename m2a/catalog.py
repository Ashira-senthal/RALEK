import copy

# Mock in-memory product catalog.
# Designed to be "heavy" to simulate realistic DOM/HTML weight for token-savings demonstration.

CATALOG = {
    "prod_001": {
        "id": "prod_001",
        "name": "AuraX Pro Wireless Noise-Cancelling Headphones",
        "price": 29999,
        "currency": "INR",
        "description": "Experience pure auditory bliss with the AuraX Pro. Featuring dual-chip active noise cancellation, beryllium-coated drivers, and 40 hours of continuous playback. The ultra-plush memory foam earcups provide all-day comfort. Includes spatial audio support and lossless high-resolution audio decoding. Built for audiophiles who refuse to compromise.",
        "category": "Electronics > Audio",
        "brand": "AuraX",
        "images": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=1000&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?q=80&w=1000&auto=format&fit=crop"
        ],
        "dimensions": {
            "weight_g": 250,
            "length_cm": 18,
            "width_cm": 15,
            "height_cm": 7
        },
        "materials": ["Aerospace-grade aluminum", "Memory foam", "Vegan leather"],
        "sizes": ["One Size"],
        "colors": ["Midnight Black", "Lunar Silver", "Rose Gold"],
        "stock_count": 42,
        "sku": "AUX-PRO-001-MB",
        "rating": 4.8,
        "reviews_count": 1254,
        "shipping_info": "Free standard shipping on all orders. Delivers in 3-5 business days. Express next-day shipping available at checkout.",
        "return_policy": "30-day money-back guarantee. Item must be in original condition and packaging. Free return shipping within India.",
        "trust_badges": ["Hi-Res Audio Certified", "1 Year Warranty", "100% Authentic"]
    },
    "prod_002": {
        "id": "prod_002",
        "name": "Lumina ErgoMesh Office Chair",
        "price": 14500,
        "currency": "INR",
        "description": "Redefine your workspace with the Lumina ErgoMesh. Designed with a dynamic lumbar support system that adapts to your posture in real-time. The breathable Korean mesh keeps you cool during long working hours. Features 4D adjustable armrests, tilt-tension control, and a heavy-duty aluminum base tested for 150kg weight capacity.",
        "category": "Furniture > Office",
        "brand": "Lumina Workspace",
        "images": [
            "https://images.unsplash.com/photo-1592078615290-033ee584e267?q=80&w=1000&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1505843490538-5133c6c7d0e1?q=80&w=1000&auto=format&fit=crop"
        ],
        "dimensions": {
            "weight_g": 18500,
            "length_cm": 65,
            "width_cm": 65,
            "height_cm": 120
        },
        "materials": ["Korean breathable mesh", "High-density polyurethane", "Aluminum alloy base"],
        "sizes": ["Standard"],
        "colors": ["Graphite Grey", "Onyx Black"],
        "stock_count": 15,
        "sku": "LUM-ERGO-02-GRY",
        "rating": 4.6,
        "reviews_count": 482,
        "shipping_info": "Heavy item shipping. Arrives in 5-7 business days. Requires minor assembly (tools included).",
        "return_policy": "15-day return window. Requires disassembly and repacking in original box. Restocking fee may apply.",
        "trust_badges": ["BIFMA Certified", "Ergonomic Approved", "3 Year Warranty"]
    },
    "prod_003": {
        "id": "prod_003",
        "name": "Velocity V2 Carbon Running Shoes",
        "price": 8999,
        "currency": "INR",
        "description": "Shatter your personal records with the Velocity V2. Engineered with a full-length carbon fiber plate for explosive energy return and our proprietary AeroFoam midsole for featherlight cushioning. The engineered mesh upper provides targeted support while maximizing airflow. Perfect for half and full marathons.",
        "category": "Apparel > Footwear",
        "brand": "Velocity Athletics",
        "images": [
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1000&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1608231387042-66d1773070a5?q=80&w=1000&auto=format&fit=crop"
        ],
        "dimensions": {
            "weight_g": 210,
            "length_cm": 30,
            "width_cm": 11,
            "height_cm": 12
        },
        "materials": ["Carbon Fiber", "AeroFoam EVA", "Engineered breathable mesh"],
        "sizes": ["UK 7", "UK 8", "UK 9", "UK 10", "UK 11"],
        "colors": ["Neon Yellow", "Crimson Red", "Arctic White"],
        "stock_count": 87,
        "sku": "VEL-V2-RUN-NY-9",
        "rating": 4.9,
        "reviews_count": 3150,
        "shipping_info": "Free shipping. Delivers in 2-4 business days.",
        "return_policy": "30-day no-questions-asked returns. Shoes must be unworn and in original box.",
        "trust_badges": ["Marathon Approved", "Eco-friendly materials", "Secure Checkout"]
    },
    "prod_004": {
        "id": "prod_004",
        "name": "Kawa 75% Mechanical Keyboard",
        "price": 6500,
        "currency": "INR",
        "description": "The ultimate enthusiast keyboard. The Kawa 75% features a gasket-mounted design for a bouncy typing feel and deep acoustic signature. Comes pre-lubricated with custom linear switches. Hot-swappable PCB allows you to change switches without soldering. Includes double-shot PBT keycaps and per-key RGB backlighting with 18 dynamic effects.",
        "category": "Electronics > Peripherals",
        "brand": "Kawa Peripherals",
        "images": [
            "https://images.unsplash.com/photo-1595225476474-87563907a212?q=80&w=1000&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?q=80&w=1000&auto=format&fit=crop"
        ],
        "dimensions": {
            "weight_g": 950,
            "length_cm": 32,
            "width_cm": 14,
            "height_cm": 3.5
        },
        "materials": ["Polycarbonate case", "PBT keycaps", "Silicone dampening foam"],
        "sizes": ["75% Layout"],
        "colors": ["Retro Beige", "Translucent Purple"],
        "stock_count": 0,
        "sku": "KAW-75-LIN-RB",
        "rating": 4.7,
        "reviews_count": 890,
        "shipping_info": "Standard shipping 3-5 days.",
        "return_policy": "14-day return policy for unused items.",
        "trust_badges": ["Enthusiast Grade", "Hot-Swappable", "RoHS Compliant"]
    }
}

def get_all_products():
    """Returns a list of all products in the catalog."""
    return list(copy.deepcopy(CATALOG).values())

def get_product(product_id):
    """Returns a specific product by ID, or None if not found."""
    product = CATALOG.get(product_id)
    return copy.deepcopy(product) if product else None

def get_product_field(product_id, field):
    """Returns a specific field for a product, or None if not found."""
    product = CATALOG.get(product_id)
    if product:
        return product.get(field)
    return None
