"""
Database package for OrderMitra AI.
Provides SQLite storage, schema initialization, and CRUD operations.
"""

from database.db import (
    get_db_connection,
    init_db,
    generate_order_number,
    create_order,
    get_orders,
    get_order_by_id,
    update_order_status,
    delete_order,
    get_orders_dataframe,
    get_summary_stats,
)

__all__ = [
    "get_db_connection",
    "init_db",
    "generate_order_number",
    "create_order",
    "get_orders",
    "get_order_by_id",
    "update_order_status",
    "delete_order",
    "get_orders_dataframe",
    "get_summary_stats",
]
