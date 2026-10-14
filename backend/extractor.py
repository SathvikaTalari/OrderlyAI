"""
Order Extraction module for OrderMitra AI.
Formats prompts for Gemma 3, invokes local Ollama, sanitizes and validates JSON,
and strictly enforces rules against hallucinating missing information.
Includes an offline fallback extractor for testing when Ollama is unavailable.
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from backend.ollama_service import generate_local_completion
from backend.config import DEFAULT_MODEL, DEFAULT_OLLAMA_URL

SYSTEM_PROMPT = """You are an accurate, strict order information extractor for a local business order management system called OrderMitra AI.
Your sole job is to extract customer details and ordered items from unstructured messages (like WhatsApp, SMS, or Instagram messages) into valid JSON.

Strict Schema Requirements:
{
  "customer_name": string or null,
  "customer_phone": string or null,
  "delivery_date": string or null,
  "delivery_instructions": string or null,
  "items": [
    {
      "product_name": string,
      "quantity": number,
      "unit": string or null,
      "unit_price": number or null
    }
  ],
  "notes": string or null
}

CRITICAL ACCURACY RULES:
1. NEVER INVENT, GUESS, OR HALLUCINATE missing details.
2. If customer name is NOT mentioned, set customer_name to null.
3. If phone number is NOT mentioned, set customer_phone to null.
4. If delivery date is NOT mentioned, set delivery_date to null.
5. If delivery instructions are NOT mentioned, set delivery_instructions to null.
6. If product price is NOT explicitly stated in the message, set unit_price to null.
7. Only extract items actually requested by the customer.
8. Output ONLY the raw JSON object. Do not wrap with explanations or greetings."""


def build_user_prompt(raw_message: str) -> str:
    """Builds the extraction prompt for Gemma 3."""
    return f"""Please extract the order information from the following customer message into the specified JSON schema.
Remember: Do NOT invent missing details. Use null for absent fields.

Customer Message:
\"\"\"
{raw_message.strip()}
\"\"\"

Output strictly valid JSON:"""


def clean_and_parse_json(text: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Sanitizes raw model output to extract and parse valid JSON.
    Handles markdown code fences, trailing commas, and wrapping text.
    """
    if not text or not text.strip():
        return False, None, "Empty response received from AI model."

    cleaned = text.strip()

    # Remove markdown code blocks if present
    if "```" in cleaned:
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Find the outermost JSON object if surrounded by preamble/postscript
    brace_match = re.search(r"(\{[\s\S]*\})", cleaned)
    if brace_match:
        cleaned = brace_match.group(1).strip()

    # Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            return False, None, f"Expected a JSON object, but got {type(data).__name__}."
        
        # Normalize fields
        normalized = normalize_extracted_data(data)
        return True, normalized, None
    except json.JSONDecodeError as exc:
        return False, None, f"Invalid JSON returned by AI: {str(exc)}. Raw output: {text[:200]}"


def normalize_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes extracted fields to ensure strict data integrity.
    Never invents data; converts 'None', 'N/A', 'unknown' strings to None.
    """
    def sanitize_field(val: Any) -> Optional[str]:
        if val is None:
            return None
        val_str = str(val).strip()
        if val_str.lower() in ("", "null", "none", "n/a", "unknown", "not specified", "nil"):
            return None
        return val_str

    customer_name = sanitize_field(data.get("customer_name"))
    customer_phone = sanitize_field(data.get("customer_phone"))
    delivery_date = sanitize_field(data.get("delivery_date"))
    delivery_instructions = sanitize_field(data.get("delivery_instructions"))
    notes = sanitize_field(data.get("notes"))

    raw_items = data.get("items")
    items: List[Dict[str, Any]] = []

    if isinstance(raw_items, list):
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            
            p_name = sanitize_field(raw_item.get("product_name"))
            if not p_name:
                continue

            # Quantity handling
            qty_raw = raw_item.get("quantity")
            try:
                if qty_raw is not None and str(qty_raw).strip() != "":
                    qty = float(qty_raw)
                else:
                    qty = 1.0
            except (ValueError, TypeError):
                qty = 1.0

            unit = sanitize_field(raw_item.get("unit"))

            # Unit price handling (Strictly null if absent)
            price_raw = raw_item.get("unit_price")
            unit_price = None
            if price_raw is not None and str(price_raw).strip() != "":
                try:
                    price_str = str(price_raw).replace("$", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
                    unit_price = float(price_str)
                except (ValueError, TypeError):
                    unit_price = None

            items.append({
                "product_name": p_name,
                "quantity": qty,
                "unit": unit or "",
                "unit_price": unit_price if unit_price is not None else "",
            })

    return {
        "customer_name": customer_name or "",
        "customer_phone": customer_phone or "",
        "delivery_date": delivery_date or "",
        "delivery_instructions": delivery_instructions or "",
        "items": items,
        "notes": notes or "",
    }


def extract_order_offline_fallback(raw_message: str) -> Dict[str, Any]:
    """
    Intelligent heuristic parser used when Ollama is offline or for instant local testing.
    Extracts phone numbers, potential customer names, items with units/quantities,
    delivery instructions, and prices strictly from explicit message tokens.
    """
    text = raw_message.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    customer_name = ""
    customer_phone = ""
    delivery_date = ""
    delivery_instructions = ""
    items = []

    # 1. Phone number detection
    phone_pattern = r"(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}|\b\d{10,12}\b"
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        customer_phone = phone_match.group(0).replace(" ", "").replace("-", "")

    # 2. Customer name detection
    name_patterns = [
        r"(?:name|from|customer|regards|thanks|thank you|by)[,:\s-]+([A-Za-z\s]{2,25})",
        r"(?:this is|i am|myself)\s+([A-Za-z]{2,25})",
    ]
    for pattern in name_patterns:
        name_match = re.search(pattern, text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            if candidate.lower() not in ("ordering", "sending", "interested", "please", "urgent"):
                customer_name = candidate
                break

    # 3. Delivery date & instructions
    date_patterns = [
        r"(?:deliver|delivery|by|on|date)[:\s-]+((?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?))",
        r"\b(?:tomorrow|today|day after tomorrow)\b",
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            delivery_date = date_match.group(0).strip()
            break

    instr_patterns = [
        r"(?:instruction|note|address|drop at|deliver at|call before)[:\s-]+(.*)",
        r"(?:leave with security|call when arriving|urgent delivery|deliver before \d+ ?[ap]m)",
    ]
    for pattern in instr_patterns:
        instr_match = re.search(pattern, text, re.IGNORECASE)
        if instr_match:
            delivery_instructions = instr_match.group(0).strip()
            break

    # 4. Item extraction
    unit_regex = r"(?:kg|g|gm|grams|kilograms|liters|liter|ltr|l|ml|packets|packet|pkts|pkt|boxes|box|pieces|piece|pcs|pc|dozen|doz|bottles|bottle|bags|bag)"
    
    candidate_lines = []
    for line in lines:
        subparts = re.split(r"[,;•\*\-]\s*", line)
        for part in subparts:
            part = part.strip()
            if part:
                candidate_lines.append(part)

    for item_str in candidate_lines:
        if any(w in item_str.lower() for w in ["hello", "hi ", "dear", "regards", "thank", "address", "phone", "total", "paytm", "gpay", "upi"]):
            continue
        if phone_match and phone_match.group(0) in item_str:
            continue

        # Strip conversational prefix words
        candidate_text = re.sub(
            r"^(?:please\s+send|please\s+give|please\s+deliver|please|send\s+me|send|give\s+me|give|need|want|and|plus|add|\d+[\.\)]|\-|\*)\s+",
            "",
            item_str,
            flags=re.IGNORECASE,
        ).strip()

        # Pattern: [Qty] [Optional Unit] [Product Name] [@ or at or for Optional Price]
        item_match = re.search(
            rf"^(\d+(?:\.\d+)?)\s*({unit_regex})?\s+(?:of\s+)?(.+?)(?:\s*(?:@|at|for|rs\.?|₹)\s*(\d+(?:\.\d+)?)(?:[/\s].*)?)?$",
            candidate_text,
            re.IGNORECASE,
        )

        if item_match:
            qty_val = float(item_match.group(1))
            unit_val = item_match.group(2) or ""
            prod_val = item_match.group(3).strip()
            price_val = float(item_match.group(4)) if item_match.group(4) else ""
            if prod_val and len(prod_val) > 1:
                items.append({
                    "product_name": prod_val,
                    "quantity": qty_val,
                    "unit": unit_val,
                    "unit_price": price_val,
                })
        else:
            # Reverse pattern: "Basmati rice 2 kg"
            rev_match = re.search(
                rf"^(.+?)\s+(\d+(?:\.\d+)?)\s*({unit_regex})?(?:\s*(?:@|at|for|rs\.?|₹)\s*(\d+(?:\.\d+)?)(?:[/\s].*)?)?$",
                candidate_text,
                re.IGNORECASE,
            )
            if rev_match and rev_match.group(1).lower() not in ("deliver", "date", "call"):
                prod_val = rev_match.group(1).strip()
                qty_val = float(rev_match.group(2))
                unit_val = rev_match.group(3) or ""
                price_val = float(rev_match.group(4)) if rev_match.group(4) else ""
                if prod_val and len(prod_val) > 1:
                    items.append({
                        "product_name": prod_val,
                        "quantity": qty_val,
                        "unit": unit_val,
                        "unit_price": price_val,
                    })

    if not items and len(lines) > 0:
        for line in lines:
            if not any(w in line.lower() for w in ["hi", "hello", "thanks", "phone", "deliver"]):
                items.append({
                    "product_name": line,
                    "quantity": 1.0,
                    "unit": "",
                    "unit_price": "",
                })

    return {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "delivery_date": delivery_date,
        "delivery_instructions": delivery_instructions,
        "items": items,
        "notes": "Extracted via Local Heuristic Engine (Offline Mode)",
    }


def extract_order_from_message(
    raw_message: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    allow_fallback: bool = True,
) -> Tuple[bool, Dict[str, Any], Optional[str], str]:
    """
    Main extraction pipeline.
    Attempts extraction via local Ollama (Gemma 3).
    If Ollama is offline or unavailable and allow_fallback is True,
    it falls back to the local heuristic engine.
    """
    if not raw_message or not raw_message.strip():
        return False, {}, "Customer message is empty. Please paste an order message to extract.", "none"

    user_prompt = build_user_prompt(raw_message)

    # 1. Attempt Local AI via Ollama
    ai_success, response_text, ai_error = generate_local_completion(
        prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        model=model,
        base_url=base_url,
    )

    if ai_success and response_text:
        parse_ok, parsed_data, parse_err = clean_and_parse_json(response_text)
        if parse_ok and parsed_data:
            return True, parsed_data, None, f"Ollama ({model})"
        else:
            if allow_fallback:
                fallback_data = extract_order_offline_fallback(raw_message)
                return True, fallback_data, f"AI returned invalid JSON: {parse_err}. Switched to local heuristic engine.", "Local Heuristic Fallback"
            return False, {}, f"AI output could not be parsed as valid JSON: {parse_err}", f"Ollama ({model})"

    # 2. Ollama connection or model error fallback
    if allow_fallback:
        fallback_data = extract_order_offline_fallback(raw_message)
        return (
            True,
            fallback_data,
            f"Ollama AI unavailable: {ai_error}. Extracted using local offline rule-based parser.",
            "Local Heuristic Fallback",
        )

    return False, {}, ai_error or "Unknown error calling local AI.", "none"
