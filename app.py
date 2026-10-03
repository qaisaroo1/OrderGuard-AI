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

# Custom Styling for polished hackathon presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F3F4F6;
        border-radius: 8px;
        padding: 12px;
        border-left: 5px solid #3B82F6;
    }
    .critical-badge {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .high-badge {
        background-color: #FFEDD5;
        color: #9A3412;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .medium-badge {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .low-badge {
        background-color: #DCFCE7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .quote-box {
        font-style: italic;
        background: #F8FAFC;
        border-left: 3px solid #64748B;
        padding: 8px 12px;
        margin-top: 6px;
        font-size: 0.9rem;
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
        help="Enter your Google Gemini API key or use mock mode."
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

col_btn, col_date = st.columns([1, 1])
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
        with st.spinner("Multi-agent analysis running: Isolating obligations, conditions, deadlines & consequences..."):
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
    
    # Case Overview Banner
    st.markdown(f"### 📋 {meta.case_title}")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Case / Petition No.", meta.case_number)
    with col_m2:
        st.metric("Court / Bench", meta.court_name)
    with col_m3:
        st.metric("Total Obligations", action_map.total_obligations)
    with col_m4:
        st.metric("Critical / High Risks", action_map.critical_risks_count)

    # Executive Summary Card
    with st.expander("📌 Case Summary & Presiding Bench", expanded=True):
        st.write(f"**Presiding Bench:** {meta.judge_names or 'Not specified'}")
        st.write(f"**Order Date:** {meta.order_date}")
        st.info(f"**Summary:** {meta.brief_summary}")

    st.markdown("---")

    # Perspective & Filter Switcher
    st.markdown("### 🎯 Legal Action Map & Risk Matrix")
    
    parties = list(set([a.obligated_party for a in action_map.actions]))
    filter_col1, filter_col2 = st.columns([1, 1])
    
    with filter_col1:
        selected_party = st.selectbox(
            "👤 Filter by Obligated Party (Perspective Switcher):",
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
            # Determine badge styling
            badge_class = {
                "CRITICAL": "critical-badge",
                "HIGH": "high-badge",
                "MEDIUM": "medium-badge",
                "LOW": "low-badge"
            }.get(item.risk_severity, "low-badge")

            # Calculate estimated deadline date if relative
            calculated_date_str = ""
            if item.days_offset is not None:
                calc_date = trigger_base_date + timedelta(days=item.days_offset)
                calculated_date_str = f" ➔ **Target Date:** `{calc_date.strftime('%d %b %Y')}`"

            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 14px; margin-bottom: 12px; background: #FFFFFF;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 1.05rem; color: #1F2937;">{item.id}: {item.obligated_party}</span>
                        <span class="{badge_class}">{item.risk_severity} RISK</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 1.05rem; color: #111827;">
                        <strong>Action:</strong> {item.action_required}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_det1, col_det2 = st.columns([1.2, 1])
                with col_det1:
                    st.write(f"⏱️ **Deadline:** `{item.deadline_text}` ({item.deadline_type}){calculated_date_str}")
                    if item.condition:
                        st.warning(f"⚠️ **Prerequisite Condition:** {item.condition}")
                    if item.target_party:
                        st.caption(f"🎯 **Beneficiary / Target:** {item.target_party}")

                with col_det2:
                    st.error(f"🚨 **Fallout if Missed:** {item.consequence_risk}")

                # Grounding & Citation
                with st.expander(f"🔍 Citation Proof (Page {item.source_citation.page_number})"):
                    st.markdown(f"**Reference:** {item.source_citation.paragraph_reference or 'Paragraph'}")
                    st.markdown(f'<div class="quote-box">"{item.source_citation.verbatim_quote}"</div>', unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

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
