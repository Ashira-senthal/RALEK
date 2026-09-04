"""
M2A Detection Layer — Protocol-Aware Client Detection

Distinguishes human browsers from AI buyer agents using a priority-based
detection hierarchy. Favors modern content negotiation and protocol-native
signals over raw user-agent sniffing (which the industry is actively moving
away from due to cloaking concerns raised by Google's John Mueller).

Detection Priority:
  1. Accept: application/vnd.m2a+json  → ACP-native M2A agent
  2. Accept: text/markdown             → Markdown-aware agent (Cloudflare convention)
  3. Signature-Agent header present     → RFC 9421 authenticated agent (ChatGPT-style)
  4. X-Agent-Protocol / X-Agent-Intent  → ACP-compatible agent
  5. User-Agent heuristic               → Known bot strings (fallback only)
  6. None matched                       → Default: human browser
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# Known AI agent user-agent substrings (fallback heuristic only).
# This list is intentionally conservative — false positives here would
# serve a human the wrong response, which is worse than missing an agent.
KNOWN_AGENT_UA_FRAGMENTS = [
    "gptbot",
    "chatgpt-user",
    "claudebot",
    "claude-web",
    "anthropic-ai",
    "google-extended",
    "googleother",
    "cohere-ai",
    "perplexitybot",
    "bytespider",
    "amazonbot",
    "meta-externalagent",
    "facebookbot",
    "applebot-extended",
    "ccbot",
    "diffbot",
    "youbot",
    "iaskbot",
]


@dataclass
class DetectionResult:
    """Result of client detection for a single incoming request.

    Attributes:
        client_type: 'agent' or 'human'.
        protocol: Detection method that matched ('acp', 'markdown',
                  'signature', 'header', 'heuristic', 'browser').
        confidence: 'high', 'medium', or 'low'.
        raw_signals: Dict of all relevant signals extracted from headers.
        agent_intent: Optional intent extracted from X-Agent-Intent header,
                      if present. Passed downstream to the classifier.
    """
    client_type: str       # 'agent' | 'human'
    protocol: str          # 'acp' | 'markdown' | 'signature' | 'header' | 'heuristic' | 'browser'
    confidence: str        # 'high' | 'medium' | 'low'
    raw_signals: dict = field(default_factory=dict)
    agent_intent: Optional[str] = None

    def to_dict(self):
        """Serialize for audit trail logging."""
        return asdict(self)

    @property
    def is_agent(self):
        return self.client_type == "agent"


def detect_client(headers) -> DetectionResult:
    """Detect whether an incoming request is from a human browser or AI agent.

    Args:
        headers: A dict-like object of HTTP request headers.
                 Works with both plain dicts (for testing) and Flask's
                 request.headers (which is a MultiDict).

    Returns:
        DetectionResult with classification, protocol, confidence, and
        any extracted signals (including agent intent if provided).
    """
    # Normalize headers to a case-insensitive lookup.
    # Flask headers are already case-insensitive, but plain dicts are not.
    normalized = {k.lower(): v for k, v in headers.items()} if isinstance(headers, dict) else {
        k.lower(): v for k, v in headers.items()
    }

    # Collect raw signals for audit trail transparency.
    raw_signals = {
        "accept": normalized.get("accept", ""),
        "user_agent": normalized.get("user-agent", ""),
        "signature_agent": normalized.get("signature-agent"),
        "x_agent_protocol": normalized.get("x-agent-protocol"),
        "x_agent_intent": normalized.get("x-agent-intent"),
    }

    # Extract agent intent if provided (passed to classifier later).
    agent_intent = normalized.get("x-agent-intent")

    accept_header = normalized.get("accept", "").lower()

    # --- Priority 1: ACP-native M2A content negotiation ---
    if "application/vnd.m2a+json" in accept_header:
        return DetectionResult(
            client_type="agent",
            protocol="acp",
            confidence="high",
            raw_signals=raw_signals,
            agent_intent=agent_intent,
        )

    # --- Priority 2: Markdown content negotiation (Cloudflare convention) ---
    if "text/markdown" in accept_header:
        return DetectionResult(
            client_type="agent",
            protocol="markdown",
            confidence="high",
            raw_signals=raw_signals,
            agent_intent=agent_intent,
        )

    # --- Priority 3: RFC 9421 Signature-Agent header ---
    if normalized.get("signature-agent"):
        return DetectionResult(
            client_type="agent",
            protocol="signature",
            confidence="high",
            raw_signals=raw_signals,
            agent_intent=agent_intent,
        )

    # --- Priority 4: Custom ACP protocol headers ---
    if normalized.get("x-agent-protocol") or normalized.get("x-agent-intent"):
        return DetectionResult(
            client_type="agent",
            protocol="header",
            confidence="medium",
            raw_signals=raw_signals,
            agent_intent=agent_intent,
        )

    # --- Priority 5: User-Agent heuristic (fallback) ---
    user_agent = normalized.get("user-agent", "").lower()
    if user_agent:
        for fragment in KNOWN_AGENT_UA_FRAGMENTS:
            if fragment in user_agent:
                return DetectionResult(
                    client_type="agent",
                    protocol="heuristic",
                    confidence="low",
                    raw_signals=raw_signals,
                    agent_intent=agent_intent,
                )

    # --- Priority 6: Default — human browser ---
    return DetectionResult(
        client_type="human",
        protocol="browser",
        confidence="high",
        raw_signals=raw_signals,
        agent_intent=None,
    )


def get_vary_headers() -> str:
    """Returns the Vary header value that should be set on every response.

    This tells caches and intermediaries that the response varies based on
    these headers, which prevents cloaking accusations (serving different
    content to different clients without transparent signaling).
    """
    return "Accept, Signature-Agent, X-Agent-Protocol, X-Agent-Intent"
