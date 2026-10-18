"""
Unit tests for file parser module (PDF, CSV, Excel, TXT).
"""

import io
import pandas as pd
import pypdf
from backend.file_parser import extract_text_from_file, get_file_extension, format_file_size


def test_file_extension():
    assert get_file_extension("order.PDF") == "pdf"
    assert get_file_extension("data.csv") == "csv"
    assert get_file_extension("items.XLSX") == "xlsx"
    assert get_file_extension("note.txt") == "txt"
    assert get_file_extension("noext") == ""


def test_format_file_size():
    assert format_file_size(500) == "500 B"
    assert "KB" in format_file_size(2048)
    assert "MB" in format_file_size(2 * 1024 * 1024)


def test_txt_parser():
    content = "Hello, please deliver 5 kg rice to Flat 101."
    ok, text, err = extract_text_from_file(content.encode("utf-8"), "order.txt")
    assert ok is True
    assert err is None
    assert "5 kg rice" in text


def test_csv_parser():
    csv_bytes = b"Product,Quantity,Price\nAtta,5 kg,45\nFortune Oil,2 ltr,140"
    ok, text, err = extract_text_from_file(csv_bytes, "items.csv")
    assert ok is True
    assert err is None
    assert "Atta" in text
    assert "Fortune Oil" in text
    assert "Row 1:" in text


def test_excel_parser():
    df = pd.DataFrame([{"Item": "Belgian Cake", "Qty": 2, "Price": 600}])
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    ok, text, err = extract_text_from_file(buf.getvalue(), "order.xlsx")
    assert ok is True
    assert err is None
    assert "Belgian Cake" in text
    assert "Sheet: Sheet1" in text


def test_empty_file():
    ok, text, err = extract_text_from_file(b"", "empty.txt")
    assert ok is False
    assert "empty" in err.lower()


def test_unsupported_file():
    ok, text, err = extract_text_from_file(b"content", "order.docx")
    assert ok is False
    assert "unsupported" in err.lower()
