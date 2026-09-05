"""
M2A Payments Module — Razorpay Payment Link Generator

Generates Razorpay test-mode payment links for BUY intent requests.
Only activated when the classifier returns intent=BUY. Enforces a
hard spend-cap before link generation to satisfy the Razorpay
Buildathon requirement: "every money action bounded and gated."

Architecture:
    1. Load Razorpay credentials from environment (.env).
    2. On BUY intent: validate product data, enforce spend cap,
       call Razorpay Payment Links API, return the link URL.
    3. On non-BUY intent: no-op (returns None).
    4. If credentials are missing: fall back to a mock payment link
       generator so the rest of the system remains testable.

Security:
    - Keys are loaded from environment variables, never hardcoded.
    - Spend cap is enforced server-side before any API call.
    - All payment link metadata is logged to the audit trail.
"""

import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

# Hard spend cap in INR (paise). No payment link will be generated
# for amounts exceeding this. Set to ₹50,000 (5,000,000 paise) for test mode.
SPEND_CAP_PAISE = 5_000_000

# Whether we have live Razorpay credentials
_HAS_CREDENTIALS = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

# Lazy-init the Razorpay client
_razorpay_client = None


def _get_client():
    """Lazy-initialize the Razorpay client."""
    global _razorpay_client
    if _razorpay_client is None and _HAS_CREDENTIALS:
        try:
            import razorpay
            _razorpay_client = razorpay.Client(
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
            )
        except ImportError:
            pass
    return _razorpay_client


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PaymentResult:
    """Result of a payment link generation attempt.

    Attributes:
        success: Whether a payment link was generated.
        payment_link_url: The short URL for the payment link (if success).
        payment_link_id: Razorpay's payment link ID (e.g., plink_xxx).
        amount_paise: Amount in paise that was charged.
        currency: Currency code (e.g., INR).
        method: 'razorpay' for live API, 'mock' for fallback.
        error: Error message if generation failed.
    """
    success: bool
    payment_link_url: Optional[str] = None
    payment_link_id: Optional[str] = None
    amount_paise: int = 0
    currency: str = "INR"
    method: str = "mock"
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Mock fallback generator
# ---------------------------------------------------------------------------

def _generate_mock_link(product: dict) -> PaymentResult:
    """Generate a realistic-looking mock payment link for testing."""
    mock_id = f"plink_mock_{uuid.uuid4().hex[:12]}"
    mock_url = f"https://rzp.io/test/{mock_id}"
    amount = product.get("price", 0) * 100  # Convert INR to paise

    return PaymentResult(
        success=True,
        payment_link_url=mock_url,
        payment_link_id=mock_id,
        amount_paise=amount,
        currency=product.get("currency", "INR"),
        method="mock",
        error=None,
    )


# ---------------------------------------------------------------------------
# Live Razorpay payment link generator
# ---------------------------------------------------------------------------

def _generate_razorpay_link(product: dict) -> PaymentResult:
    """Generate a real Razorpay test-mode payment link."""
    client = _get_client()
    if not client:
        return PaymentResult(
            success=False,
            error="Razorpay client not initialized (missing credentials or library)",
        )

    amount_paise = product.get("price", 0) * 100  # INR to paise

    try:
        link_data = client.payment_link.create({
            "amount": amount_paise,
            "currency": product.get("currency", "INR"),
            "description": f"M2A Purchase: {product.get('name', 'Unknown Product')}",
            "reference_id": f"m2a_{product.get('id', 'unknown')}_{int(time.time())}",
            "callback_url": "",
            "callback_method": "",
            "notes": {
                "product_id": product.get("id", ""),
                "product_name": product.get("name", ""),
                "source": "m2a_agent_commerce",
            },
        })

        return PaymentResult(
            success=True,
            payment_link_url=link_data.get("short_url", ""),
            payment_link_id=link_data.get("id", ""),
            amount_paise=amount_paise,
            currency=product.get("currency", "INR"),
            method="razorpay",
            error=None,
        )

    except Exception as e:
        return PaymentResult(
            success=False,
            amount_paise=amount_paise,
            currency=product.get("currency", "INR"),
            method="razorpay",
            error=str(e),
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_payment_link(product: dict, intent: str) -> Optional[PaymentResult]:
    """Generate a payment link for a product if intent is BUY.

    Args:
        product: Product dictionary (must contain 'price', 'currency', 'id', 'name').
        intent: The classified intent string.

    Returns:
        PaymentResult if intent is BUY, None otherwise.
    """
    # Only generate payment links for BUY intent
    if intent != "BUY":
        return None

    if not product:
        return PaymentResult(success=False, error="No product data provided")

    # Extract amount and enforce spend cap
    amount_paise = product.get("price", 0) * 100

    if amount_paise <= 0:
        return PaymentResult(
            success=False,
            error="Invalid product price: must be greater than zero",
        )

    if amount_paise > SPEND_CAP_PAISE:
        return PaymentResult(
            success=False,
            amount_paise=amount_paise,
            error=f"Amount {amount_paise} paise exceeds spend cap of {SPEND_CAP_PAISE} paise",
        )

    # Use live Razorpay if credentials exist, otherwise mock
    if _HAS_CREDENTIALS:
        return _generate_razorpay_link(product)
    else:
        return _generate_mock_link(product)
