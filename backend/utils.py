"""
Utilities and sample data presets for Orderly AI.
Provides realistic sample customer messages (WhatsApp, SMS, Instagram DMs)
for 1-click testing and formatting helpers.
"""

from typing import Dict, List, Any

SAMPLE_MESSAGES = {
    "Kirana / Grocery WhatsApp Order": """Hi Bhaiya! Please send the following to Flat 402, Sunshine Heights tomorrow morning before 10 AM:
- 5 kg Aashirvaad Atta
- 2 kg Fortune Sunflower Oil @ 140/kg
- 1 kg Tata Salt
- 2 packets Amul Butter (100g)
- 1 dozen Farm Fresh Eggs
Please leave with security if I am not available.
Thanks, Rajesh Kumar, 9876543210""",

    "Bakery & Cafe Party Order": """Hey! I need to order treats for an office celebration on Friday:
- 2 kg Belgian Chocolate Truffle Cake
- 15 veg puff patties @ 25
- 10 blueberry muffins
Deliver to Tech Park, Tower B reception by 3 PM.
Name: Sneha Sharma (Ph: 9123456789). Please pack with knife and candles.""",

    "Organic Farm / Veggie Box": """Hello Orderly AI! Order for Anita Desai:
Organic Spinach - 2 bunches
Tomatoes - 3 kg @ 40
Potatoes - 5 kg
Carrots - 1 kg @ 60
Fresh Mint - 1 bunch
Deliver on Saturday. Call 9845012345 when you reach the gate.""",

    "Minimal Message (Missing Details)": """Need 3 packs of green tea and 2 jars of honey urgently.
Drop at door.""",

    "Wholesale / Distributor": """Good morning! Please send the monthly stock replenishment:
- Parle-G Biscuits: 10 cartons @ 480/carton
- Maggi Noodles 70g: 5 cartons @ 960/carton
- Tata Tea Premium 250g: 50 packets @ 90 each
- Aashirvaad Salt 1kg: 30 packets @ 22 each
Payment via UPI. Deliver to Godown No. 3, APMC Yard. Contact: Manoj Wholesale, 9700011223""",
}


def format_currency(amount: Any, symbol: str = "₹") -> str:
    """Formats float/int amount with currency symbol or returns '-'."""
    if amount is None or amount == "" or amount == "null":
        return "-"
    try:
        val = float(amount)
        return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return str(amount)


def get_status_color(status: str) -> str:
    """Returns aesthetic status color hex code."""
    colors = {
        "Pending": "#F59E0B",          # Amber
        "Confirmed": "#3B82F6",        # Blue
        "Preparing": "#8B5CF6",        # Purple
        "Out for Delivery": "#06B6D4", # Cyan
        "Delivered": "#10B981",        # Green
        "Cancelled": "#EF4444",        # Red
    }
    return colors.get(status, "#6B7280")
