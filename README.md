# 🛍️ OrderlyAI

**Smart Orders. Local AI. Greater Control.**

OrderlyAI is a local-first AI-powered order management application designed for small businesses (grocery stores, bakeries, cafes, boutique brands, wholesalers, and independent sellers). It converts unstructured customer messages from messaging platforms (WhatsApp, SMS, Instagram DMs) into organized, editable order records with SQLite persistence, status progression, business analytics, and CSV reporting—**all running 100% locally with zero cloud API dependencies.**

---

## 🌟 Key Features

1. **Local AI Extraction with Gemma 3 (`gemma3:4b`)**:
   - Extracts customer name, phone number, delivery dates, delivery instructions, and product line items (quantities, units, and unit prices when specified).
   - **Zero Hallucination Policy**: Strictly leaves absent fields blank (`null`). It never invents customer phone numbers, missing prices, or arbitrary delivery dates.
2. **Review & Editable Fields Before Save**:
   - Displays all extracted data in an intuitive form and dynamic data table.
   - Edit quantities, units, product names, and prices before saving.
   - **Explicit Confirmation Safeguard**: Orders cannot be accidentally saved without explicit confirmation.
3. **Local SQLite Persistence**:
   - Atomic database transactions with relational tables (`orders` and `order_items`).
   - Fast full-text search across customer names, phone numbers, order references, and products.
   - Safe status progression: `Pending` ➔ `Confirmed` ➔ `Preparing` ➔ `Out for Delivery` ➔ `Delivered` ➔ `Cancelled`.
   - **Destructive Operation Protection**: Order deletion requires a two-step explicit confirmation prompt.
4. **Instant CSV Export**:
   - Export filtered orders into a clean, normalized CSV file for accounting, Excel, or reporting using Pandas.
5. **Offline Fallback Engine & Diagnostics**:
   - Built-in connection tester and health check for local Ollama.
   - Includes an offline rule-based heuristic extractor so the application and testing workflows function seamlessly even if Ollama is paused or not yet installed.

---

## 🏗️ Architecture & Project Structure

```
OrderlyAI/
├── app.py                      # Root launcher (delegates to frontend/app.py)
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules for virtualenvs, SQLite DB, cache
├── README.md                   # Project documentation & guide
├── frontend/                   # UI & Streamlit application layer
│   ├── __init__.py
│   └── app.py                  # Streamlit dashboard, extraction UI, directory & settings
├── backend/                    # Business logic & AI processing layer
│   ├── __init__.py
│   ├── config.py               # Constants, environment variables, model & DB paths
│   ├── ollama_service.py       # Ollama HTTP API client, health checks, model discovery
│   ├── extractor.py            # Gemma 3 prompt engineering, JSON parser & heuristic fallback
│   └── utils.py                # Sample customer order presets, currency formatting, status badges
├── database/                   # Persistent storage layer
│   ├── __init__.py
│   ├── db.py                   # SQLite connection, schema, CRUD, search, and Pandas CSV export
│   └── orderly.db              # SQLite database file (created automatically)
└── tests/                      # Automated unit test suite
    ├── __init__.py
    ├── test_database.py        # Database schema, CRUD, search, and CSV export tests
    ├── test_extractor.py       # JSON cleaning, validation, and extraction logic tests
    └── test_ollama.py          # Ollama connectivity and offline error handling tests
```

---

## ⚙️ Tech Stack

- **Python**: 3.11+ (Compatible with Python 3.11, 3.12, 3.13, 3.14)
- **Frontend**: Streamlit
- **Local AI Engine**: Ollama with Gemma 3 (`gemma3:4b`)
- **Database**: SQLite 3 (Built-in)
- **Data Export & Manipulation**: Pandas
- **Testing**: Pytest

---

## 🚀 Setup & Installation (Windows PowerShell)

Follow these exact steps in your Windows PowerShell terminal:

### Step 1: Clone and Navigate to the Repository
```powershell
cd c:\Hactober\OrderlyAI
```

### Step 2: Create and Activate a Python Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# If you encounter an execution policy warning in PowerShell, run:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Python Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 4: Configure Environment (Optional)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default settings in `.env`:
```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=60
APP_CURRENCY=₹
```

### Step 5: Install and Start Ollama with Gemma 3
1. Download Ollama for Windows from [https://ollama.com/download](https://ollama.com/download).
2. Open a separate PowerShell terminal and pull Google's Gemma 3 model:
```powershell
ollama pull gemma3:4b
```
3. Make sure the Ollama service is running:
```powershell
ollama serve
```

---

## 💻 Running the Application

Launch the Streamlit web dashboard:
```powershell
python -m streamlit run app.py
```

The application will automatically open in your default browser at:
```
http://localhost:8501
```

---

## 🧪 Running Automated Tests

Run the full automated test suite with pytest:
```powershell
python -m pytest tests -v
```

All 14 tests cover:
- SQLite schema generation and foreign-key constraints
- Order and order-item creation, line total computations
- Searching by customer, phone, order number, and product
- Status updates and safe cascaded deletion
- Pandas DataFrame export formatting
- JSON code fence parsing and repair
- Enforcement of strict no-hallucination rules (absent values remain blank)
- Offline heuristic parsing fallback
- Ollama offline connection failure handling

---

## 🛡️ Privacy & Guardrails

- **No Third-Party APIs**: No data is sent to external cloud APIs (e.g. OpenAI, Anthropic, or external proxies). All inference runs strictly on your machine via local Ollama.
- **Strict Data Extraction Rules**: If an incoming message says *"Send 2 kg sugar tomorrow"*, Orderly AI records customer name and phone as `Unknown / Blank` rather than guessing or fabricating customer details.
- **Explicit Confirmation**: Every order requires user review and verification before persisting to SQLite.
- **Safe Destructive Operations**: Deleting an order displays an alert with two-step confirmation to prevent accidental loss of business records.

---

## 📄 License
MIT License. Free and open-source for small business owners and developers.
