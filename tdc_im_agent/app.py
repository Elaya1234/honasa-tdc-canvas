import os
import sys
import time
import streamlit as st

# Add base directory to path so imports work cleanly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tdc_im_agent.config import APP_NAME, APP_VERSION, OUTPUT_DIR
from tdc_im_agent.orchestrator import TDCOrchestrator
from tdc_im_agent.collector_adapter import AuthState

st.set_page_config(
    page_title=f"{APP_NAME} v{APP_VERSION}",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling adhering to TDC Brand Palette
st.markdown("""
<style>
    .tdc-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.1rem;
    }
    .tdc-sub {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .found-card {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .rec-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    .metric-chip {
        display: inline-block;
        background: #E0E7FF;
        color: #3730A3;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .status-complete {
        background: #DCFCE7;
        color: #166534;
        font-weight: bold;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
    }
    .status-partial {
        background: #FEF9C3;
        color: #854D0E;
        font-weight: bold;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = TDCOrchestrator()
if "inspect_result" not in st.session_state:
    st.session_state.inspect_result = None
if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None
if "selected_sheet" not in st.session_state:
    st.session_state.selected_sheet = None
if "run_result" not in st.session_state:
    st.session_state.run_result = None

# Sidebar: Credentials & Engine Configuration
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    
    # Instagram Session State
    auth_state = st.session_state.orchestrator.collector_adapter.auth_state
    if auth_state == AuthState.CONNECTED:
        st.success("🟢 Instagram: Connected")
    elif auth_state == AuthState.EXPIRED:
        st.error("🔴 Instagram: Session Expired")
    else:
        st.info("⚪ Instagram: Not Configured (Public Mode)")

    with st.expander("🔑 Manage Credentials"):
        new_session_id = st.text_input("Instagram sessionid Cookie", type="password")
        if st.button("Update Instagram Session"):
            st.session_state.orchestrator.collector_adapter.update_session_id(new_session_id)
            st.success("Updated session credentials.")
            st.rerun()

        gemini_key = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
        if gemini_key:
            st.session_state.orchestrator.collector_adapter.gemini_api_key = gemini_key

    engine_pref = st.selectbox(
        "Extraction Engine",
        options=["auto", "direct", "apify", "demo"],
        index=0,
        format_func=lambda x: {
            "auto": "⚡ Auto (Direct GraphQL + Fallbacks)",
            "direct": "🔍 GraphQL Direct (High Performance)",
            "apify": "🌐 Apify Managed Scraper",
            "demo": "🧪 Demo Simulation Mode"
        }.get(x, x)
    )
    st.session_state.orchestrator.collector_adapter.engine_preference = engine_pref

    reprocess_opt = st.checkbox("Force Reprocess All (Bypass Cache)", value=False)
    st.markdown("---")
    st.caption(f"TDC Analytics • {APP_NAME} v{APP_VERSION}")

# Main App View
st.markdown(f'<div class="tdc-header">🔬 {APP_NAME}</div>', unsafe_allow_html=True)
st.markdown('<div class="tdc-sub">Production-grade AI-assisted analytics and reporting platform for The Derma Co Influencer Marketing campaigns.</div>', unsafe_allow_html=True)

# Step 1: File Upload / Selection
col_upload, col_sample = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload Influencer Marketing Excel Tracker (.xlsx)",
        type=["xlsx"],
        help="Upload any TDC IM monthly, quarterly, or yearly campaign tracker."
    )

with col_sample:
    st.markdown("##### 📁 Baseline Test Datasets")
    sept_path = os.path.join(BASE_DIR, "IM", "Sept'26 FW & SS.xlsx")
    if os.path.exists(sept_path):
        if st.button("Load Sept'26 FW & SS (Golden Set)", use_container_width=True):
            st.session_state.uploaded_file_path = sept_path
            st.session_state.selected_sheet = None
            with st.spinner("Analyzing workbook structure..."):
                st.session_state.inspect_result = st.session_state.orchestrator.inspect_and_recommend(sept_path)
            st.rerun()

if uploaded_file is not None and st.session_state.uploaded_file_path != uploaded_file.name:
    temp_save_path = os.path.join(OUTPUT_DIR, f"uploaded_{uploaded_file.name}")
    with open(temp_save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.uploaded_file_path = temp_save_path
    st.session_state.selected_sheet = None
    with st.spinner("Analyzing uploaded workbook..."):
        st.session_state.inspect_result = st.session_state.orchestrator.inspect_and_recommend(temp_save_path)

# Step 2: Show "I FOUND" & "RECOMMENDED" Cards
if st.session_state.inspect_result:
    res = st.session_state.inspect_result
    avail_sheets = res.get("available_campaign_sheets", [])

    # Multi-Sheet Campaign Selector
    if len(avail_sheets) > 1:
        st.markdown("---")
        st.markdown("#### 📑 Campaign Selection")
        
        all_option = {
            "sheet_name": "__ALL_CAMPAIGNS__",
            "display": "🌟 All Active Campaigns (Consolidated Full Year 2026)"
        }
        dropdown_items = [all_option] + avail_sheets
        current_sel = st.session_state.selected_sheet or res.get("selected_sheet")
        
        curr_idx = 0
        for i, it in enumerate(dropdown_items):
            if it["sheet_name"] == current_sel:
                curr_idx = i
                break
        
        col_sheet_sel, _ = st.columns([2, 1])
        with col_sheet_sel:
            new_selection = st.selectbox(
                "Select Campaign Period / Sheet to Analyze:",
                options=[it["sheet_name"] for it in dropdown_items],
                index=curr_idx,
                format_func=lambda s: next((it["display"] for it in dropdown_items if it["sheet_name"] == s), s),
                help="Switch between monthly campaign sheets or consolidate all months together."
            )
            if new_selection != current_sel:
                st.session_state.selected_sheet = new_selection
                with st.spinner("Loading selected campaign data..."):
                    st.session_state.inspect_result = st.session_state.orchestrator.inspect_and_recommend(
                        st.session_state.uploaded_file_path, sheet_name=new_selection
                    )
                st.rerun()

    st.markdown("---")
    col_found, col_rec = st.columns(2)

    with col_found:
        st.markdown(f"""
        <div class="found-card">
            <h4 style="margin-top:0; color:#166534;">📊 I FOUND:</h4>
            <p><strong>Reporting Period:</strong> {res['period_label']} ({res['period_type']})</p>
            <p><strong>Deliverables:</strong> {res['total_reels']} Reels identified</p>
            <p><strong>Active SKUs:</strong> {res['total_skus']} distinct products</p>
            <p><strong>Creator Partners:</strong> {res['total_creators']} creators</p>
            <p><strong>Cache Status:</strong> {res['cached_reels_available']} / {res['total_reels']} Reels cached</p>
        </div>
        """, unsafe_allow_html=True)

    with col_rec:
        st.markdown(f"""
        <div class="rec-card">
            <h4 style="margin-top:0; color:#1E3A8A;">🎯 RECOMMENDED ANALYSIS:</h4>
            <p><strong>Primary Structure:</strong> SKU-wise Analytical Sheets + Consolidated All SKUs</p>
            <p><strong>Dimensions:</strong> {' '.join([f'<span class=\"metric-chip\">{d}</span>' for d in res['recommended_dimensions']])}</p>
            <p><strong>Performance KPIs:</strong> {' '.join([f'<span class=\"metric-chip\">{m}</span>' for m in res['recommended_metrics']])}</p>
            <p><strong>Statistical Relationships:</strong> Spend vs Views, Spend vs Engagement</p>
        </div>
        """, unsafe_allow_html=True)

    # Action Buttons
    col_btn1, col_btn2, _ = st.columns([2, 1.5, 3])

    with col_btn1:
        start_clicked = st.button("🚀 START RECOMMENDED ANALYSIS", type="primary", use_container_width=True)

    with col_btn2:
        customize_expander = st.expander("🛠️ Customize Output")

    if customize_expander:
        with customize_expander:
            st.selectbox("Select Organization", ["SKU-wise + Consolidated", "Consolidated Only", "Creator-wise"])
            st.multiselect("Select Dimensions to Compare", ["Language", "Gender", "Content Bucket", "Content Category", "Creator", "SKU"], default=["Language", "Gender", "Content Bucket", "Content Category"])

    # Execution Progress
    if start_clicked and st.session_state.uploaded_file_path:
        target_sheet = st.session_state.selected_sheet or res.get("selected_sheet")
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        
        def ui_progress_callback(curr: int, total: int, msg: str, row):
            pct = curr / total if total > 0 else 1.0
            progress_bar.progress(pct)
            status_text.markdown(f"**Processing Reel {curr}/{total}:** {msg}")

        with st.spinner("Processing campaign analysis..."):
            run_out = st.session_state.orchestrator.execute_analysis(
                file_path=st.session_state.uploaded_file_path,
                sheet_name=target_sheet,
                reprocess_all=reprocess_opt,
                progress_callback=ui_progress_callback
            )
            st.session_state.run_result = run_out

        progress_bar.progress(1.0)
        status_text.empty()
        st.rerun()

# Step 3: Display Final Completion & Validation Report
if st.session_state.run_result:
    r = st.session_state.run_result
    st.markdown("---")
    st.markdown("### 📋 Final Analysis & QA Report")

    # Status Pill
    if r["completion_status"] == "COMPLETE":
        st.markdown('<span class="status-complete">✅ Status: COMPLETE (100% Quality Assurance Passed)</span>', unsafe_allow_html=True)
    elif r["completion_status"] == "PARTIAL":
        st.markdown('<span class="status-partial">⚠️ Status: PARTIAL (Useful Report Produced; Audio/Speech Nuances Flagged)</span>', unsafe_allow_html=True)
    else:
        st.error("❌ Status: FAILED")

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Total Reels", r["total_reels"])
    col_m2.metric("Speech Transcribed", r["verified_count"])
    col_m3.metric("Instrumental / No Speech", r["no_speech_count"])
    col_m4.metric("Caption Only", r["caption_only_count"])
    col_m5.metric("Blended CPV", f"₹{r['avg_cpv']:.2f}")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown(f"""
        - **Reporting Period:** {r['period']}
        - **Total Campaign Spend:** ₹{r['total_spend']:,.0f}
        - **Total Collab Views:** {r['total_views']:,}
        - **QA Workbook Integrity:** {r['qa_status']}
        - **Numerical Reconciliation:** {r['reconciliation_status']}
        """)

    with col_q2:
        if r["discrepancy_reasons"]:
            st.markdown("**Auditing Notes:**")
            for reason in r["discrepancy_reasons"]:
                st.caption(f"• {reason}")

    # Download Button for the Generated Excel
    if os.path.exists(r["output_path"]):
        with open(r["output_path"], "rb") as f:
            excel_bytes = f.read()

        st.download_button(
            label=f"📥 Download {r['output_file']}",
            data=excel_bytes,
            file_name=r["output_file"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
