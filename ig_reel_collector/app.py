import os
import sys
import time
import tempfile
import pandas as pd
import streamlit as st
from typing import List

# Add current dir to head of path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ReelProcessedRecord
from ig_extractor import InstagramExtractor, extract_shortcode
from analyzer import ReelAnalyzer
from exporter import records_to_excel_bytes, records_to_csv_bytes

# Page configuration
st.set_page_config(
    page_title="Instagram Reel Intelligence Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.6rem;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E293B;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-success { background-color: #DEF7EC; color: #03543F; }
    .badge-warning { background-color: #FEF08A; color: #854D0E; }
    .badge-info { background-color: #E0E7FF; color: #3730A3; }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper to read / save .env keys
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def load_saved_env():
    keys = {}
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        keys[k.strip()] = v.strip().strip("\"'")
        except Exception:
            pass
    return keys

def save_env_keys(keys_dict):
    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for k, v in keys_dict.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        st.sidebar.error(f"Could not save .env: {e}")

saved_keys = load_saved_env()

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### ⚙️ Agent Configuration")

    # API Keys
    st.markdown("#### 🔑 API Keys (Free Tier)")
    gemini_key_input = st.text_input(
        "Google Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY") or saved_keys.get("GEMINI_API_KEY", ""),
        type="password",
        help="Free Developer Tier: 15 requests/min. Powers transcription, hook extraction, and categorization."
    )
    with st.expander("ℹ️ How to get free Gemini key"):
        st.markdown("""
        1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. Sign in with any Google account.
        3. Click **Create API Key** (Free Tier requires no credit card).
        """)

    apify_token_input = st.text_input(
        "Apify Token (Optional)",
        value=os.environ.get("APIFY_TOKEN") or saved_keys.get("APIFY_TOKEN", ""),
        type="password",
        help="Free Developer Tier: $5/month recurring credit (~1,000 reels/mo with live views/likes/comments)."
    )
    with st.expander("ℹ️ How to get free Apify token"):
        st.markdown("""
        1. Visit [Apify Console](https://console.apify.com/account/integrations).
        2. Create a free account ($5 free credit renewed monthly).
        3. Copy your Personal API Token.
        """)

    session_id_input = st.text_input(
        "Instagram Session ID (Optional - For Live Views)",
        value=os.environ.get("INSTAGRAM_SESSION_ID") or saved_keys.get("INSTAGRAM_SESSION_ID", ""),
        type="password",
        help="Optional: Paste your browser sessionid cookie to unlock exact live play counts directly from Instagram."
    )
    with st.expander("ℹ️ How to get sessionid from Chrome"):
        st.markdown("""
        1. Open **instagram.com** in Chrome or Edge.
        2. Press **F12** -> Go to **Application** (or Storage) tab.
        3. Expand **Cookies** -> Click `https://www.instagram.com`.
        4. Find the cookie named **`sessionid`**, copy its value and paste it here.
        """)

    save_keys = st.checkbox("Save keys locally to .env", value=True)
    if save_keys and (gemini_key_input or apify_token_input or session_id_input):
        new_keys = {}
        if gemini_key_input: new_keys["GEMINI_API_KEY"] = gemini_key_input
        if apify_token_input: new_keys["APIFY_TOKEN"] = apify_token_input
        if session_id_input: new_keys["INSTAGRAM_SESSION_ID"] = session_id_input
        save_env_keys(new_keys)

    st.markdown("---")
    st.markdown("#### 🎯 Execution Mode")
    engine_choice = st.selectbox(
        "Extraction Engine",
        options=["auto", "direct", "apify", "demo"],
        format_func=lambda x: {
            "auto": "⚡ Auto (Apify if token set, else GraphQL Direct)",
            "direct": "🔍 GraphQL Direct (Fast & Downloads Real Video)",
            "apify": "🌐 Apify Actor (Managed Scraper)",
            "demo": "🧪 Demo Mode (Instant test, zero API keys needed)"
        }.get(x, x)
    )

    model_choice = st.selectbox(
        "Gemini AI Model",
        options=["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.8-flash", "gemini-3.6-flash"],
        index=0,
        help="gemini-flash-lite-latest provides fast multimodal transcription with high free-tier quotas and reliable audio processing."
    )

    batch_delay = st.slider("Delay between reels (sec)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)

    st.markdown("---")
    st.markdown("Built for **Honasa Consumer** • TDC Analytics")

# --- MAIN CONTENT ---
st.markdown('<div class="main-title">📈 Instagram Reel Intelligence Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Batch process Instagram Reels to extract live public engagement metrics, transcripts, hooks, genre classifications, concept styles, and creator demographics.</div>', unsafe_allow_html=True)

# Sample URLs button helper
SAMPLE_URLS = """https://www.instagram.com/reel/C8q_sample1/
https://www.instagram.com/reel/DLUO_sample2/
https://www.instagram.com/reel/C-X-sample3/
https://www.instagram.com/reel/DPj_sample4/"""

col_in_header, col_sample_btn, col_clear_btn = st.columns([4, 1.3, 1])
with col_in_header:
    st.markdown("##### 📋 Input Instagram Reel URLs")
with col_sample_btn:
    if st.button("✨ Load Sample URLs", use_container_width=True):
        st.session_state["url_input_text"] = SAMPLE_URLS
with col_clear_btn:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state["url_input_text"] = ""

initial_text = st.session_state.get("url_input_text", "")
urls_input = st.text_area(
    "Paste Reel URLs (one per line):",
    value=initial_text,
    height=140,
    placeholder="https://www.instagram.com/reel/C-...\nhttps://www.instagram.com/reel/D-...",
    label_visibility="collapsed"
)

# Parse URLs
raw_url_list = [u.strip() for u in urls_input.splitlines() if u.strip() and "instagram.com" in u]

col_run, col_count = st.columns([1.5, 4])
with col_run:
    run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True, disabled=(len(raw_url_list) == 0))
with col_count:
    if raw_url_list:
        st.caption(f"Ready to process **{len(raw_url_list)}** valid Reel URL(s).")
    else:
        st.caption("Paste one or more Instagram Reel links above to begin.")

# Session state to store processed records
if "processed_records" not in st.session_state:
    st.session_state["processed_records"] = []

# --- EXECUTION FLOW ---
if run_button and raw_url_list:
    records: List[ReelProcessedRecord] = []
    total_urls = len(raw_url_list)

    progress_bar = st.progress(0)
    status_text = st.empty()

    extractor = InstagramExtractor(apify_token=apify_token_input, session_id=session_id_input)
    analyzer = ReelAnalyzer(api_key=gemini_key_input, model_name=model_choice)

    with tempfile.TemporaryDirectory() as temp_dir:
        for idx, url in enumerate(raw_url_list):
            current_progress = (idx) / total_urls
            progress_bar.progress(current_progress)
            status_text.markdown(f"**Step 1/3**: Extracting public metrics for `[{idx+1}/{total_urls}]` `{url}`...")

            # 1. Extract raw metrics
            def progress_cb(current, total, msg):
                status_text.markdown(f"**Extractor**: {msg}")

            raw_batch = extractor.extract_batch([url], engine_preference=engine_choice, progress_callback=progress_cb)
            raw_metric = raw_batch[0] if raw_batch else None

            if not raw_metric:
                continue

            # 2. Attempt media download if not in demo mode
            media_path = None
            if engine_choice != "demo":
                status_text.markdown(f"**Step 2/3**: Downloading Reel audio/video for transcript extraction...")
                media_path = extractor.download_video_or_audio(raw_metric, temp_dir)

            # 3. Analyze content with Gemini
            status_text.markdown(f"**Step 3/3**: Running Gemini Multimodal AI content analysis...")
            analysis = analyzer.analyze(raw_metric, media_path)

            # 4. Construct unified record
            record = ReelProcessedRecord(
                reel_url=raw_metric.reel_url,
                channel_standard_name=raw_metric.creator_username,
                creator_ig_link=raw_metric.creator_profile_url or f"https://www.instagram.com/{raw_metric.creator_username}/",
                current_views=raw_metric.current_views,
                likes=raw_metric.likes,
                comments=raw_metric.comments,
                language=analysis.language,
                whole_script=analysis.whole_script,
                hook=analysis.hook,
                genre_category_subcat=analysis.genre_category_subcat,
                concept_bucketing=analysis.concept_bucketing,
                gender=analysis.gender,
                caption=raw_metric.caption,
                duration_seconds=raw_metric.duration_seconds,
                status=raw_metric.status
            )
            records.append(record)

            # Rate limit delay
            if idx < total_urls - 1 and batch_delay > 0:
                time.sleep(batch_delay)

        progress_bar.progress(1.0)
        status_text.success(f" Successfully processed {len(records)} Reel(s)!")

    st.session_state["processed_records"] = records

# --- DISPLAY RESULTS & METRICS ---
if st.session_state["processed_records"]:
    records = st.session_state["processed_records"]
    df = pd.DataFrame([r.to_dict() for r in records])

    st.markdown("---")
    st.markdown("### 📊 Dataset Overview")

    # High-level summary KPI cards
    total_views = sum(r.current_views for r in records)
    total_likes = sum(r.likes for r in records)
    total_comments = sum(r.comments for r in records)
    top_concept = df["Concept Bucketing"].mode()[0] if not df["Concept Bucketing"].empty else "N/A"
    top_lang = df["Language"].mode()[0] if not df["Language"].empty else "N/A"

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(records):,}</div>
            <div class="metric-label">Reels Processed</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_views:,}</div>
            <div class="metric-label">Total Views</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_likes:,}</div>
            <div class="metric-label">Total Likes</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{top_concept}</div>
            <div class="metric-label">Top Concept</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{top_lang}</div>
            <div class="metric-label">Dominant Language</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs: Data Table & Detailed Inspector
    tab_table, tab_inspect = st.tabs(["📑 Data Spreadsheet", "🔍 Deep Dive Inspector"])

    with tab_table:
        # Reorder columns to match user spec exactly
        ordered_cols = [
            "Channel Standard Name",
            "Creator IG Link",
            "Current Views",
            "Likes",
            "Comments",
            "Language",
            "Hook",
            "Genre / Category / Sub Cat",
            "Concept Bucketing",
            "Gender",
            "Whole script extraction",
            "Reel URL",
        ]
        display_df = df[[c for c in ordered_cols if c in df.columns]]

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Creator IG Link": st.column_config.LinkColumn("Creator IG Link"),
                "Reel URL": st.column_config.LinkColumn("Reel URL"),
                "Current Views": st.column_config.NumberColumn(format="%d"),
                "Likes": st.column_config.NumberColumn(format="%d"),
                "Comments": st.column_config.NumberColumn(format="%d"),
            }
        )

        # Download Buttons
        d_col1, d_col2, _ = st.columns([1.5, 1.5, 4])
        with d_col1:
            excel_data = records_to_excel_bytes(records)
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data,
                file_name=f"instagram_reels_intelligence_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with d_col2:
            csv_data = records_to_csv_bytes(records)
            st.download_button(
                label="📥 Download CSV (.csv)",
                data=csv_data,
                file_name=f"instagram_reels_intelligence_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab_inspect:
        st.markdown("#### Select a Reel to inspect full transcript and AI classifications:")
        selected_idx = st.selectbox(
            "Select Reel:",
            options=range(len(records)),
            format_func=lambda i: f"Reel #{i+1} - @{records[i].channel_standard_name} ({records[i].current_views:,} views)"
        )
        rec = records[selected_idx]

        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown(f"**Creator Profile:** [{rec.channel_standard_name}]({rec.creator_ig_link})")
            st.markdown(f"**Reel Link:** [Open on Instagram]({rec.reel_url})")
            st.metric("Current Views", f"{rec.current_views:,}")
            st.metric("Likes", f"{rec.likes:,}")
            st.metric("Comments", f"{rec.comments:,}")
            st.info(f"**Gender Inferred:** {rec.gender}")
            st.info(f"**Language:** {rec.language}")
            st.info(f"**Concept:** {rec.concept_bucketing}")
            st.info(f"**Category:** {rec.genre_category_subcat}")

        with c2:
            st.markdown("##### 🪝 Hook (Opening Statement)")
            st.code(rec.hook or "No hook extracted", language="markdown")

            st.markdown("##### 📜 Whole Script Extraction (Audio Transcript)")
            st.text_area(
                "Full Transcript",
                value=rec.whole_script or "No script available",
                height=220,
                disabled=True
            )

            if rec.caption:
                with st.expander("Original Caption"):
                    st.write(rec.caption)
