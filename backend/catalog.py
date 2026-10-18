"""
Product Catalog & Inventory management for OrderlyAI.
Handles the products table: CRUD operations, stock tracking, price catalog.
"""

import sqlite3
import datetime
from typing import Dict, List, Any, Optional
from backend.config import DATABASE_PATH


def init_catalog_tables(db_path: str = DATABASE_PATH) -> None:
    """Creates the products/inventory catalog table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
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
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
        conn.commit()
    finally:
        conn.close()


def get_all_products(db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns all active products from the catalog."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return []
        cursor.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY category ASC, name ASC;"
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def add_product(product: Dict[str, Any], db_path: str = DATABASE_PATH) -> int:
    """Inserts a new product into the catalog. Returns new product ID."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, category, unit, unit_price, min_price, max_price,
                stock_quantity, low_stock_threshold, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?);
        """, (
            product.get("name", "").strip(),
            product.get("category", "General"),
            product.get("unit", "pcs"),
            product.get("unit_price"),
            product.get("min_price"),
            product.get("max_price"),
            product.get("stock_quantity", 0.0),
            product.get("low_stock_threshold", 5.0),
            now, now,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_product(product_id: int, updates: Dict[str, Any], db_path: str = DATABASE_PATH) -> bool:
    """Updates an existing product record."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allowed = ["name", "category", "unit", "unit_price", "min_price", "max_price",
               "stock_quantity", "low_stock_threshold", "is_active"]
    fields = [(k, v) for k, v in updates.items() if k in allowed]
    if not fields:
        return False
    conn = sqlite3.connect(db_path)
    try:
        set_clause = ", ".join([f"{k} = ?" for k, _ in fields])
        values = [v for _, v in fields] + [now, product_id]
        conn.execute(f"UPDATE products SET {set_clause}, updated_at = ? WHERE id = ?;", values)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_product(product_id: int, db_path: str = DATABASE_PATH) -> bool:
    """Soft-deletes a product (marks is_active = 0)."""
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE products SET is_active = 0, updated_at = ? WHERE id = ?;",
            (now, product_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def adjust_stock(product_id: int, delta: float, db_path: str = DATABASE_PATH) -> bool:
    """Adjusts stock quantity by delta (can be negative for deductions)."""
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE products SET stock_quantity = MAX(0, stock_quantity + ?), updated_at = ? WHERE id = ?;",
            (delta, now, product_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_low_stock_products(db_path: str = DATABASE_PATH) -> List[Dict[str, Any]]:
    """Returns products where stock_quantity <= low_stock_threshold."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if not cursor.fetchone():
            conn.close()
            return []
        cursor.execute("""
            SELECT * FROM products
            WHERE is_active = 1 AND stock_quantity <= low_stock_threshold
            ORDER BY stock_quantity ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def seed_demo_catalog(db_path: str = DATABASE_PATH) -> int:
    """Seeds the catalog with a set of common retail products for demo/testing."""
    demo_products = [
        {"name": "Aashirvaad Atta", "category": "Grocery", "unit": "kg", "unit_price": 45.0, "min_price": 40.0, "max_price": 55.0, "stock_quantity": 50.0, "low_stock_threshold": 10.0},
        {"name": "Fortune Sunflower Oil", "category": "Grocery", "unit": "ltr", "unit_price": 140.0, "min_price": 120.0, "max_price": 160.0, "stock_quantity": 30.0, "low_stock_threshold": 5.0},
        {"name": "Tata Salt", "category": "Grocery", "unit": "kg", "unit_price": 28.0, "min_price": 25.0, "max_price": 35.0, "stock_quantity": 40.0, "low_stock_threshold": 10.0},
        {"name": "Amul Butter", "category": "Dairy", "unit": "pcs", "unit_price": 55.0, "min_price": 50.0, "max_price": 65.0, "stock_quantity": 20.0, "low_stock_threshold": 5.0},
        {"name": "Farm Fresh Eggs", "category": "Dairy", "unit": "dozen", "unit_price": 85.0, "min_price": 75.0, "max_price": 100.0, "stock_quantity": 15.0, "low_stock_threshold": 3.0},
        {"name": "Parle-G Biscuits", "category": "Snacks", "unit": "carton", "unit_price": 480.0, "min_price": 450.0, "max_price": 520.0, "stock_quantity": 10.0, "low_stock_threshold": 2.0},
        {"name": "Maggi Noodles", "category": "Snacks", "unit": "carton", "unit_price": 960.0, "min_price": 900.0, "max_price": 1020.0, "stock_quantity": 8.0, "low_stock_threshold": 2.0},
        {"name": "Tata Tea Premium", "category": "Beverages", "unit": "packet", "unit_price": 90.0, "min_price": 80.0, "max_price": 110.0, "stock_quantity": 25.0, "low_stock_threshold": 5.0},
        {"name": "Tomatoes", "category": "Vegetables", "unit": "kg", "unit_price": 40.0, "min_price": 25.0, "max_price": 80.0, "stock_quantity": 12.0, "low_stock_threshold": 3.0},
        {"name": "Potatoes", "category": "Vegetables", "unit": "kg", "unit_price": 35.0, "min_price": 20.0, "max_price": 60.0, "stock_quantity": 20.0, "low_stock_threshold": 5.0},
        {"name": "Organic Spinach", "category": "Vegetables", "unit": "bunch", "unit_price": 30.0, "min_price": 20.0, "max_price": 50.0, "stock_quantity": 8.0, "low_stock_threshold": 2.0},
        {"name": "Belgian Chocolate Truffle Cake", "category": "Bakery", "unit": "kg", "unit_price": 650.0, "min_price": 600.0, "max_price": 750.0, "stock_quantity": 5.0, "low_stock_threshold": 1.0},
        {"name": "Sona Masoori Rice", "category": "Grocery", "unit": "kg", "unit_price": 65.0, "min_price": 55.0, "max_price": 75.0, "stock_quantity": 40.0, "low_stock_threshold": 10.0},
        {"name": "Vijaya Milk", "category": "Dairy", "unit": "packet", "unit_price": 32.0, "min_price": 30.0, "max_price": 35.0, "stock_quantity": 25.0, "low_stock_threshold": 5.0},
        {"name": "Freedom Sunflower Oil", "category": "Grocery", "unit": "ltr", "unit_price": 135.0, "min_price": 120.0, "max_price": 150.0, "stock_quantity": 18.0, "low_stock_threshold": 4.0},
        {"name": "Sugar", "category": "Grocery", "unit": "kg", "unit_price": 42.0, "min_price": 38.0, "max_price": 48.0, "stock_quantity": 35.0, "low_stock_threshold": 8.0},
        {"name": "Toor Dal (Kandi Pappu)", "category": "Grocery", "unit": "kg", "unit_price": 160.0, "min_price": 140.0, "max_price": 180.0, "stock_quantity": 15.0, "low_stock_threshold": 3.0},
    ]
    count = 0
    for product in demo_products:
        try:
            add_product(product, db_path)
            count += 1
        except Exception:
            pass
    return count
