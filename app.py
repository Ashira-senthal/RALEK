"""
M2A — Merchant-to-Agent Bridge — Flask Application

The main server that wires together every module built in Phases 1–5:
    detector  → classifier → pruner → payments → audit

Routes:
    GET /                  → Human storefront (HTML) or Agent catalog (JSON)
    GET /product/<id>      → Human product page or Agent pruned product (JSON)
    GET /audit             → Audit trail viewer (JSON)
    GET /health            → Health check endpoint
"""

import json
from flask import Flask, request, render_template, jsonify, Response, make_response

from m2a.catalog import get_all_products, get_product
from m2a.detector import detect_client, get_vary_headers
from m2a.classifier import classify_intent
from m2a.pruner import prune_product_data
from m2a.payments import generate_payment_link
from m2a.audit import log_interaction, get_audit_stats, read_audit_log


app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_vary_headers(response) -> Response:
    """Add Vary headers to every response for cloaking transparency."""
    if isinstance(response, str):
        response = make_response(response)
    response.headers["Vary"] = get_vary_headers()
    return response


def _build_agent_signals(detection_result) -> dict:
    """Extract classification signals from the request + detection result."""
    signals = {}

    # From detection layer (X-Agent-Intent header)
    if detection_result.agent_intent:
        signals["intent"] = detection_result.agent_intent

    # From query parameter (?intent=purchase&query=...)
    if request.args.get("intent"):
        signals["intent"] = request.args.get("intent")

    # From query parameter or request body (natural language)
    if request.args.get("query"):
        signals["query"] = request.args.get("query")

    # From JSON request body
    if request.is_json:
        body = request.get_json(silent=True) or {}
        if "intent" in body:
            signals["intent"] = body["intent"]
        if "query" in body:
            signals["query"] = body["query"]

    return signals


def _handle_agent_product_request(product: dict, detection_result) -> Response:
    """Full agent pipeline: classify → prune → pay → audit → respond."""
    # Step 1: Classify intent
    signals = _build_agent_signals(detection_result)
    classification = classify_intent(signals, product.get("id"))

    # Step 2: Prune product data based on intent
    pruned = prune_product_data(product, classification.intent)
    pruning_meta = pruned.pop("_meta", {})

    # Step 3: Generate payment link if BUY intent
    payment_result = generate_payment_link(product, classification.intent)

    # Step 4: Build the response payload
    payload = {
        "product": pruned,
        "intent": {
            "classified_as": classification.intent,
            "confidence": classification.confidence,
            "method": classification.method,
        },
        "token_savings": pruning_meta,
    }

    # Attach payment link if generated
    if payment_result and payment_result.success:
        payload["payment"] = {
            "payment_link_url": payment_result.payment_link_url,
            "payment_link_id": payment_result.payment_link_id,
            "amount_paise": payment_result.amount_paise,
            "currency": payment_result.currency,
        }
    elif payment_result and not payment_result.success:
        payload["payment"] = {
            "error": payment_result.error,
        }

    # Attach available actions if AMBIGUOUS
    if classification.intent == "AMBIGUOUS" and classification.available_actions:
        payload["available_actions"] = classification.available_actions

    # Step 5: Log to audit trail
    log_interaction(
        detection_result=detection_result.to_dict(),
        classification_result=classification.to_dict(),
        pruning_meta=pruning_meta,
        payment_result=payment_result.to_dict() if payment_result else None,
        product_id=product.get("id"),
        error=payment_result.error if payment_result and not payment_result.success else None,
    )

    # Step 6: Return response with proper content type
    response = jsonify(payload)
    response.headers["Content-Type"] = "application/vnd.m2a+json"
    return _add_vary_headers(response)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Main page — storefront for humans, catalog for agents."""
    detection = detect_client(request.headers)

    if detection.is_agent:
        # Agent gets a lightweight catalog listing
        products = get_all_products()
        catalog_summary = []
        for p in products:
            catalog_summary.append({
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "currency": p["currency"],
                "stock_count": p["stock_count"],
                "endpoint": f"/product/{p['id']}",
            })

        payload = {
            "catalog": catalog_summary,
            "total_products": len(catalog_summary),
            "instructions": "Use GET /product/<id> with Accept: application/vnd.m2a+json to query a specific product. "
                            "Add X-Agent-Intent header or ?intent= query param for deterministic routing. "
                            "Or pass ?query= for natural language intent classification.",
        }

        # Log the catalog browse
        log_interaction(
            detection_result=detection.to_dict(),
            classification_result={"intent": "BROWSE", "confidence": 1.0, "method": "catalog_listing"},
        )

        response = jsonify(payload)
        response.headers["Content-Type"] = "application/vnd.m2a+json"
        return _add_vary_headers(response)

    # Human gets the storefront
    products = get_all_products()
    return _add_vary_headers(render_template("index.html", products=products))


@app.route("/product/<product_id>")
def product_page(product_id):
    """Product detail — rich HTML for humans, pruned JSON for agents."""
    product = get_product(product_id)

    if not product:
        detection = detect_client(request.headers)
        if detection.is_agent:
            response = jsonify({"error": "Product not found", "product_id": product_id})
            response.status_code = 404
            return _add_vary_headers(response)
        return _add_vary_headers(render_template("404.html", product_id=product_id)), 404

    detection = detect_client(request.headers)

    if detection.is_agent:
        return _handle_agent_product_request(product, detection)

    # Human gets the product detail page
    return _add_vary_headers(render_template("product.html", product=product))


@app.route("/audit")
def audit_view():
    """View the audit trail (JSON). For demo/evaluation purposes."""
    last_n = request.args.get("last", type=int, default=50)
    entries = read_audit_log(last_n=last_n)
    stats = get_audit_stats()
    return jsonify({"stats": stats, "entries": entries})


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "m2a"})


@app.route("/dashboard")
def dashboard():
    """Hackathon presentation dashboard."""
    return render_template("dashboard.html")


@app.route("/api/benchmark")
def api_benchmark():
    """Runs a live benchmark comparing HTML vs M2A JSON for the dashboard."""
    import time
    import tiktoken
    from html.parser import HTMLParser
    
    enc = tiktoken.get_encoding("cl100k_base")
    product_id = request.args.get("product_id", "prod_001")
    query = request.args.get("query", "is this in stock?")
    
    # 1. Simulate HTML Request
    start = time.time()
    html_product = get_product(product_id)
    html_content = render_template("product.html", product=html_product)
    html_latency = (time.time() - start) * 1000
    
    # Strip tags for a realistic agent DOM parse
    class HTMLTextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.res = []
        def handle_data(self, d):
            if d.strip():
                self.res.append(d.strip())
    
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    html_tokens = len(enc.encode(' '.join(extractor.res)))
    
    # 2. Simulate JSON Request
    start = time.time()
    from collections import namedtuple
    DetectionMock = namedtuple('DetectionMock', ['is_agent', 'agent_intent', 'to_dict'])
    det = DetectionMock(is_agent=True, agent_intent=None, to_dict=lambda: {})
    
    # Force the query into request args for the classifier
    request.args = {"query": query}
    json_response = _handle_agent_product_request(html_product, det)
    json_latency = (time.time() - start) * 1000
    
    json_data = json_response.get_data(as_text=True)
    json_tokens = len(enc.encode(json_data))
    
    parsed_json = json_response.get_json()
    classified_intent = parsed_json.get("intent", {}).get("classified_as", "UNKNOWN")
    
    return jsonify({
        "html": {
            "latency_ms": round(html_latency + 15, 2), # Add fake network latency for realism
            "tokens": html_tokens,
            "size_kb": round(len(html_content.encode('utf-8')) / 1024, 2)
        },
        "m2a": {
            "latency_ms": round(json_latency + 15, 2),
            "tokens": json_tokens,
            "size_kb": round(len(json_data.encode('utf-8')) / 1024, 2),
            "classified_intent": classified_intent
        }
    })

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
