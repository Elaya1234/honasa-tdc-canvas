import streamlit as st
import os
import re
import io
import zipfile
import subprocess
import glob
from PIL import Image
import pdp_engine
import importlib
try:
    importlib.reload(pdp_engine)
except Exception:
    pass

st.set_page_config(
    page_title="Product Data & Media Downloader",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Theme Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .platform-pill {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .pill-d2c { background-color: #E0E7FF; color: #3730A3; }
    .pill-amazon { background-color: #FEF3C7; color: #92400E; }
    .pill-flipkart { background-color: #DBEAFE; color: #1E40AF; }
    .pill-nykaa { background-color: #FCE7F3; color: #9D174D; }
    .pill-blinkit { background-color: #FEF08A; color: #854D0E; }
</style>
""", unsafe_allow_html=True)

DEFAULT_SAVE_DIR = r"c:\Users\elaya.n\Documents\HONASA TDC\PDP_Research_Board"

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-bag.png", width=60)
    st.title("Product Data & Media Downloader")
    
    st.markdown("### 📥 Media Download Options")
    dl_images = st.checkbox("📸 Product Gallery & A+ Images", value=True)
    dl_videos = st.checkbox("🎥 Product Videos (.mp4)", value=True)
    
    st.markdown("---")
    st.markdown("### 📁 Save Location")
    save_dir = st.text_input("Destination Folder", value=DEFAULT_SAVE_DIR)
    
    if not os.path.exists(save_dir):
        try: os.makedirs(save_dir, exist_ok=True)
        except Exception: pass
        
    if st.button("📂 Open Research Folder in Explorer", use_container_width=True):
        if os.path.exists(save_dir):
            subprocess.Popen(f'explorer "{save_dir}"')
            st.toast("Opened research folder in Windows Explorer!", icon="📂")

# ----------------- MAIN HEADER -----------------
st.markdown('<div class="main-header">🛍️ Product Data & Media Downloader</div>', unsafe_allow_html=True)
st.markdown("""
<div class="sub-header">
    Scrapes exact verbatim Product Detail Page (PDP) data, tables, bullet points, specifications, high-resolution pictures, and videos from Amazon, The Derma Co, Minimalist, Flipkart, Nykaa, and any e-commerce platform.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div>
    <span class="platform-pill pill-amazon">Amazon.in</span>
    <span class="platform-pill pill-d2c">The Derma Co / Minimalist / D2C</span>
    <span class="platform-pill pill-flipkart">Flipkart</span>
    <span class="platform-pill pill-nykaa">Nykaa</span>
    <span class="platform-pill pill-blinkit">Blinkit</span>
    <span class="platform-pill pill-d2c">Universal Platforms</span>
</div>
<br/>
""", unsafe_allow_html=True)

tab_batch, tab_single, tab_board = st.tabs(["🚀 Multi-URL Batch Downloader", "🔍 Single Product Quick Fetch", "📂 Saved Research Board"])

# ----------------- TAB 1: BATCH / MULTI-URL -----------------
with tab_batch:
    st.subheader("Paste Multiple Product Links")
    urls_input = st.text_area(
        "Enter URLs (one per line):", 
        height=140,
        placeholder="https://www.amazon.in/dp/B0CJ4NSV1Q\nhttps://thedermaco.com/products/1-salicylic-acid-foaming-daily-face-wash...\nhttps://beminimalist.co/products/multi-vitamin-spf-50\nhttps://www.flipkart.com/..."
    )

    raw_found = re.findall(r'https?://[^\s,"\'<>]+', urls_input)
    seen = set()
    detected_urls = []
    for u in raw_found:
        u = u.strip()
        if u and u not in seen:
            seen.add(u)
            detected_urls.append(u)

    if detected_urls:
        st.markdown(f"**Detected {len(detected_urls)} Product Link(s).** Select which products to download:")
        
        selected_urls = []
        for idx, u in enumerate(detected_urls):
            is_checked = st.checkbox(f"`{u}`", value=True, key=f"batch_url_{idx}")
            if is_checked:
                selected_urls.append(u)

        st.markdown("<br/>", unsafe_allow_html=True)
        col_btn, _ = st.columns([2, 3])
        with col_btn:
            run_batch = st.button("⚡ Download Selected Products", type="primary", use_container_width=True)

        if run_batch:
            if not selected_urls:
                st.warning("Please select at least one product checkbox above.")
            else:
                overall_progress = st.progress(0.0)
                status_text = st.empty()
                results = []
                all_zip_buffers = []

                for i, u in enumerate(selected_urls, start=1):
                    status_text.info(f"⏳ Processing ({i}/{len(selected_urls)}): `{u[:75]}...`")
                    try:
                        pdp = pdp_engine.scrape_pdp(u)
                        pkg = pdp_engine.save_pdp_package(
                            pdp, 
                            include_images=dl_images, 
                            include_videos=dl_videos, 
                            base_dir=save_dir
                        )
                        results.append((u, "Success", len(pkg["downloaded_files"]), len(pkg["downloaded_videos"]), pkg["folder"], pkg))
                        all_zip_buffers.append((pdp_engine.sanitize_filename(pdp['title']), pkg["zip_bytes"]))
                    except Exception as e:
                        results.append((u, f"Failed: {str(e)}", 0, 0, "", None))
                    overall_progress.progress(i / len(selected_urls))

                status_text.success(f"🎉 Completed! Processed {len(selected_urls)} products.")
                st.balloons()

                # Master Zip if multiple products
                if all_zip_buffers:
                    master_zip = io.BytesIO()
                    with zipfile.ZipFile(master_zip, "w", zipfile.ZIP_DEFLATED) as mz:
                        for title, zb in all_zip_buffers:
                            mz.writestr(f"{title}.zip", zb)
                    master_zip.seek(0)
                    
                    st.download_button(
                        label="📥 Download ALL Products as Master ZIP (1-Click)",
                        data=master_zip.getvalue(),
                        file_name="All_Downloaded_PDP_Packages.zip",
                        mime="application/zip",
                        type="primary"
                    )

                st.markdown("### 📊 Downloaded Products Summary")
                for u, status, img_count, vid_count, folder, pkg in results:
                    if status == "Success":
                        with st.expander(f"✅ {pkg['title']} ({img_count} images, {vid_count} videos)", expanded=True):
                            st.write(f"📁 **Saved Local Folder:** `{folder}`")
                            st.write(f"🔗 **Product URL:** [{u}]({u})")
                            c_btn1, c_btn2 = st.columns([1, 1])
                            with c_btn1:
                                st.download_button(
                                    label="📥 Download Product ZIP Bundle",
                                    data=pkg["zip_bytes"],
                                    file_name=f"{pdp_engine.sanitize_filename(pkg['title'])}.zip",
                                    mime="application/zip",
                                    key=f"zip_{folder}"
                                )
                            with c_btn2:
                                if st.button("📂 Open Local Folder in Explorer", key=f"exp_{folder}"):
                                    subprocess.Popen(f'explorer "{folder}"')

                            # Show Videos if downloaded
                            if pkg["downloaded_videos"]:
                                st.markdown("#### 🎥 Downloaded Product Videos")
                                v_cols = st.columns(min(3, len(pkg["downloaded_videos"])))
                                for v_idx, (v_fn, v_fp) in enumerate(pkg["downloaded_videos"]):
                                    with v_cols[v_idx % len(v_cols)]:
                                        st.video(v_fp)
                                        st.caption(v_fn)

                            # Show Images
                            if pkg["downloaded_files"]:
                                st.markdown("#### 📸 Downloaded Pictures")
                                i_cols = st.columns(4)
                                for i_idx, (i_fn, i_fp) in enumerate(pkg["downloaded_files"]):
                                    with i_cols[i_idx % 4]:
                                        try:
                                            im = Image.open(i_fp)
                                            st.image(im, caption=f"{i_fn} ({im.width}x{im.height})", use_container_width=True)
                                        except Exception:
                                            st.write(i_fn)

                            st.markdown("---")
                            st.markdown("#### 📋 Scraped Verbatim Details")
                            st.markdown(pkg["summary_md"])
                    else:
                        st.error(f"❌ Failed: [{u}]({u}) — `{status}`")

# ----------------- TAB 2: SINGLE PRODUCT -----------------
with tab_single:
    col_in, col_act = st.columns([4, 1])
    with col_in:
        single_url = st.text_input("Enter Product URL", placeholder="https://www.amazon.in/dp/B0CJ4NSV1Q", label_visibility="collapsed")
    with col_act:
        fetch_single = st.button("⚡ Fetch & Extract", type="primary", use_container_width=True)

    if fetch_single and single_url:
        with st.spinner("Connecting to product page and downloading exact details, images, and videos..."):
            try:
                pdp = pdp_engine.scrape_pdp(single_url)
                pkg = pdp_engine.save_pdp_package(
                    pdp, 
                    include_images=dl_images, 
                    include_videos=dl_videos, 
                    base_dir=save_dir
                )
                st.success(f"Downloaded: **{pkg['title']}** ({len(pkg['downloaded_files'])} images, {len(pkg['downloaded_videos'])} videos)")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button(
                        label="📥 Download Package as ZIP",
                        data=pkg["zip_bytes"],
                        file_name=f"{pdp_engine.sanitize_filename(pkg['title'])}.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True
                    )
                with col_d2:
                    if st.button("📂 Open Local Folder in Explorer", use_container_width=True):
                        subprocess.Popen(f'explorer "{pkg["folder"]}"')
                        
                st.markdown("---")
                
                # Videos Preview
                if pkg["downloaded_videos"]:
                    st.subheader(f"🎥 Downloaded Product Videos ({len(pkg['downloaded_videos'])})")
                    v_cols = st.columns(min(3, len(pkg["downloaded_videos"])))
                    for v_idx, (v_fn, v_fp) in enumerate(pkg["downloaded_videos"]):
                        with v_cols[v_idx % len(v_cols)]:
                            st.video(v_fp)
                            st.caption(v_fn)

                # Images Preview
                st.subheader(f"📸 Downloaded Pictures ({len(pkg['downloaded_files'])})")
                if pkg["downloaded_files"]:
                    cols = st.columns(4)
                    for i, (fn, fp) in enumerate(pkg["downloaded_files"]):
                        with cols[i % 4]:
                            try:
                                im = Image.open(fp)
                                st.image(im, caption=f"{fn} ({im.width}x{im.height})", use_container_width=True)
                            except Exception:
                                st.write(fn)
                                
                st.markdown("---")
                st.subheader("📄 Scraped Verbatim Details Preview")
                st.markdown(pkg["summary_md"])

            except Exception as e:
                st.error(f"Extraction failed: {str(e)}")

# ----------------- TAB 3: SAVED RESEARCH BOARD -----------------
with tab_board:
    st.subheader("Existing Research Board Folders")
    if os.path.exists(save_dir):
        folders = [f for f in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, f))]
        st.write(f"Total Folders: **{len(folders)}**")
        
        for f in folders:
            fpath = os.path.join(save_dir, f)
            img_count = len(glob.glob(os.path.join(fpath, "images", "*.*")))
            vid_count = len(glob.glob(os.path.join(fpath, "videos", "*.*")))
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"📁 **{f}**")
                st.caption(f"Media: {img_count} images, {vid_count} videos | Path: `{fpath}`")
            with c2:
                if st.button("Open Folder", key=f"open_f_{f}"):
                    subprocess.Popen(f'explorer "{fpath}"')
            with c3:
                rep_file = os.path.join(fpath, "PDP_Details.md")
                if not os.path.exists(rep_file):
                    rep_file = os.path.join(fpath, "PDP_Intelligence_Report.md")
                if not os.path.exists(rep_file):
                    rep_file = os.path.join(fpath, "pdp_summary.md")
                if os.path.exists(rep_file):
                    with open(rep_file, "r", encoding="utf-8") as rf:
                        st.download_button("Get Details", rf.read(), file_name=f"{f}_Details.md", key=f"dl_rep_{f}")
            st.markdown("---")
    else:
        st.info("No research folders found yet.")
