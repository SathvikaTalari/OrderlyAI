"""
Unit tests for OrderMitra AI Extraction & Prompt Sanitization Module.
"""

from backend.extractor import (
    clean_and_parse_json,
    normalize_extracted_data,
    extract_order_offline_fallback,
    extract_order_from_message,
)


def test_clean_and_parse_valid_json():
    """Tests clean JSON parsing."""
    raw = '{"customer_name": "Rohan", "customer_phone": "9876543210", "items": [{"product_name": "Bread", "quantity": 2, "unit": "pkt", "unit_price": 40}]}'
    ok, data, err = clean_and_parse_json(raw)
    assert ok is True
    assert err is None
    assert data["customer_name"] == "Rohan"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name"] == "Bread"
    assert data["items"][0]["quantity"] == 2.0


def test_clean_and_parse_markdown_fences():
    """Tests handling when model wraps output in markdown code blocks."""
    raw = """Here is the extracted JSON:
```json
{
  "customer_name": "Kavita",
  "customer_phone": null,
  "delivery_date": "Tomorrow",
  "delivery_instructions": null,
  "items": [
    {
      "product_name": "Organic Honey",
      "quantity": 1,
      "unit": "bottle",
      "unit_price": null
    }
  ]
}
```
Hope this helps!"""
    ok, data, err = clean_and_parse_json(raw)
    assert ok is True
    assert err is None
    assert data["customer_name"] == "Kavita"
    assert data["customer_phone"] == ""  # Normalized to empty string
    assert data["items"][0]["product_name"] == "Organic Honey"
    assert data["items"][0]["unit_price"] == ""  # Never invented


def test_clean_and_parse_invalid_json():
    """Tests graceful failure when AI output is malformed."""
    raw = "This is not json at all."
    ok, data, err = clean_and_parse_json(raw)
    assert ok is False
    assert data is None
    assert "Invalid JSON" in err or "Expected" in err


def test_normalize_never_hallucinates():
    """Tests normalization ensures null/unknown values remain empty and not fabricated."""
    data = {
        "customer_name": "null",
        "customer_phone": "N/A",
        "delivery_date": "unknown",
        "delivery_instructions": None,
        "items": [
            {
                "product_name": "Wheat Flour",
                "quantity": "5",
                "unit": "kg",
                "unit_price": "none",
            }
        ],
    }
    normalized = normalize_extracted_data(data)
    assert normalized["customer_name"] == ""
    assert normalized["customer_phone"] == ""
    assert normalized["delivery_date"] == ""
    assert normalized["delivery_instructions"] == ""
    assert len(normalized["items"]) == 1
    assert normalized["items"][0]["product_name"] == "Wheat Flour"
    assert normalized["items"][0]["quantity"] == 5.0
    assert normalized["items"][0]["unit_price"] == ""


def test_offline_fallback_extractor():
    """Tests intelligent heuristic fallback on unstructured kirana WhatsApp order."""
    message = """Hi Bhaiya, please send 2 kg sugar, 1 kg salt @ 30, and 3 packets milk.
Deliver tomorrow. Call 9876543210.
Thanks, Suresh Sharma"""
    extracted = extract_order_offline_fallback(message)
    assert extracted["customer_phone"] == "9876543210"
    assert "Suresh" in extracted["customer_name"]
    assert len(extracted["items"]) >= 2
    # Verify price extracted only if explicitly given
    salt_item = next((i for i in extracted["items"] if "salt" in i["product_name"].lower()), None)
    if salt_item:
        assert salt_item["unit_price"] == 30.0


def test_extract_order_with_offline_fallback():
    """Tests full pipeline returns valid order and clear notice when Ollama is offline."""
    message = "Need 5 kg rice and 2 kg dal. Deliver today. Contact 9123456789. From Anita."
    ok, data, notice, engine = extract_order_from_message(
        raw_message=message,
        base_url="http://localhost:9999",  # Non-existent port to test offline behavior
        allow_fallback=True,
    )
    assert ok is True
    assert "Anita" in data["customer_name"]
    assert data["customer_phone"] == "9123456789"
    assert "Fallback" in engine
    assert "Ollama AI unavailable" in notice
