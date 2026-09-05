"""
M2A Immutable Audit Trail

Append-only JSONL log that records every agent interaction for compliance,
debugging, and Razorpay Buildathon evaluation. Each line is a self-contained
JSON object with a monotonic sequence number to detect tampering or gaps.

Razorpay Track Requirement:
    "Every money action explainable, bounded, and gated."
    "Show the audit trail and one failure handled gracefully."

The audit trail captures:
    - Timestamp (ISO 8601 UTC)
    - Sequence number (monotonic, gap-detectable)
    - Client detection result (type, protocol, confidence)
    - Intent classification result (intent, confidence, method)
    - Pruning metadata (original/pruned tokens, savings %)
    - Payment result (if BUY intent — link ID, amount, success/failure)
    - Error details (if any step failed)
"""

import json
import os
import time
import threading
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default audit log path. Can be overridden via environment variable.
AUDIT_LOG_PATH = os.environ.get(
    "M2A_AUDIT_LOG",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "audit_trail.jsonl")
)

# Thread lock for safe concurrent writes
_write_lock = threading.Lock()

# Monotonic sequence counter
_sequence_counter = 0
_counter_lock = threading.Lock()


def _next_sequence() -> int:
    """Return the next monotonic sequence number (thread-safe)."""
    global _sequence_counter
    with _counter_lock:
        _sequence_counter += 1
        return _sequence_counter


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_interaction(
    detection_result: dict = None,
    classification_result: dict = None,
    pruning_meta: dict = None,
    payment_result: dict = None,
    product_id: str = None,
    error: str = None,
    extra: dict = None,
) -> dict:
    """Append a single audit entry to the JSONL log file.

    All arguments are optional — log whatever is available at the
    point of the request lifecycle where logging occurs.

    Args:
        detection_result: Serialized DetectionResult (from detector.py).
        classification_result: Serialized ClassificationResult (from classifier.py).
        pruning_meta: The '_meta' block from pruner.py output.
        payment_result: Serialized PaymentResult (from payments.py).
        product_id: The product ID being accessed.
        error: Error message if any step in the pipeline failed.
        extra: Arbitrary extra data to attach.

    Returns:
        The audit entry dict that was written (for testing/inspection).
    """
    entry = {
        "seq": _next_sequence(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "product_id": product_id,
        "detection": detection_result,
        "classification": classification_result,
        "pruning": pruning_meta,
        "payment": payment_result,
        "error": error,
    }

    if extra:
        entry["extra"] = extra

    # Write atomically: serialize first, then write in one call
    line = json.dumps(entry, separators=(",", ":"), default=str) + "\n"

    with _write_lock:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)

    return entry


def read_audit_log(last_n: int = None) -> list:
    """Read audit entries from the JSONL log file.

    Args:
        last_n: If provided, return only the last N entries.

    Returns:
        List of audit entry dicts.
    """
    if not os.path.exists(AUDIT_LOG_PATH):
        return []

    entries = []
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if last_n is not None:
        return entries[-last_n:]
    return entries


def get_audit_stats() -> dict:
    """Return summary statistics from the audit trail.

    Returns:
        Dict with counts of total interactions, agent vs human,
        intent distribution, payment successes/failures, and errors.
    """
    entries = read_audit_log()

    stats = {
        "total_interactions": len(entries),
        "agent_requests": 0,
        "human_requests": 0,
        "intent_distribution": {},
        "payments_attempted": 0,
        "payments_succeeded": 0,
        "payments_failed": 0,
        "errors": 0,
        "avg_token_savings_pct": 0.0,
    }

    savings_values = []

    for entry in entries:
        # Detection stats
        detection = entry.get("detection") or {}
        if detection.get("client_type") == "agent":
            stats["agent_requests"] += 1
        elif detection.get("client_type") == "human":
            stats["human_requests"] += 1

        # Intent stats
        classification = entry.get("classification") or {}
        intent = classification.get("intent")
        if intent:
            stats["intent_distribution"][intent] = (
                stats["intent_distribution"].get(intent, 0) + 1
            )

        # Pruning stats
        pruning = entry.get("pruning") or {}
        savings = pruning.get("savings_percentage")
        if savings is not None:
            savings_values.append(savings)

        # Payment stats
        payment = entry.get("payment") or {}
        if payment:
            stats["payments_attempted"] += 1
            if payment.get("success"):
                stats["payments_succeeded"] += 1
            else:
                stats["payments_failed"] += 1

        # Error stats
        if entry.get("error"):
            stats["errors"] += 1

    if savings_values:
        stats["avg_token_savings_pct"] = round(
            sum(savings_values) / len(savings_values), 2
        )

    return stats
