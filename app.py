"""
OrderGuard AI: Autonomous Legal Action Mapping & Execution Engine
Interactive Streamlit Dashboard.
"""
import streamlit as st
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from core.schemas import LegalActionMap
from core.extractor import DocumentExtractor
from core.pipeline import LegalExtractionPipeline
from samples.generate_sample_order import SAMPLE_ORDER_TEXT

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="OrderGuard AI | Autonomous Legal Action Mapping",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling - Dark & Light Mode Adaptive with Modern Glassmorphism
st.markdown("""
<style>
    /* Header typography */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        opacity: 0.85;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    
    /* Metadata and Stats Cards */
    .meta-box {
        background: rgba(125, 125, 125, 0.08);
        border: 1px solid rgba(125, 125, 125, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        height: 100%;
    }
    .stat-card {
        background: rgba(125, 125, 125, 0.08);
        border: 1px solid rgba(125, 125, 125, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .stat-card.risk-critical {
        border: 1px solid rgba(239, 68, 68, 0.4);
        background: rgba(239, 68, 68, 0.08);
    }
    .stat-number {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 6px;
    }
    .stat-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        opacity: 0.8;
    }
    
    /* Action item cards */
    .action-card {
        background: rgba(125, 125, 125, 0.06);
        border: 1px solid rgba(125, 125, 125, 0.2);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 14px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .action-card:hover {
        border-color: rgba(59, 130, 246, 0.5);
    }
    
    /* Risk Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.5);
    }
    .badge-high {
        background-color: rgba(249, 115, 22, 0.2);
        color: #FB923C;
        border: 1px solid rgba(249, 115, 22, 0.5);
    }
    .badge-medium {
        background-color: rgba(234, 179, 8, 0.2);
        color: #FACC15;
        border: 1px solid rgba(234, 179, 8, 0.5);
    }
    .badge-low {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.5);
    }
    
    .quote-box {
        font-style: italic;
        background: rgba(125, 125, 125, 0.05);
        border-left: 3px solid #3B82F6;
        padding: 10px 14px;
        margin-top: 8px;
        border-radius: 0 6px 6px 0;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .party-title {
        font-size: 1.15rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/scales--v1.png", width=64)
    st.title("OrderGuard AI")
    st.caption("v1.0.0 (MVP) • Legal Execution Engine")
    st.markdown("---")
    
    st.subheader("⚙️ AI Configuration")
    user_api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Enter your Google Gemini API key or use demo fallback mode."
    )
    
    model_choice = st.selectbox(
        "Extraction Model",
        ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    
    use_mock_fallback = st.checkbox("Allow Demo / Fallback Mode", value=True)

    st.markdown("---")
    st.subheader("⚡ Quick Hackathon Demo")
    if st.button("📄 Load Sample Court Order", use_container_width=True):
        st.session_state["raw_text_input"] = SAMPLE_ORDER_TEXT
        st.session_state["uploaded_file_name"] = "Orient_Textiles_vs_Sindh_CP2849.txt"
        st.session_state["action_map"] = None
        st.success("Sample order loaded into workspace!")

    st.markdown("---")
    st.info("💡 **Hackathon Tip:** Switch between **Petitioner** and **Respondent** views in the dashboard to see party-specific risk.")


# --- MAIN HEADER ---
st.markdown('<div class="main-header">⚖️ OrderGuard AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous Legal Action Mapping & Execution Engine — Transform complex court judgments into an active, zero-failure compliance roadmap.</div>', unsafe_allow_html=True)


# --- INPUT SECTION ---
col_upload, col_input_text = st.columns([1, 1])

with col_upload:
    st.markdown("##### 📁 Upload Court Judgment (PDF)")
    uploaded_file = st.file_uploader("Upload scanned or digital court judgment", type=["pdf", "txt"])
    if uploaded_file:
        st.session_state["uploaded_file_name"] = uploaded_file.name

with col_input_text:
    st.markdown("##### 📝 Or Paste / View Order Text")
    raw_text = st.text_area(
        "Judgment Text Preview",
        value=st.session_state.get("raw_text_input", ""),
        height=140,
        placeholder="Paste legal judgment text here or upload a file above..."
    )
    if raw_text:
        st.session_state["raw_text_input"] = raw_text

col_btn, col_date = st.columns([1.2, 1])
with col_btn:
    analyze_btn = st.button("🚀 Parse & Map Legal Actions", type="primary", use_container_width=True)

with col_date:
    trigger_base_date = st.date_input(
        "🗓️ Service / Announcement Date (for timeline calculation)",
        value=datetime.today()
    )


# --- PROCESSING PIPELINE ---
if analyze_btn:
    document_text = ""
    
    if uploaded_file is not None:
        with st.spinner("Extracting text and page boundaries from document..."):
            if uploaded_file.name.lower().endswith(".pdf"):
                extracted = DocumentExtractor.extract_from_pdf(uploaded_file.getvalue())
                document_text = extracted["full_text_with_pages"]
            else:
                document_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    elif st.session_state.get("raw_text_input", "").strip():
        document_text = st.session_state["raw_text_input"]
    else:
        st.warning("Please upload a court order PDF or paste the judgment text to continue.")

    if document_text:
        with st.spinner("Analyzing judgment: Isolating obligations, conditions, deadlines & consequences..."):
            try:
                pipeline = LegalExtractionPipeline(api_key=user_api_key, model_name=model_choice)
                action_map = pipeline.analyze_order(document_text, use_mock_fallback=use_mock_fallback)
                st.session_state["action_map"] = action_map
                st.success("Legal Action Map successfully generated!")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")


# --- DISPLAY RESULTS ---
if st.session_state.get("action_map"):
    action_map: LegalActionMap = st.session_state["action_map"]
    meta = action_map.metadata

    st.markdown("---")
    
    # Case Overview Header
    st.markdown(f"### 📋 {meta.case_title}")
    
    # IMPROVED: Non-truncated, responsive metadata & stat cards
    col_meta, col_stat1, col_stat2 = st.columns([2.2, 1, 1])
    
    with col_meta:
        st.markdown(f"""
        <div class="meta-box">
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.8px; opacity: 0.75; font-weight: 600;">Case & Jurisdiction Details</div>
            <div style="font-size: 1.25rem; font-weight: 700; margin: 4px 0;">{meta.case_number}</div>
            <div style="font-size: 0.98rem; opacity: 0.9; margin-bottom: 6px;">🏛️ <strong>{meta.court_name}</strong></div>
            <div style="font-size: 0.88rem; opacity: 0.75;">📅 Order Announced: <strong>{meta.order_date}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_stat1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #3B82F6;">{action_map.total_obligations}</div>
            <div class="stat-label">Total Obligations</div>
            <div style="font-size: 0.75rem; opacity: 0.65; margin-top: 4px;">Directives Tracked</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_stat2:
        st.markdown(f"""
        <div class="stat-card risk-critical">
            <div class="stat-number" style="color: #EF4444;">{action_map.critical_risks_count}</div>
            <div class="stat-label" style="color: #EF4444;">Critical / High Risks</div>
            <div style="font-size: 0.75rem; opacity: 0.75; margin-top: 4px;">Severe Legal Fallout</div>
        </div>
        """, unsafe_allow_html=True)

    # Executive Summary Card
    with st.expander("📌 Presiding Bench & Executive Case Summary", expanded=True):
        st.markdown(f"**Presiding Bench:** {meta.judge_names or 'Presiding Bench not specified'}")
        st.info(f"**Dispute Summary:** {meta.brief_summary}")

    st.markdown("---")

    # Perspective & Filter Switcher
    st.markdown("### 🎯 Legal Action Map & Execution Matrix")
    
    parties = list(set([a.obligated_party for a in action_map.actions]))
    filter_col1, filter_col2 = st.columns([1, 1])
    
    with filter_col1:
        selected_party = st.selectbox(
            "👤 Perspective Switcher (Filter by Obligated Party):",
            ["All Parties"] + parties
        )
    with filter_col2:
        selected_severity = st.selectbox(
            "⚠️ Filter by Risk Level:",
            ["All Severities", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
        )

    # Filter actions
    filtered_actions = action_map.actions
    if selected_party != "All Parties":
        filtered_actions = [a for a in filtered_actions if a.obligated_party == selected_party]
    if selected_severity != "All Severities":
        filtered_actions = [a for a in filtered_actions if a.risk_severity == selected_severity]

    # Action Items List
    if not filtered_actions:
        st.info("No action items match the selected filter criteria.")
    else:
        for item in filtered_actions:
            # Determine badge styling class
            badge_class = {
                "CRITICAL": "badge-critical",
                "HIGH": "badge-high",
                "MEDIUM": "badge-medium",
                "LOW": "badge-low"
            }.get(item.risk_severity, "badge-low")

            # Calculate estimated deadline date if relative
            calculated_date_str = ""
            if item.days_offset is not None:
                calc_date = trigger_base_date + timedelta(days=item.days_offset)
                calculated_date_str = f" ➔ **Target Date:** `{calc_date.strftime('%d %b %Y')}`"

            # Render action card
            st.markdown(f"""
            <div class="action-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="party-title">{item.id}: {item.obligated_party}</span>
                    <span class="badge {badge_class}">{item.risk_severity} RISK</span>
                </div>
                <div style="font-size: 1.05rem; line-height: 1.5;">
                    <strong>Directive:</strong> {item.action_required}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_det1, col_det2 = st.columns([1.2, 1])
            with col_det1:
                st.markdown(f"⏱️ **Deadline:** `{item.deadline_text}` ({item.deadline_type}){calculated_date_str}")
                if item.condition:
                    st.warning(f"⚠️ **Prerequisite Condition:** {item.condition}")
                if item.target_party:
                    st.caption(f"🎯 **Beneficiary / Target:** {item.target_party}")

            with col_det2:
                st.error(f"🚨 **Fallout if Missed:** {item.consequence_risk}")

            # Grounding & Citation
            with st.expander(f"🔍 Citation Proof (Page {item.source_citation.page_number})"):
                st.markdown(f"**Reference:** {item.source_citation.paragraph_reference or 'Paragraph Reference'}")
                st.markdown(f'<div class="quote-box">"{item.source_citation.verbatim_quote}"</div>', unsafe_allow_html=True)

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --- EXPORT & INTEGRATION SECTION ---
    st.markdown("---")
    st.markdown("### 📤 Export & Developer Integration")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        # Download JSON for Razeen and other developers
        json_data = action_map.model_dump_json(indent=2)
        st.download_button(
            label="💾 Download Structured JSON (Data Contract for UI/Team)",
            data=json_data,
            file_name=f"legal_action_map_{meta.case_number.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True
        )

    with col_exp2:
        # Generate simple ICS calendar file
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//OrderGuard AI//Court Compliance Calendar//EN"
        ]
        for act in action_map.actions:
            offset = act.days_offset if act.days_offset is not None else 1
            due = trigger_base_date + timedelta(days=offset)
            due_str = due.strftime("%Y%m%d")
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:[OrderGuard] {act.id}: {act.action_required[:40]}...",
                f"DESCRIPTION:Party: {act.obligated_party}\\nRisk: {act.consequence_risk}",
                f"DTSTART:{due_str}",
                f"DTEND:{due_str}",
                "STATUS:CONFIRMED",
                "END:VEVENT"
            ])
        ics_lines.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics_lines)

        st.download_button(
            label="📅 Export to Calendar (.ics)",
            data=ics_content,
            file_name="court_obligations.ics",
            mime="text/calendar",
            use_container_width=True
        )
