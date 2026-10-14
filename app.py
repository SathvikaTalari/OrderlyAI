"""
OrderMitra AI - Root Entry Point
Delegates execution to frontend.app
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.app import render_app

if __name__ == "__main__" or "streamlit" in sys.modules:
    render_app()
