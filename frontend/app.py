"""
OrderMitra AI - Local-First AI Order Management Application
Frontend Streamlit Application
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import datetime
import pandas as pd
import streamlit as st

from backend.config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DEFAULT_OLLAMA_URL,
    DEFAULT_MODEL,
    DATABASE_PATH,
    CURRENCY_SYMBOL,
    ORDER_STATUSES,
    DEFAULT_STATUS,
)
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
from backend.ollama_service import check_ollama_status
from backend.extractor import extract_order_from_message
from backend.utils import SAMPLE_MESSAGES, format_currency, get_status_color


def render_app():
    """Main Streamlit application entrypoint."""
    # Page Configuration
    st.set_page_config(
        page_title=f"{APP_NAME} - Local AI Order Management",
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for modern visual design
    st.markdown(
        """
        <style>
        .main-header {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            padding: 24px 30px;
            border-radius: 14px;
            color: #FFFFFF;
            margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .main-header h1 {
            color: #F8FAFC;
            font-size: 2.1rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }
        .main-header p {
            color: #94A3B8;
            font-size: 1.05rem;
            margin: 6px 0 0 0;
        }
        .metric-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #E2E8F0;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .metric-title {
            color: #64748B;
            font-size: 0.85rem;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .metric-value {
            color: #0F172A;
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #FFFFFF;
        }
        .safe-banner {
            background: #F0FDF4;
            border-left: 4px solid #16A34A;
            padding: 12px 18px;
            border-radius: 6px;
            color: #166534;
            font-size: 0.95rem;
            margin-bottom: 15px;
        }
        .warning-banner {
            background: #FFFBEB;
            border-left: 4px solid #D97706;
            padding: 12px 18px;
            border-radius: 6px;
            color: #92400E;
            font-size: 0.95rem;
            margin-bottom: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize Database on startup
    init_db(DATABASE_PATH)

    # Initialize Session State
    if "raw_message_input" not in st.session_state:
        st.session_state.raw_message_input = ""
    if "extracted_order" not in st.session_state:
        st.session_state.extracted_order = None
    if "extraction_notice" not in st.session_state:
        st.session_state.extraction_notice = None
    if "extraction_engine" not in st.session_state:
        st.session_state.extraction_engine = None
    if "delete_confirmation_id" not in st.session_state:
        st.session_state.delete_confirmation_id = None
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Dashboard"

    # Inspect Ollama status for sidebar indicator
    ollama_info = check_ollama_status(DEFAULT_OLLAMA_URL, DEFAULT_MODEL, timeout=1.5)

    # ----------------- SIDEBAR -----------------
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <h2 style="margin: 0; color: #1E293B;">🛍️ {APP_NAME}</h2>
                <p style="margin: 4px 0; font-size: 0.85rem; color: #64748B;">{APP_TAGLINE}</p>
                <span style="font-size: 0.75rem; background: #E2E8F0; padding: 2px 8px; border-radius: 4px;">v{APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Local AI Health Indicator
        if ollama_info["connected"]:
            if ollama_info["has_target_model"]:
                st.success(f"🟢 Ollama Ready ({DEFAULT_MODEL})", icon="✅")
            else:
                st.warning(f"🟡 Ollama Active (Model '{DEFAULT_MODEL}' missing)", icon="⚠️")
        else:
            st.info("⚪ Ollama Offline (Offline fallback available)", icon="ℹ️")

        st.markdown("### Navigation")
        pages = [
            "📊 Dashboard",
            "📝 New Order (AI Extraction)",
            "📦 Orders Directory & Export",
            "⚙️ Settings & System Health",
        ]
        
        page_selection = st.radio(
            "Go to page:",
            pages,
            index=0 if st.session_state.selected_page == "Dashboard" else 
                  1 if "New Order" in st.session_state.selected_page else
                  2 if "Orders Directory" in st.session_state.selected_page else 3,
            label_visibility="collapsed",
        )
        st.session_state.selected_page = page_selection

        st.markdown("---")
        st.markdown(
            """
            **Privacy & Security**
            - 🔒 **100% Local Processing**
            - 🚫 Zero Cloud API Calls
            - 💾 Local SQLite Storage
            - 🛡️ Strict hallucination guards
            """
        )

    # ----------------- PAGE 1: DASHBOARD -----------------
    if "Dashboard" in st.session_state.selected_page:
        st.markdown(
            f"""
            <div class="main-header">
                <h1>📊 Business Dashboard</h1>
                <p>Welcome to {APP_NAME}. Here is an overview of your local order operations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        stats = get_summary_stats(DATABASE_PATH)
        recent_orders = get_orders(limit=5, db_path=DATABASE_PATH)

        # Metric KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Total Orders</div>
                    <div class="metric-value">{stats['total_orders']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Pending Orders</div>
                    <div class="metric-value" style="color: #D97706;">{stats['pending_orders']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Delivered Orders</div>
                    <div class="metric-value" style="color: #16A34A;">{stats['delivered_orders']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Recorded Sales</div>
                    <div class="metric-value" style="color: #2563EB;">{format_currency(stats['total_revenue'], CURRENCY_SYMBOL)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Quick Action Buttons
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("➕ Extract New Order from Message", use_container_width=True, type="primary"):
                st.session_state.selected_page = "📝 New Order (AI Extraction)"
                st.rerun()
        with action_col2:
            if st.button("📦 View Orders Directory & CSV Export", use_container_width=True):
                st.session_state.selected_page = "📦 Orders Directory & Export"
                st.rerun()
        with action_col3:
            if st.button("⚙️ View Ollama & Model Status", use_container_width=True):
                st.session_state.selected_page = "⚙️ Settings & System Health"
                st.rerun()

        st.markdown("---")
        st.subheader("Recent Orders")

        if not recent_orders:
            st.info("No orders recorded yet. Paste a customer message in 'New Order' to extract and save your first order!")
        else:
            table_rows = []
            for o in recent_orders:
                table_rows.append({
                    "Order #": o["order_number"],
                    "Date": o["created_at"],
                    "Customer": o["customer_name"] or "Unknown",
                    "Phone": o["customer_phone"] or "-",
                    "Status": o["status"],
                    "Items": o["item_names_summary"] or f"{o['item_count']} items",
                    "Total": format_currency(o["total_amount"], CURRENCY_SYMBOL),
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # ----------------- PAGE 2: NEW ORDER (AI EXTRACTION) -----------------
    elif "New Order" in st.session_state.selected_page:
        st.markdown(
            f"""
            <div class="main-header">
                <h1>📝 New Order (Local AI Extraction)</h1>
                <p>Paste raw customer messages from WhatsApp, SMS, or Instagram. Gemma 3 extracts structured items instantly.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### 💡 Load Sample Customer Message:")
        preset_cols = st.columns(len(SAMPLE_MESSAGES))
        for idx, (title, sample_text) in enumerate(SAMPLE_MESSAGES.items()):
            with preset_cols[idx]:
                if st.button(f"📄 {title}", key=f"sample_btn_{idx}", use_container_width=True):
                    st.session_state.raw_message_input = sample_text
                    st.session_state.extracted_order = None
                    st.session_state.extraction_notice = None
                    st.rerun()

        raw_message = st.text_area(
            "Paste Customer Order Message:",
            value=st.session_state.raw_message_input,
            height=160,
            placeholder="Paste message here e.g.:\nHi bhaiya, please send 2 kg rice, 1 packet bread, and 1 dozen eggs to Flat 204 tomorrow morning. Call 9876543210. Thanks Ramesh.",
            help="Paste raw text from WhatsApp, SMS, Instagram DM, or notes.",
        )
        st.session_state.raw_message_input = raw_message

        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            extract_clicked = st.button("⚡ Extract Order Details", type="primary", use_container_width=True)
        with btn_col2:
            if st.button("🧹 Clear Form", use_container_width=True):
                st.session_state.raw_message_input = ""
                st.session_state.extracted_order = None
                st.session_state.extraction_notice = None
                st.session_state.extraction_engine = None
                st.rerun()

        if extract_clicked:
            if not raw_message.strip():
                st.warning("Please paste or type a customer message first.")
            else:
                with st.spinner("Processing message with local intelligence..."):
                    ok, extracted_data, notice, engine = extract_order_from_message(
                        raw_message=raw_message,
                        model=DEFAULT_MODEL,
                        base_url=DEFAULT_OLLAMA_URL,
                        allow_fallback=True,
                    )
                    if ok:
                        st.session_state.extracted_order = extracted_data
                        st.session_state.extraction_notice = notice
                        st.session_state.extraction_engine = engine
                        st.success(f"Order parsed successfully using {engine}!")
                    else:
                        st.error(f"Extraction failed: {notice}")

        if st.session_state.extraction_notice:
            st.markdown(
                f"""
                <div class="warning-banner">
                    <strong>ℹ️ Extraction Notice:</strong> {st.session_state.extraction_notice}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.session_state.extracted_order:
            data = st.session_state.extracted_order

            st.markdown("---")
            st.subheader("🔍 Review & Correct Extracted Order Details")
            st.caption("Review all extracted fields carefully. You can edit customer details and add/edit/remove product line items.")

            with st.container():
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    edit_name = st.text_input(
                        "Customer Name",
                        value=data.get("customer_name") or "",
                        placeholder="Unknown / Not provided",
                        help="Never hallucinated; left blank if absent.",
                    )
                with col_c2:
                    edit_phone = st.text_input(
                        "Customer Phone",
                        value=data.get("customer_phone") or "",
                        placeholder="e.g. 9876543210",
                        help="Phone number if mentioned in message.",
                    )
                with col_c3:
                    edit_status = st.selectbox(
                        "Initial Order Status",
                        ORDER_STATUSES,
                        index=0,
                    )

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    edit_date = st.text_input(
                        "Delivery Date / Time",
                        value=data.get("delivery_date") or "",
                        placeholder="e.g. Tomorrow, 2026-10-15, Friday 3 PM",
                    )
                with col_d2:
                    edit_instructions = st.text_input(
                        "Delivery Instructions / Address Note",
                        value=data.get("delivery_instructions") or "",
                        placeholder="e.g. Leave with security, call before arriving",
                    )

                st.markdown("##### 🛒 Order Items Breakdown")
                st.caption("Edit quantities, units, and unit prices. Add or delete rows as needed.")

                initial_items = data.get("items", [])
                if not initial_items:
                    initial_items = [{"product_name": "", "quantity": 1.0, "unit": "", "unit_price": ""}]

                items_df = pd.DataFrame(initial_items)
                for col in ["product_name", "quantity", "unit", "unit_price"]:
                    if col not in items_df.columns:
                        items_df[col] = ""

                items_df = items_df[["product_name", "quantity", "unit", "unit_price"]]
                items_df.columns = ["Product Name", "Quantity", "Unit", "Unit Price"]

                edited_df = st.data_editor(
                    items_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Product Name": st.column_config.TextColumn("Product Name", required=True),
                        "Quantity": st.column_config.NumberColumn("Quantity", min_value=0.01, step=1.0, default=1.0),
                        "Unit": st.column_config.TextColumn("Unit (kg, pcs, pkt...)"),
                        "Unit Price": st.column_config.NumberColumn("Unit Price", step=1.0, format=f"{CURRENCY_SYMBOL}%0.2f"),
                    },
                    key="order_items_editor",
                )

                calc_items = []
                calculated_total = 0.0
                for _, row in edited_df.iterrows():
                    p_name = str(row["Product Name"]).strip() if pd.notna(row["Product Name"]) else ""
                    if not p_name:
                        continue
                    try:
                        q = float(row["Quantity"]) if pd.notna(row["Quantity"]) else 1.0
                    except (ValueError, TypeError):
                        q = 1.0

                    u = str(row["Unit"]).strip() if pd.notna(row["Unit"]) else ""

                    p_val = None
                    line_total = 0.0
                    if pd.notna(row["Unit Price"]) and str(row["Unit Price"]).strip() != "":
                        try:
                            p_val = float(row["Unit Price"])
                            line_total = round(q * p_val, 2)
                            calculated_total += line_total
                        except (ValueError, TypeError):
                            p_val = None

                    calc_items.append({
                        "product_name": p_name,
                        "quantity": q,
                        "unit": u,
                        "unit_price": p_val,
                        "line_total": line_total if p_val is not None else None,
                    })

                st.markdown(
                    f"""
                    <div style="text-align: right; margin-top: 10px; font-size: 1.15rem; font-weight: 600;">
                        Estimated Order Total: <span style="color: #2563EB;">{format_currency(calculated_total, CURRENCY_SYMBOL)}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("---")
                st.markdown(
                    """
                    <div class="safe-banner">
                        <strong>🛡️ Order Confirmation Safeguard:</strong>
                        Order will NOT be saved to the database until you explicitly review and verify the details above.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                confirm_check = st.checkbox(
                    "I have verified the customer details and line items above.",
                    key="confirm_order_save",
                )

                save_col1, save_col2 = st.columns([1, 3])
                with save_col1:
                    save_button = st.button(
                        "💾 Confirm & Save Order",
                        type="primary",
                        disabled=not confirm_check,
                        use_container_width=True,
                    )

                if save_button:
                    if not calc_items:
                        st.error("Cannot save order with no valid products. Please specify at least one product.")
                    else:
                        order_payload = {
                            "customer_name": edit_name.strip() if edit_name else None,
                            "customer_phone": edit_phone.strip() if edit_phone else None,
                            "delivery_date": edit_date.strip() if edit_date else None,
                            "delivery_instructions": edit_instructions.strip() if edit_instructions else None,
                            "raw_message": raw_message.strip(),
                            "status": edit_status,
                        }

                        new_id = create_order(order_payload, calc_items, db_path=DATABASE_PATH)
                        saved_order = get_order_by_id(new_id, db_path=DATABASE_PATH)
                        
                        st.success(f"🎉 Order #{saved_order['order_number']} successfully saved to SQLite database!")
                        st.session_state.extracted_order = None
                        st.session_state.raw_message_input = ""
                        st.session_state.extraction_notice = None

                        if st.button("👉 View in Orders Directory", key="goto_orders_after_save"):
                            st.session_state.selected_page = "📦 Orders Directory & Export"
                            st.rerun()

    # ----------------- PAGE 3: ORDERS DIRECTORY & EXPORT -----------------
    elif "Orders Directory" in st.session_state.selected_page:
        st.markdown(
            f"""
            <div class="main-header">
                <h1>📦 Orders Directory & Export</h1>
                <p>Search, filter, view details, update fulfillment statuses, and export orders to CSV.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        f_col1, f_col2, f_col3 = st.columns([3, 2, 2])
        with f_col1:
            search_query = st.text_input(
                "Search orders:",
                placeholder="Search by customer name, phone, order #, or product...",
                help="Full-text query across orders and item names.",
            )
        with f_col2:
            status_filter = st.selectbox(
                "Filter by status:",
                ["All"] + ORDER_STATUSES,
                index=0,
            )
        with f_col3:
            export_df = get_orders_dataframe(
                search_query=search_query,
                status_filter=status_filter,
                db_path=DATABASE_PATH,
            )
            csv_bytes = export_df.to_csv(index=False).encode("utf-8")
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Export to CSV",
                data=csv_bytes,
                file_name=f"ordermitra_orders_{timestamp_str}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Download filtered orders and itemized records as a clean CSV file.",
            )

        orders_list = get_orders(
            search_query=search_query,
            status_filter=status_filter,
            limit=200,
            db_path=DATABASE_PATH,
        )

        st.markdown(f"**Found {len(orders_list)} order(s)**")

        if not orders_list:
            st.info("No matching orders found. Try clearing your search query or extract a new order!")
        else:
            for order in orders_list:
                o_id = order["id"]
                o_num = order["order_number"]
                o_name = order["customer_name"] or "Unknown Customer"
                o_phone = order["customer_phone"] or "No phone"
                o_status = order["status"]
                o_total = format_currency(order["total_amount"], CURRENCY_SYMBOL)
                o_date = order["created_at"]
                status_color = get_status_color(o_status)

                header_label = f"**{o_num}** — {o_name} ({o_phone}) | Total: {o_total} | Status: {o_status} ({o_date})"

                with st.expander(header_label, expanded=False):
                    det_col1, det_col2 = st.columns([2, 1])

                    with det_col1:
                        st.markdown(f"**Customer:** {o_name}")
                        st.markdown(f"**Phone:** {o_phone}")
                        st.markdown(f"**Delivery Target:** {order['delivery_date'] or 'Not specified'}")
                        st.markdown(f"**Instructions / Address:** {order['delivery_instructions'] or 'None'}")
                        if order.get("raw_message"):
                            with st.expander("📄 View Original Message"):
                                st.text(order["raw_message"])

                    with det_col2:
                        st.markdown(
                            f"""
                            <div style="padding: 10px; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 0.85rem; color: #64748B;">CURRENT STATUS</div>
                                <span class="status-badge" style="background-color: {status_color}; font-size: 0.95rem;">
                                    {o_status}
                                </span>
                                <div style="margin-top: 10px; font-size: 0.85rem; color: #64748B;">ORDER VALUE</div>
                                <div style="font-size: 1.3rem; font-weight: 700; color: #0F172A;">{o_total}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        
                        new_st = st.selectbox(
                            "Update Status:",
                            ORDER_STATUSES,
                            index=ORDER_STATUSES.index(o_status) if o_status in ORDER_STATUSES else 0,
                            key=f"status_select_{o_id}",
                        )
                        if new_st != o_status:
                            if st.button("Apply Status", key=f"apply_status_{o_id}"):
                                update_order_status(o_id, new_st, db_path=DATABASE_PATH)
                                st.success(f"Order #{o_num} updated to {new_st}")
                                st.rerun()

                    full_order = get_order_by_id(o_id, db_path=DATABASE_PATH)
                    if full_order and full_order.get("items"):
                        st.markdown("##### Ordered Items")
                        items_table = []
                        for it in full_order["items"]:
                            items_table.append({
                                "Product": it["product_name"],
                                "Quantity": it["quantity"],
                                "Unit": it["unit"] or "-",
                                "Unit Price": format_currency(it["unit_price"], CURRENCY_SYMBOL),
                                "Line Total": format_currency(it["line_total"], CURRENCY_SYMBOL),
                            })
                        st.dataframe(pd.DataFrame(items_table), use_container_width=True, hide_index=True)

                    st.markdown("---")
                    if st.session_state.delete_confirmation_id == o_id:
                        st.error(f"⚠️ Are you sure you want to permanently delete order {o_num}? This action cannot be undone.")
                        del_c1, del_c2 = st.columns(2)
                        with del_c1:
                            if st.button("🚨 Yes, Permanently Delete", key=f"confirm_del_btn_{o_id}", type="primary"):
                                delete_order(o_id, db_path=DATABASE_PATH)
                                st.session_state.delete_confirmation_id = None
                                st.success(f"Order {o_num} was deleted.")
                                st.rerun()
                        with del_c2:
                            if st.button("Cancel", key=f"cancel_del_btn_{o_id}"):
                                st.session_state.delete_confirmation_id = None
                                st.rerun()
                    else:
                        if st.button(f"🗑️ Delete Order {o_num}", key=f"del_req_{o_id}"):
                            st.session_state.delete_confirmation_id = o_id
                            st.rerun()

    # ----------------- PAGE 4: SETTINGS & SYSTEM HEALTH -----------------
    elif "Settings" in st.session_state.selected_page:
        st.markdown(
            f"""
            <div class="main-header">
                <h1>⚙️ Settings & System Health</h1>
                <p>Inspect local Ollama connectivity, model availability, and local SQLite database statistics.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("1. Local Ollama AI Diagnostics")
        
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            ollama_url_input = st.text_input("Ollama Host URL:", value=DEFAULT_OLLAMA_URL)
            model_input = st.text_input("Target Model:", value=DEFAULT_MODEL)
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True)
            test_btn = st.button("🔄 Test Ollama Connection", use_container_width=True, type="primary")

        diag_result = check_ollama_status(ollama_url_input, model_input)

        st.markdown("##### Connection Status")
        if diag_result["connected"]:
            st.success(f"Connected to Ollama at {diag_result['base_url']}")
            if diag_result.get("version"):
                st.caption(f"Ollama Version: {diag_result['version']}")

            st.markdown("##### Installed Local Models")
            if diag_result["models"]:
                st.write(diag_result["models"])
            else:
                st.warning("No models found in Ollama yet. You need to pull a model first.")

            if diag_result["has_target_model"]:
                st.success(f"Target model '{model_input}' is installed and ready for inference!")
            else:
                st.error(f"Target model '{model_input}' is NOT installed in Ollama.")
                st.code(f"ollama pull {model_input}", language="powershell")
        else:
            st.error(diag_result["error_message"] or "Unable to connect to Ollama.")
            st.markdown(
                """
                <div class="warning-banner">
                    <strong>Ollama is not running.</strong> To run local AI on Windows:
                    <ol>
                        <li>Download & install Ollama from <a href="https://ollama.com" target="_blank">ollama.com</a></li>
                        <li>Open Windows PowerShell and start Ollama: <code>ollama serve</code></li>
                        <li>Pull Gemma 3: <code>ollama pull gemma3:4b</code></li>
                    </ol>
                    <em>Note: OrderMitra AI includes an automatic offline rule-based parser so you can still test extraction even when Ollama is offline!</em>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.subheader("2. SQLite Database Information")

        db_stats = get_summary_stats(DATABASE_PATH)
        db_file_exists = os.path.exists(DATABASE_PATH)
        db_size_kb = os.path.getsize(DATABASE_PATH) / 1024 if db_file_exists else 0

        col_db1, col_db2, col_db3 = st.columns(3)
        with col_db1:
            st.metric("Database Path", os.path.basename(DATABASE_PATH), help=DATABASE_PATH)
        with col_db2:
            st.metric("Database File Size", f"{db_size_kb:.1f} KB")
        with col_db3:
            st.metric("Total Stored Orders", db_stats["total_orders"])

        st.markdown("##### Demo Data")
        if st.button("🌱 Load 3 Sample Orders into Database"):
            demo_orders = [
                (
                    {
                        "customer_name": "Rajesh Kumar",
                        "customer_phone": "9876543210",
                        "delivery_date": "Tomorrow morning",
                        "delivery_instructions": "Flat 402, Sunshine Heights. Leave with security.",
                        "raw_message": "Hi Bhaiya! Send 5 kg Aashirvaad Atta, 2 kg Fortune Oil @ 140/kg, 1 kg Tata Salt. Rajesh 9876543210",
                        "status": "Pending",
                    },
                    [
                        {"product_name": "Aashirvaad Atta", "quantity": 5.0, "unit": "kg", "unit_price": 45.0},
                        {"product_name": "Fortune Sunflower Oil", "quantity": 2.0, "unit": "kg", "unit_price": 140.0},
                        {"product_name": "Tata Salt", "quantity": 1.0, "unit": "kg", "unit_price": 28.0},
                    ],
                ),
                (
                    {
                        "customer_name": "Sneha Sharma",
                        "customer_phone": "9123456789",
                        "delivery_date": "Friday 3 PM",
                        "delivery_instructions": "Tech Park, Tower B reception. Pack with knife and candles.",
                        "raw_message": "2 kg Belgian Chocolate Truffle Cake, 15 veg puff patties @ 25. Sneha 9123456789",
                        "status": "Confirmed",
                    },
                    [
                        {"product_name": "Belgian Chocolate Truffle Cake", "quantity": 2.0, "unit": "kg", "unit_price": 650.0},
                        {"product_name": "Veg Puff Patties", "quantity": 15.0, "unit": "pcs", "unit_price": 25.0},
                    ],
                ),
                (
                    {
                        "customer_name": "Anita Desai",
                        "customer_phone": "9845012345",
                        "delivery_date": "Saturday",
                        "delivery_instructions": "Call when you reach gate.",
                        "raw_message": "Organic Spinach 2 bunches, Tomatoes 3 kg @ 40, Potatoes 5 kg. Anita 9845012345",
                        "status": "Delivered",
                    },
                    [
                        {"product_name": "Organic Spinach", "quantity": 2.0, "unit": "bunches", "unit_price": 30.0},
                        {"product_name": "Tomatoes", "quantity": 3.0, "unit": "kg", "unit_price": 40.0},
                        {"product_name": "Potatoes", "quantity": 5.0, "unit": "kg", "unit_price": 35.0},
                    ],
                ),
            ]
            for ord_data, itms in demo_orders:
                create_order(ord_data, itms, db_path=DATABASE_PATH)
            st.success("Successfully seeded 3 demo orders! Check the 'Dashboard' or 'Orders Directory'.")
            st.rerun()


if __name__ == "__main__" or "streamlit" in sys.modules:
    render_app()
