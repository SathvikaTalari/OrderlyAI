"""
Theme and Styling module for OrderlyAI.
Enterprise SaaS design system — slate-and-indigo palette, fully responsive,
PRD-aligned premium UI tokens, CSS, and HTML component builders.
"""

# ── Color Palette: Enterprise Slate & Indigo ──────────────────────────────────
THEME = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_light": "#EEF2FF",
    "primary_border": "#C7D2FE",
    "navy_header": "#0F172A",
    "navy_card": "#1E293B",
    "bg_main": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "text_main": "#0F172A",
    "text_muted": "#64748B",
    "text_subtle": "#94A3B8",
    "border_subtle": "#E2E8F0",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
}

# ── Order Status Configuration ────────────────────────────────────────────────
STATUS_CONFIG = {
    "Pending":          {"color": "#92400E", "bg": "#FEF3C7", "border": "#FDE68A", "dot": "#F59E0B",  "icon": "⏳"},
    "Confirmed":        {"color": "#1E40AF", "bg": "#DBEAFE", "border": "#BFDBFE", "dot": "#3B82F6",  "icon": "✅"},
    "Preparing":        {"color": "#5B21B6", "bg": "#EDE9FE", "border": "#DDD6FE", "dot": "#7C3AED",  "icon": "⚙️"},
    "Out for Delivery": {"color": "#155E75", "bg": "#CFFAFE", "border": "#A5F3FC", "dot": "#0891B2",  "icon": "🚚"},
    "Delivered":        {"color": "#065F46", "bg": "#D1FAE5", "border": "#A7F3D0", "dot": "#059669",  "icon": "📦"},
    "Cancelled":        {"color": "#991B1B", "bg": "#FEE2E2", "border": "#FECACA", "dot": "#DC2626",  "icon": "✕"},
}

# ── Valid Status Transitions (PRD §10) ────────────────────────────────────────
STATUS_TRANSITIONS = {
    "Pending":          ["Confirmed", "Cancelled"],
    "Confirmed":        ["Preparing", "Cancelled"],
    "Preparing":        ["Out for Delivery", "Cancelled"],
    "Out for Delivery": ["Delivered", "Cancelled"],
    "Delivered":        ["Delivered"],   # terminal — no forward moves
    "Cancelled":        ["Cancelled"],   # terminal
}


def allowed_next_statuses(current: str) -> list:
    """Returns the list of valid next statuses for a given current status."""
    return STATUS_TRANSITIONS.get(current, list(STATUS_CONFIG.keys()))


def get_status_badge_html(status: str) -> str:
    """Generates a pill-shaped status badge with dot indicator."""
    cfg = STATUS_CONFIG.get(status, {"color": "#475569", "bg": "#F1F5F9", "border": "#CBD5E1", "dot": "#94A3B8", "icon": "•"})
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'background:{cfg["bg"]};color:{cfg["color"]};'
        f'border:1px solid {cfg["border"]};padding:3px 10px;'
        f'border-radius:9999px;font-size:0.76rem;font-weight:700;'
        f'letter-spacing:0.02em;line-height:1.3;white-space:nowrap;">'
        f'<span style="width:7px;height:7px;border-radius:50%;'
        f'background:{cfg["dot"]};flex-shrink:0;display:inline-block;"></span>'
        f'{cfg["icon"]} {status}</span>'
    )


def get_kpi_card_html(label: str, value: str, subtext: str, icon: str, accent: str, icon_bg: str = "") -> str:
    """Renders a KPI metric card."""
    if not icon_bg:
        icon_bg = f"{accent}18"
    val_color = accent if accent not in ("#4F46E5", "#6366F1") else "#0F172A"
    return f"""
    <div class="oa-kpi-card" style="--kpi-accent:{accent};">
        <div class="oa-kpi-header">
            <span class="oa-kpi-label">{label}</span>
            <div class="oa-kpi-icon-wrap" style="background:{icon_bg};color:{accent};">{icon}</div>
        </div>
        <div class="oa-kpi-value" style="color:{val_color};">{value}</div>
        <div class="oa-kpi-sub">{subtext}</div>
    </div>"""


def get_custom_css() -> str:
    """Returns the complete production CSS for OrderlyAI — PRD §5 visual specification."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── Streamlit Chrome Removal ── */
    #MainMenu { display:none !important; }
    header[data-testid="stHeader"] { display:none !important; pointer-events:none !important; }
    footer { display:none !important; }
    div[data-testid="stToolbar"] { display:none !important; pointer-events:none !important; }
    div[data-testid="stDecoration"] { display:none !important; pointer-events:none !important; }
    div[data-testid="collapsedControl"] { color: #FFFFFF !important; }
    div[data-testid="stToast"], div[class*="stToast"] { display:none !important; }

    /* ── Global Reset ── */
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        color: #0F172A;
    }

    /* ── Layout ── */
    .stApp { background: #F8FAFC !important; }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1340px !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0B1120 !important;
        border-right: 1px solid rgba(255,255,255,0.07) !important;
        box-shadow: 4px 0 24px rgba(0,0,0,0.18);
    }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }

    /* Sidebar nav radio pills */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 4px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        padding: 9px 12px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.18s ease !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.12) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, rgba(79,70,229,0.3), rgba(99,102,241,0.18)) !important;
        border: 1px solid rgba(129,140,248,0.4) !important;
        box-shadow: 0 2px 10px rgba(79,70,229,0.25) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* ── Page Header ── */
    .oa-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 55%, #1e1b4b 100%);
        border-radius: 16px;
        padding: 22px 28px;
        margin-bottom: 22px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 30px -5px rgba(15,23,42,0.22);
        position: relative;
        overflow: hidden;
    }
    .oa-header::before {
        content:''; position:absolute; top:-60px; right:-60px;
        width:240px; height:240px;
        background: radial-gradient(circle, rgba(99,102,241,0.22) 0%, transparent 70%);
        border-radius:50%; pointer-events:none;
    }
    .oa-header-inner {
        display:flex; align-items:center; justify-content:space-between;
        flex-wrap:wrap; gap:14px; position:relative; z-index:1;
    }
    .oa-header-left { display:flex; align-items:center; gap:14px; }
    .oa-header-icon {
        width:50px; height:50px;
        background: linear-gradient(135deg,rgba(79,70,229,0.35),rgba(99,102,241,0.2));
        border: 1px solid rgba(165,180,252,0.35);
        border-radius:13px; display:flex; align-items:center;
        justify-content:center; font-size:1.6rem; flex-shrink:0;
    }
    .oa-header-title {
        color:#FFFFFF !important; font-size:1.6rem !important;
        font-weight:800 !important; margin:0 !important;
        letter-spacing:-0.03em; line-height:1.2;
    }
    .oa-header-sub {
        color:#94A3B8 !important; font-size:0.875rem !important;
        margin:3px 0 0 !important; font-weight:400; line-height:1.5;
    }
    .oa-header-badge {
        display:inline-flex; align-items:center; gap:6px;
        background:rgba(79,70,229,0.22); border:1px solid rgba(129,140,248,0.32);
        border-radius:9999px; padding:5px 13px; font-size:0.77rem;
        color:#C7D2FE; font-weight:600; white-space:nowrap;
    }

    /* ── KPI Cards ── */
    .oa-kpi-card {
        background:#FFFFFF; border-radius:14px; padding:20px 22px;
        border:1px solid #E2E8F0;
        box-shadow: 0 2px 6px rgba(15,23,42,0.04);
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
        position:relative; overflow:hidden;
        display:flex; flex-direction:column; justify-content:space-between;
        height:100%;
    }
    .oa-kpi-card::before {
        content:''; position:absolute; top:0; left:0; right:0;
        height:3.5px; background:var(--kpi-accent,#4F46E5);
    }
    .oa-kpi-card:hover {
        border-color:#CBD5E1;
        box-shadow: 0 10px 25px -4px rgba(15,23,42,0.08);
        transform: translateY(-3px);
    }
    .oa-kpi-header {
        display:flex; align-items:center;
        justify-content:space-between; margin-bottom:12px;
    }
    .oa-kpi-label { color:#64748B; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.07em; }
    .oa-kpi-icon-wrap {
        width:36px; height:36px; border-radius:10px;
        display:flex; align-items:center; justify-content:center; font-size:1.15rem;
    }
    .oa-kpi-value { font-size:2rem; font-weight:800; letter-spacing:-0.03em; line-height:1.1; margin-bottom:4px; }
    .oa-kpi-sub { font-size:0.78rem; color:#94A3B8; font-weight:400; line-height:1.4; }

    /* ── Stepper ── */
    .oa-stepper {
        display:flex; align-items:center; background:#FFFFFF;
        border:1px solid #E2E8F0; border-radius:14px; padding:15px 22px;
        margin-bottom:22px; gap:10px; overflow-x:auto;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    }
    .oa-step {
        display:flex; align-items:center; gap:9px;
        font-size:0.83rem; font-weight:600; color:#94A3B8; white-space:nowrap; flex-shrink:0;
    }
    .oa-step.active { color:#4F46E5; }
    .oa-step.done   { color:#059669; }
    .oa-step-circle {
        width:27px; height:27px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-size:0.75rem; font-weight:700;
        background:#F1F5F9; color:#94A3B8; border:2px solid #E2E8F0; flex-shrink:0;
        transition:all 0.2s ease;
    }
    .oa-step.active .oa-step-circle { background:#4F46E5; color:#FFF; border-color:#4F46E5; box-shadow:0 0 0 3px rgba(79,70,229,0.2); }
    .oa-step.done   .oa-step-circle { background:#DCFCE7; color:#059669; border-color:#86EFAC; }
    .oa-step-line { flex:1; height:2px; background:#E2E8F0; min-width:20px; border-radius:2px; }
    .oa-step-line.done { background:#10B981; }

    /* ── Alert banners ── */
    .oa-alert {
        border-radius:11px; padding:13px 17px; font-size:0.875rem; line-height:1.5;
        display:flex; align-items:flex-start; gap:11px;
        margin-bottom:14px; border:1px solid transparent;
    }
    .oa-alert-success { background:#F0FDF4; border-color:#BBF7D0; color:#14532D; }
    .oa-alert-warning { background:#FFFBEB; border-color:#FDE68A; color:#78350F; }
    .oa-alert-info    { background:#EEF2FF; border-color:#C7D2FE; color:#312E81; }
    .oa-alert-danger  { background:#FFF1F2; border-color:#FECDD3; color:#881337; }
    .oa-alert-note    { background:#F8FAFC; border-color:#CBD5E1; color:#334155; }

    /* ── Section Cards ── */
    .oa-card {
        background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px;
        padding:20px 24px; box-shadow:0 2px 6px rgba(15,23,42,0.03); margin-bottom:18px;
    }
    .oa-card-title {
        font-size:1.0rem; font-weight:700; color:#0F172A;
        margin:0 0 14px; display:flex; align-items:center; gap:8px;
        padding-bottom:12px; border-bottom:1px solid #F1F5F9;
    }

    /* ── Empty State ── */
    .oa-empty {
        text-align:center; padding:52px 24px; background:#FFFFFF;
        border:1.5px dashed #CBD5E1; border-radius:16px; margin:12px 0;
    }
    .oa-empty-icon { font-size:3rem; margin-bottom:12px; display:block; opacity:0.6; }
    .oa-empty-title { font-size:1.1rem; font-weight:700; color:#0F172A; margin-bottom:6px; }
    .oa-empty-desc { font-size:0.875rem; color:#64748B; max-width:400px; margin:0 auto; line-height:1.6; }

    /* ── Total Bar ── */
    .oa-total-bar {
        background: linear-gradient(135deg, #EEF2FF 0%, #F0FDF4 100%);
        border:1.5px solid #C7D2FE; border-radius:12px; padding:15px 20px;
        margin-top:12px; display:flex; align-items:center;
        justify-content:space-between; flex-wrap:wrap; gap:12px;
        box-shadow:0 2px 8px rgba(79,70,229,0.06);
    }
    .oa-total-label { font-size:0.85rem; color:#475569; font-weight:600; display:flex; align-items:center; gap:8px; }
    .oa-total-value { font-size:1.45rem; font-weight:800; color:#4F46E5; letter-spacing:-0.02em; }

    /* ── Order Summary Box (Stage 4 confirm) ── */
    .oa-summary-box {
        background:#F8FAFC; border:1.5px solid #C7D2FE;
        border-radius:12px; padding:18px 22px; margin:14px 0;
    }
    .oa-summary-row {
        display:flex; align-items:baseline; justify-content:space-between;
        padding:5px 0; border-bottom:1px solid #F1F5F9;
        font-size:0.875rem; color:#334155;
    }
    .oa-summary-row:last-child { border-bottom:none; }
    .oa-summary-label { font-weight:600; color:#64748B; min-width:140px; }

    /* ── Status Distribution Bar ── */
    .oa-status-bar {
        display:flex; border-radius:8px; overflow:hidden;
        height:10px; margin-bottom:10px; gap:2px;
    }
    .oa-status-seg { height:100%; transition:width 0.4s ease; }

    /* ── Buttons ── */
    div[data-testid="stButton"] > button {
        border-radius:10px !important; font-weight:600 !important;
        font-size:0.875rem !important;
        transition:all 0.18s cubic-bezier(0.4,0,0.2,1) !important;
        padding:0.53rem 1.2rem !important;
        border:1px solid #CBD5E1 !important;
        background:#FFFFFF !important; color:#1E293B !important;
        box-shadow:0 1px 3px rgba(0,0,0,0.06) !important;
        cursor:pointer !important;
    }
    div[data-testid="stButton"] > button:hover {
        border-color:#818CF8 !important; color:#4F46E5 !important;
        background:#F8FAFC !important;
        box-shadow:0 4px 14px rgba(79,70,229,0.12) !important;
        transform:translateY(-1.5px) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background:linear-gradient(135deg,#4F46E5 0%,#6366F1 100%) !important;
        border:1px solid #4338CA !important; color:#FFFFFF !important;
        box-shadow:0 2px 8px rgba(79,70,229,0.35) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background:linear-gradient(135deg,#4338CA 0%,#4F46E5 100%) !important;
        color:#FFFFFF !important;
        box-shadow:0 6px 20px rgba(79,70,229,0.45) !important;
        transform:translateY(-2px) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius:10px !important; border:1.5px solid #E2E8F0 !important;
        font-family:'Inter',sans-serif !important; font-size:0.875rem !important;
        background:#FFFFFF !important; color:#0F172A !important;
        transition:border-color 0.18s ease, box-shadow 0.18s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color:#6366F1 !important;
        box-shadow:0 0 0 3px rgba(99,102,241,0.15) !important;
        outline:none !important;
    }
    .stSelectbox > div > div {
        border-radius:10px !important; border:1.5px solid #E2E8F0 !important;
        background:#FFFFFF !important; font-size:0.875rem !important;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        background:#FFFFFF !important; border:1px solid #E2E8F0 !important;
        border-radius:12px !important; overflow:hidden !important;
        margin-bottom:10px !important; box-shadow:0 1px 4px rgba(15,23,42,0.03) !important;
        transition:all 0.2s ease !important;
    }
    [data-testid="stExpander"]:hover { border-color:#CBD5E1 !important; box-shadow:0 4px 14px rgba(15,23,42,0.06) !important; }
    [data-testid="stExpander"] summary { font-weight:600 !important; font-size:0.875rem !important; padding:13px 18px !important; color:#0F172A !important; }
    [data-testid="stExpander"] > div > div { padding:6px 18px 18px !important; background:#FAFAFA !important; border-top:1px solid #F1F5F9 !important; }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"],[data-testid="stDataEditor"] {
        border:1px solid #E2E8F0 !important; border-radius:12px !important;
        overflow:hidden !important; background:#FFFFFF !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background:#FFFFFF; border:1px solid #E2E8F0;
        border-radius:12px; padding:14px 18px;
        box-shadow:0 1px 3px rgba(15,23,42,0.04);
    }
    [data-testid="stMetricLabel"] { color:#64748B !important; font-size:0.8rem !important; }
    [data-testid="stMetricValue"] { color:#0F172A !important; font-weight:800 !important; }

    /* ── Native messages ── */
    [data-testid="stSuccess"] { border-radius:10px !important; border:1px solid #BBF7D0 !important; background:#F0FDF4 !important; }
    [data-testid="stWarning"] { border-radius:10px !important; border:1px solid #FDE68A !important; background:#FFFBEB !important; }
    [data-testid="stError"]   { border-radius:10px !important; border:1px solid #FECACA !important; background:#FEF2F2 !important; }
    [data-testid="stInfo"]    { border-radius:10px !important; border:1px solid #BFDBFE !important; background:#EFF6FF !important; }

    /* ── Pulse animation ── */
    @keyframes pulseDot {
        0%   { box-shadow:0 0 0 0 rgba(16,185,129,0.5); }
        70%  { box-shadow:0 0 0 7px rgba(16,185,129,0); }
        100% { box-shadow:0 0 0 0 rgba(16,185,129,0); }
    }
    .oa-pulse-live { animation:pulseDot 2s infinite; }

    /* ── Char counter ── */
    .oa-char-counter { font-size:0.75rem; color:#94A3B8; text-align:right; margin-top:-8px; margin-bottom:6px; }
    .oa-char-counter.warn { color:#D97706; }
    .oa-char-counter.error { color:#DC2626; }

    /* ── Responsive ── */
    @media (max-width: 992px) {
        .block-container { padding-left:1.25rem !important; padding-right:1.25rem !important; }
        .oa-header { padding:18px 20px; }
        .oa-header-title { font-size:1.35rem !important; }
    }
    @media (max-width: 768px) {
        .oa-header-inner { flex-direction:column; align-items:flex-start; }
        .oa-stepper { flex-direction:column; align-items:flex-start; gap:12px; }
        .oa-step-line { display:none; }
        .oa-total-bar { flex-direction:column; align-items:flex-start; }
    }
    </style>
    """
