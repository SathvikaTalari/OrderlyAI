"""
Intelligence module for OrderlyAI.
Provides:
  - Smart order validation (missing fields, ambiguous items, missing prices)
  - Business Memory (returning customer suggestions from order history)
  - Price & Duplicate Guard (catalog price comparison, duplicate detection)
  - Telugu-English mixed message pre-processing
"""

import re
import sqlite3
import difflib
from typing import Dict, List, Any, Optional, Tuple
from backend.config import DATABASE_PATH


# ─────────────────────────────────────────────────────────────────────────────
# 1. SMART ORDER INTELLIGENCE — Validation & Warnings
# ─────────────────────────────────────────────────────────────────────────────

def analyze_order_quality(extracted: Dict[str, Any], db_path: str = DATABASE_PATH) -> Dict[str, Any]:
    """
    Analyzes an extracted order dict for common issues:
    - Missing customer name / phone
    - No delivery date or instructions
    - Items missing quantity or unit
    - Items with no price (and not in catalog)
    - Ambiguous product names
    Returns a structured report with issues categorized by severity.
    """
    issues = []
    suggestions = []
    score = 100  # start at 100, deduct for each issue

    items = extracted.get("items") or []

    # ── Customer info gaps ──
    if not extracted.get("customer_name") or str(extracted.get("customer_name")).strip() in ("", "null", "None"):
        issues.append({
            "severity": "warning",
            "field": "customer_name",
            "message": "Customer name is missing — consider asking the customer for their name.",
        })
        score -= 10

    if not extracted.get("customer_phone") or str(extracted.get("customer_phone")).strip() in ("", "null", "None"):
        issues.append({
            "severity": "warning",
            "field": "customer_phone",
            "message": "Phone number not found — you won't be able to contact this customer later.",
        })
        score -= 8

    if not extracted.get("delivery_date") or str(extracted.get("delivery_date")).strip() in ("", "null", "None"):
        issues.append({
            "severity": "info",
            "field": "delivery_date",
            "message": "Delivery date/time not specified — confirm with the customer when they need it.",
        })
        score -= 5

    if not extracted.get("delivery_instructions") or str(extracted.get("delivery_instructions")).strip() in ("", "null", "None"):
        issues.append({
            "severity": "info",
            "field": "delivery_instructions",
            "message": "No delivery address or instructions — ask the customer for their full address.",
        })
        score -= 5

    # ── Item-level checks ──
    if not items:
        issues.append({
            "severity": "error",
            "field": "items",
            "message": "No product items were detected in this message. Please add items manually.",
        })
        score -= 30
    else:
        for idx, item in enumerate(items):
            name = (item.get("product_name") or "").strip()
            qty = item.get("quantity")
            price = item.get("unit_price")

            if not name:
                issues.append({
                    "severity": "error",
                    "field": f"item[{idx}].product_name",
                    "message": f"Item #{idx + 1} has no product name — remove or correct it.",
                })
                score -= 10

            if qty is None or str(qty).strip() in ("", "null", "None", "0"):
                issues.append({
                    "severity": "warning",
                    "field": f"item[{idx}].quantity",
                    "message": f"'{name}' has no quantity — defaulting to 1. Please verify.",
                })
                score -= 5

            if price is None or str(price).strip() in ("", "null", "None"):
                # Look up catalog price
                catalog_price = get_catalog_price(name, db_path)
                if catalog_price is not None:
                    suggestions.append({
                        "item": name,
                        "type": "catalog_price",
                        "message": f"'{name}' has no price in the message. Catalog price: ₹{catalog_price:.2f}.",
                        "suggested_price": catalog_price,
                    })
                else:
                    issues.append({
                        "severity": "info",
                        "field": f"item[{idx}].unit_price",
                        "message": f"'{name}' has no price — you may want to add it manually or check your catalog.",
                    })
                score -= 3

            # Ambiguous product name check (very short or generic)
            if name and len(name) <= 2:
                issues.append({
                    "severity": "warning",
                    "field": f"item[{idx}].product_name",
                    "message": f"Product name '{name}' seems very short — is this correct?",
                })
                score -= 4

    score = max(0, score)

    # Quality tier
    if score >= 85:
        quality_label = "Excellent"
        quality_color = "#059669"
    elif score >= 65:
        quality_label = "Good"
        quality_color = "#2563EB"
    elif score >= 40:
        quality_label = "Needs Attention"
        quality_color = "#D97706"
    else:
        quality_label = "Incomplete"
        quality_color = "#DC2626"

    return {
        "score": score,
        "quality_label": quality_label,
        "quality_color": quality_color,
        "issues": issues,
        "suggestions": suggestions,
        "error_count": sum(1 for i in issues if i["severity"] == "error"),
        "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
        "info_count": sum(1 for i in issues if i["severity"] == "info"),
    }


def get_catalog_price(product_name: str, db_path: str = DATABASE_PATH) -> Optional[float]:
    """Looks up a product's catalog price by fuzzy name match."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return None
        cursor.execute("SELECT name, unit_price FROM products WHERE unit_price IS NOT NULL;")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return None
        names = [r["name"] for r in rows]
        matches = difflib.get_close_matches(product_name.lower(), [n.lower() for n in names], n=1, cutoff=0.6)
        if matches:
            for row in rows:
                if row["name"].lower() == matches[0]:
                    return float(row["unit_price"])
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. BUSINESS MEMORY — Returning Customer Lookup
# ─────────────────────────────────────────────────────────────────────────────

def find_returning_customer(phone: str, name: str = "", db_path: str = DATABASE_PATH) -> Optional[Dict[str, Any]]:
    """
    Searches order history for a returning customer by phone or name.
    Returns their last order's items and summary for suggestion.
    """
    if not phone and not name:
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        order_row = None
        if phone and phone.strip():
            cursor.execute(
                "SELECT * FROM orders WHERE customer_phone = ? ORDER BY id DESC LIMIT 1;",
                (phone.strip(),),
            )
            order_row = cursor.fetchone()

        if not order_row and name and len(name.strip()) >= 3:
            cursor.execute(
                "SELECT * FROM orders WHERE customer_name LIKE ? ORDER BY id DESC LIMIT 1;",
                (f"%{name.strip()}%",),
            )
            order_row = cursor.fetchone()

        if not order_row:
            conn.close()
            return None

        order_id = order_row["id"]
        cursor.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC;",
            (order_id,),
        )
        items = [dict(r) for r in cursor.fetchall()]

        # Count total orders from this customer
        if phone:
            cursor.execute(
                "SELECT COUNT(*) FROM orders WHERE customer_phone = ?;",
                (phone.strip(),),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM orders WHERE customer_name LIKE ?;",
                (f"%{name.strip()}%",),
            )
        total_orders = cursor.fetchone()[0]
        conn.close()

        return {
            "found": True,
            "customer_name": order_row["customer_name"],
            "customer_phone": order_row["customer_phone"],
            "last_order_number": order_row["order_number"],
            "last_order_date": order_row["created_at"],
            "last_order_total": order_row["total_amount"],
            "last_order_status": order_row["status"],
            "total_orders": total_orders,
            "last_items": items,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. PRICE GUARD — Compare against catalog, detect anomalies
# ─────────────────────────────────────────────────────────────────────────────

def check_price_anomalies(items: List[Dict[str, Any]], db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """
    For each item in the order, compares the extracted unit_price against the
    product catalog. Returns a list of price anomaly alerts.
    """
    alerts = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return alerts
        cursor.execute("SELECT name, unit_price, min_price, max_price FROM products WHERE unit_price IS NOT NULL;")
        catalog = {r["name"].lower(): dict(r) for r in cursor.fetchall()}
        conn.close()

        for item in items:
            name = (item.get("product_name") or "").strip()
            price = item.get("unit_price")
            if not name or price is None or str(price).strip() in ("", "null", "None"):
                continue
            try:
                price = float(price)
            except (ValueError, TypeError):
                continue

            matches = difflib.get_close_matches(name.lower(), list(catalog.keys()), n=1, cutoff=0.6)
            if matches:
                cat = catalog[matches[0]]
                cat_price = cat.get("unit_price")
                min_p = cat.get("min_price")
                max_p = cat.get("max_price")
                if cat_price:
                    diff_pct = abs(price - cat_price) / cat_price * 100
                    if diff_pct > 25:
                        alerts.append({
                            "item": name,
                            "entered_price": price,
                            "catalog_price": cat_price,
                            "diff_pct": round(diff_pct, 1),
                            "message": (
                                f"⚠️ '{name}' price ₹{price:.2f} differs by {diff_pct:.0f}% "
                                f"from catalog price ₹{cat_price:.2f}."
                            ),
                        })
                if min_p and max_p:
                    if price < min_p or price > max_p:
                        alerts.append({
                            "item": name,
                            "entered_price": price,
                            "min_price": min_p,
                            "max_price": max_p,
                            "message": (
                                f"🚨 '{name}' price ₹{price:.2f} is outside the allowed range "
                                f"₹{min_p:.2f}–₹{max_p:.2f}."
                            ),
                        })
    except Exception:
        pass
    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# 4. DUPLICATE GUARD — Detect near-duplicate recent orders
# ─────────────────────────────────────────────────────────────────────────────

def detect_duplicate_order(
    customer_phone: str,
    items: List[Dict[str, Any]],
    within_minutes: int = 30,
    db_path: str = DATABASE_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Checks if a very similar order was recently submitted for the same customer.
    Returns the potential duplicate order record if found.
    """
    if not customer_phone or not items:
        return None
    try:
        import datetime
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cutoff = (datetime.datetime.now() - datetime.timedelta(minutes=within_minutes)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            SELECT o.id, o.order_number, o.created_at, o.total_amount, o.status
            FROM orders o
            WHERE o.customer_phone = ? AND o.created_at >= ?
            ORDER BY o.id DESC;
            """,
            (customer_phone.strip(), cutoff),
        )
        recent_orders = cursor.fetchall()
        if not recent_orders:
            conn.close()
            return None

        new_product_names = {(item.get("product_name") or "").lower().strip() for item in items}

        for order_row in recent_orders:
            cursor.execute(
                "SELECT product_name FROM order_items WHERE order_id = ?;",
                (order_row["id"],),
            )
            existing_names = {r["product_name"].lower().strip() for r in cursor.fetchall()}
            overlap = len(new_product_names & existing_names)
            if overlap > 0 and overlap >= min(len(new_product_names), len(existing_names)):
                conn.close()
                return {
                    "order_number": order_row["order_number"],
                    "created_at": order_row["created_at"],
                    "total_amount": order_row["total_amount"],
                    "status": order_row["status"],
                    "overlap_count": overlap,
                }
        conn.close()
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 5. TELUGU-ENGLISH PRE-PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

# Common Telugu-English transliteration mappings for grocery/retail terms
TELUGU_EN_MAPPING = {
    # Numbers
    "okati": "1", "rendu": "2", "moodu": "3", "nalugu": "4", "aidu": "5",
    "aaru": "6", "edu": "7", "enimidi": "8", "tommidi": "9", "padi": "10",
    # Units
    "kilo": "kg", "kilolu": "kg", "kilos": "kg", "gramu": "g", "gramulu": "g",
    "liter": "ltr", "liters": "ltr", "packet": "packet", "packets": "packets",
    "paki": "packet", "packetlu": "packets", "bottle": "bottle", "dabbulu": "boxes",
    # Delivery & Timing
    "repu": "tomorrow", "podduna": "morning", "sayantram": "evening", "madhyahnam": "afternoon",
    "ippudu": "now", "tvaraga": "quickly", "urgently": "urgently", "gantalu": "o'clock",
    # Request phrases
    "kavali": "need", "ivvu": "give", "ivvandi": "please give", "pampu": "send",
    "pampandi": "please send", "pampinchu": "send", "pampinchandi": "please send",
    "pathikilo": "quarter kg", "aragilo": "half kg", "malli": "again", "adhe": "same",
    # Common products (Telugu transliterated)
    "palu": "milk", "nune": "oil", "uppu": "salt", "biyyam": "rice",
    "chakkera": "sugar", "panchadara": "sugar", "bellam": "jaggery",
    "kandipappu": "toor dal", "pappu": "dal", "minumulu": "urad dal",
    "pesarlu": "moong dal", "senagapappu": "chana dal",
    "godhuma": "wheat", "pindi": "flour", "godhumapindi": "wheat flour",
    "maidha": "maida", "kura": "vegetable", "avakaya": "mango pickle",
    "chintapandu": "tamarind", "jeelakarra": "cumin", "karam": "chilli powder",
    "pasupu": "turmeric", "allam": "ginger", "vellulli": "garlic",
    "ulli": "onion", "ullipayalu": "onions", "tomato": "tomatoes",
    "tamatalu": "tomatoes", "batani": "peas", "dondakaya": "tindora",
    "bendakaya": "okra", "vankaya": "brinjal",
    # Common Telugu Unicode terms
    "బియ్యం": "rice", "పాలు": "milk", "నూనె": "oil", "కందిపప్పు": "toor dal",
    "చక్కెర": "sugar", "ఉప్పు": "salt", "గోధుమ": "wheat", "పిండి": "flour",
    "కిలో": "kg", "కిలోలు": "kg", "ప్యాకెట్లు": "packets", "లీటర్": "ltr",
}

def preprocess_telugu_english(message: str) -> Tuple[str, bool]:
    """
    Detects Telugu script or transliterated Telugu words in a message
    and normalizes them for better AI and rule-based extraction.
    Returns (processed_message, was_telugu_detected).
    """
    telugu_script_pattern = re.compile(r'[\u0C00-\u0C7F]')
    has_telugu_script = bool(telugu_script_pattern.search(message))

    processed = message

    # Replace known Telugu Unicode words
    for te_word, en_word in TELUGU_EN_MAPPING.items():
        if re.search(r'[\u0C00-\u0C7F]', te_word):
            processed = processed.replace(te_word, en_word)

    # Replace transliterated words
    words = processed.split()
    normalized_words = []
    found_translit = False
    for word in words:
        cleaned_word = re.sub(r'[^\w]', '', word.lower())
        if cleaned_word in TELUGU_EN_MAPPING:
            normalized_words.append(TELUGU_EN_MAPPING[cleaned_word])
            found_translit = True
        else:
            normalized_words.append(word)
    processed = " ".join(normalized_words)

    was_telugu = has_telugu_script or found_translit
    return processed, was_telugu


# ─────────────────────────────────────────────────────────────────────────────
# 6. INVENTORY CHECK — Stock level guard before order confirmation
# ─────────────────────────────────────────────────────────────────────────────

def check_stock_availability(items: List[Dict[str, Any]], db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """
    Checks each order item against the inventory catalog.
    Returns a list of stock warnings for items below required quantity.
    """
    warnings = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return warnings

        cursor.execute("SELECT name, stock_quantity, low_stock_threshold FROM products;")
        catalog = {r["name"].lower(): dict(r) for r in cursor.fetchall()}
        conn.close()

        for item in items:
            name = (item.get("product_name") or "").strip()
            qty = item.get("quantity") or 1
            try:
                qty = float(qty)
            except (ValueError, TypeError):
                qty = 1.0

            matches = difflib.get_close_matches(name.lower(), list(catalog.keys()), n=1, cutoff=0.65)
            if matches:
                cat = catalog[matches[0]]
                stock = cat.get("stock_quantity")
                threshold = cat.get("low_stock_threshold") or 0
                if stock is not None:
                    if stock < qty:
                        warnings.append({
                            "item": name,
                            "requested": qty,
                            "available": stock,
                            "severity": "error",
                            "message": f"🚨 '{name}' — only {stock} in stock, but {qty} ordered.",
                        })
                    elif stock <= threshold:
                        warnings.append({
                            "item": name,
                            "requested": qty,
                            "available": stock,
                            "severity": "warning",
                            "message": f"⚠️ '{name}' is running low (only {stock} left after this order).",
                        })
    except Exception:
        pass
    return warnings
