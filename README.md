# M2A — Merchant-to-Agent Bridge

**Token-Optimized Dual-Reality Storefront for AI Agents**

M2A is a Flask-based middleware routing system designed for the **Razorpay AI Buildathon 2026 (AI Growth & Agentic Commerce Track)**. 

It serves two different representations of the same e-commerce storefront depending on who (or what) is requesting it:
- **For Humans**: A full visual frontend (Y2K aesthetic, glassmorphism UI) returning standard HTML.
- **For AI Agents**: Bypasses the DOM entirely to return a hyper-lightweight, intent-pruned, data-only payload (reducing token consumption by up to 95%). For purchase intents, it attaches a live Razorpay test-mode payment link.

## Why this exists (The Token Economics Problem)

AI agents don't see web pages like humans do; they read raw HTML, DOM trees, or screenshots. Every byte of navigation chrome, inline CSS, tracking pixels, and boilerplate text costs the agent **tokens** (and therefore money) to parse. 

> *Reference: Cloudflare measured their own blog page at 16,180 tokens as raw HTML vs. 3,150 tokens as markdown.*

If reading a merchant's site costs an AI buyer too many tokens relative to the value of the information, the agent either abandons the site (lost sale) or reads a partial/cached version and hallucinates (broken trust). M2A solves this on the merchant side.

## Architecture

```text
                       [Incoming Request]
                                |
               +----------------+----------------+
               |                                 |
         [Human Browser]                   [AI Buyer Agent]
       (Accept: text/html)        (Accept: application/vnd.m2a+json)
               |                                 |
               v                                 v
     +-------------------+              +-------------------+
     | Human UI Layer    |              | Detection & ACP   |
     | Glassmorphism/Y2K |              | Negotiation Layer |
     | Storefront        |              +-------------------+
     +-------------------+                        |
                                                  v
                                        +-------------------+
                                        | Hybrid Intent     |
                                        | Router/Classifier |
                                        +-------------------+
                                           /      |      \
                            [Stock/Specs]   [Compare]   [Buy Intent]
                                  |               |           |
                                  |               |           v
                                  |               |     +-------------------+
                                  |               |     | Razorpay API      |
                                  |               |     | Order/PaymentLink |
                                  |               |     +-------------------+
                                  \               |           /
                                   \              |          /
                                    v             v         v
                                    +-----------------------+
                                    | Semantic Pruner       |
                                    | (<500 tokens payload) |
                                    +-----------------------+
                                                |
                                                v
                                    +-----------------------+
                                    | Immutable Audit Trail |
                                    | (audit_trail.jsonl)   |
                                    +-----------------------+
```

## Setup & Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure environment:**
   Create a `.env` file (see `.env.example` when available) with your Razorpay Test API keys.
3. **Run the application:**
   ```bash
   python app.py
   ```

## Track Alignment (Razorpay AI Buildathon 2026)
- **Every money action explainable, bounded, and gated**: Enabled via the immutable JSONL audit trail and hard spend-cap limits applied before payment link generation.
- **Show the audit trail and one failure handled gracefully**: The test harness demonstrates graceful failure when handling ambiguous intents.
- **Deterministic solutions where AI is unnecessary**: Uses a hybrid classifier (rules-first, ML-fallback) rather than forcing LLMs to do basic routing.
