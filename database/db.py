"""
SQLite Database module for Orderly AI.
Provides tables, schema initialization, atomic transactions, and queries for orders and items.
"""

import sqlite3
import datetime
import uuid
from typing import Dict, List, Optional, Any
import pandas as pd
from backend.config import DATABASE_PATH, DEFAULT_STATUS


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a database connection with row factory enabled."""
    target_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes SQLite tables and indexes if they do not exist."""
    target_path = db_path or DATABASE_PATH
    conn = get_db_connection(target_path)
    try:
        cursor = conn.cursor()

        # Orders Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                customer_phone TEXT,
                delivery_date TEXT,
                delivery_instructions TEXT,
                raw_message TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                total_amount REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Order Items Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1.0,
                unit TEXT,
                unit_price REAL,
                line_total REAL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            );
            """
        )

        # Indexes for fast lookup & search
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_num ON orders(order_number);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_name ON orders(customer_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);")

        # Products / Inventory Catalog Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                unit TEXT DEFAULT 'pcs',
                unit_price REAL,
                min_price REAL,
                max_price REAL,
                stock_quantity REAL DEFAULT 0.0,
                low_stock_threshold REAL DEFAULT 5.0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")

        conn.commit()

        # Check if products catalog needs initial seeding
        cursor.execute("SELECT COUNT(*) FROM products;")
        if cursor.fetchone()[0] == 0:
            from backend.catalog import seed_demo_catalog
            seed_demo_catalog(target_path)
    finally:
        conn.close()


def generate_order_number() -> str:
    """Generates a human-friendly unique order reference e.g., ORD-20261014-A7F2."""
    now_str = datetime.datetime.now().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    return f"ORD-{now_str}-{unique_suffix}"


def create_order(
    order_data: Dict[str, Any],
    items: List[Dict[str, Any]],
    db_path: Optional[str] = None,
) -> int:
    """
    Creates a new order with its line items in an atomic transaction.
    Returns the newly created order ID.
    """
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_number = order_data.get("order_number") or generate_order_number()

    # Calculate item line totals and order total
    total_amount = 0.0
    processed_items = []
    for item in items:
        p_name = str(item.get("product_name", "")).strip()
        if not p_name:
            continue
        try:
            qty = float(item.get("quantity", 1.0))
        except (ValueError, TypeError):
            qty = 1.0

        unit = item.get("unit")
        unit = str(unit).strip() if unit else None

        unit_price = item.get("unit_price")
        if unit_price is not None and unit_price != "" and unit_price != "null":
            try:
                unit_price = float(unit_price)
                line_total = round(qty * unit_price, 2)
                total_amount += line_total
            except (ValueError, TypeError):
                unit_price = None
                line_total = None
        else:
            unit_price = None
            line_total = None

        processed_items.append({
            "product_name": p_name,
            "quantity": qty,
            "unit": unit,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (
                order_number, customer_name, customer_phone,
                delivery_date, delivery_instructions, raw_message,
                status, total_amount, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                order_number,
                order_data.get("customer_name") or None,
                order_data.get("customer_phone") or None,
                order_data.get("delivery_date") or None,
                order_data.get("delivery_instructions") or None,
                order_data.get("raw_message") or None,
                order_data.get("status") or DEFAULT_STATUS,
                round(total_amount, 2),
                now_iso,
                now_iso,
            ),
        )
        order_id = cursor.lastrowid

        for item in processed_items:
            cursor.execute(
                """
                INSERT INTO order_items (
                    order_id, product_name, quantity, unit, unit_price, line_total
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    order_id,
                    item["product_name"],
                    item["quantity"],
                    item["unit"],
                    item["unit_price"],
                    item["line_total"],
                ),
            )

        conn.commit()
        return order_id
    finally:
        conn.close()


def get_orders(
    search_query: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 200,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches list of orders matching search query and status filter.
    Includes item count and summary info.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        sql = """
            SELECT 
                o.id,
                o.order_number,
                o.customer_name,
                o.customer_phone,
                o.delivery_date,
                o.delivery_instructions,
                o.raw_message,
                o.status,
                o.total_amount,
                o.created_at,
                o.updated_at,
                COUNT(i.id) AS item_count,
                GROUP_CONCAT(i.product_name, ', ') AS item_names_summary
            FROM orders o
            LEFT JOIN order_items i ON o.id = i.order_id
            WHERE 1=1
        """
        params: List[Any] = []

        if status_filter and status_filter != "All":
            sql += " AND o.status = ?"
            params.append(status_filter)

        if search_query and search_query.strip():
            query_term = f"%{search_query.strip()}%"
            sql += """ AND (
                o.order_number LIKE ? OR
                o.customer_name LIKE ? OR
                o.customer_phone LIKE ? OR
                o.delivery_instructions LIKE ? OR
                o.id IN (
                    SELECT order_id FROM order_items 
                    WHERE product_name LIKE ?
                )
            )"""
            params.extend([query_term, query_term, query_term, query_term, query_term])

        sql += " GROUP BY o.id ORDER BY o.id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_order_by_id(order_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves full order record with its line items."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            return None

        order_dict = dict(order_row)
        cursor.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC;", (order_id,))
        items_rows = cursor.fetchall()
        order_dict["items"] = [dict(item) for item in items_rows]
        return order_dict
    finally:
        conn.close()


def update_order_status(order_id: int, new_status: str, db_path: Optional[str] = None) -> bool:
    """Updates the status of an existing order."""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?;",
            (new_status, now_iso, order_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_order(order_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes an order and its cascaded items."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE order_id = ?;", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id = ?;", (order_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_orders_dataframe(
    search_query: Optional[str] = None,
    status_filter: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Returns a flattened pandas DataFrame combining orders and order items,
    perfect for CSV export and reporting.
    """
    conn = get_db_connection(db_path)
    try:
        sql = """
            SELECT 
                o.order_number AS "Order Number",
                o.created_at AS "Order Date",
                o.status AS "Status",
                COALESCE(o.customer_name, 'Unknown') AS "Customer Name",
                COALESCE(o.customer_phone, '') AS "Customer Phone",
                COALESCE(i.product_name, 'No items') AS "Product Name",
                COALESCE(i.quantity, 0) AS "Quantity",
                COALESCE(i.unit, '') AS "Unit",
                COALESCE(i.unit_price, '') AS "Unit Price",
                COALESCE(i.line_total, '') AS "Line Total",
                COALESCE(o.total_amount, 0.0) AS "Order Total",
                COALESCE(o.delivery_date, '') AS "Delivery Date",
                COALESCE(o.delivery_instructions, '') AS "Delivery Instructions",
                COALESCE(o.raw_message, '') AS "Original Message"
            FROM orders o
            LEFT JOIN order_items i ON o.id = i.order_id
            WHERE 1=1
        """
        params: List[Any] = []

        if status_filter and status_filter != "All":
            sql += " AND o.status = ?"
            params.append(status_filter)

        if search_query and search_query.strip():
            query_term = f"%{search_query.strip()}%"
            sql += """ AND (
                o.order_number LIKE ? OR
                o.customer_name LIKE ? OR
                o.customer_phone LIKE ? OR
                o.delivery_instructions LIKE ? OR
                i.product_name LIKE ?
            )"""
            params.extend([query_term, query_term, query_term, query_term, query_term])

        sql += " ORDER BY o.id DESC, i.id ASC"
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def get_summary_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes summary metrics for the dashboard."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM orders;")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending';")
        pending_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Confirmed';")
        confirmed_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered';")
        delivered_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) FROM orders WHERE status != 'Cancelled';")
        total_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT customer_phone) FROM orders WHERE customer_phone IS NOT NULL AND customer_phone != '';")
        unique_customers = cursor.fetchone()[0]

        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "delivered_orders": delivered_orders,
            "total_revenue": round(total_revenue, 2),
            "unique_customers": unique_customers,
        }
    finally:
        conn.close()
