import os
import gc
import tempfile
import pytest
import pandas as pd
from database.db import (
    init_db,
    create_order,
    get_orders,
    get_order_by_id,
    update_order_status,
    delete_order,
    get_orders_dataframe,
    get_summary_stats,
)


@pytest.fixture
def temp_db():
    """Creates a temporary SQLite database for isolated test execution."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def test_init_db(temp_db):
    """Verifies tables are created properly without errors."""
    stats = get_summary_stats(temp_db)
    assert stats["total_orders"] == 0
    assert stats["pending_orders"] == 0
    assert stats["total_revenue"] == 0.0


def test_create_and_get_order(temp_db):
    """Tests creating an order with items and retrieving it."""
    order_data = {
        "customer_name": "Ramesh Gupta",
        "customer_phone": "9876543210",
        "delivery_date": "Tomorrow 10 AM",
        "delivery_instructions": "Gate 2, Flat 101",
        "raw_message": "Need 2 kg sugar and 1 packet salt. Ramesh 9876543210",
        "status": "Pending",
    }
    items = [
        {"product_name": "Sugar", "quantity": 2.0, "unit": "kg", "unit_price": 45.0},
        {"product_name": "Salt", "quantity": 1.0, "unit": "packet", "unit_price": 25.0},
    ]

    order_id = create_order(order_data, items, db_path=temp_db)
    assert order_id > 0

    fetched = get_order_by_id(order_id, db_path=temp_db)
    assert fetched is not None
    assert fetched["customer_name"] == "Ramesh Gupta"
    assert fetched["customer_phone"] == "9876543210"
    # Total calculation: (2 * 45) + (1 * 25) = 115.0
    assert fetched["total_amount"] == 115.0
    assert len(fetched["items"]) == 2
    assert fetched["items"][0]["product_name"] == "Sugar"
    assert fetched["items"][0]["line_total"] == 90.0
    assert fetched["items"][1]["product_name"] == "Salt"
    assert fetched["items"][1]["line_total"] == 25.0


def test_search_and_filter(temp_db):
    """Tests searching by customer name, order number, and filtering by status."""
    order1 = {
        "customer_name": "Anita Roy",
        "customer_phone": "9111111111",
        "status": "Pending",
    }
    order2 = {
        "customer_name": "Sunil Verma",
        "customer_phone": "9222222222",
        "status": "Delivered",
    }
    create_order(order1, [{"product_name": "Milk", "quantity": 2.0, "unit": "liters"}], db_path=temp_db)
    create_order(order2, [{"product_name": "Atta", "quantity": 5.0, "unit": "kg"}], db_path=temp_db)

    # Search by customer name
    results = get_orders(search_query="Anita", db_path=temp_db)
    assert len(results) == 1
    assert results[0]["customer_name"] == "Anita Roy"

    # Search by item name
    item_search = get_orders(search_query="Atta", db_path=temp_db)
    assert len(item_search) == 1
    assert item_search[0]["customer_name"] == "Sunil Verma"

    # Filter by status
    delivered = get_orders(status_filter="Delivered", db_path=temp_db)
    assert len(delivered) == 1
    assert delivered[0]["customer_name"] == "Sunil Verma"


def test_update_order_status(temp_db):
    """Tests changing status of an order."""
    order_data = {"customer_name": "Pooja", "status": "Pending"}
    items = [{"product_name": "Tea", "quantity": 1.0}]
    order_id = create_order(order_data, items, db_path=temp_db)

    success = update_order_status(order_id, "Delivered", db_path=temp_db)
    assert success is True

    fetched = get_order_by_id(order_id, db_path=temp_db)
    assert fetched["status"] == "Delivered"


def test_delete_order(temp_db):
    """Tests deleting an order and ensuring cascaded removal."""
    order_data = {"customer_name": "To Delete", "status": "Pending"}
    items = [{"product_name": "Item A", "quantity": 1.0}]
    order_id = create_order(order_data, items, db_path=temp_db)

    deleted = delete_order(order_id, db_path=temp_db)
    assert deleted is True

    fetched = get_order_by_id(order_id, db_path=temp_db)
    assert fetched is None


def test_dataframe_export(temp_db):
    """Tests generating a pandas DataFrame for CSV export."""
    order_data = {
        "customer_name": "Export Customer",
        "customer_phone": "9999999999",
        "delivery_date": "Today",
        "delivery_instructions": "Leave at front desk",
        "status": "Confirmed",
    }
    items = [
        {"product_name": "Apples", "quantity": 3.0, "unit": "kg", "unit_price": 100.0},
        {"product_name": "Oranges", "quantity": 2.0, "unit": "kg", "unit_price": 80.0},
    ]
    create_order(order_data, items, db_path=temp_db)

    df = get_orders_dataframe(db_path=temp_db)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2  # 2 line items
    assert "Order Number" in df.columns
    assert "Product Name" in df.columns
    assert "Customer Name" in df.columns
    assert df["Customer Name"].iloc[0] == "Export Customer"
