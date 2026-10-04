
"""
OrderGuard AI: Autonomous Legal Action Mapping & Execution Engine
Clean Streamlit Dashboard UI.
"""

import os
from datetime import datetime, timedelta
from html import escape

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

from core.schemas import LegalActionMap
from core.api_client import API_BASE_URL, submit_analysis
from samples.generate_sample_order import SAMPLE_ORDER_TEXT

# -------------------------------------------------------------------
# DEADLINE DISPLAY HELPERS
# -------------------------------------------------------------------
def calculate_deadline_date(base_date, action):
    """Calculate a safe date for the frontend countdown."""
    if action.days_offset is not None:
        return base_date + timedelta(days=action.days_offset)

    deadline_text = str(action.deadline_text or "")

    # Absolute ISO date: 2026-11-04
    import re
    match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", deadline_text)
    if match:
        try:
            from datetime import date
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass

    # Common court-order date: 04.11.2026 / 04-11-2026 / 04/11/2026
    match = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b", deadline_text)
    if match:
        try:
            from datetime import date
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        except ValueError:
            pass

    return None


def render_deadline_countdown(action, base_date):
    """Render a live browser-local countdown to the target date's end."""
    due_date = calculate_deadline_date(base_date, action)

    if due_date is None:
        st.markdown(
            """
            <div class="deadline-panel">
                <div style="color:#10213F;font-size:.78rem;font-weight:850;text-transform:uppercase;letter-spacing:.7px;">
                    Deadline countdown
                </div>
                <div style="color:#64748B;font-size:.75rem;margin-top:.35rem;">
                    The order contains a deadline, but no exact machine-readable date was available for a live countdown.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    due_iso = due_date.strftime("%Y-%m-%d")
    base_iso = base_date.strftime("%Y-%m-%d")

    countdown_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin:0; padding:0; background:transparent; font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif; }}
        .panel {{ background:#F8FAFC; border:1px solid #E2E8F0; border-radius:13px; padding:13px 15px 12px; color:#10213F; }}
        .head {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:6px; }}
        .title {{ font-size:12px; font-weight:850; text-transform:uppercase; letter-spacing:.7px; }}
        .zone {{ color:#64748B; font-size:11px; white-space:nowrap; }}
        .time {{ color:#1D4ED8; font-size:23px; font-weight:850; line-height:1.1; letter-spacing:.2px; }}
        .date {{ color:#64748B; font-size:11px; margin-top:3px; }}
        .track {{ height:7px; background:#E2E8F0; border-radius:999px; overflow:hidden; margin-top:10px; }}
        .fill {{ height:100%; width:0%; background:#1D4ED8; border-radius:999px; transition:width .5s linear; }}
        .panel.urgent {{ background:#FFF7ED; border-color:#FED7AA; }}
        .panel.urgent .time {{ color:#D97706; }} .panel.urgent .fill {{ background:#D97706; }}
        .panel.overdue {{ background:#FEF2F2; border-color:#FECACA; }}
        .panel.overdue .time {{ color:#DC2626; }} .panel.overdue .fill {{ background:#DC2626; }}
      </style>
    </head>
    <body>
      <div id="panel" class="panel">
        <div class="head"><div id="title" class="title">Time remaining</div><div id="zone" class="zone">Local time</div></div>
        <div id="time" class="time">Calculating...</div>
        <div id="date" class="date"></div>
        <div class="track"><div id="fill" class="fill"></div></div>
      </div>
      <script>
        const due = new Date("{due_iso}T23:59:59");
        const start = new Date("{base_iso}T00:00:00");
        const panel = document.getElementById("panel");
        const title = document.getElementById("title");
        const timeEl = document.getElementById("time");
        const dateEl = document.getElementById("date");
        const fill = document.getElementById("fill");
        document.getElementById("zone").textContent = Intl.DateTimeFormat().resolvedOptions().timeZone || "Local timezone";
        function update() {{
          const now = new Date();
          const remaining = due.getTime() - now.getTime();
          const total = due.getTime() - start.getTime();
          let progress = total > 0 ? ((now.getTime()-start.getTime())/total)*100 : 0;
          progress = Math.max(0, Math.min(100, progress));
          fill.style.width = progress + "%";
          dateEl.textContent = "Target: " + new Intl.DateTimeFormat(undefined, {{weekday:"short",year:"numeric",month:"short",day:"numeric"}}).format(due) + " • End of local day";
          if (remaining <= 0) {{
            panel.className="panel overdue"; title.textContent="Deadline reached"; timeEl.textContent="00d 00h 00m 00s"; return;
          }}
          const sec=Math.floor(remaining/1000), d=Math.floor(sec/86400), h=Math.floor((sec%86400)/3600), m=Math.floor((sec%3600)/60), ss=sec%60;
          const pad=n=>String(n).padStart(2,"0");
          timeEl.textContent=pad(d)+"d "+pad(h)+"h "+pad(m)+"m "+pad(ss)+"s";
          if (remaining <= 86400000) {{ panel.className="panel urgent"; title.textContent="Less than 24 hours"; }}
          else {{ panel.className="panel"; title.textContent="Time remaining"; }}
        }}
        update(); setInterval(update,1000);
      </script>
    </body>
    </html>
    """
    components.html(countdown_html, height=116, scrolling=False)


# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="OrderGuard AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------------------
if "raw_text_input" not in st.session_state:
    st.session_state["raw_text_input"] = ""

if "uploaded_file_name" not in st.session_state:
    st.session_state["uploaded_file_name"] = ""

if "action_map" not in st.session_state:
    st.session_state["action_map"] = None

if "extraction_warnings" not in st.session_state:
    st.session_state["extraction_warnings"] = []

if "extraction_pages" not in st.session_state:
    st.session_state["extraction_pages"] = []

if "agent_traces" not in st.session_state:
    st.session_state["agent_traces"] = []

# -------------------------------------------------------------------
# DESIGN SYSTEM
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---------- Global ---------- */
    :root {
        --og-blue: #1D4ED8;
        --og-blue-dark: #173B8F;
        --og-blue-soft: #EFF6FF;
        --og-blue-line: #BFDBFE;
        --og-ink: #10213F;
        --og-muted: #64748B;
        --og-border: #DCE6F2;
        --og-bg: #F7FAFE;
        --og-white: #FFFFFF;
        --og-danger: #DC2626;
        --og-danger-soft: #FEF2F2;
        --og-warning: #D97706;
        --og-warning-soft: #FFFBEB;
        --og-success: #15803D;
        --og-success-soft: #F0FDF4;
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                     BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--og-bg) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 250, 254, 0.92) !important;
    }

    [data-testid="stMain"] {
        background: var(--og-bg) !important;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 2.2rem !important;
        padding-bottom: 4rem !important;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid var(--og-border);
    }

    [data-testid="stSidebar"] * {
        color: var(--og-ink);
    }

    [data-testid="stSidebar"] .stButton > button {
        background: var(--og-blue) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--og-blue) !important;
        border-radius: 10px !important;
        min-height: 42px;
        font-weight: 700;
    }

    /* ---------- Hero ---------- */
    .og-hero {
        text-align: center;
        padding: 0.5rem 0 2rem 0;
    }

    .og-logo {
        width: 82px;
        height: 82px;
        margin: 0 auto 1rem auto;
        border-radius: 24px;
        background: linear-gradient(145deg, #2563EB, #1E40AF);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 14px 35px rgba(29, 78, 216, 0.22);
        font-size: 2.8rem;
    }

    .og-title {
        color: var(--og-ink) !important;
        font-size: 2.55rem;
        line-height: 1.1;
        font-weight: 800;
        letter-spacing: -0.8px;
        margin: 0;
    }

    .og-subtitle {
        color: var(--og-muted);
        font-size: 1rem;
        max-width: 760px;
        margin: 0.7rem auto 0 auto;
        line-height: 1.65;
    }

    .og-eyebrow {
        color: var(--og-blue);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 1.3px;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    /* ---------- Section headings ---------- */
    .section-title {
        color: var(--og-ink);
        font-size: 1.12rem;
        font-weight: 800;
        margin: 0 0 0.2rem 0;
    }

    .section-caption {
        color: var(--og-muted);
        font-size: 0.86rem;
        margin-bottom: 1rem;
    }

    /* ---------- Input panel ---------- */
    .input-panel {
        background: #FFFFFF;
        border: 1px solid var(--og-border);
        border-radius: 18px;
        padding: 1.3rem 1.35rem 1.1rem 1.35rem;
        box-shadow: 0 8px 30px rgba(16, 33, 63, 0.05);
    }

    .input-label {
        color: var(--og-ink);
        font-weight: 750;
        font-size: 0.94rem;
        margin-bottom: 0.3rem;
    }

    .input-help {
        color: var(--og-muted);
        font-size: 0.78rem;
        margin-bottom: 0.65rem;
    }

    /* Native Streamlit bordered containers are used for the input cards. */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid var(--og-border) !important;
        border-radius: 18px !important;
        box-shadow: 0 8px 30px rgba(16, 33, 63, 0.05);
        padding: 0.15rem 0.2rem;
    }

    /* ---------- Streamlit controls ---------- */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput input {
        background: #FFFFFF !important;
        color: var(--og-ink) !important;
        border-color: var(--og-border) !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--og-blue-soft) !important;
        border: 1.5px dashed var(--og-blue-line) !important;
        border-radius: 14px !important;
    }

    [data-testid="stFileUploaderDropzone"] * {
        color: var(--og-ink) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: var(--og-blue) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--og-blue) !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background: var(--og-blue-dark) !important;
        border-color: var(--og-blue-dark) !important;
    }

    [data-testid="stFileUploaderDropzone"] button * {
        color: #FFFFFF !important;
    }

    /* Primary action button */
    .stButton > button[kind="primary"] {
        background: var(--og-blue) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--og-blue) !important;
        border-radius: 11px !important;
        min-height: 48px;
        font-size: 0.95rem;
        font-weight: 800;
        box-shadow: 0 8px 18px rgba(29, 78, 216, 0.18);
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--og-blue-dark) !important;
        border-color: var(--og-blue-dark) !important;
    }

    .secondary-action .stButton > button {
        background: #FFFFFF !important;
        color: var(--og-ink) !important;
        border: 1px solid var(--og-border) !important;
        border-radius: 11px !important;
        min-height: 48px;
        font-weight: 700;
    }

    /* ---------- Stats ---------- */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid var(--og-border);
        border-radius: 16px;
        padding: 1.15rem 1.2rem;
        min-height: 118px;
        box-shadow: 0 6px 24px rgba(16, 33, 63, 0.045);
    }

    .stat-label {
        color: var(--og-muted);
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.85px;
    }

    .stat-number {
        color: var(--og-ink);
        font-size: 2rem;
        font-weight: 850;
        line-height: 1;
        margin: 0.55rem 0 0.25rem 0;
    }

    .stat-note {
        color: var(--og-muted);
        font-size: 0.76rem;
    }

    .stat-danger {
        border-top: 3px solid var(--og-danger);
    }

    .stat-blue {
        border-top: 3px solid var(--og-blue);
    }

    .stat-green {
        border-top: 3px solid var(--og-success);
    }

    /* ---------- Case summary ---------- */
    .case-card {
        background: #FFFFFF;
        border: 1px solid var(--og-border);
        border-radius: 16px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 6px 24px rgba(16, 33, 63, 0.04);
    }

    .case-kicker {
        color: var(--og-blue);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 850;
    }

    .case-title {
        color: var(--og-ink);
        font-size: 1.25rem;
        line-height: 1.35;
        font-weight: 800;
        margin: 0.25rem 0 0.6rem 0;
    }

    .case-meta {
        color: var(--og-muted);
        font-size: 0.83rem;
        line-height: 1.75;
    }

    /* ---------- Action cards ---------- */
    .action-card {
        background: #FFFFFF;
        border: 1px solid var(--og-border);
        border-radius: 16px;
        padding: 1.2rem 1.25rem;
        margin: 0.55rem 0 0.9rem 0;
        box-shadow: 0 6px 22px rgba(16, 33, 63, 0.04);
    }

    .action-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.75rem;
    }

    .action-id {
        color: var(--og-muted);
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.8px;
    }

    .party {
        color: var(--og-ink);
        font-size: 0.96rem;
        font-weight: 800;
        margin-top: 0.15rem;
    }

    .risk-badge {
        display: inline-block;
        padding: 0.34rem 0.65rem;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: 0.55px;
        white-space: nowrap;
    }

    .risk-critical,
    .risk-high {
        background: var(--og-danger-soft);
        color: var(--og-danger);
        border: 1px solid #FECACA;
    }

    .risk-medium {
        background: var(--og-warning-soft);
        color: var(--og-warning);
        border: 1px solid #FDE68A;
    }

    .risk-low {
        background: var(--og-success-soft);
        color: var(--og-success);
        border: 1px solid #BBF7D0;
    }

    .directive {
        color: var(--og-ink);
        font-size: 1rem;
        font-weight: 650;
        line-height: 1.6;
    }

    .detail-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.7rem;
        margin-top: 1rem;
    }

    .detail-box {
        background: #F8FAFC;
        border: 1px solid #E7EDF5;
        border-radius: 11px;
        padding: 0.8rem 0.9rem;
    }

    .detail-label {
        color: var(--og-muted);
        font-size: 0.68rem;
        font-weight: 850;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-bottom: 0.3rem;
    }

    .detail-value {
        color: var(--og-ink);
        font-size: 0.84rem;
        line-height: 1.45;
        font-weight: 600;
    }

    .consequence-box {
        background: var(--og-danger-soft);
        border: 1px solid #FECACA;
        border-radius: 11px;
        padding: 0.8rem 0.9rem;
        margin-top: 0.7rem;
    }

    .consequence-box .detail-value {
        color: #991B1B;
    }

    /* ---------- Deadline countdown ---------- */
    .deadline-panel {
        margin-top: 0.85rem;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 13px;
        padding: 0.9rem 1rem;
    }

    /* ---------- Evidence ---------- */
    .evidence-box {
        background: var(--og-blue-soft);
        border-left: 3px solid var(--og-blue);
        border-radius: 0 10px 10px 0;
        padding: 0.85rem 1rem;
        color: var(--og-ink);
        line-height: 1.65;
        font-size: 0.86rem;
    }

    /* ---------- Footer ---------- */
    .footer {
        text-align: center;
        color: #94A3B8;
        font-size: 0.75rem;
        padding: 2rem 0 0.5rem 0;
    }

    @media (max-width: 800px) {
        .og-title { font-size: 2rem; }
        .detail-grid { grid-template-columns: 1fr; }
        .action-top { align-items: flex-start; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# SIDEBAR — KEEP FUNCTIONAL SETTINGS, REMOVE CLUTTER
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding:0.7rem 0 1.1rem 0;">
            <div style="font-size:2.2rem;">⚖️</div>
            <div style="font-size:1.25rem;font-weight:850;color:#10213F;">OrderGuard AI</div>
            <div style="font-size:0.75rem;color:#64748B;">Legal Action Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("AI Settings", expanded=False):
        if os.getenv("GEMINI_API_KEY"):
            st.success("Gemini API key is configured on the backend.")
        else:
            st.warning("Set GEMINI_API_KEY in the backend environment to use Gemini.")
        st.caption(f"Backend: {API_BASE_URL}")
        model_choice = st.selectbox(
            "Extraction Model",
            ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.7-flash"],
            index=0,
        )
        use_mock_fallback = st.checkbox(
            "Allow Demo / Fallback Mode",
            value=False,
        )

    st.markdown("#### Quick Start")
    if st.button("Load Sample Court Order", use_container_width=True):
        st.session_state["raw_text_input"] = SAMPLE_ORDER_TEXT
        st.session_state["uploaded_file_name"] = (
            "Orient_Textiles_vs_Sindh_CP2849.txt"
        )
        st.session_state["action_map"] = None
        st.rerun()

    st.markdown(
        """
        <div style="
            margin-top:1.1rem;
            padding:0.85rem;
            background:#EFF6FF;
            border:1px solid #BFDBFE;
            border-radius:12px;
            color:#1E3A8A;
            font-size:0.78rem;
            line-height:1.5;">
            <strong>Demo mode</strong><br>
            Load the sample order to preview the complete legal action dashboard.
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------------------------
# HERO
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="og-hero">
        <div class="og-logo">⚖️</div>
        <div class="og-eyebrow">LEGAL ACTION INTELLIGENCE</div>
        <h1 class="og-title">OrderGuard AI</h1>
        <div class="og-subtitle">
            Turn complex court judgments into clear obligations, deadlines,
            risks and evidence-backed actions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# INPUT WORKSPACE
# -------------------------------------------------------------------
st.markdown('<div class="section-title">Analyze a Court Judgment</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">Upload a judgment or paste its text. OrderGuard will extract obligations, deadlines and risks.</div>',
    unsafe_allow_html=True,
)

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.markdown('<div class="input-label">Upload document</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="input-help">PDF or TXT • Digital or scanned court judgment</div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Court judgment",
            type=["pdf", "txt"],
            label_visibility="collapsed",
            max_upload_size=20,
        )
        if uploaded_file:
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.markdown(
                f'<div class="input-help">Selected: <strong>{escape(uploaded_file.name)}</strong></div>',
                unsafe_allow_html=True,
            )

with right:
    with st.container(border=True):
        st.markdown('<div class="input-label">Paste judgment text</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="input-help">Use this if you do not have a PDF/TXT file</div>',
            unsafe_allow_html=True,
        )
        raw_text = st.text_area(
            "Judgment text",
            value=st.session_state.get("raw_text_input", ""),
            height=154,
            placeholder="Paste the relevant court judgment here...",
            label_visibility="collapsed",
        )
        if raw_text:
            st.session_state["raw_text_input"] = raw_text

st.write("")

# Analysis controls: compact, balanced row. No unsupported 'analysis mode' selector is added.
date_col, action_col = st.columns([1, 1], gap="large")

with date_col:
    trigger_base_date = st.date_input(
        "Service / Announcement Date",
        value=datetime.today(),
        help="Used to calculate relative deadlines.",
    )

with action_col:
    st.markdown('<div style="height:1.78rem;"></div>', unsafe_allow_html=True)
    analyze_btn = st.button(
        "Analyze Judgment →",
        type="primary",
        use_container_width=True,
    )

# -------------------------------------------------------------------
# PROCESSING PIPELINE — ORIGINAL LOGIC PRESERVED
# -------------------------------------------------------------------
if analyze_btn:
    st.session_state["action_map"] = None
    st.session_state["extraction_warnings"] = []
    st.session_state["extraction_pages"] = []
    st.session_state["agent_traces"] = []

    if uploaded_file is not None:
        source = {
            "file_name": uploaded_file.name,
            "file_bytes": uploaded_file.getvalue(),
        }
    elif st.session_state.get("raw_text_input", "").strip():
        source = {"raw_text": st.session_state["raw_text_input"]}
    else:
        source = None
        st.warning("Please upload a court order PDF/TXT or paste the judgment text first.")

    if source is not None:
        try:
            with st.spinner("Sending document to the local API for OCR and Gemini analysis..."):
                action_map = submit_analysis(
                    **source,
                    model_name=model_choice,
                    use_mock_fallback=use_mock_fallback,
                )
            st.session_state["action_map"] = action_map
            st.session_state["extraction_warnings"] = action_map.extraction_warnings
            st.session_state["extraction_pages"] = action_map.extraction_pages
            st.session_state["agent_traces"] = action_map.agent_traces
            if action_map.analysis_warnings:
                for warning in action_map.analysis_warnings:
                    st.warning(warning)
            elif action_map.actions:
                st.success("Legal Action Map returned by the FastAPI and Gemini pipeline.")
            else:
                st.info("Analysis completed, but no actionable obligations were identified.")
        except (RuntimeError, ValueError) as error:
            st.error(str(error))

if analyze_btn:
    for warning in st.session_state["extraction_warnings"]:
        st.warning(warning)

    review_pages = [
        page
        for page in st.session_state["extraction_pages"]
        if (
            page.raw_text
            or page.urdu_ocr_text
            or page.method == "ocr"
            or (
                st.session_state.get("action_map") is not None
                and not st.session_state["action_map"].actions
            )
        )
    ]
    if review_pages:
        with st.expander(
            "Extracted text and OCR details for manual review",
            expanded=bool(
                st.session_state.get("action_map") is not None
                and not st.session_state["action_map"].actions
            ),
        ):
            for page in review_pages:
                confidence = (
                    f"{page.ocr_confidence:.0f}%"
                    if page.ocr_confidence is not None
                    else "not available"
                )
                st.markdown(
                    f"**Page {page.page_number}: {page.method} extraction, "
                    f"{confidence} confidence, {page.char_count} characters**"
                )
                if page.text_preview:
                    suffix = " (preview)" if page.char_count > len(page.text_preview) else ""
                    st.text_area(
                        f"Extracted text{suffix}",
                        value=page.text_preview,
                        key=f"extracted-text-preview-{page.page_number}",
                    )
                if page.raw_text:
                    st.text_area(
                        "Original PDF text",
                        value=page.raw_text,
                        key=f"raw-extraction-page-{page.page_number}",
                    )
                if page.urdu_ocr_text:
                    st.text_area(
                        "Unverified Urdu OCR attempt",
                        value=page.urdu_ocr_text,
                        key=f"urdu-ocr-page-{page.page_number}",
                    )

# -------------------------------------------------------------------
# RESULTS DASHBOARD
# -------------------------------------------------------------------
if st.session_state.get("action_map"):
    action_map: LegalActionMap = st.session_state["action_map"]
    meta = action_map.metadata

    st.markdown("---")

    # Case header
    case_header_html = f"""<div class="case-card">
<div class="case-kicker">ACTIVE CASE</div>
<div class="case-title">{escape(str(meta.case_title))}</div>
<div class="case-meta">
<strong>{escape(str(meta.case_number))}</strong>
&nbsp; • &nbsp;
{escape(str(meta.court_name))}
&nbsp; • &nbsp;
Order date: {escape(str(meta.order_date))}
</div>
</div>"""
    st.markdown(case_header_html, unsafe_allow_html=True)

    st.write("")

    if action_map.actions:
        upcoming_count = sum(
            1
            for a in action_map.actions
            if a.days_offset is not None and a.days_offset >= 0
        )
        k1, k2, k3 = st.columns(3, gap="medium")

        with k1:
            st.markdown(
                f"""<div class="stat-card stat-blue">
<div class="stat-label">Future Obligations</div>
<div class="stat-number">{action_map.total_obligations}</div>
<div class="stat-note">Obligations identified</div>
</div>""",
                unsafe_allow_html=True,
            )

        with k2:
            st.markdown(
                f"""<div class="stat-card stat-danger">
<div class="stat-label">Critical / High Risk</div>
<div class="stat-number">{action_map.critical_risks_count}</div>
<div class="stat-note">Require close attention</div>
</div>""",
                unsafe_allow_html=True,
            )

        with k3:
            st.markdown(
                f"""<div class="stat-card stat-green">
<div class="stat-label">Tracked Deadlines</div>
<div class="stat-number">{upcoming_count}</div>
<div class="stat-note">Relative deadlines detected</div>
</div>""",
                unsafe_allow_html=True,
            )

        st.write("")

    # Summary
    summary_left, summary_right = st.columns([1, 2], gap="large")

    with summary_left:
        st.markdown(
            f"""<div class="case-card">
<div class="case-kicker">COURT INFORMATION</div>
<div style="margin-top:.6rem;color:#10213F;font-weight:750;">Presiding Bench</div>
<div class="case-meta">{escape(str(meta.judge_names or "Not specified"))}</div>
<div style="margin-top:.9rem;color:#10213F;font-weight:750;">Order Date</div>
<div class="case-meta">{escape(str(meta.order_date))}</div>
</div>""",
            unsafe_allow_html=True,
        )

    with summary_right:
        st.markdown(
            f"""<div class="case-card">
<div class="case-kicker">CASE SUMMARY</div>
<div style="color:#334155;line-height:1.65;font-size:.9rem;margin-top:.55rem;">{escape(str(meta.brief_summary))}</div>
</div>""",
            unsafe_allow_html=True,
        )

    st.write("")
    if action_map.actions:
        st.markdown(
            '<div class="section-title">Legal Action Map</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-caption">Review obligations by responsible party and risk level.</div>',
            unsafe_allow_html=True,
        )
        parties = sorted(
            list(set(a.obligated_party for a in action_map.actions))
        )
        filter_col1, filter_col2 = st.columns(2, gap="medium")

        with filter_col1:
            selected_party = st.selectbox(
                "Responsible party",
                ["All Parties"] + parties,
            )

        with filter_col2:
            selected_severity = st.selectbox(
                "Risk level",
                ["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
            )

        filtered_actions = action_map.actions
        if selected_party != "All Parties":
            filtered_actions = [
                a for a in filtered_actions if a.obligated_party == selected_party
            ]
        if selected_severity != "All Severities":
            filtered_actions = [
                a for a in filtered_actions if a.risk_severity == selected_severity
            ]

        st.caption(f"{len(filtered_actions)} action(s) shown")
        if not filtered_actions:
            st.info("No action items match the selected filters.")
    else:
        st.markdown(
            '<div class="section-title">Court Outcome</div>',
            unsafe_allow_html=True,
        )
        st.info(
            "Analysis completed. This judgment does not order a future task or "
            "deadline, so there are no obligation cards to show."
        )
        st.markdown(
            f"""<div class="case-card">
<div class="case-kicker">DECISION IN THIS JUDGMENT</div>
<div style="color:#334155;line-height:1.65;font-size:.95rem;margin-top:.55rem;">{escape(str(meta.brief_summary))}</div>
</div>""",
            unsafe_allow_html=True,
        )
        if st.session_state["extraction_pages"]:
            st.caption(
                "Extracted page text is expanded above for checking against the original."
            )

    # Action cards
    if action_map.actions and filtered_actions:
        for item in filtered_actions:
            severity = str(item.risk_severity).upper()
            risk_class = {
                "CRITICAL": "risk-critical",
                "HIGH": "risk-high",
                "MEDIUM": "risk-medium",
                "LOW": "risk-low",
            }.get(severity, "risk-low")

            calculated_date_str = ""
            if item.days_offset is not None:
                calc_date = trigger_base_date + timedelta(
                    days=item.days_offset
                )
                calculated_date_str = calc_date.strftime("%d %b %Y")

            condition_html = (
                f'<div class="detail-box"><div class="detail-label">Condition</div><div class="detail-value">{escape(str(item.condition))}</div></div>'
                if item.condition
                else ""
            )

            target_html = (
                f'<div class="detail-box"><div class="detail-label">Target / Beneficiary</div><div class="detail-value">{escape(str(item.target_party))}</div></div>'
                if item.target_party
                else ""
            )

            date_html = (
                f'<div class="detail-box"><div class="detail-label">Target Date</div><div class="detail-value">{escape(calculated_date_str)}</div></div>'
                if calculated_date_str
                else ""
            )

            action_card_html = f"""<div class="action-card">
<div class="action-top">
<div>
<div class="action-id">{escape(str(item.id))}</div>
<div class="party">{escape(str(item.obligated_party))}</div>
</div>
<span class="risk-badge {risk_class}">{escape(severity)} RISK</span>
</div>
<div class="directive">{escape(str(item.action_required))}</div>
<div class="detail-grid">
<div class="detail-box">
<div class="detail-label">Deadline</div>
<div class="detail-value">{escape(str(item.deadline_text))}{f" • {escape(str(item.deadline_type))}" if item.deadline_type else ""}</div>
</div>
{date_html}
{condition_html}
{target_html}
</div>
<div class="consequence-box">
<div class="detail-label">If missed</div>
<div class="detail-value">{escape(str(item.consequence_risk))}</div>
</div>
</div>"""
            st.markdown(action_card_html, unsafe_allow_html=True)

            # Live deadline countdown. Uses backend days_offset/deadline_text
            # and the viewer's browser-local timezone.
            render_deadline_countdown(item, trigger_base_date)

            # Evidence stays functional but is visually secondary.
            citation = item.source_citation
            with st.expander(
                f"View source evidence • Page {citation.page_number}"
            ):
                st.markdown(
                    f"**{escape(str(citation.paragraph_reference or 'Reference'))}**"
                )
                st.markdown(
                    f'<div class="evidence-box">“{escape(str(citation.verbatim_quote))}”</div>',
                    unsafe_allow_html=True,
                )

    # ----------------------------------------------------------------
    # MULTI-AGENT EXECUTION AUDIT LOG
    # ----------------------------------------------------------------
    if hasattr(action_map, "agent_traces") and action_map.agent_traces:
        with st.expander("🤖 Multi-Agent Execution Audit Log (Judge View)", expanded=False):
            st.markdown("##### Specialized Agent Pipeline Execution Trace")
            for trace in action_map.agent_traces:
                trace_html = f"""<div style="background: rgba(125, 125, 125, 0.05); border-left: 3px solid #1D4ED8; padding: 10px 14px; margin-bottom: 10px; border-radius: 4px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<strong style="color: #1D4ED8; font-size: 0.95rem;">{escape(str(trace.agent_name))}</strong>
<span style="color: #10B981; font-weight: 700; font-size: 0.8rem;">● {escape(str(trace.status))}</span>
</div>
<div style="font-size: 0.85rem; opacity: 0.75; margin: 2px 0;">{escape(str(trace.role))}</div>
<div style="font-size: 0.9rem; margin-top: 4px;">{escape(str(trace.findings_summary))}</div>
</div>"""
                st.markdown(trace_html, unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # EXPORTS — CLEAN, SECONDARY ACTIONS
    # ----------------------------------------------------------------
    st.markdown("---")
    st.markdown(
        '<div class="section-title">Export</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">Take the structured action map or deadlines with you.</div>',
        unsafe_allow_html=True,
    )

    export_left, export_right = st.columns(2, gap="medium")

    with export_left:
        json_data = action_map.model_dump_json(indent=2)
        st.download_button(
            label="Download Action Map (.json)",
            data=json_data,
            file_name=(
                f"legal_action_map_"
                f"{str(meta.case_number).replace(' ', '_')}.json"
            ),
            mime="application/json",
            use_container_width=True,
        )

    with export_right:
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//OrderGuard AI//Court Compliance Calendar//EN",
        ]

        for act in action_map.actions:
            offset = act.days_offset if act.days_offset is not None else 1
            due = trigger_base_date + timedelta(days=offset)
            due_str = due.strftime("%Y%m%d")

            ics_lines.extend(
                [
                    "BEGIN:VEVENT",
                    (
                        f"SUMMARY:[OrderGuard] {act.id}: "
                        f"{act.action_required[:40]}..."
                    ),
                    (
                        f"DESCRIPTION:Party: {act.obligated_party}\\n"
                        f"Risk: {act.consequence_risk}"
                    ),
                    f"DTSTART:{due_str}",
                    f"DTEND:{due_str}",
                    "STATUS:CONFIRMED",
                    "END:VEVENT",
                ]
            )

        ics_lines.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics_lines)

        st.download_button(
            label="Export Deadlines (.ics)",
            data=ics_content,
            file_name="court_obligations.ics",
            mime="text/calendar",
            use_container_width=True,
        )

st.markdown(
    """
    <div class="footer">
        OrderGuard AI • Legal Action Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)
