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


def get_kpi_card_html(label: str, value: str, subtext: str, icon: str = "", accent: str = "#4F46E5", icon_bg: str = "") -> str:
    """Renders a clean KPI metric card."""
    val_color = accent if accent not in ("#4F46E5", "#6366F1") else "#0F172A"
    return f"""
    <div class="oa-kpi-card" style="--kpi-accent:{accent};">
        <div class="oa-kpi-header">
            <span class="oa-kpi-label">{label}</span>
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

    /* ── Global Reset & Typography ── */
    *, *::before, *::after { box-sizing: border-box; }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        color: #0F172A;
    }

    /* ── Main Layout (Full Screen Visibility) ── */
    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        overflow-x: hidden !important;
    }
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2.75rem !important;
        padding-right: 2.75rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* ── Labels & Text Visibility ── */
    label[data-testid="stWidgetLabel"],
    div[data-testid="stWidgetLabel"] p,
    label p {
        color: #0F172A !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-bottom: 4px !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #0F172A;
    }

    /* ── Modern Segmented Control for Tabs (PRD §5) ── */
    div[data-testid="stTabs"] {
        margin-top: 6px !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-list"],
    div[data-testid="stTabs"] [role="tablist"] {
        background: #F1F5F9 !important;
        padding: 5px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        gap: 6px !important;
        display: flex !important;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04) !important;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] div[data-baseweb="tab-border"],
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"],
    div[data-testid="stTabs"] button[role="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 8px 18px !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
    div[data-testid="stTabs"] button[role="tab"]:hover {
        color: #0F172A !important;
        background: rgba(255, 255, 255, 0.65) !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #FFFFFF !important;
        color: #4F46E5 !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
    }
    div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #4F46E5 !important;
        font-weight: 700 !important;
    }

    /* ── Form Inputs & Textareas (High Contrast & Clear Visibility) ── */
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea,
    .stTextInput input,
    .stTextArea textarea {
        background-color: transparent !important;
        color: #0F172A !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        line-height: 1.55 !important;
        padding: 10px 14px !important;
    }
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder,
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }
    /* Disabled inputs */
    div[data-baseweb="input"]:has(input:disabled),
    div[data-baseweb="textarea"]:has(textarea:disabled) {
        background-color: #F8FAFC !important;
        border-color: #E2E8F0 !important;
    }
    div[data-baseweb="input"] input:disabled,
    div[data-baseweb="textarea"] textarea:disabled {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
    }

    /* ── Select Boxes ── */
    div[data-baseweb="select"] {
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        min-height: 42px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #94A3B8 !important;
    }
    div[data-baseweb="select"]:focus-within > div {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
    }
    div[data-baseweb="select"] svg {
        fill: #475569 !important;
    }
    /* Popover menu options */
    div[data-baseweb="popover"],
    ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12) !important;
        padding: 4px !important;
    }
    li[role="option"] {
        color: #0F172A !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 9px 14px !important;
        border-radius: 7px !important;
        transition: background-color 0.15s ease !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #EEF2FF !important;
        color: #4F46E5 !important;
    }

    /* ── File Uploader Styling ── */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #CBD5E1 !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #4F46E5 !important;
        background-color: #F8FAFC !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 8px !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] section div,
    div[data-testid="stFileUploader"] section span {
        color: #334155 !important;
        font-size: 0.875rem !important;
    }
    div[data-testid="stFileUploader"] section button {
        background: #EEF2FF !important;
        border: 1.5px solid #C7D2FE !important;
        color: #4F46E5 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stFileUploader"] section button:hover {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        border-color: #4338CA !important;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25) !important;
    }
    div[data-testid="stFileUploader"] small {
        color: #64748B !important;
        font-size: 0.8rem !important;
    }

    /* ── Buttons (High-Impact Enterprise SaaS) ── */
    div[data-testid="stButton"] > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.25rem !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        border: 1.5px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #818CF8 !important;
        color: #4F46E5 !important;
        background: #F8FAFC !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.12) !important;
        transform: translateY(-1.5px) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"],
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
        border: 1px solid #3730A3 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.32) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover {
        background: linear-gradient(135deg, #4338CA 0%, #3730A3 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.42) !important;
        transform: translateY(-2px) !important;
    }
    div[data-testid="stButton"] > button:disabled {
        opacity: 0.55 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Download button */
    div[data-testid="stDownloadButton"] > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.25rem !important;
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.18s ease !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
        background: #EEF2FF !important;
        transform: translateY(-1.5px) !important;
    }

    /* ── Popover Trigger Button ── */
    div[data-testid="stPopover"] > button {
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.38rem 0.85rem !important;
        background: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #4F46E5 !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.18s ease !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #4F46E5 !important;
        background: #EEF2FF !important;
        color: #4338CA !important;
        transform: translateY(-1px) !important;
    }

    /* ── Checkbox ── */
    div[data-testid="stCheckbox"] label span {
        color: #0F172A !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
    }

    /* ── Sidebar (Wider & Large Prominent Navigators) ── */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        background: #0B1120 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 6px 0 30px rgba(0, 0, 0, 0.3) !important;
        min-width: 320px !important;
        max-width: 360px !important;
        width: 340px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        width: 340px !important;
        min-width: 320px !important;
    }
    [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.8rem !important;
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* Sidebar nav radio pills (Large, Prominent, Enterprise-Style) */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
        position: relative !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.09) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    }
    /* Cleanly hide the radio dot so navigation options look like large modern tab buttons */
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-baseweb="radio"] {
        position: absolute !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        pointer-events: none !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important;
        margin: 0 !important;
        letter-spacing: -0.01em !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        line-height: 1.4 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }
    /* Active / Selected Tab State */
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        border: 1.5px solid #818CF8 !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45) !important;
        transform: translateX(4px) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: #A5B4FC;
        border-top-left-radius: 12px;
        border-bottom-left-radius: 12px;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
    }

    /* ── Page Header Banner ── */
    .oa-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 55%, #1e1b4b 100%);
        border-radius: 16px;
        padding: 22px 28px;
        margin-bottom: 22px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.22);
        position: relative;
        overflow: hidden;
    }
    .oa-header::before {
        content: ''; position: absolute; top: -60px; right: -60px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none;
    }
    .oa-header-inner {
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 14px; position: relative; z-index: 1;
    }
    .oa-header-left { display: flex; align-items: center; gap: 15px; }
    .oa-header-icon {
        display: none !important;
    }
    .oa-header-title {
        color: #FFFFFF !important; font-size: 1.65rem !important;
        font-weight: 800 !important; margin: 0 !important;
        letter-spacing: -0.03em; line-height: 1.2;
    }
    .oa-header-sub {
        color: #94A3B8 !important; font-size: 0.88rem !important;
        margin: 4px 0 0 !important; font-weight: 400; line-height: 1.5;
    }
    .oa-header-badge {
        display: none !important;
    }

    /* ── KPI Cards (High Contrast & Elevation) ── */
    .oa-kpi-card {
        background: #FFFFFF; border-radius: 14px; padding: 20px 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative; overflow: hidden;
        display: flex; flex-direction: column; justify-content: space-between;
        height: 100%;
    }
    .oa-kpi-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0;
        height: 4px; background: var(--kpi-accent, #4F46E5);
    }
    .oa-kpi-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 10px 25px -4px rgba(15, 23, 42, 0.08);
        transform: translateY(-3px);
    }
    .oa-kpi-header {
        display: flex; align-items: center;
        justify-content: space-between; margin-bottom: 12px;
    }
    .oa-kpi-label { color: #64748B; font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
    .oa-kpi-icon-wrap {
        display: none !important;
    }
    .oa-kpi-value { font-size: 2.1rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; margin-bottom: 4px; }
    .oa-kpi-sub { font-size: 0.8rem; color: #64748B; font-weight: 500; line-height: 1.4; }

    /* ── Stepper ── */
    .oa-stepper {
        display: flex; align-items: center; background: #FFFFFF;
        border: 1px solid #E2E8F0; border-radius: 14px; padding: 15px 22px;
        margin-bottom: 22px; gap: 10px; overflow-x: auto;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .oa-step {
        display: flex; align-items: center; gap: 9px;
        font-size: 0.85rem; font-weight: 600; color: #94A3B8; white-space: nowrap; flex-shrink: 0;
    }
    .oa-step.active { color: #4F46E5; }
    .oa-step.done   { color: #059669; }
    .oa-step-circle {
        width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 700;
        background: #F1F5F9; color: #94A3B8; border: 2px solid #E2E8F0; flex-shrink: 0;
        transition: all 0.2s ease;
    }
    .oa-step.active .oa-step-circle {
        background: #4F46E5; color: #FFF; border-color: #4F46E5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.25);
    }
    .oa-step.done .oa-step-circle { background: #DCFCE7; color: #059669; border-color: #86EFAC; }
    .oa-step-line { flex: 1; height: 2px; background: #E2E8F0; min-width: 20px; border-radius: 2px; }
    .oa-step-line.done { background: #10B981; }

    /* ── Alert Banners (Rich & High Contrast) ── */
    .oa-alert {
        border-radius: 12px; padding: 14px 18px; font-size: 0.88rem; line-height: 1.55;
        display: flex; align-items: flex-start; gap: 12px;
        margin-bottom: 16px; border: 1.5px solid transparent;
    }
    .oa-alert-success { background: #F0FDF4; border-color: #86EFAC; color: #14532D; }
    .oa-alert-warning { background: #FFFBEB; border-color: #FDE68A; color: #78350F; }
    .oa-alert-info    { background: #EEF2FF; border-color: #C7D2FE; color: #1E1B4B; }
    .oa-alert-danger  { background: #FEF2F2; border-color: #FECACA; color: #7F1D1D; }
    .oa-alert-note    { background: #F8FAFC; border-color: #CBD5E1; color: #0F172A; }

    /* ── Section Cards ── */
    .oa-card {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 22px 24px; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03); margin-bottom: 18px;
    }
    .oa-card-title {
        font-size: 1.05rem; font-weight: 700; color: #0F172A;
        margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
        padding-bottom: 12px; border-bottom: 1px solid #F1F5F9;
    }

    /* ── Empty State ── */
    .oa-empty {
        text-align: center; padding: 52px 24px; background: #FFFFFF;
        border: 2px dashed #CBD5E1; border-radius: 16px; margin: 14px 0;
    }
    .oa-empty-icon { font-size: 3.2rem; margin-bottom: 12px; display: block; opacity: 0.7; }
    .oa-empty-title { font-size: 1.15rem; font-weight: 700; color: #0F172A; margin-bottom: 6px; }
    .oa-empty-desc { font-size: 0.88rem; color: #64748B; max-width: 440px; margin: 0 auto; line-height: 1.6; }

    /* ── Total Bar ── */
    .oa-total-bar {
        background: linear-gradient(135deg, #EEF2FF 0%, #F0FDF4 100%);
        border: 1.5px solid #C7D2FE; border-radius: 12px; padding: 16px 22px;
        margin-top: 14px; display: flex; align-items: center;
        justify-content: space-between; flex-wrap: wrap; gap: 12px;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.06);
    }
    .oa-total-label { font-size: 0.88rem; color: #334155; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .oa-total-value { font-size: 1.55rem; font-weight: 800; color: #4F46E5; letter-spacing: -0.02em; }

    /* ── Order Summary Box (Stage 3 confirm) ── */
    .oa-summary-box {
        background: #FFFFFF; border: 1.5px solid #CBD5E1;
        border-radius: 12px; padding: 18px 22px; margin: 14px 0;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
    }
    .oa-summary-row {
        display: flex; align-items: baseline; justify-content: space-between;
        padding: 7px 0; border-bottom: 1px solid #F1F5F9;
        font-size: 0.88rem; color: #1E293B;
    }
    .oa-summary-row:last-child { border-bottom: none; }
    .oa-summary-label { font-weight: 600; color: #64748B; min-width: 140px; }

    /* ── Status Distribution Bar ── */
    .oa-status-bar {
        display: flex; border-radius: 8px; overflow: hidden;
        height: 10px; margin-bottom: 10px; gap: 2px;
    }
    .oa-status-seg { height: 100%; transition: width 0.4s ease; }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        background: #FFFFFF !important; border: 1.5px solid #E2E8F0 !important;
        border-radius: 12px !important; overflow: hidden !important;
        margin-bottom: 12px !important; box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stExpander"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
    }
    [data-testid="stExpander"] summary {
        font-weight: 600 !important; font-size: 0.88rem !important;
        padding: 14px 18px !important; color: #0F172A !important;
    }
    [data-testid="stExpander"] > div > div {
        padding: 10px 20px 20px !important;
        background: #FAFAFA !important;
        border-top: 1px solid #F1F5F9 !important;
    }

    /* ── Dataframes & Data Editors ── */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border: 1.5px solid #CBD5E1 !important; border-radius: 12px !important;
        overflow: hidden !important; background: #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: #FFFFFF !important; border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important; padding: 14px 18px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.8rem !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #0F172A !important; font-weight: 800 !important; }

    /* ── Native Messages / Alerts ── */
    [data-testid="stSuccess"] {
        border-radius: 10px !important; border: 1.5px solid #86EFAC !important;
        background: #F0FDF4 !important; color: #14532D !important;
    }
    [data-testid="stWarning"] {
        border-radius: 10px !important; border: 1.5px solid #FDE68A !important;
        background: #FFFBEB !important; color: #78350F !important;
    }
    [data-testid="stError"] {
        border-radius: 10px !important; border: 1.5px solid #FECACA !important;
        background: #FEF2F2 !important; color: #7F1D1D !important;
    }
    [data-testid="stInfo"] {
        border-radius: 10px !important; border: 1.5px solid #C7D2FE !important;
        background: #EEF2FF !important; color: #1E1B4B !important;
    }

    /* ── Pulse animation ── */
    @keyframes pulseDot {
        0%   { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
        70%  { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .oa-pulse-live { animation: pulseDot 2s infinite; }

    /* ── Char Counter ── */
    .oa-char-counter { font-size: 0.76rem; color: #64748B; text-align: right; margin-top: -6px; margin-bottom: 8px; font-weight: 500; }
    .oa-char-counter.warn { color: #D97706; font-weight: 700; }
    .oa-char-counter.error { color: #DC2626; font-weight: 700; }

    /* ── Intelligence & Memory Cards ── */
    .oa-intel-box {
        background: #FFFFFF; border: 1.5px solid #E2E8F0;
        border-radius: 14px; padding: 18px 22px; margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .oa-score-pill {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 9999px; font-weight: 700;
        font-size: 0.8rem; letter-spacing: 0.02em;
    }
    .oa-badge-telugu {
        background: #FFF7ED; color: #C2410C; border: 1px solid #FFEDD5;
        border-radius: 9999px; padding: 2px 10px; font-size: 0.72rem; font-weight: 700;
        display: inline-flex; align-items: center; gap: 5px;
    }
    .oa-badge-memory {
        background: #EFF6FF; color: #1D4ED8; border: 1px solid #DBEAFE;
        border-radius: 9999px; padding: 2px 10px; font-size: 0.72rem; font-weight: 700;
        display: inline-flex; align-items: center; gap: 5px;
    }
    .oa-badge-stock {
        background: #FEF2F2; color: #B91C1C; border: 1px solid #FEE2E2;
        border-radius: 9999px; padding: 2px 10px; font-size: 0.72rem; font-weight: 700;
        display: inline-flex; align-items: center; gap: 5px;
    }

    /* ── Responsive & Aesthetic Mobile Architecture ── */
    @media (max-width: 1024px) {
        .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 1.25rem !important;
        }
        .oa-header {
            padding: 18px 22px !important;
        }
        .oa-header-title {
            font-size: 1.45rem !important;
        }
        .oa-kpi-value {
            font-size: 1.75rem !important;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 0.85rem !important;
            padding-bottom: 2.5rem !important;
        }

        /* ── Header Mobile ── */
        .oa-header {
            padding: 15px 16px !important;
            border-radius: 12px !important;
            margin-bottom: 16px !important;
        }
        .oa-header-inner {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 10px !important;
        }
        .oa-header-left {
            gap: 12px !important;
            width: 100% !important;
        }
        .oa-header-icon {
            width: 42px !important;
            height: 42px !important;
            font-size: 1.35rem !important;
            border-radius: 10px !important;
        }
        .oa-header-title {
            font-size: 1.22rem !important;
            line-height: 1.25 !important;
        }
        .oa-header-sub {
            font-size: 0.78rem !important;
            line-height: 1.4 !important;
        }
        .oa-header-badge {
            font-size: 0.72rem !important;
            padding: 3px 10px !important;
            align-self: flex-start !important;
        }

        /* ── Stepper Mobile: Clean Horizontal Scroll ── */
        .oa-stepper {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            overflow-x: auto !important;
            padding: 10px 14px !important;
            gap: 6px !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: none !important;
        }
        .oa-stepper::-webkit-scrollbar {
            display: none;
        }
        .oa-step span {
            font-size: 0.76rem !important;
        }
        .oa-step-circle {
            width: 22px !important;
            height: 22px !important;
            font-size: 0.7rem !important;
        }
        .oa-step-line {
            min-width: 12px !important;
            height: 2px !important;
        }

        /* ── Streamlit Horizontal Block Auto-Wrapping ── */
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 10px !important;
        }

        /* General mobile column full-width */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* 2-column actions stay 2 across on mobile */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(2):last-child) > div[data-testid="column"] {
            min-width: calc(50% - 6px) !important;
            flex: 1 1 calc(50% - 6px) !important;
        }

        /* 4-column KPI cards become a neat 2x2 grid */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(4):last-child) > div[data-testid="column"] {
            min-width: calc(50% - 6px) !important;
            flex: 1 1 calc(50% - 6px) !important;
        }

        /* KPI Card inner mobile scaling */
        .oa-kpi-card {
            padding: 14px 16px !important;
            border-radius: 12px !important;
        }
        .oa-kpi-header {
            margin-bottom: 8px !important;
        }
        .oa-kpi-label {
            font-size: 0.68rem !important;
        }
        .oa-kpi-value {
            font-size: 1.35rem !important;
            margin-bottom: 2px !important;
        }
        .oa-kpi-sub {
            font-size: 0.72rem !important;
        }
        .oa-kpi-icon-wrap {
            width: 32px !important;
            height: 32px !important;
            font-size: 1rem !important;
            border-radius: 8px !important;
        }

        /* ── Total Bar Mobile ── */
        .oa-total-bar {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 10px !important;
            padding: 14px 16px !important;
        }
        .oa-total-label {
            font-size: 0.82rem !important;
        }
        .oa-total-value {
            font-size: 1.35rem !important;
        }

        /* ── Tabs on Mobile ── */
        div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
            flex-direction: column !important;
            gap: 4px !important;
            padding: 4px !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"],
        div[data-testid="stTabs"] button[role="tab"] {
            width: 100% !important;
            text-align: left !important;
            padding: 9px 14px !important;
            font-size: 0.82rem !important;
        }
    }

    /* Keep inline stock adjustment controls horizontal on all screens */
    div[data-testid="stHorizontalBlock"]:has(button[key*="sub5_"]) {
        flex-wrap: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="sub5_"]) > div[data-testid="column"] {
        min-width: auto !important;
        flex: 1 1 auto !important;
    }

    @media (max-width: 480px) {
        .oa-kpi-value {
            font-size: 1.25rem !important;
        }
        /* On very narrow phones (<480px), KPI cards stack 1 per row for maximum readability */
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(4):last-child) > div[data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
    </style>
    """

