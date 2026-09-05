import pytest
import json
from app import app
from m2a.detector import detect_client
from m2a.classifier import classify_intent
from m2a.pruner import prune_product_data
from m2a.catalog import get_product

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_catalog_retrieval():
    product = get_product("prod_001")
    assert product is not None
    assert product["name"] == "AuraX Pro Wireless Noise-Cancelling Headphones"
    assert "image_url" not in product  # We use images array now
    assert len(product["images"]) > 0

def test_detector():
    # Human detection
    human_headers = {"User-Agent": "Mozilla/5.0"}
    res = detect_client(human_headers)
    assert not res.is_agent
    
    # Explicit agent detection
    agent_headers = {"Signature-Agent": "1"}
    res = detect_client(agent_headers)
    assert res.is_agent

def test_classifier():
    # Explicit intent
    res = classify_intent({"intent": "BUY"})
    assert res.intent == "BUY"
    assert res.confidence == 1.0
    
    # ML Natural language classification
    res_stock = classify_intent({"query": "are these available right now?"})
    assert res_stock.intent == "STOCK"
    assert res_stock.confidence > 0.5
    
    # Unknown/Ambiguous
    res_amb = classify_intent({"query": "qwertyuiop asdfghjkl"})
    assert res_amb.intent == "AMBIGUOUS"
    assert res_amb.available_actions is not None

def test_pruner():
    product = get_product("prod_001")
    pruned = prune_product_data(product, "STOCK")
    
    assert "stock_count" in pruned
    assert "description" not in pruned
    assert "materials" not in pruned
    
    meta = pruned.get("_meta", {})
    assert meta["savings_percentage"] > 70.0

def test_human_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"text/html" in response.headers["Content-Type"].encode('utf-8')
    assert b"M2A" in response.data

def test_agent_catalog_route(client):
    response = client.get("/", headers={"Signature-Agent": "1"})
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/vnd.m2a+json"
    
    data = json.loads(response.data)
    assert "catalog" in data
    assert len(data["catalog"]) == 4

def test_agent_buy_route(client):
    response = client.get("/product/prod_001?intent=BUY", headers={"Signature-Agent": "1"})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["intent"]["classified_as"] == "BUY"
    assert "payment" in data
    assert "payment_link_url" in data["payment"]
