"""
OrderlyAI — Frontend Application
PRD-aligned, professional, fully responsive Streamlit UI.
Smart Orders. Local AI. Greater Control.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import datetime
import pandas as pd
import streamlit as st

from backend.config import (
    APP_NAME, APP_TAGLINE, APP_VERSION,
    DEFAULT_OLLAMA_URL, DEFAULT_MODEL, DATABASE_PATH,
    CURRENCY_SYMBOL, ORDER_STATUSES, DEFAULT_STATUS,
)
from database.db import (
    init_db, create_order, get_orders, get_order_by_id,
    update_order_status, delete_order,
    get_orders_dataframe, get_summary_stats,
)
from backend.ollama_service import check_ollama_status
from backend.extractor import extract_order_from_message
from backend.file_parser import extract_text_from_file, format_file_size, get_file_extension
from backend.utils import SAMPLE_MESSAGES, format_currency
from backend.catalog import (
    get_all_products, add_product, update_product, delete_product,
    adjust_stock, get_low_stock_products, seed_demo_catalog,
)
from backend.intelligence import (
    analyze_order_quality, find_returning_customer, check_price_anomalies,
    detect_duplicate_order, check_stock_availability, preprocess_telugu_english,
    get_catalog_price,
)
from backend.insights import (
    get_top_products, get_sales_trend, get_pending_deliveries,
    get_top_customers, get_revenue_summary, generate_ai_insights,
)
from frontend.theme import (
    get_custom_css, get_status_badge_html, get_kpi_card_html,
    STATUS_CONFIG, allowed_next_statuses,
)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_MESSAGE_CHARS = 2000
PAGES = [
    "📊 Dashboard",
    "📝 New Order",
    "📦 Orders Directory",
    "🏪 Product Catalog & Stock",
    "📈 Business Insights",
    "⚙️ Settings & Health",
]


# ─────────────────────────────────────────────────────────────────────────────
# Shared UI Helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_header(icon: str = "", title: str = "", subtitle: str = "", badge_text: str = ""):
    st.markdown(f"""
    <div class="oa-header">
        <div class="oa-header-inner">
            <div class="oa-header-left">
                <div>
                    <div class="oa-header-title">{title}</div>
                    <div class="oa-header-sub">{subtitle}</div>
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)


def alert(kind: str, icon: str, text: str):
    st.markdown(
        f'<div class="oa-alert oa-alert-{kind}"><span>{icon}</span><span>{text}</span></div>',
        unsafe_allow_html=True,
    )


def divider():
    st.markdown("<hr style='border:none;border-top:1px solid #E2E8F0;margin:22px 0;'>", unsafe_allow_html=True)


def section_title(text: str):
    st.markdown(f"<div style='font-size:1rem;font-weight:700;color:#0F172A;margin-bottom:12px;'>{text}</div>", unsafe_allow_html=True)


def label_tag(text: str, color="#4F46E5", bg="#EEF2FF", border="#C7D2FE"):
    return (f'<span style="background:{bg};color:{color};border:1px solid {border};'
            f'border-radius:9999px;padding:3px 11px;font-size:0.74rem;font-weight:700;'
            f'letter-spacing:0.03em;">{text}</span>')


def nav_to(page_keyword: str):
    """Switches navigation page safely before widgets instantiate (or via rerun)."""
    if "order_saved_success" in st.session_state:
        st.session_state.order_saved_success = None
    for p in PAGES:
        if page_keyword.lower() in p.lower():
            st.session_state.nav_target = p
            try:
                st.session_state.nav_radio = p
                st.session_state.current_page = p
            except Exception:
                st.rerun()
            return


def on_nav_change():
    st.session_state.current_page = st.session_state.nav_radio


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def render_dashboard():
    today = datetime.datetime.now().strftime("%d %b %Y")
    render_header("📊", "Business Dashboard",
                  "Real-time order activity, pipeline metrics, and quick operations.",
                  f"Live · {today}")

    stats = get_summary_stats(DATABASE_PATH)
    recent = get_orders(limit=8, db_path=DATABASE_PATH)

    # ── KPI Cards ──
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(get_kpi_card_html(
            "Total Orders", str(stats["total_orders"]),
            f"{stats['unique_customers']} unique customers",
            "📦", "#4F46E5", "#EEF2FF"), unsafe_allow_html=True)
    with k2:
        st.markdown(get_kpi_card_html(
            "Pending Action", str(stats["pending_orders"]),
            "Awaiting review, prep, or dispatch",
            "⏳", "#D97706", "#FEF3C7"), unsafe_allow_html=True)
    with k3:
        st.markdown(get_kpi_card_html(
            "Delivered", str(stats["delivered_orders"]),
            f"{stats['confirmed_orders']} confirmed in pipeline",
            "📦", "#059669", "#D1FAE5"), unsafe_allow_html=True)
    with k4:
        st.markdown(get_kpi_card_html(
            "Recorded Sales", format_currency(stats["total_revenue"], CURRENCY_SYMBOL),
            "Excl. cancelled orders¹", "💰", "#6366F1", "#EEF2FF"), unsafe_allow_html=True)

    # Revenue policy footnote
    st.markdown(
        "<div style='font-size:0.73rem;color:#94A3B8;margin-top:4px;'>¹ Recorded Sales = sum of order totals excluding Cancelled status orders. "
        "Does not imply payment received.</div>",
        unsafe_allow_html=True)

    # ── Status Distribution ──
    if stats["total_orders"] > 0:
        st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
        divider()
        section_title("Order Status Distribution")

        # Fetch per-status counts
        all_orders = get_orders(limit=5000, db_path=DATABASE_PATH)
        status_counts = {}
        for s in ORDER_STATUSES:
            status_counts[s] = sum(1 for o in all_orders if o["status"] == s)

        total = sum(status_counts.values()) or 1

        # Horizontal stacked bar
        segments = []
        for s, count in status_counts.items():
            if count == 0:
                continue
            cfg = STATUS_CONFIG.get(s, {})
            pct = round((count / total) * 100, 1)
            segments.append(
                f'<div class="oa-status-seg" title="{s}: {count}" '
                f'style="background:{cfg.get("dot","#CBD5E1")};width:{pct}%;min-width:4px;border-radius:4px;"></div>'
            )
        st.markdown(
            f'<div class="oa-status-bar">{"".join(segments)}</div>',
            unsafe_allow_html=True,
        )

        # Legend
        legend_parts = []
        for s, count in status_counts.items():
            if count == 0:
                continue
            cfg = STATUS_CONFIG.get(s, {})
            pct = round((count / total) * 100, 1)
            legend_parts.append(
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'font-size:0.78rem;color:#334155;margin-right:14px;">'
                f'<span style="width:9px;height:9px;border-radius:50%;background:{cfg.get("dot","#CBD5E1")};flex-shrink:0;"></span>'
                f'{cfg.get("icon","")} {s} ({count})</span>'
            )
        st.markdown(
            f'<div style="margin-bottom:6px;">{"".join(legend_parts)}</div>',
            unsafe_allow_html=True,
        )

    divider()

    # ── Quick Actions ──
    st.markdown(
        "<div style='font-size:0.74rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>Quick Operations</div>",
        unsafe_allow_html=True,
    )
    qa1, qa2, qa3, qa4 = st.columns(4, gap="medium")
    with qa1:
        st.button("Extract New Order", type="primary", use_container_width=True,
                  key="dash_new", on_click=nav_to, args=("New Order",))
    with qa2:
        st.button("Orders Directory", use_container_width=True,
                  key="dash_dir", on_click=nav_to, args=("Orders Directory",))
    with qa3:
        st.button("Catalog & Stock", use_container_width=True,
                  key="dash_cat", on_click=nav_to, args=("Catalog",))
    with qa4:
        st.button("Business Insights", use_container_width=True,
                  key="dash_ins", on_click=nav_to, args=("Insights",))

    # Low stock notification alert on dashboard
    low_stock = get_low_stock_products(DATABASE_PATH)
    if low_stock:
        alert("warning", "⚠️",
              f"<strong>Inventory Alert:</strong> {len(low_stock)} product(s) are low or out of stock "
              f"({', '.join([p['name'] for p in low_stock[:3]])}{'...' if len(low_stock) > 3 else ''}). "
              f"Visit Catalog &amp; Stock to adjust quantities.")

    divider()

    # ── Recent Orders Table ──
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;'>"
        f"<div style='font-size:1rem;font-weight:700;color:#0F172A;'>Recent Orders</div>"
        f"<div style='font-size:0.8rem;color:#64748B;'>Showing latest {len(recent)}</div></div>",
        unsafe_allow_html=True,
    )

    if not recent:
        st.markdown("""
        <div class="oa-empty">
            <span class="oa-empty-icon">📋</span>
            <div class="oa-empty-title">No Orders Yet</div>
            <div class="oa-empty-desc">Extract your first customer order using the New Order page,
            or seed realistic demo data from Settings &amp; Health.</div>
        </div>""", unsafe_allow_html=True)
        _, c, _ = st.columns([1, 2, 1])
        with c:
            st.button("Create Your First Order", type="primary", use_container_width=True,
                      key="dash_first_order", on_click=nav_to, args=("New Order",))
    else:
        rows = []
        for o in recent:
            rows.append({
                "Order #": o["order_number"],
                "Date": (o["created_at"] or "")[:16],
                "Customer": o["customer_name"] or "—",
                "Phone": o["customer_phone"] or "—",
                "Status": o["status"],
                "Items": o.get("item_names_summary") or f"{o.get('item_count', 0)} item(s)",
                "Total": format_currency(o["total_amount"], CURRENCY_SYMBOL),
            })
        st.dataframe(
            pd.DataFrame(rows), use_container_width=True, hide_index=True,
            column_config={
                "Order #": st.column_config.TextColumn("Order #", width="medium"),
                "Date": st.column_config.TextColumn("Date/Time", width="medium"),
                "Customer": st.column_config.TextColumn("Customer", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Items": st.column_config.TextColumn("Items", width="large"),
                "Total": st.column_config.TextColumn("Total", width="small"),
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: NEW ORDER — 4-Stage Workflow (PRD §7)
# ─────────────────────────────────────────────────────────────────────────────

def render_new_order():
    render_header("📝", "New Order Extraction",
                  "Paste a customer message — local Gemma 3 extracts it into a structured, editable order.",
                  "Local AI · On-Device")

    # Stepper state
    has_extract = st.session_state.extracted_order is not None
    has_confirm = st.session_state.get("order_confirm_ready", False)
    step = 3 if has_confirm else (2 if has_extract else 1)

    def _step(n, label):
        cls = "active" if step == n else ("done" if step > n else "")
        circle = "✓" if step > n else str(n)
        return f'<div class="oa-step {cls}"><div class="oa-step-circle">{circle}</div><span>{label}</span></div>'

    def _line(n):
        cls = "done" if step > n else ""
        return f'<div class="oa-step-line {cls}"></div>'

    st.markdown(f"""
    <div class="oa-stepper">
        {_step(1, "Enter Message")}
        {_line(1)}
        {_step(2, "Review &amp; Edit")}
        {_line(2)}
        {_step(3, "Final Summary")}
        {_line(3)}
        {_step(4, "Saved ✓")}
    </div>""", unsafe_allow_html=True)

    # Success banner
    if st.session_state.get("order_saved_success"):
        saved = st.session_state.order_saved_success
        alert("success", "🎉",
              f"<strong>Order {saved['number']} saved successfully!</strong> "
              f"Customer: {saved['customer']} · {saved['items']} items · "
              f"Total: {saved['total']}")
        col_a, col_b, _ = st.columns([1.5, 1.5, 3])
        with col_a:
            st.button("📦 View in Orders Directory", key="post_save_dir",
                      on_click=nav_to, args=("Orders Directory",))
        with col_b:
            if st.button("➕ New Order", key="post_save_new", type="primary"):
                st.session_state.order_saved_success = None
                st.rerun()
        st.session_state.order_saved_success = None
        return

    # ── STAGE 1: Input Order Data (3 Methods) ──────────────────────────────
    if not st.session_state.extracted_order:
        section_title("Step 1: Add Order Data")
        st.markdown(
            "<div style='font-size:0.83rem;color:#64748B;margin-bottom:14px;'>"
            "Choose your preferred method to add an order: paste a message, upload a document or spreadsheet, or input details manually."
            "</div>",
            unsafe_allow_html=True,
        )

        tab_text, tab_file, tab_manual = st.tabs([
            "💬 Paste Customer Message",
            "📁 Upload Document / Sheet (PDF, CSV, Excel, TXT)",
            "✍️ Add Manually",
        ])

        # ── METHOD 1: Paste Customer Message ──
        with tab_text:
            # Compact header row with small Sample Data dropdown in the top right corner
            col_lbl, col_sample = st.columns([7, 3], gap="small")
            with col_lbl:
                st.markdown(
                    "<div style='font-size:0.875rem;font-weight:600;color:#0F172A;padding-top:8px;'>"
                    "Customer Message <span style='font-size:0.76rem;font-weight:400;color:#64748B;'>(WhatsApp / SMS / DM)</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with col_sample:
                with st.popover("💡 Load Sample ▾", use_container_width=True):
                    st.markdown(
                        "<div style='font-size:0.76rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;'>"
                        "Choose Sample Order:</div>",
                        unsafe_allow_html=True,
                    )
                    sample_options = [
                        ("🛒 Kirana / Grocery", "Kirana / Grocery WhatsApp Order"),
                        ("🇮🇳 Telugu-English Mixed", "Telugu-English Mixed (Kirana)"),
                        ("🧠 Returning Customer", "Returning Customer (Memory)"),
                        ("🔤 Telugu Script (తెలుగు)", "Telugu Script (తెలుగు ఆర్డర్)"),
                        ("🎂 Bakery & Cafe Party", "Bakery & Cafe Party Order"),
                        ("🥬 Organic Farm / Veggies", "Organic Farm / Veggie Box"),
                        ("☕ Minimal (Missing Details)", "Minimal Message (Missing Details)"),
                        ("📦 Wholesale Replenishment", "Wholesale / Distributor"),
                    ]
                    for label, full_title in sample_options:
                        if st.button(label, key=f"pop_btn_{full_title[:8]}", use_container_width=True):
                            st.session_state.target_raw_msg = SAMPLE_MESSAGES[full_title]
                            st.session_state.extracted_order = None
                            st.session_state.extraction_notice = None
                            st.session_state.order_confirm_ready = False
                            st.rerun()

            # Apply target raw message before instantiating text_area widget
            if st.session_state.get("target_raw_msg") is not None:
                st.session_state.raw_msg_area = st.session_state.target_raw_msg
                st.session_state.target_raw_msg = None

            raw_message = st.text_area(
                "Customer Message",
                label_visibility="collapsed",
                key="raw_msg_area",
                height=136,
                placeholder=(
                    "e.g. Hi Bhaiya! Send 5 kg Aashirvaad Atta @ 45/kg, "
                    "2 kg Fortune Oil @ 140/kg. Deliver tomorrow 10 AM. "
                    "Flat 402. Rajesh 9876543210\n"
                    "Or Telugu: 2 packets Vijaya milk kavali, repu podduna pampandi."
                ),
                help="Paste the verbatim customer message in English, Telugu, or mixed Telugu-English.",
            )

            # Real-time Telugu detection badge
            if raw_message:
                _, is_telugu = preprocess_telugu_english(raw_message)
                if is_telugu:
                    st.markdown(
                        '<div style="margin-top:-6px;margin-bottom:8px;">'
                        '<span class="oa-badge-telugu">🇮🇳 Telugu-English Mixed Language Detected</span></div>',
                        unsafe_allow_html=True,
                    )

            # Real-time Business Memory lookup
            if raw_message:
                import re as _re
                phone_m = _re.search(r"(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}|\b\d{10,12}\b", raw_message)
                if phone_m:
                    ret_cust = find_returning_customer(phone_m.group(0), db_path=DATABASE_PATH)
                    if ret_cust:
                        st.markdown(f"""
                        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:10px 14px;margin:4px 0 10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                <span style="font-size:1.2rem;">🧠</span>
                                <div>
                                    <span style="font-weight:700;font-size:0.82rem;color:#1E40AF;">Business Memory:</span>
                                    <span style="font-size:0.8rem;color:#1E3A8A;"> Returning customer <strong>{ret_cust['customer_name']}</strong> ({ret_cust['total_orders']} previous orders).</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🔄 Auto-Populate Items from Previous Order", key="btn_load_memory"):
                            st.session_state.extracted_order = {
                                "customer_name": ret_cust["customer_name"],
                                "customer_phone": ret_cust["customer_phone"],
                                "delivery_date": "",
                                "delivery_instructions": "",
                                "items": [
                                    {
                                        "product_name": it["product_name"],
                                        "quantity": it["quantity"],
                                        "unit": it["unit"],
                                        "unit_price": it["unit_price"],
                                    }
                                    for it in ret_cust["last_items"]
                                ],
                                "notes": f"Business Memory Re-Order (Previous #{ret_cust['last_order_number']})",
                            }
                            st.session_state.extraction_engine = "Business Memory"
                            st.rerun()

            # Character counter
            char_len = len(raw_message)
            counter_cls = "error" if char_len > MAX_MESSAGE_CHARS else ("warn" if char_len > 1600 else "")
            st.markdown(
                f'<div class="oa-char-counter {counter_cls}">'
                f'{char_len} / {MAX_MESSAGE_CHARS} characters</div>',
                unsafe_allow_html=True,
            )

            b1, b2 = st.columns([3, 1], gap="medium")
            with b1:
                extract_clicked = st.button("⚡ Extract Order with Local AI", type="primary",
                                            use_container_width=True, key="extract_btn")
            with b2:
                if st.button("🧹 Clear", use_container_width=True, key="clear_btn"):
                    st.session_state.target_raw_msg = ""
                    st.session_state.extracted_order = None
                    st.session_state.extraction_notice = None
                    st.session_state.extraction_engine = None
                    st.session_state.order_confirm_ready = False
                    st.rerun()

            if extract_clicked:
                msg_text = (raw_message or st.session_state.get("raw_msg_area", "")).strip()
                if not msg_text:
                    st.warning("⚠️ Please paste a customer message before extracting.")
                elif len(msg_text) > MAX_MESSAGE_CHARS:
                    st.error(f"❌ Message too long ({len(msg_text)} characters). Please keep it under {MAX_MESSAGE_CHARS} characters.")
                else:
                    with st.spinner("🤖 Analyzing message with local Gemma 3 (on-device)…"):
                        ok, data, notice, engine = extract_order_from_message(
                            raw_message=msg_text,
                            model=DEFAULT_MODEL,
                            base_url=DEFAULT_OLLAMA_URL,
                            allow_fallback=True,
                        )
                    if ok:
                        st.session_state.extracted_order = data
                        st.session_state.extraction_notice = notice
                        st.session_state.extraction_engine = engine
                        st.session_state.order_confirm_ready = False
                        for k in ["ed_name", "ed_phone", "ed_status", "ed_date", "ed_instr", "items_editor"]:
                            st.session_state.pop(k, None)
                        st.rerun()
                    else:
                        st.error(f"Extraction failed: {notice}")

        # ── METHOD 2: Upload Document / Sheet ──
        with tab_file:
            st.markdown("""
            <div style="font-size:0.84rem;color:#475569;margin:8px 0 12px;line-height:1.5;">
                Upload customer invoices, purchase orders, product catalogs, or spreadsheets. 
                Supported formats: <strong>PDF (.pdf)</strong>, <strong>CSV (.csv)</strong>, <strong>Excel (.xlsx, .xls)</strong>, and <strong>Plain Text (.txt)</strong>.
            </div>
            """, unsafe_allow_html=True)

            uploaded_file = st.file_uploader(
                "Choose an order file to upload",
                type=["pdf", "csv", "xlsx", "xls", "txt"],
                key="order_file_uploader",
                help="Upload PDF, CSV, Excel, or Text file. All parsing and AI extraction runs 100% locally on your machine.",
            )

            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                file_name = uploaded_file.name
                file_ext = get_file_extension(file_name)
                file_size_str = format_file_size(len(file_bytes))

                # Parse text from file
                parse_ok, parsed_text, parse_err = extract_text_from_file(file_bytes, file_name)

                if not parse_ok:
                    st.error(f"❌ {parse_err}")
                else:
                    # File info badge
                    ext_icons = {"pdf": "📄", "csv": "📊", "xlsx": "📈", "xls": "📈", "txt": "📝"}
                    icon = ext_icons.get(file_ext, "📁")
                    st.markdown(f"""
                    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:12px 16px;margin:10px 0 14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <span style="font-size:1.4rem;">{icon}</span>
                            <div>
                                <div style="font-weight:700;font-size:0.9rem;color:#166534;">{file_name}</div>
                                <div style="font-size:0.75rem;color:#15803D;">{file_ext.upper()} Document · {file_size_str} · {len(parsed_text)} characters extracted</div>
                            </div>
                        </div>
                        <span style="background:#DCFCE7;color:#166534;font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:9999px;">Ready for AI</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Tabular preview if CSV or Excel
                    if file_ext in ("csv", "xlsx", "xls"):
                        try:
                            import io
                            if file_ext == "csv":
                                try:
                                    df_prev = pd.read_csv(io.BytesIO(file_bytes))
                                except Exception:
                                    df_prev = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
                            else:
                                df_prev = pd.read_excel(io.BytesIO(file_bytes))
                            with st.expander(f"📊 Preview Table ({len(df_prev)} rows)", expanded=False):
                                st.dataframe(df_prev.head(10), use_container_width=True)
                        except Exception:
                            pass

                    with st.expander("👁️ Preview Extracted Document Text", expanded=False):
                        st.text_area("Document Content", value=parsed_text[:2000], height=120, disabled=True, key="prev_doc_txt")

                    f_col1, f_col2 = st.columns([3, 1], gap="medium")
                    with f_col1:
                        extract_file_clicked = st.button(
                            "⚡ Extract Order from File with Local AI",
                            type="primary",
                            use_container_width=True,
                            key="extract_file_btn"
                        )
                    with f_col2:
                        if st.button("📝 Copy to Message Tab", use_container_width=True, key="copy_to_msg_btn"):
                            st.session_state.target_raw_msg = parsed_text
                            st.rerun()

                    if extract_file_clicked:
                        trimmed_f = parsed_text.strip()
                        if not trimmed_f:
                            st.warning("⚠️ The uploaded file contains no readable text to extract.")
                        else:
                            with st.spinner(f"🤖 Analyzing {file_name} with local Gemma 3 (on-device)…"):
                                ok, data, notice, engine = extract_order_from_message(
                                    raw_message=trimmed_f,
                                    model=DEFAULT_MODEL,
                                    base_url=DEFAULT_OLLAMA_URL,
                                    allow_fallback=True,
                                )
                            if ok:
                                st.session_state.extracted_order = data
                                st.session_state.extraction_notice = notice
                                st.session_state.extraction_engine = f"{engine} ({file_name})"
                                st.session_state.order_confirm_ready = False
                                for k in ["ed_name", "ed_phone", "ed_status", "ed_date", "ed_instr", "items_editor"]:
                                    st.session_state.pop(k, None)
                                st.rerun()
                            else:
                                st.error(f"Extraction failed: {notice}")

        # ── METHOD 3: Add Manually ──
        with tab_manual:
            st.markdown("""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:22px;margin:10px 0 16px;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                    <div style="width:38px;height:38px;border-radius:10px;background:#EEF2FF;color:#4F46E5;display:flex;align-items:center;justify-content:center;font-size:1.25rem;">
                        ✍️
                    </div>
                    <div>
                        <div style="font-size:1.05rem;font-weight:700;color:#0F172A;">Manual Order Entry</div>
                        <div style="font-size:0.78rem;color:#64748B;">Direct data input without AI processing</div>
                    </div>
                </div>
                <div style="font-size:0.84rem;color:#475569;line-height:1.65;margin-bottom:16px;">
                    Prefer to enter details directly? Start with a blank order template to specify customer name, phone number, delivery address, and add products directly into the interactive line items editor.
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✍️ Create Blank Order Form", type="primary", use_container_width=True, key="manual_entry_btn"):
                st.session_state.extracted_order = {
                    "customer_name": "",
                    "customer_phone": "",
                    "delivery_date": "",
                    "delivery_instructions": "",
                    "items": [{"product_name": "", "quantity": 1.0, "unit": "", "unit_price": ""}],
                    "notes": "Manual Entry",
                }
                st.session_state.extraction_notice = None
                st.session_state.extraction_engine = "Manual Entry"
                st.session_state.order_confirm_ready = False
                for k in ["ed_name", "ed_phone", "ed_status", "ed_date", "ed_instr", "items_editor"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # ── STAGE 2: Review & Edit ─────────────────────────────────────────────
    if not st.session_state.extracted_order:
        return

    data = st.session_state.extracted_order

    # Extraction engine notice
    engine = st.session_state.get("extraction_engine", "")
    if engine == "Manual Entry":
        alert("info", "✍️",
              "<strong>Manual Order Entry:</strong> Fill in the customer details and line items below.")
    elif st.session_state.get("extraction_notice"):
        alert("warning", "⚠️", f"<strong>Notice:</strong> {st.session_state.extraction_notice}")
    elif engine:
        is_fallback = "Fallback" in engine or "Heuristic" in engine
        if is_fallback:
            alert("warning", "🔁",
                  f"Extracted by <strong>{engine}</strong> — the offline heuristic parser. "
                  "Results may be less accurate than the AI model. Please review carefully.")
        else:
            alert("info", "🤖",
                  f"Extracted by <strong>{engine}</strong>. "
                  "All inference ran locally on your machine. Review and correct before saving.")

    divider()

    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:10px;">
        <div>
            <div style="font-size:1.05rem;font-weight:700;color:#0F172A;">
                Stage 2 — Review &amp; Correct Order Details
            </div>
            <div style="font-size:0.83rem;color:#64748B;margin-top:2px;">
                Verify every field. Nothing is saved until you confirm in Stage 3.
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    s2_col1, s2_col2 = st.columns([3, 1])
    with s2_col2:
        if st.button("← Choose Different Input", use_container_width=True, key="stage2_reset_btn"):
            st.session_state.extracted_order = None
            st.session_state.extraction_notice = None
            st.session_state.extraction_engine = None
            st.session_state.order_confirm_ready = False
            for k in ["ed_name", "ed_phone", "ed_status", "ed_date", "ed_instr", "items_editor"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── 1. Smart Order Intelligence: Quality Audit ──
    intel_data = {
        "customer_name": data.get("customer_name"),
        "customer_phone": data.get("customer_phone"),
        "delivery_date": data.get("delivery_date"),
        "delivery_instructions": data.get("delivery_instructions"),
        "items": data.get("items") or [],
    }
    quality_report = analyze_order_quality(intel_data, db_path=DATABASE_PATH)

    with st.expander(f"🧠 Smart Order Intelligence · Quality Score: {quality_report['score']}% ({quality_report['quality_label']})", expanded=quality_report['score'] < 85):
        q_col1, q_col2 = st.columns([1, 2])
        with q_col1:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1.5px solid #E2E8F0;border-radius:12px;padding:16px;text-align:center;">
                <div style="font-size:0.75rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Order Health</div>
                <div style="font-size:2.2rem;font-weight:800;color:{quality_report['quality_color']};line-height:1;">{quality_report['score']}%</div>
                <div style="margin-top:6px;"><span class="oa-score-pill" style="background:{quality_report['quality_color']}18;color:{quality_report['quality_color']};">● {quality_report['quality_label']}</span></div>
            </div>
            """, unsafe_allow_html=True)
        with q_col2:
            if quality_report["issues"]:
                for iss in quality_report["issues"][:4]:
                    sev_icon = "🚨" if iss["severity"] == "error" else ("⚠️" if iss["severity"] == "warning" else "ℹ️")
                    st.markdown(f"<div style='font-size:0.83rem;color:#334155;margin-bottom:4px;'>{sev_icon} {iss['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:0.85rem;color:#059669;font-weight:600;'>✅ Complete order! All essential customer details and pricing information are present.</div>", unsafe_allow_html=True)

            if quality_report.get("suggestions"):
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                for sug in quality_report["suggestions"]:
                    st.markdown(f"<div style='font-size:0.82rem;color:#2563EB;'>💡 <strong>Catalog Match:</strong> {sug['message']}</div>", unsafe_allow_html=True)

                if st.button("⚡ Apply Catalog Prices to Unpriced Items", key="btn_apply_cat_prices"):
                    for item in data.get("items", []):
                        if not item.get("unit_price") or str(item.get("unit_price")).strip() in ("", "null", "None"):
                            cat_p = get_catalog_price(item.get("product_name", ""), DATABASE_PATH)
                            if cat_p is not None:
                                item["unit_price"] = cat_p
                    st.session_state.pop("items_editor", None)
                    st.success("✅ Applied catalog prices!")
                    st.rerun()

    # Customer fields
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        edit_name = st.text_input("Customer Name", value=data.get("customer_name") or "",
                                   placeholder="Leave blank if not mentioned", key="ed_name")
    with c2:
        edit_phone = st.text_input("Phone Number", value=data.get("customer_phone") or "",
                                    placeholder="e.g. 9876543210", key="ed_phone")
    with c3:
        edit_status = st.selectbox("Initial Order Status", ORDER_STATUSES, index=0, key="ed_status",
                                    help="The status assigned when this order is first saved.")

    d1, d2 = st.columns(2, gap="medium")
    with d1:
        edit_date = st.text_input("Delivery Date / Schedule",
                                   value=data.get("delivery_date") or "",
                                   placeholder="e.g. Tomorrow 10 AM, Friday, 2026-10-16", key="ed_date")
    with d2:
        edit_instr = st.text_input("Delivery Address / Instructions",
                                    value=data.get("delivery_instructions") or "",
                                    placeholder="e.g. Flat 402, Sunshine Heights — leave with security", key="ed_instr")

    # Items editor
    st.markdown("<div style='font-size:0.9rem;font-weight:700;color:#0F172A;margin:18px 0 5px;'>Ordered Items &amp; Pricing</div>",
                unsafe_allow_html=True)
    st.caption("Add, remove, or correct items, quantities, units, and prices. Line totals update live.")

    if not data.get("items"):
        st.info("ℹ️ No specific product line items were detected in the message. You can add them below.")

    raw_items = data.get("items") or [{"product_name": "", "quantity": 1.0, "unit": "", "unit_price": ""}]
    df_in = pd.DataFrame(raw_items)
    for col in ["product_name", "quantity", "unit", "unit_price"]:
        if col not in df_in.columns:
            df_in[col] = ""
    df_in = df_in[["product_name", "quantity", "unit", "unit_price"]]
    df_in.columns = ["Product Name", "Quantity", "Unit", "Unit Price"]

    edited_df = st.data_editor(
        df_in, num_rows="dynamic", use_container_width=True,
        column_config={
            "Product Name": st.column_config.TextColumn("Product Name", required=True),
            "Quantity": st.column_config.NumberColumn("Qty", min_value=0.001, step=1.0, default=1.0),
            "Unit": st.column_config.TextColumn("Unit (kg / pcs / ltr…)"),
            "Unit Price": st.column_config.NumberColumn(f"Unit Price ({CURRENCY_SYMBOL})", step=0.5, format=f"{CURRENCY_SYMBOL}%.2f"),
        },
        key="items_editor",
    )

    # Live total calc
    calc_items, calculated_total, priced_count = [], 0.0, 0
    for _, row in edited_df.iterrows():
        p = str(row["Product Name"]).strip() if pd.notna(row["Product Name"]) else ""
        if not p:
            continue
        try:
            q = float(row["Quantity"]) if pd.notna(row["Quantity"]) else 1.0
        except (ValueError, TypeError):
            q = 1.0
        u = str(row["Unit"]).strip() if pd.notna(row["Unit"]) else ""
        p_val, line_total = None, None
        if pd.notna(row["Unit Price"]) and str(row["Unit Price"]).strip() not in ("", "nan"):
            try:
                p_val = float(row["Unit Price"])
                line_total = round(q * p_val, 2)
                calculated_total += line_total
                priced_count += 1
            except (ValueError, TypeError):
                p_val = None
        calc_items.append({"product_name": p, "quantity": q, "unit": u,
                           "unit_price": p_val, "line_total": line_total})

    # ── 2. Guards: Price Guard, Duplicate Guard, Stock Guard ──
    price_alerts = check_price_anomalies(calc_items, db_path=DATABASE_PATH)
    if price_alerts:
        for pa in price_alerts:
            alert("warning", "🏷️", f"<strong>Price Guard:</strong> {pa['message']}")

    stock_alerts = check_stock_availability(calc_items, db_path=DATABASE_PATH)
    if stock_alerts:
        for sa in stock_alerts:
            sev = "danger" if sa["severity"] == "error" else "warning"
            icon = "🚨" if sa["severity"] == "error" else "⚠️"
            alert(sev, icon, f"<strong>Stock Guard:</strong> {sa['message']}")

    if edit_phone:
        dup = detect_duplicate_order(edit_phone, calc_items, within_minutes=30, db_path=DATABASE_PATH)
        if dup:
            alert("warning", "🚨",
                  f"<strong>Duplicate Guard:</strong> Similar order <strong>{dup['order_number']}</strong> "
                  f"was submitted {dup['created_at'][:16]} (overlapping {dup['overlap_count']} items). "
                  f"Please verify this is not an unintentional duplicate.")

    unpriced_note = f" · {len(calc_items)-priced_count} item(s) without price" if len(calc_items) > priced_count else ""
    st.markdown(f"""
    <div class="oa-total-bar">
        <div class="oa-total-label">
            <span>📦 {len(calc_items)} item(s)</span>
            <span>·</span>
            <span>🏷️ {priced_count} priced{unpriced_note}</span>
        </div>
        <div>
            <span style="font-size:0.84rem;color:#475569;font-weight:600;margin-right:8px;">Order Total:</span>
            <span class="oa-total-value">{format_currency(calculated_total, CURRENCY_SYMBOL)}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Proceed to Stage 3
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    if not calc_items:
        alert("warning", "⚠️", "Please add at least one product before proceeding.")
        return

    if st.button("➡️ Proceed to Final Review", type="primary", key="proceed_to_confirm"):
        st.session_state.staged_order = {
            "customer_name": edit_name.strip() or None,
            "customer_phone": edit_phone.strip() or None,
            "delivery_date": edit_date.strip() or None,
            "delivery_instructions": edit_instr.strip() or None,
            "raw_message": st.session_state.get("raw_msg_area", "").strip(),
            "status": edit_status,
        }
        st.session_state.staged_items = calc_items
        st.session_state.staged_total = calculated_total
        st.session_state.order_confirm_ready = True
        st.rerun()

    # ── STAGE 3: Final Summary & Confirm ──────────────────────────────────
    if not st.session_state.get("order_confirm_ready"):
        return

    staged = st.session_state.get("staged_order", {})
    staged_items = st.session_state.get("staged_items", [])
    staged_total = st.session_state.get("staged_total", 0.0)

    divider()
    st.markdown("""
    <div style="font-size:1.05rem;font-weight:700;color:#0F172A;margin-bottom:12px;">
        Stage 3 — Final Order Summary
    </div>
    <div style="font-size:0.83rem;color:#64748B;margin-bottom:14px;">
        Review the complete order below before saving. This is your last chance to go back.
    </div>""", unsafe_allow_html=True)

    # Summary box
    rows_html = ""
    fields = [
        ("Customer", staged.get("customer_name") or "<em style='color:#94A3B8'>Not provided</em>"),
        ("Phone", staged.get("customer_phone") or "<em style='color:#94A3B8'>Not provided</em>"),
        ("Delivery", staged.get("delivery_date") or "<em style='color:#94A3B8'>Not specified</em>"),
        ("Address", staged.get("delivery_instructions") or "<em style='color:#94A3B8'>Not specified</em>"),
        ("Status", staged.get("status", "Pending")),
        ("Items", f"{len(staged_items)} product(s)"),
    ]
    for label, val in fields:
        rows_html += f'<div class="oa-summary-row"><span class="oa-summary-label">{label}</span><span>{val}</span></div>'

    st.markdown(f'<div class="oa-summary-box">{rows_html}</div>', unsafe_allow_html=True)

    # Item table
    items_preview = [{"Product": it["product_name"], "Qty": it["quantity"],
                       "Unit": it["unit"] or "—",
                       "Price": format_currency(it["unit_price"], CURRENCY_SYMBOL),
                       "Total": format_currency(it["line_total"], CURRENCY_SYMBOL)} for it in staged_items]
    st.dataframe(pd.DataFrame(items_preview), use_container_width=True, hide_index=True)

    st.markdown(
        f'<div style="text-align:right;font-size:1.3rem;font-weight:800;color:#4F46E5;margin:10px 0 14px;">'
        f'Grand Total: {format_currency(staged_total, CURRENCY_SYMBOL)}</div>',
        unsafe_allow_html=True)

    alert("info", "✅", "<strong>Review Required:</strong> Confirm all details are correct. "
          "Save cannot be undone from this screen.")

    confirm_check = st.checkbox(
        "I have reviewed and verified all customer details, items, quantities, and prices.",
        key="confirm_save_chk")

    col_save, col_back, _ = st.columns([2, 1.5, 3])
    with col_save:
        save_btn = st.button("💾 Save Order to Database", type="primary",
                             disabled=not confirm_check, use_container_width=True,
                             key="save_order_btn")
    with col_back:
        if st.button("← Back to Edit", key="back_to_edit"):
            st.session_state.order_confirm_ready = False
            st.rerun()

    if save_btn and confirm_check:
        if not staged_items:
            st.error("Cannot save an empty order.")
            return
        try:
            new_id = create_order(staged, staged_items, db_path=DATABASE_PATH)
            saved_rec = get_order_by_id(new_id, db_path=DATABASE_PATH)
            st.session_state.order_saved_success = {
                "number": saved_rec["order_number"],
                "customer": saved_rec.get("customer_name") or "Customer",
                "items": len(staged_items),
                "total": format_currency(saved_rec["total_amount"], CURRENCY_SYMBOL),
            }
            # Reset all order state
            for k in ["extracted_order", "extraction_notice", "extraction_engine",
                       "order_confirm_ready", "staged_order", "staged_items", "staged_total"]:
                st.session_state[k] = None if k != "order_confirm_ready" else False
            st.session_state.target_raw_msg = ""
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to save order: {e}. No partial data was written.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: ORDERS DIRECTORY (PRD §10)
# ─────────────────────────────────────────────────────────────────────────────

def render_orders_directory():
    render_header("📦", "Orders Directory",
                  "Search, filter, manage fulfillment status, and export order records to CSV.",
                  "Full History")

    # Toolbar
    tb1, tb2, tb3 = st.columns([3, 2, 2], gap="medium")
    with tb1:
        search_q = st.text_input("Search", placeholder="Order #, customer, phone, or product…",
                                  label_visibility="collapsed", key="dir_search")
    with tb2:
        status_filter = st.selectbox("Filter", ["All"] + ORDER_STATUSES,
                                      index=0, label_visibility="collapsed", key="dir_filter")
    with tb3:
        exp_df = get_orders_dataframe(search_query=search_q, status_filter=status_filter, db_path=DATABASE_PATH)
        csv_bytes = exp_df.to_csv(index=False).encode("utf-8")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("📥 Export CSV", data=csv_bytes,
                           file_name=f"orderly_export_{ts}.csv", mime="text/csv",
                           use_container_width=True, key="export_btn")

    orders = get_orders(search_query=search_q, status_filter=status_filter, limit=250, db_path=DATABASE_PATH)

    st.markdown(
        f"<div style='font-size:0.84rem;color:#64748B;margin-bottom:12px;'>"
        f"Showing <strong>{len(orders)}</strong> order(s)</div>",
        unsafe_allow_html=True)

    if not orders:
        st.markdown("""
        <div class="oa-empty">
            <span class="oa-empty-icon">🔍</span>
            <div class="oa-empty-title">No Matching Orders</div>
            <div class="oa-empty-desc">Try adjusting your search or changing the status filter to "All".</div>
        </div>""", unsafe_allow_html=True)
        return

    for order in orders:
        o_id = order["id"]
        o_num = order["order_number"]
        o_name = order["customer_name"] or "Unknown Customer"
        o_phone = order["customer_phone"] or "—"
        o_status = order["status"]
        o_total = format_currency(order["total_amount"], CURRENCY_SYMBOL)
        o_date = (order["created_at"] or "")[:16]
        badge = get_status_badge_html(o_status)
        cfg = STATUS_CONFIG.get(o_status, {})

        label = f"{o_num}  ·  {o_name}  ·  {o_total}  ·  {o_status}  ({o_date})"
        with st.expander(label, expanded=False):
            left, right = st.columns([3, 2], gap="large")

            with left:
                st.markdown(f"""
                <div style="font-size:0.875rem;line-height:1.85;color:#1E293B;">
                    <div style="font-size:0.73rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.07em;">
                        Customer &amp; Delivery</div>
                    <div style="font-size:1.0rem;font-weight:700;color:#0F172A;margin:4px 0 8px;">
                        {o_name}
                        <span style="font-size:0.84rem;color:#64748B;font-weight:400;"> · {o_phone}</span>
                    </div>
                    <div><strong style="color:#475569;">Delivery:</strong> {order.get('delivery_date') or '—'}</div>
                    <div><strong style="color:#475569;">Address:</strong> {order.get('delivery_instructions') or '—'}</div>
                    <div><strong style="color:#475569;">Created:</strong> {o_date}</div>
                </div>""", unsafe_allow_html=True)

                if order.get("raw_message"):
                    with st.expander("📄 Original Customer Message"):
                        st.code(order["raw_message"], language="text")

            with right:
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:15px 18px;margin-bottom:12px;">
                    <div style="font-size:0.7rem;font-weight:800;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:5px;">Stage</div>
                    <div style="margin-bottom:10px;">{badge}</div>
                    <div style="font-size:0.7rem;font-weight:800;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;">Order Total</div>
                    <div style="font-size:1.45rem;font-weight:800;color:#4F46E5;">{o_total}</div>
                </div>""", unsafe_allow_html=True)

                # Status updater — only show valid transitions (PRD §10)
                next_statuses = allowed_next_statuses(o_status)
                if len(next_statuses) > 1 or (next_statuses and next_statuses[0] != o_status):
                    available = [o_status] + [s for s in next_statuses if s != o_status]
                    new_st = st.selectbox("Update status:", available, index=0, key=f"st_sel_{o_id}")
                    if new_st != o_status:
                        if st.button("Apply", key=f"apply_st_{o_id}", type="primary"):
                            update_order_status(o_id, new_st, db_path=DATABASE_PATH)
                            st.success(f"Order {o_num} → {new_st}")
                            st.rerun()
                else:
                    st.markdown(
                        f'<div style="font-size:0.8rem;color:#94A3B8;font-style:italic;">Status is terminal — no further transitions.</div>',
                        unsafe_allow_html=True)

            # Line items
            full = get_order_by_id(o_id, db_path=DATABASE_PATH)
            if full and full.get("items"):
                st.markdown("<div style='font-size:0.84rem;font-weight:700;color:#0F172A;margin:14px 0 7px;'>Itemized Receipt</div>",
                            unsafe_allow_html=True)
                tbl = [{"Product": it["product_name"], "Qty": it["quantity"],
                         "Unit": it["unit"] or "—",
                         "Unit Price": format_currency(it["unit_price"], CURRENCY_SYMBOL),
                         "Line Total": format_currency(it["line_total"], CURRENCY_SYMBOL)}
                        for it in full["items"]]
                st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)

            # Delete safeguard
            st.markdown("<hr style='border:none;border-top:1px solid #F1F5F9;margin:14px 0;'>", unsafe_allow_html=True)
            if st.session_state.delete_confirmation_id == o_id:
                alert("danger", "⚠️",
                      f"<strong>Permanent deletion:</strong> Order <strong>{o_num}</strong> and all its items "
                      "will be permanently removed. This action cannot be undone.")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button(f"🚨 Delete {o_num}", key=f"confirm_del_{o_id}", type="primary"):
                        delete_order(o_id, db_path=DATABASE_PATH)
                        st.session_state.delete_confirmation_id = None
                        st.success(f"Order {o_num} deleted.")
                        st.rerun()
                with dc2:
                    if st.button("Cancel", key=f"cancel_del_{o_id}"):
                        st.session_state.delete_confirmation_id = None
                        st.rerun()
            else:
                if st.button(f"🗑️ Delete Order {o_num}", key=f"del_req_{o_id}"):
                    st.session_state.delete_confirmation_id = o_id
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: PRODUCT CATALOG & INVENTORY (Feature 5)
# ─────────────────────────────────────────────────────────────────────────────

def render_catalog_inventory():
    render_header("🏪", "Product Catalog & Inventory",
                  "Catalog of retail products, price guard limits, and real-time stock levels.",
                  "Catalog Active")

    products = get_all_products(DATABASE_PATH)
    low_stock = get_low_stock_products(DATABASE_PATH)

    # ── KPI Cards ──
    total_prods = len(products)
    low_count = len(low_stock)
    out_of_stock = sum(1 for p in products if (p.get("stock_quantity") or 0) <= 0)
    total_units = sum(float(p.get("stock_quantity") or 0) for p in products)

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(get_kpi_card_html("Active Products", str(total_prods), "In Store Catalog", "🏷️", "#4F46E5"), unsafe_allow_html=True)
    with k2:
        st.markdown(get_kpi_card_html("Total Stock", f"{total_units:,.0f} units", "Across All Categories", "📦", "#059669"), unsafe_allow_html=True)
    with k3:
        st.markdown(get_kpi_card_html("Low Stock", str(low_count), "Below Threshold", "⚠️", "#D97706"), unsafe_allow_html=True)
    with k4:
        st.markdown(get_kpi_card_html("Out of Stock", str(out_of_stock), "Needs Urgent Reorder", "🚨", "#DC2626"), unsafe_allow_html=True)

    divider()

    # ── Toolbar: Search, Filters & Add Product ──
    t1, t2, t3 = st.columns([3, 2, 2], gap="medium")
    with t1:
        cat_search = st.text_input("Search catalog", placeholder="Search by product name...", label_visibility="collapsed", key="cat_search_inp")
    with t2:
        categories = sorted(list({p.get("category", "General") for p in products}))
        cat_filter = st.selectbox("Category", ["All Categories"] + categories, index=0, label_visibility="collapsed", key="cat_filter_sel")
    with t3:
        stock_filter = st.selectbox("Stock Filter", ["All Stock Levels", "⚠️ Low / Out of Stock Only", "✅ In Stock Only"], index=0, label_visibility="collapsed", key="stock_filter_sel")

    # ── Add Product Expander Form ──
    with st.expander("Add New Product to Catalog", expanded=False):
        with st.form("new_product_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                p_name = st.text_input("Product Name *", placeholder="e.g. Sona Masoori Rice")
            with f2:
                p_cat = st.text_input("Category", value="Grocery", placeholder="e.g. Grocery, Dairy, Bakery")
            with f3:
                p_unit = st.text_input("Unit", value="kg", placeholder="e.g. kg, ltr, pcs, packet")

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                p_price = st.number_input(f"Retail Price ({CURRENCY_SYMBOL}) *", min_value=0.0, step=1.0, value=50.0)
            with p2:
                p_min = st.number_input(f"Min Allowed Price ({CURRENCY_SYMBOL})", min_value=0.0, step=1.0, value=40.0)
            with p3:
                p_max = st.number_input(f"Max Allowed Price ({CURRENCY_SYMBOL})", min_value=0.0, step=1.0, value=65.0)
            with p4:
                p_stock = st.number_input("Initial Stock Quantity", min_value=0.0, step=1.0, value=20.0)

            p_thresh = st.number_input("Low Stock Threshold Alert", min_value=0.0, step=1.0, value=5.0)

            submitted = st.form_submit_button("Save Product to Catalog", type="primary", use_container_width=True)
            if submitted:
                if not p_name.strip():
                    st.error("Please enter a product name.")
                else:
                    add_product({
                        "name": p_name.strip(),
                        "category": p_cat.strip() or "General",
                        "unit": p_unit.strip() or "pcs",
                        "unit_price": p_price,
                        "min_price": p_min,
                        "max_price": p_max,
                        "stock_quantity": p_stock,
                        "low_stock_threshold": p_thresh,
                    }, DATABASE_PATH)
                    st.success(f"Added '{p_name}' to catalog!")
                    st.rerun()

    # ── Filter products ──
    filtered = products
    if cat_search and cat_search.strip():
        q = cat_search.strip().lower()
        filtered = [p for p in filtered if q in p["name"].lower() or q in (p.get("category") or "").lower()]
    if cat_filter != "All Categories":
        filtered = [p for p in filtered if p.get("category") == cat_filter]
    if stock_filter == "⚠️ Low / Out of Stock Only":
        filtered = [p for p in filtered if (p.get("stock_quantity") or 0) <= (p.get("low_stock_threshold") or 5)]
    elif stock_filter == "✅ In Stock Only":
        filtered = [p for p in filtered if (p.get("stock_quantity") or 0) > (p.get("low_stock_threshold") or 5)]

    st.markdown(f"<div style='font-size:0.83rem;color:#64748B;margin:12px 0 10px;'>Showing <strong>{len(filtered)}</strong> products in catalog</div>", unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="oa-empty">
            <span class="oa-empty-icon">🏪</span>
            <div class="oa-empty-title">Catalog is Empty</div>
            <div class="oa-empty-desc">No products found matching your filter criteria.</div>
        </div>
        """, unsafe_allow_html=True)
        if not products:
            if st.button("🌱 Load Demo Retail Catalog (17 Products)", type="primary", key="load_cat_demo_btn"):
                seed_demo_catalog(DATABASE_PATH)
                st.success("Loaded demo catalog products!")
                st.rerun()
        return

    # ── Render Product Cards ──
    for prod in filtered:
        pid = prod["id"]
        pname = prod["name"]
        pcat = prod.get("category") or "General"
        punit = prod.get("unit") or "pcs"
        price = prod.get("unit_price")
        min_p = prod.get("min_price")
        max_p = prod.get("max_price")
        stock = float(prod.get("stock_quantity") or 0.0)
        thresh = float(prod.get("low_stock_threshold") or 5.0)

        if stock <= 0:
            stock_badge = '<span style="background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:9999px;font-size:0.75rem;font-weight:700;">🚨 Out of Stock</span>'
        elif stock <= thresh:
            stock_badge = f'<span style="background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:9999px;font-size:0.75rem;font-weight:700;">⚠️ Low Stock ({stock:.0f} {punit})</span>'
        else:
            stock_badge = f'<span style="background:#DCFCE7;color:#166534;padding:3px 10px;border-radius:9999px;font-size:0.75rem;font-weight:700;">✅ In Stock ({stock:.0f} {punit})</span>'

        price_str = format_currency(price, CURRENCY_SYMBOL) if price else "Not set"
        range_str = f"Range: {CURRENCY_SYMBOL}{min_p:.0f}–{CURRENCY_SYMBOL}{max_p:.0f}" if min_p and max_p else ""

        with st.container():
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:38px;height:38px;border-radius:10px;background:#EEF2FF;color:#4F46E5;display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:700;">
                        🏷️
                    </div>
                    <div>
                        <div style="font-weight:700;font-size:0.95rem;color:#0F172A;">
                            {pname} <span style="font-size:0.74rem;background:#F1F5F9;color:#64748B;padding:2px 8px;border-radius:9999px;font-weight:600;">{pcat}</span>
                        </div>
                        <div style="font-size:0.78rem;color:#64748B;margin-top:2px;">
                            Price: <strong>{price_str} / {punit}</strong> · {range_str}
                        </div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    {stock_badge}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Quick stock adjustment controls
            stk_col1, stk_col2, stk_col3, stk_col4, stk_del = st.columns([1, 1, 1, 1, 1.2], gap="small")
            with stk_col1:
                if st.button("−5", key=f"sub5_{pid}", use_container_width=True, help="Deduct 5 units"):
                    adjust_stock(pid, -5.0, DATABASE_PATH)
                    st.rerun()
            with stk_col2:
                if st.button("−1", key=f"sub1_{pid}", use_container_width=True, help="Deduct 1 unit"):
                    adjust_stock(pid, -1.0, DATABASE_PATH)
                    st.rerun()
            with stk_col3:
                if st.button("+1", key=f"add1_{pid}", use_container_width=True, help="Add 1 unit"):
                    adjust_stock(pid, 1.0, DATABASE_PATH)
                    st.rerun()
            with stk_col4:
                if st.button("+5", key=f"add5_{pid}", use_container_width=True, help="Add 5 units"):
                    adjust_stock(pid, 5.0, DATABASE_PATH)
                    st.rerun()
            with stk_del:
                if st.button("🗑️ Remove", key=f"del_prod_{pid}", use_container_width=True, help="Remove from catalog"):
                    delete_product(pid, DATABASE_PATH)
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: BUSINESS INSIGHTS & ANALYTICS (Feature 6)
# ─────────────────────────────────────────────────────────────────────────────

def render_business_insights():
    render_header("📈", "Business Insights & Analytics",
                  "AI-driven sales intelligence, trend velocity, top products, and customer value.",
                  "Insights Live")

    rev_summary = get_revenue_summary(DATABASE_PATH)
    stats = get_summary_stats(DATABASE_PATH)

    # ── KPI Cards ──
    b1, b2, b3, b4 = st.columns(4, gap="medium")
    with b1:
        st.markdown(get_kpi_card_html("Total Revenue", format_currency(rev_summary["all_time"], CURRENCY_SYMBOL), "Lifetime Revenue", "💰", "#059669"), unsafe_allow_html=True)
    with b2:
        st.markdown(get_kpi_card_html("Today's Sales", format_currency(rev_summary["today"], CURRENCY_SYMBOL), f"Week: {format_currency(rev_summary['this_week'], CURRENCY_SYMBOL)}", "📅", "#4F46E5"), unsafe_allow_html=True)
    with b3:
        st.markdown(get_kpi_card_html("Avg Order Value", format_currency(rev_summary["avg_order_value"], CURRENCY_SYMBOL), "Per Processed Order", "🏷️", "#7C3AED"), unsafe_allow_html=True)
    with b4:
        st.markdown(get_kpi_card_html("Total Orders", str(stats["total_orders"]), f"{stats['unique_customers']} Unique Customers", "🛍️", "#0891B2"), unsafe_allow_html=True)

    divider()

    # ── Actionable AI Recommendations ──
    st.markdown('<div class="oa-card-title">Actionable AI Business Recommendations</div>', unsafe_allow_html=True)
    ai_insights = generate_ai_insights(DATABASE_PATH)

    ins_cols = st.columns(min(len(ai_insights), 3), gap="medium")
    for idx, item in enumerate(ai_insights[:3]):
        with ins_cols[idx % len(ins_cols)]:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1.5px solid #E2E8F0;border-left:4px solid {item['color']};border-radius:12px;padding:16px 18px;height:100%;box-shadow:0 1px 4px rgba(15,23,42,0.04);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="font-weight:700;font-size:0.92rem;color:#0F172A;">{item['title']}</span>
                </div>
                <div style="font-size:0.82rem;color:#475569;line-height:1.6;">{item['body']}</div>
            </div>
            """, unsafe_allow_html=True)

    divider()

    # ── Charts & Analysis Split ──
    c_left, c_right = st.columns([1, 1], gap="large")

    with c_left:
        st.markdown('<div class="oa-card-title">Top Selling Products</div>', unsafe_allow_html=True)
        top_prods = get_top_products(limit=8, db_path=DATABASE_PATH)
        if top_prods:
            df_prods = pd.DataFrame([
                {
                    "Product": p["product_name"],
                    "Orders": p["order_count"],
                    "Quantity": f"{p['total_quantity']:.1f}",
                    "Revenue": format_currency(p["total_revenue"], CURRENCY_SYMBOL),
                }
                for p in top_prods
            ])
            st.dataframe(df_prods, use_container_width=True, hide_index=True)
        else:
            st.info("No product sales data yet. Once orders are saved, top products will appear here.")

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="oa-card-title">Top Customers by Lifetime Value</div>', unsafe_allow_html=True)
        top_custs = get_top_customers(limit=6, db_path=DATABASE_PATH)
        if top_custs:
            df_custs = pd.DataFrame([
                {
                    "Customer": c["customer_name"],
                    "Phone": c["customer_phone"] or "—",
                    "Orders": c["order_count"],
                    "Total Spent": format_currency(c["total_spent"], CURRENCY_SYMBOL),
                }
                for c in top_custs
            ])
            st.dataframe(df_custs, use_container_width=True, hide_index=True)
        else:
            st.info("No customer history recorded yet.")

    with c_right:
        st.markdown('<div class="oa-card-title">14-Day Sales Velocity</div>', unsafe_allow_html=True)
        trends = get_sales_trend(days=14, db_path=DATABASE_PATH)
        if trends:
            df_trend = pd.DataFrame([
                {
                    "Date": t["order_date"],
                    "Orders": t["order_count"],
                    "Daily Revenue": t["daily_revenue"],
                }
                for t in trends
            ])
            st.line_chart(df_trend.set_index("Date")["Daily Revenue"], use_container_width=True)
            with st.expander("View Daily Breakdown Table"):
                st.dataframe(df_trend, use_container_width=True, hide_index=True)
        else:
            st.info("Sales trends will chart here as orders accumulate across days.")

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="oa-card-title">Active Delivery Pipeline</div>', unsafe_allow_html=True)
        pending = get_pending_deliveries(DATABASE_PATH)
        if pending:
            df_pend = pd.DataFrame([
                {
                    "Order #": p["order_number"],
                    "Customer": p["customer_name"] or "—",
                    "Schedule": p["delivery_date"] or "Asap",
                    "Status": p["status"],
                    "Total": format_currency(p["total_amount"], CURRENCY_SYMBOL),
                }
                for p in pending[:6]
            ])
            st.dataframe(df_pend, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 All active deliveries are fulfilled! No pending orders awaiting action.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6: SETTINGS & SYSTEM HEALTH (PRD §14)
# ─────────────────────────────────────────────────────────────────────────────

def render_settings():
    render_header("⚙️", "Settings & System Diagnostics",
                  "Verify local AI engine status, installed models, and database health.",
                  "System Health")

    # ── Section 1: Ollama AI Engine ──
    st.markdown('<div class="oa-card-title">Local Ollama AI Engine</div>', unsafe_allow_html=True)

    cfg1, cfg2 = st.columns([3, 1], gap="medium")
    with cfg1:
        ollama_url = st.text_input("Ollama Host URL", value=DEFAULT_OLLAMA_URL, key="cfg_url")
        model_name = st.text_input("Extraction Model", value=DEFAULT_MODEL, key="cfg_model")
    with cfg2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.button("Test Connection", use_container_width=True, type="primary", key="test_conn")

    diag = check_ollama_status(ollama_url, model_name)

    if diag["connected"]:
        alert("success", "✅",
              f"<strong>Ollama Online</strong> · Connected at <code>{diag['base_url']}</code> "
              f"· Version: {diag.get('version') or 'ready'}")
        mc1, mc2 = st.columns(2, gap="medium")
        with mc1:
            st.markdown("**Installed Models**")
            for m in (diag.get("models") or []):
                icon = "🟢" if model_name.lower() in m.lower() else "⚪"
                st.markdown(f"<div style='font-size:0.84rem;padding:3px 0;'>{icon} <code>{m}</code></div>",
                            unsafe_allow_html=True)
            if not diag.get("models"):
                st.warning("No models installed. Run `ollama pull gemma3:4b`")
        with mc2:
            st.markdown("**Target Model Status**")
            if diag["has_target_model"]:
                st.success(f"'{model_name}' is ready for inference.")
            else:
                st.warning(f"'{model_name}' not installed.")
                st.code(f"ollama pull {model_name}", language="bash")
    else:
        alert("warning", "⚠️", f"<strong>Ollama Offline:</strong> {diag['error_message']}")
        st.markdown("""
        <div class="oa-card" style="margin-top:0;">
            <div style="font-weight:700;color:#0F172A;margin-bottom:8px;">Quick Setup</div>
            <ol style="margin:0;padding-left:18px;font-size:0.875rem;color:#475569;line-height:1.85;">
                <li>Open a terminal and run: <code>ollama serve</code></li>
                <li>Pull the model: <code>ollama pull gemma3:4b</code></li>
                <li>Click <strong>Test Connection</strong> above to verify.</li>
            </ol>
            <div style="margin-top:10px;font-size:0.8rem;color:#94A3B8;">
                OrderlyAI uses a local heuristic fallback parser when Ollama is unavailable.
                The fallback is less accurate — it will always be clearly labeled when active.
            </div>
        </div>""", unsafe_allow_html=True)

    divider()

    # ── Section 2: Database ──
    st.markdown('<div class="oa-card-title">SQLite Database</div>', unsafe_allow_html=True)
    db_stats = get_summary_stats(DATABASE_PATH)
    db_exists = os.path.exists(DATABASE_PATH)
    db_kb = os.path.getsize(DATABASE_PATH) / 1024 if db_exists else 0

    db1, db2, db3, db4 = st.columns(4, gap="medium")
    with db1:
        st.metric("File", os.path.basename(DATABASE_PATH), help=DATABASE_PATH)
    with db2:
        st.metric("Size", f"{db_kb:.1f} KB")
    with db3:
        st.metric("Total Orders", db_stats["total_orders"])
    with db4:
        st.metric("Unique Customers", db_stats["unique_customers"])

    divider()

    # ── Section 3: Demo Data (clearly labeled — PRD §14) ──
    st.markdown('<div class="oa-card-title">Demo Data Loader</div>', unsafe_allow_html=True)
    alert("note", "ℹ️",
          "<strong>Demo data only.</strong> These orders are fictional test records. "
          "They will appear alongside real orders. Remove them via Orders Directory when done testing.")

    if st.button("Load 3 Demo Orders", key="load_demo"):
        _seed_demo_data()
        st.success("✅ 3 demo orders seeded. Visit Orders Directory to review them.")
        st.rerun()

    divider()

    # ── Section 4: About ──
    st.markdown(f"""
    <div class="oa-card" style="margin-top:0;">
        <div class="oa-card-title">About {APP_NAME}</div>
        <div style="font-size:0.875rem;color:#475569;line-height:1.9;">
            <strong>Version:</strong> {APP_VERSION}<br>
            <strong>Tagline:</strong> <em>{APP_TAGLINE}</em><br>
            <strong>Stack:</strong> Python · Streamlit · Ollama · Gemma 3 · SQLite<br>
            <strong>Model:</strong> {DEFAULT_MODEL} — local on-device inference<br>
            <strong>Database:</strong> <code>{DATABASE_PATH}</code><br>
            <strong>Privacy:</strong> All AI inference and data storage happen on your computer.
            No customer data is sent to any external service.
        </div>
    </div>""", unsafe_allow_html=True)


def _seed_demo_data():
    demo = [
        (
            {"customer_name": "Rajesh Kumar", "customer_phone": "9876543210",
             "delivery_date": "Tomorrow morning", "delivery_instructions": "Flat 402, Sunshine Heights. Leave with security.",
             "raw_message": "[DEMO] Kirana grocery order", "status": "Pending"},
            [{"product_name": "Aashirvaad Atta", "quantity": 5.0, "unit": "kg", "unit_price": 45.0},
             {"product_name": "Fortune Sunflower Oil", "quantity": 2.0, "unit": "ltr", "unit_price": 140.0},
             {"product_name": "Tata Salt", "quantity": 1.0, "unit": "kg", "unit_price": 28.0}],
        ),
        (
            {"customer_name": "Sneha Sharma", "customer_phone": "9123456789",
             "delivery_date": "Friday 3 PM", "delivery_instructions": "Tech Park Tower B reception. Pack with knife.",
             "raw_message": "[DEMO] Bakery party order", "status": "Confirmed"},
            [{"product_name": "Belgian Chocolate Truffle Cake", "quantity": 2.0, "unit": "kg", "unit_price": 650.0},
             {"product_name": "Veg Puff Patties", "quantity": 15.0, "unit": "pcs", "unit_price": 25.0}],
        ),
        (
            {"customer_name": "Anita Desai", "customer_phone": "9845012345",
             "delivery_date": "Saturday", "delivery_instructions": "Call when you reach gate.",
             "raw_message": "[DEMO] Organic produce order", "status": "Delivered"},
            [{"product_name": "Organic Spinach", "quantity": 2.0, "unit": "bunches", "unit_price": 30.0},
             {"product_name": "Tomatoes", "quantity": 3.0, "unit": "kg", "unit_price": 40.0},
             {"product_name": "Potatoes", "quantity": 5.0, "unit": "kg", "unit_price": 35.0}],
        ),
    ]
    for od, items in demo:
        create_order(od, items, db_path=DATABASE_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# APP ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_app():
    st.set_page_config(
        page_title=f"{APP_NAME} · {APP_TAGLINE}",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(get_custom_css(), unsafe_allow_html=True)
    init_db(DATABASE_PATH)

    # Session state defaults
    defaults = {
        "raw_msg_area": "",
        "target_raw_msg": None,
        "extracted_order": None,
        "extraction_notice": None,
        "extraction_engine": None,
        "delete_confirmation_id": None,
        "current_page": PAGES[0],
        "nav_radio": PAGES[0],
        "nav_target": None,
        "order_saved_success": None,
        "order_confirm_ready": False,
        "staged_order": None,
        "staged_items": None,
        "staged_total": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Apply programmatic navigation target before sidebar widgets instantiate
    if st.session_state.get("nav_target"):
        st.session_state.nav_radio = st.session_state.nav_target
        st.session_state.current_page = st.session_state.nav_target
        st.session_state.nav_target = None

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand (Clean Typography Wordmark)
        st.markdown(f"""
        <div style="padding:14px 8px 22px 8px;border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:20px;">
            <div style="font-weight:900;font-size:1.45rem;color:#FFFFFF;letter-spacing:-0.03em;line-height:1.2;">
                Orderly<span style="color:#818CF8;">AI</span>
            </div>
            <div style="font-size:0.75rem;color:#94A3B8;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;margin-top:4px;">
                Order Intelligence
            </div>
        </div>""", unsafe_allow_html=True)

        # Navigation
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:800;color:#94A3B8;text-transform:uppercase;"
            "letter-spacing:0.12em;margin-bottom:14px;padding-left:6px;display:flex;align-items:center;gap:8px;'>"
            "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;background:#6366F1;'></span>"
            "Navigation Menu</div>",
            unsafe_allow_html=True)

        if st.session_state.nav_radio not in PAGES:
            st.session_state.nav_radio = PAGES[0]

        st.radio(
            "Navigation", PAGES,
            label_visibility="collapsed",
            key="nav_radio",
            on_change=on_nav_change,
        )
        st.session_state.current_page = st.session_state.nav_radio

    # ── ROUTE TO PAGES ────────────────────────────────────────────────────────
    page = st.session_state.current_page
    if "Dashboard" in page:
        render_dashboard()
    elif "New Order" in page:
        render_new_order()
    elif "Orders Directory" in page:
        render_orders_directory()
    elif "Catalog" in page:
        render_catalog_inventory()
    elif "Insights" in page:
        render_business_insights()
    elif "Settings" in page:
        render_settings()


if __name__ == "__main__":
    render_app()
