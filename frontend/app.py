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
from backend.utils import SAMPLE_MESSAGES, format_currency
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
    "⚙️ Settings & Health",
]


# ─────────────────────────────────────────────────────────────────────────────
# Shared UI Helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_header(icon: str, title: str, subtitle: str, badge_text: str = ""):
    badge = f'<div class="oa-header-badge">● {badge_text}</div>' if badge_text else ""
    st.markdown(f"""
    <div class="oa-header">
        <div class="oa-header-inner">
            <div class="oa-header-left">
                <div class="oa-header-icon">{icon}</div>
                <div>
                    <div class="oa-header-title">{title}</div>
                    <div class="oa-header-sub">{subtitle}</div>
                </div>
            </div>
            {badge}
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
    """Switches navigation page and triggers rerun."""
    for p in PAGES:
        if page_keyword.lower() in p.lower():
            st.session_state.current_page = p
            st.session_state.nav_radio = p
            st.rerun()


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
        section_title("📈 Order Status Distribution")

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
    qa1, qa2, qa3 = st.columns(3, gap="medium")
    with qa1:
        if st.button("➕  Extract New Order", type="primary", use_container_width=True, key="dash_new"):
            nav_to("New Order")
    with qa2:
        if st.button("📋  Orders Directory", use_container_width=True, key="dash_dir"):
            nav_to("Orders Directory")
    with qa3:
        if st.button("⚙️  System Diagnostics", use_container_width=True, key="dash_diag"):
            nav_to("Settings")

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
            if st.button("✨ Create Your First Order", type="primary", use_container_width=True, key="dash_first_order"):
                nav_to("New Order")
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
                "Order #": st.column_config.TextColumn("Order #", width="small"),
                "Date": st.column_config.TextColumn("Date/Time", width="small"),
                "Customer": st.column_config.TextColumn("Customer", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
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
            if st.button("📦 View in Orders Directory", key="post_save_dir"):
                st.session_state.order_saved_success = None
                nav_to("Orders Directory")
        with col_b:
            if st.button("➕ New Order", key="post_save_new", type="primary"):
                st.session_state.order_saved_success = None
                st.rerun()
        st.session_state.order_saved_success = None
        return

    # ── STAGE 1: Enter Message ─────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:600;color:#475569;margin-bottom:7px;'>"
        "💡 Load a sample message to test extraction:</div>", unsafe_allow_html=True)

    sample_keys = list(SAMPLE_MESSAGES.keys())
    preset_cols = st.columns(len(sample_keys), gap="small")
    for idx, title in enumerate(sample_keys):
        short = title.split(" / ")[0].replace(" Message", "").replace(" Order", "").replace(" WhatsApp", "")
        with preset_cols[idx]:
            if st.button(f"📄 {short}", key=f"preset_{idx}", use_container_width=True):
                st.session_state.raw_msg_area = SAMPLE_MESSAGES[title]
                st.session_state.extracted_order = None
                st.session_state.extraction_notice = None
                st.session_state.order_confirm_ready = False
                st.rerun()

    raw_message = st.text_area(
        "Customer Message (WhatsApp / SMS / DM)",
        value=st.session_state.get("raw_msg_area", ""),
        key="raw_msg_area",
        height=136,
        placeholder=(
            "e.g. Hi Bhaiya! Send 5 kg Aashirvaad Atta @ 45/kg, "
            "2 kg Fortune Oil @ 140/kg. Deliver tomorrow 10 AM. "
            "Flat 402. Rajesh 9876543210"
        ),
        help="Paste the verbatim customer message. All AI processing runs locally on your machine.",
    )

    # Character counter (PRD §7 Stage 1 — input validation)
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
            st.session_state.raw_msg_area = ""
            st.session_state.extracted_order = None
            st.session_state.extraction_notice = None
            st.session_state.extraction_engine = None
            st.session_state.order_confirm_ready = False
            st.rerun()

    # Input validation
    if extract_clicked:
        trimmed = raw_message.strip()
        if not trimmed:
            st.warning("⚠️ Please paste a customer message before extracting.")
            return
        if len(trimmed) > MAX_MESSAGE_CHARS:
            st.error(f"❌ Message too long ({len(trimmed)} characters). Please keep it under {MAX_MESSAGE_CHARS} characters.")
            return

        with st.spinner("🤖 Analyzing with local Gemma 3…"):
            ok, data, notice, engine = extract_order_from_message(
                raw_message=trimmed,
                model=DEFAULT_MODEL,
                base_url=DEFAULT_OLLAMA_URL,
                allow_fallback=True,
            )
        if ok:
            st.session_state.extracted_order = data
            st.session_state.extraction_notice = notice
            st.session_state.extraction_engine = engine
            st.session_state.order_confirm_ready = False
            st.rerun()
        else:
            st.error(f"Extraction failed: {notice}")

    # Extraction engine notice (PRD §8 — clearly label AI vs fallback)
    engine = st.session_state.get("extraction_engine", "")
    if st.session_state.get("extraction_notice"):
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

    # ── STAGE 2: Review & Edit ─────────────────────────────────────────────
    if not st.session_state.extracted_order:
        return

    data = st.session_state.extracted_order
    divider()

    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:10px;">
        <div>
            <div style="font-size:1.05rem;font-weight:700;color:#0F172A;">
                Stage 2 — Review &amp; Correct Extracted Order
            </div>
            <div style="font-size:0.83rem;color:#64748B;margin-top:2px;">
                Verify every field. Nothing is saved until you confirm in Stage 3.
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

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
            st.session_state.raw_msg_area = ""
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
# PAGE 4: SETTINGS & SYSTEM HEALTH (PRD §14)
# ─────────────────────────────────────────────────────────────────────────────

def render_settings():
    render_header("⚙️", "Settings & System Diagnostics",
                  "Verify local AI engine status, installed models, and database health.",
                  "System Health")

    # ── Section 1: Ollama AI Engine ──
    st.markdown('<div class="oa-card-title">🤖 Local Ollama AI Engine</div>', unsafe_allow_html=True)

    cfg1, cfg2 = st.columns([3, 1], gap="medium")
    with cfg1:
        ollama_url = st.text_input("Ollama Host URL", value=DEFAULT_OLLAMA_URL, key="cfg_url")
        model_name = st.text_input("Extraction Model", value=DEFAULT_MODEL, key="cfg_model")
    with cfg2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Test Connection", use_container_width=True, type="primary", key="test_conn")

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
    st.markdown('<div class="oa-card-title">🗄️ SQLite Database</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="oa-card-title">🌱 Demo Data Loader</div>', unsafe_allow_html=True)
    alert("note", "ℹ️",
          "<strong>Demo data only.</strong> These orders are fictional test records. "
          "They will appear alongside real orders. Remove them via Orders Directory when done testing.")

    if st.button("🌱 Load 3 Demo Orders", key="load_demo"):
        _seed_demo_data()
        st.success("✅ 3 demo orders seeded. Visit Orders Directory to review them.")
        st.rerun()

    divider()

    # ── Section 4: About ──
    st.markdown(f"""
    <div class="oa-card" style="margin-top:0;">
        <div class="oa-card-title">ℹ️ About {APP_NAME}</div>
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
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(get_custom_css(), unsafe_allow_html=True)
    init_db(DATABASE_PATH)

    # Session state defaults
    defaults = {
        "raw_msg_area": "",
        "extracted_order": None,
        "extraction_notice": None,
        "extraction_engine": None,
        "delete_confirmation_id": None,
        "current_page": PAGES[0],
        "nav_radio": PAGES[0],
        "order_saved_success": None,
        "order_confirm_ready": False,
        "staged_order": None,
        "staged_items": None,
        "staged_total": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    ollama_info = check_ollama_status(DEFAULT_OLLAMA_URL, DEFAULT_MODEL, timeout=1.5)

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        # Brand
        st.markdown(f"""
        <div style="padding:10px 4px 18px 4px;">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="background:linear-gradient(135deg,#4F46E5,#6366F1);color:white;
                            width:42px;height:42px;border-radius:12px;display:flex;
                            align-items:center;justify-content:center;font-size:1.35rem;
                            box-shadow:0 4px 14px rgba(79,70,229,0.4);">
                    🛍️
                </div>
                <div>
                    <div style="font-weight:800;font-size:1.1rem;color:#FFFFFF;letter-spacing:-0.03em;">
                        {APP_NAME}
                    </div>
                    <div style="font-size:0.72rem;color:#64748B;margin-top:1px;">
                        v{APP_VERSION} · {APP_TAGLINE}
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # AI Status
        if ollama_info["connected"] and ollama_info["has_target_model"]:
            s_bg, s_border, s_color, s_dot, s_pulse = (
                "rgba(16,185,129,0.12)", "rgba(16,185,129,0.3)", "#34D399", "#10B981", "oa-pulse-live")
            s_label = f"AI Ready · {DEFAULT_MODEL}"
        elif ollama_info["connected"]:
            s_bg, s_border, s_color, s_dot, s_pulse = (
                "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)", "#FCD34D", "#F59E0B", "")
            s_label = f"Ollama On · Model not pulled"
        else:
            s_bg, s_border, s_color, s_dot, s_pulse = (
                "rgba(255,255,255,0.04)", "rgba(255,255,255,0.08)", "#94A3B8", "#64748B", "")
            s_label = "Offline · Heuristic Fallback"

        st.markdown(f"""
        <div style="background:{s_bg};border:1px solid {s_border};border-radius:10px;
                    padding:9px 12px;margin-bottom:22px;display:flex;align-items:center;gap:10px;">
            <div class="{s_pulse}" style="width:8px;height:8px;border-radius:50%;background:{s_dot};flex-shrink:0;"></div>
            <div style="font-size:0.77rem;font-weight:600;color:{s_color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {s_label}
            </div>
        </div>""", unsafe_allow_html=True)

        # Navigation
        st.markdown(
            "<div style='font-size:0.68rem;font-weight:800;color:#64748B;text-transform:uppercase;"
            "letter-spacing:0.1em;margin-bottom:9px;padding-left:4px;'>Navigation</div>",
            unsafe_allow_html=True)

        if st.session_state.nav_radio not in PAGES:
            st.session_state.nav_radio = PAGES[0]

        st.radio(
            "Navigation", PAGES,
            index=PAGES.index(st.session_state.nav_radio),
            label_visibility="collapsed",
            key="nav_radio",
            on_change=on_nav_change,
        )
        st.session_state.current_page = st.session_state.nav_radio

        # Privacy Card (PRD §5)
        st.markdown("""
        <div style="margin-top:30px;border-top:1px solid rgba(255,255,255,0.07);padding-top:18px;">
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                        border-radius:12px;padding:13px 15px;font-size:0.77rem;color:#94A3B8;">
                <div style="font-weight:700;color:#FFFFFF;margin-bottom:8px;">🛡️ Local-First Privacy</div>
                <div style="line-height:1.75;font-size:0.75rem;">
                    <span style="color:#10B981;">✓</span> On-device Gemma 3 AI inference<br>
                    <span style="color:#10B981;">✓</span> SQLite — no cloud database<br>
                    <span style="color:#10B981;">✓</span> Zero external API calls required
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── ROUTE TO PAGES ────────────────────────────────────────────────────────
    page = st.session_state.current_page
    if "Dashboard" in page:
        render_dashboard()
    elif "New Order" in page:
        render_new_order()
    elif "Orders Directory" in page:
        render_orders_directory()
    elif "Settings" in page:
        render_settings()


if __name__ == "__main__":
    render_app()
