"""
File Parser Module for Orderly AI.
Extracts text and tabular content from PDF, CSV, Excel (.xlsx, .xls), and Text files
so they can be seamlessly processed by local AI or manual order pipelines.
"""

import io
import os
from typing import Tuple, Optional, Dict, Any
import pandas as pd


def get_file_extension(filename: str) -> str:
    """Returns normalized lowercase extension without leading dot."""
    parts = filename.rsplit(".", 1)
    return parts[1].lower() if len(parts) > 1 else ""


def format_file_size(size_bytes: int) -> str:
    """Formats file size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def extract_text_from_file(file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    """
    Extracts text content from uploaded file bytes based on file extension.
    Supported formats:
      - .pdf: Extracted page text via pypdf
      - .csv: Tabular structure formatted into line items
      - .xlsx, .xls: Excel sheets formatted into line items
      - .txt: Decoded plain text (UTF-8 or Latin-1)

    Returns:
        (success: bool, extracted_text: str, error_message: Optional[str])
    """
    if not file_bytes:
        return False, "", "The uploaded file is empty (0 bytes)."

    ext = get_file_extension(filename)

    if ext == "txt":
        try:
            text = file_bytes.decode("utf-8").strip()
            return True, text, None
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1", errors="replace").strip()
                return True, text, None
            except Exception as e:
                return False, "", f"Failed to decode text file: {e}"

    elif ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_t = page.extract_text()
                if page_t and page_t.strip():
                    pages_text.append(page_t.strip())
            
            if not pages_text:
                return False, "", "The PDF file contains no readable text (it may be a scanned image or empty)."
            
            full_text = "\n\n".join(pages_text).strip()
            return True, full_text, None
        except Exception as e:
            return False, "", f"Failed to extract text from PDF: {str(e)}"

    elif ext == "csv":
        try:
            # Try UTF-8 first, fallback to Latin-1
            try:
                df = pd.read_csv(io.BytesIO(file_bytes))
            except Exception:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")

            if df.empty:
                return False, "", "The CSV file contains no data rows."

            lines = [f"Order Data from CSV ({len(df)} rows):"]
            for idx, row in df.iterrows():
                row_parts = []
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val) and str(val).strip() != "":
                        row_parts.append(f"{col}: {val}")
                if row_parts:
                    lines.append(f"Row {idx + 1}: " + " | ".join(row_parts))

            full_text = "\n".join(lines).strip()
            return True, full_text, None
        except Exception as e:
            return False, "", f"Failed to parse CSV file: {str(e)}"

    elif ext in ("xlsx", "xls"):
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            lines = [f"Order Data from Excel ({len(excel_file.sheet_names)} sheet(s)):"]
            
            has_data = False
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if df.empty:
                    continue
                has_data = True
                lines.append(f"\n--- Sheet: {sheet_name} ({len(df)} rows) ---")
                for idx, row in df.iterrows():
                    row_parts = []
                    for col in df.columns:
                        val = row[col]
                        if pd.notna(val) and str(val).strip() != "":
                            row_parts.append(f"{col}: {val}")
                    if row_parts:
                        lines.append(f"Item {idx + 1}: " + " | ".join(row_parts))

            if not has_data:
                return False, "", "The Excel file contains no data rows."

            full_text = "\n".join(lines).strip()
            return True, full_text, None
        except Exception as e:
            return False, "", f"Failed to parse Excel file: {str(e)}"

    else:
        return False, "", f"Unsupported file extension '.{ext}'. Supported types: PDF, CSV, Excel (.xlsx, .xls), Text (.txt)."
