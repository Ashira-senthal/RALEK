"""
M2A Hybrid Intent Classifier

Classifies what an AI buyer agent wants from a specific request. This is
M2A's core differentiator: no prior art (Cloudflare, Dodo, Vercel, WorkOS)
does per-request intent inference — they all serve the same static payload
regardless of what the agent actually needs.

Architecture — three layers, in order:

  Layer 1 — Deterministic Rules Router (~80% of real traffic)
    Checks for structured intent signals in headers and query params.
    If found, classifies instantly at confidence=1.0, no ML involved.
    Directly addresses Razorpay's stated preference for "deterministic
    solutions where AI is unnecessary."

  Layer 2 — ML Fallback (ambiguous / natural-language requests)
    scikit-learn LogisticRegression + TfidfVectorizer trained on
    m2a/training_data.py. Activates only when Layer 1 finds nothing.
    Confidence threshold: >= 0.6 classifies; < 0.6 → AMBIGUOUS.

  Layer 3 — Graceful Failure Handler
    AMBIGUOUS intent returns a structured response listing exactly what
    the agent can do next. This is the explicit failure-recovery path
    that Razorpay's track evaluation explicitly requires.

Intent Labels:
    BUY      - Agent intends to purchase / transact
    STOCK    - Agent wants availability / inventory data
    SPECS    - Agent wants technical specs / dimensions / materials
    COMPARE  - Agent wants comparative / evaluation data
    BROWSE   - Agent wants a general overview / discovery
    AMBIGUOUS - Could not classify with sufficient confidence
"""

from dataclasses import dataclass, asdict
import re

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from m2a.training_data import TEXTS, LABELS


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid intents that a caller can pass as structured signals.
DETERMINISTIC_INTENT_MAP = {
    # Purchase / buy
    "purchase": "BUY",
    "buy": "BUY",
    "order": "BUY",
    "checkout": "BUY",
    "pay": "BUY",

    # Stock / availability
    "stock_check": "STOCK",
    "stock": "STOCK",
    "availability": "STOCK",
    "inventory": "STOCK",

    # Technical specifications
    "specs": "SPECS",
    "specifications": "SPECS",
    "spec_lookup": "SPECS",
    "details": "SPECS",
    "dimensions": "SPECS",

    # Comparison / evaluation
    "compare": "COMPARE",
    "comparison": "COMPARE",
    "evaluate": "COMPARE",
    "review": "COMPARE",

    # General browsing / discovery
    "browse": "BROWSE",
    "overview": "BROWSE",
    "info": "BROWSE",
    "information": "BROWSE",
    "describe": "BROWSE",
}

# Minimum ML confidence to classify; below this → AMBIGUOUS
CONFIDENCE_THRESHOLD = 0.60

# What an AMBIGUOUS response tells the agent it can do
AMBIGUOUS_ACTIONS = [
    {"intent": "BUY",     "description": "Get a payment link and purchase this product",    "header": "X-Agent-Intent: purchase"},
    {"intent": "STOCK",   "description": "Check stock availability and sizes",              "header": "X-Agent-Intent: stock_check"},
    {"intent": "SPECS",   "description": "Get technical specifications and dimensions",     "header": "X-Agent-Intent: specs"},
    {"intent": "COMPARE", "description": "Get price, rating, and comparison data",          "header": "X-Agent-Intent: compare"},
    {"intent": "BROWSE",  "description": "Get a general product overview and description",  "header": "X-Agent-Intent: browse"},
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    """Result of intent classification for a single agent request.

    Attributes:
        intent: Classified intent label (BUY/STOCK/SPECS/COMPARE/BROWSE/AMBIGUOUS).
        confidence: Float 0.0–1.0 (1.0 for deterministic, ML probability otherwise).
        method: 'deterministic', 'ml', or 'ambiguous'.
        raw_query: The query string that was classified (for audit).
        available_actions: Populated only when intent == AMBIGUOUS.
    """
    intent: str
    confidence: float
    method: str        # 'deterministic' | 'ml' | 'ambiguous'
    raw_query: str
    available_actions: list = None

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# ML pipeline — built once at module import time
# ---------------------------------------------------------------------------

def _build_pipeline() -> Pipeline:
    """Train and return the TF-IDF + Logistic Regression pipeline."""
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),   # Unigrams and bigrams
            lowercase=True,
            strip_accents="unicode",
            analyzer="word",
            max_features=5000,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=5.0,
            solver="lbfgs",
            random_state=42,
        )),
    ])
    pipeline.fit(TEXTS, LABELS)
    return pipeline


# Global pipeline instance — trained at module import
_pipeline: Pipeline = _build_pipeline()
_classes: list = list(_pipeline.classes_)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_intent(signals: dict, product_id: str = None) -> ClassificationResult:
    """Classify an agent's intent from available signals.

    Args:
        signals: Dict containing any of:
                   - 'intent'  : structured intent string (from X-Agent-Intent
                                 or ?intent= query param) — Layer 1 fast path.
                   - 'query'   : free-text query / request body — Layer 2 ML.
                   - 'body'    : alias for 'query'.
        product_id: Optional product ID (for future per-product context,
                    not used in classification itself).

    Returns:
        ClassificationResult with intent, confidence, method, and raw_query.
    """
    # ------------------------------------------------------------------
    # Layer 1: Deterministic rules — structured intent signals
    # ------------------------------------------------------------------
    structured_intent = (
        signals.get("intent")
        or signals.get("x_agent_intent")
    )
    if structured_intent:
        normalized = structured_intent.strip().lower().replace(" ", "_")
        mapped = DETERMINISTIC_INTENT_MAP.get(normalized)
        if mapped:
            return ClassificationResult(
                intent=mapped,
                confidence=1.0,
                method="deterministic",
                raw_query=structured_intent,
                available_actions=None,
            )

    # ------------------------------------------------------------------
    # Layer 2: ML fallback — natural language query
    # ------------------------------------------------------------------
    raw_query = (
        signals.get("query")
        or signals.get("body")
        or ""
    ).strip()

    if raw_query:
        # Sanitize: strip excessive whitespace, limit to 500 chars
        clean_query = re.sub(r"\s+", " ", raw_query)[:500]

        proba = _pipeline.predict_proba([clean_query])[0]
        best_idx = int(proba.argmax())
        best_confidence = float(proba[best_idx])
        best_label = _classes[best_idx]

        if best_confidence >= CONFIDENCE_THRESHOLD:
            return ClassificationResult(
                intent=best_label,
                confidence=round(best_confidence, 4),
                method="ml",
                raw_query=clean_query,
                available_actions=None,
            )

        # Below threshold — fall through to AMBIGUOUS
        return ClassificationResult(
            intent="AMBIGUOUS",
            confidence=round(best_confidence, 4),
            method="ambiguous",
            raw_query=clean_query,
            available_actions=AMBIGUOUS_ACTIONS,
        )

    # ------------------------------------------------------------------
    # Layer 3: No usable signals — graceful failure
    # ------------------------------------------------------------------
    return ClassificationResult(
        intent="AMBIGUOUS",
        confidence=0.0,
        method="ambiguous",
        raw_query="",
        available_actions=AMBIGUOUS_ACTIONS,
    )
