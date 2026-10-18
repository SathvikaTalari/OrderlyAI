"""
Business Insights module for OrderlyAI.
Provides analytics, trends, and actionable recommendations
based on the live SQLite order database.
"""

import sqlite3
import datetime
from typing import Dict, List, Any, Optional
from backend.config import DATABASE_PATH


def get_top_products(limit: int = 10, db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns the top N most frequently ordered products by order count."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                product_name,
                COUNT(*) AS order_count,
                SUM(quantity) AS total_quantity,
                ROUND(SUM(COALESCE(line_total, 0)), 2) AS total_revenue
            FROM order_items
            WHERE product_name IS NOT NULL AND product_name != ''
            GROUP BY LOWER(TRIM(product_name))
            ORDER BY order_count DESC
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_sales_trend(days: int = 14, db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns daily order count and revenue for the last N days."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT
                DATE(created_at) AS order_date,
                COUNT(*) AS order_count,
                ROUND(SUM(total_amount), 2) AS daily_revenue
            FROM orders
            WHERE created_at >= ? AND status != 'Cancelled'
            GROUP BY DATE(created_at)
            ORDER BY order_date ASC;
        """, (since,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_pending_deliveries(db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns orders currently in Pending, Confirmed, or Preparing status."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                o.order_number,
                o.customer_name,
                o.customer_phone,
                o.delivery_date,
                o.status,
                o.total_amount,
                o.created_at,
                COUNT(i.id) AS item_count
            FROM orders o
            LEFT JOIN order_items i ON o.id = i.order_id
            WHERE o.status IN ('Pending', 'Confirmed', 'Preparing', 'Out for Delivery')
            GROUP BY o.id
            ORDER BY o.created_at ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_top_customers(limit: int = 10, db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns the top N customers by total order value."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(customer_name, 'Unknown') AS customer_name,
                customer_phone,
                COUNT(*) AS order_count,
                ROUND(SUM(total_amount), 2) AS total_spent,
                MAX(created_at) AS last_order_date
            FROM orders
            WHERE status != 'Cancelled'
            GROUP BY LOWER(COALESCE(TRIM(customer_phone), customer_name))
            ORDER BY total_spent DESC
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_status_breakdown(db_path: str = DATABASE_PATH) -> Dict[str, int]:
    """Returns count of orders per status."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM orders
            GROUP BY status;
        """)
        rows = cursor.fetchall()
        conn.close()
        return {r["status"]: r["cnt"] for r in rows}
    except Exception:
        return {}


def get_revenue_summary(db_path: str = DATABASE_PATH) -> Dict[str, Any]:
    """Returns revenue summary: today, this week, this month, all time."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        week_start = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        month_start = now.strftime("%Y-%m-01")

        def rev(since):
            cursor.execute(
                "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'Cancelled' AND created_at >= ?;",
                (since,)
            )
            return round(cursor.fetchone()[0], 2)

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'Cancelled';")
        all_time = round(cursor.fetchone()[0], 2)

        # Average order value
        cursor.execute("SELECT COALESCE(AVG(total_amount), 0) FROM orders WHERE status != 'Cancelled' AND total_amount > 0;")
        avg_order = round(cursor.fetchone()[0], 2)

        conn.close()
        return {
            "today": rev(today),
            "this_week": rev(week_start),
            "this_month": rev(month_start),
            "all_time": all_time,
            "avg_order_value": avg_order,
        }
    except Exception:
        return {"today": 0, "this_week": 0, "this_month": 0, "all_time": 0, "avg_order_value": 0}


def generate_ai_insights(db_path: str = DATABASE_PATH) -> List[Dict[str, str]]:
    """
    Generates plain-language business insights from database patterns.
    Returns a list of insight cards with icon, title, and explanation.
    """
    insights = []
    try:
        top_products = get_top_products(5, db_path)
        trend = get_sales_trend(7, db_path)
        pending = get_pending_deliveries(db_path)
        revenue = get_revenue_summary(db_path)
        top_customers = get_top_customers(3, db_path)

        # Insight: Top product
        if top_products:
            p = top_products[0]
            insights.append({
                "icon": "🏆",
                "title": f"Best Seller: {p['product_name']}",
                "body": f"'{p['product_name']}' has been ordered {p['order_count']} times, "
                        f"totaling {p['total_quantity']:.1f} units and ₹{p['total_revenue']:,.2f} in sales.",
                "color": "#4F46E5",
            })

        # Insight: Pending deliveries alert
        pending_count = len(pending)
        if pending_count > 0:
            old_pending = [p for p in pending if p["status"] == "Pending"]
            insights.append({
                "icon": "📦",
                "title": f"{pending_count} Order(s) Awaiting Action",
                "body": f"You have {pending_count} active orders in your pipeline. "
                        + (f"{len(old_pending)} are still in 'Pending' status and may need confirmation." if old_pending else ""),
                "color": "#D97706",
            })

        # Insight: Revenue today
        if revenue["today"] > 0:
            insights.append({
                "icon": "💰",
                "title": f"Today's Revenue: ₹{revenue['today']:,.2f}",
                "body": f"This week so far: ₹{revenue['this_week']:,.2f}. "
                        f"This month: ₹{revenue['this_month']:,.2f}. "
                        f"Average order value: ₹{revenue['avg_order_value']:,.2f}.",
                "color": "#059669",
            })

        # Insight: Sales trend
        if len(trend) >= 2:
            last_two = trend[-2:]
            delta = last_two[-1]["daily_revenue"] - last_two[-2]["daily_revenue"]
            direction = "up" if delta >= 0 else "down"
            icon = "📈" if delta >= 0 else "📉"
            insights.append({
                "icon": icon,
                "title": f"Sales {direction.capitalize()} vs Yesterday",
                "body": f"Today's revenue is ₹{abs(delta):,.2f} {'more' if delta >= 0 else 'less'} than yesterday's "
                        f"₹{last_two[-2]['daily_revenue']:,.2f}.",
                "color": "#059669" if delta >= 0 else "#DC2626",
            })

        # Insight: Top customer
        if top_customers:
            c = top_customers[0]
            insights.append({
                "icon": "⭐",
                "title": f"Top Customer: {c['customer_name']}",
                "body": f"Your highest-value customer has placed {c['order_count']} orders "
                        f"worth ₹{c['total_spent']:,.2f} in total.",
                "color": "#7C3AED",
            })

        if not insights:
            insights.append({
                "icon": "ℹ️",
                "title": "No Insights Yet",
                "body": "Add your first orders to start seeing business intelligence and trends.",
                "color": "#64748B",
            })

    except Exception as e:
        insights.append({
            "icon": "⚠️",
            "title": "Insights Unavailable",
            "body": f"Could not compute insights: {e}",
            "color": "#DC2626",
        })

    return insights
