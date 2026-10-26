import streamlit as st
import io
import time
import urllib.parse
import openpyxl
import csv
from typing import List, Dict, Any

import variant_verifier
import brand_crawler
import skuscout_engine

st.set_page_config(
    page_title="Exact SKU Marketplace Link Finder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.4rem;
    }
    .badge-exact {
        background-color: #DCFCE7;
        color: #166534;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid #86EFAC;
    }
    .badge-diverge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid #FCD34D;
    }
    .badge-search {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid #FCD34D;
    }
    .badge-none {
        background-color: #F1F5F9;
        color: #64748B;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
        border: 1px solid #CBD5E1;
    }
    .platform-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
        min-height: 280px;
    }
    .platform-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .platform-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.4rem;
    }
    .verified-pill {
        display: inline-block;
        background: #F0FDF4;
        color: #15803D;
        border: 1px solid #BBF7D0;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'results_history' not in st.session_state:
    st.session_state.results_history = []
if 'last_scouted' not in st.session_state:
    st.session_state.last_scouted = None
if 'catalog_cache' not in st.session_state:
    st.session_state.catalog_cache = []

# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/flash-on.png", width=60)
    st.title("Exact SKU Link Finder ⚡")
    st.caption("Autonomous Exact Variant & Single-Product Link Finder")
    st.markdown("---")
    
    st.markdown("### 🎯 Monitored Platforms")
    st.markdown("""
    - 🛒 **Amazon.in** (Direct `/dp/{asin}`)
    - 🛍️ **Flipkart** (Direct `/p/{itm}`)
    - 💄 **Nykaa** (Direct `/p/{id}`)
    - ⚡ **Blinkit** (Direct `/prn/{slug}/prid/{id}`)
    - 🛵 **Zepto** (Direct `/pn/{slug}/pvid/{id}`)
    - 🌐 **Brand D2C Store** (Direct canonical PDP)
    - 💜 **Purplle** (Direct `/product/{slug}`)
    """)
    
    st.markdown("---")
    st.markdown("### ⚙️ Search Settings")
    strict_size = st.checkbox("Strict ml/g Verification", value=True, help="Rejects variants if size (ml or g) differs from target.")
    no_combos = st.checkbox("Reject Combos & Multipacks", value=True, help="Strictly allows only single-product links; rejects packs of 2, 3, combos, or bundles.")
    include_purplle = st.checkbox("Include Purplle", value=True)
    
    st.markdown("---")
    if st.button("🗑️ Clear Results History"):
        st.session_state.results_history = []
        st.session_state.last_scouted = None
        st.rerun()

# Main Header
st.markdown('<div class="main-header">⚡ Exact SKU Marketplace Link Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous agent that researches, visually cross-checks, and pulls direct canonical product links with exact ml/g variants across Amazon, Flipkart, Nykaa, Zepto, Blinkit & Brand D2C (Single Products Only, Zero Combos).</div>', unsafe_allow_html=True)

# Tabs
tab_single, tab_bulk, tab_excel, tab_d2c = st.tabs([
    "🔍 Single SKU Quick Scout",
    "📝 Bulk Multi-Line Paste",
    "📊 Excel / CSV File Upload",
    "🌐 Brand D2C Catalog Auto-Scout"
])

PLATFORM_KEYS = ['Brand D2C', 'Amazon', 'Nykaa', 'Flipkart', 'Blinkit', 'Zepto', 'Purplle']

def format_summary_table(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    cols = ['Product Name', 'Brand', 'Target Size'] + PLATFORM_KEYS
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    table_lines = [header, separator]
    for r in rows:
        row_cells = [str(r.get(c, '')).replace('\n', ' ') for c in cols]
        table_lines.append("| " + " | ".join(row_cells) + " |")
    return "\n".join(table_lines)

def format_excel_export(results: List[Dict[str, Any]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Marketplace Links"
    
    headers = ['Product Input', 'Detected Brand', 'Product Name', 'Target Size (ml/g)']
    for p_key in PLATFORM_KEYS:
        headers.extend([f"{p_key} Canonical Link", f"{p_key} Status", f"{p_key} Image"])
    ws.append(headers)
    
    for r in results:
        row = [
            r.get('input', ''),
            r.get('brand', ''),
            r.get('product_name', ''),
            r.get('target_size', '')
        ]
        platforms = r.get('platforms', {})
        for p_key in PLATFORM_KEYS:
            p_data = platforms.get(p_key)
            if p_data and p_data.get('url'):
                url = p_data.get('url')
                matched = "YES (100% Exact PDP)" if p_data.get('is_exact_match') else "Search & Choose Link"
                v_found = p_data.get('variant_found', '')
                status_str = f"{matched} [{v_found}]" if v_found else matched
                row.extend([url, status_str, p_data.get('thumbnail_url', '')])
            else:
                row.extend(["", "Not Listed", ""])
        ws.append(row)
        
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# ----------------- TAB 1: SINGLE SKU QUICK SCOUT -----------------
with tab_single:
    st.markdown("#### Research a Single Product & Variant")
    col1, col2 = st.columns([3, 1])
    with col1:
        single_input = st.text_input(
            "Enter Product Name with Size (ml or g):",
            value="The Derma Co 1% Hyaluronic Sunscreen Aqua Gel 50g",
            placeholder="e.g. Minimalist 10% Niacinamide Face Serum 30ml"
        )
    with col2:
        brand_override = st.text_input(
            "Brand / D2C Domain (Optional):",
            value="",
            placeholder="e.g. thedermaco.com"
        )
        
    if st.button("🚀 Scout Exact Variant Across All Platforms", key="btn_single"):
        if not single_input.strip():
            st.warning("Please enter a product name.")
        else:
            with st.spinner("Scouting Amazon, Flipkart, Nykaa, Zepto, Blinkit & Brand D2C with visual & multi-attribute verification (Single products only)..."):
                res = skuscout_engine.scout_single_product(
                    raw_product_string=single_input,
                    brand_domain_hint=brand_override,
                    include_purplle=include_purplle
                )
                st.session_state.last_scouted = res
                st.session_state.results_history.append(res)
                
    if st.session_state.last_scouted:
        res = st.session_state.last_scouted
        st.markdown("---")
        
        # Header Info Card
        b_text = f"**Brand**: `{res.get('brand') or 'Auto-Detected'}`"
        c_text = f"**Category**: `{res.get('category') or 'Skincare'}`"
        s_text = f"**Size**: `{res.get('target_size') or 'Exact'}`"
        st.info(f"🔎 **Scouting Goal**: {res.get('input')} | {b_text} | {c_text} | {s_text} | 🚫 **Combos Rejected**")
        
        platforms = res.get('platforms', {})
        cols = st.columns(3)
        
        for idx, p_name in enumerate(PLATFORM_KEYS):
            if p_name == 'Purplle' and not include_purplle:
                continue
                
            p_data = platforms.get(p_name)
            col = cols[idx % 3]
            
            with col:
                with st.container():
                    st.markdown(f'<div class="platform-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="platform-title">{p_name}</div>', unsafe_allow_html=True)
                    
                    if p_data and p_data.get('url'):
                        is_match = p_data.get('is_exact_match')
                        confidence = p_data.get('confidence', 0)
                        found_size = p_data.get('variant_found', '')
                        url = p_data.get('url')
                        title = p_data.get('title', '')
                        thumb = p_data.get('thumbnail_url', '')
                        badges = p_data.get('verified_badges', [])
                        
                        # Match status badge
                        if is_match and confidence >= 85:
                            st.markdown(f'<span class="badge-exact">🟢 EXACT MATCH ({confidence}%)</span>', unsafe_allow_html=True)
                        elif is_match:
                            st.markdown(f'<span class="badge-exact">🟢 VERIFIED MATCH ({confidence}%)</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="badge-search">🟡 SEARCH & CHOOSE</span>', unsafe_allow_html=True)
                            
                        # Visual Thumbnail & Details layout
                        if thumb:
                            img_col, txt_col = st.columns([1, 2])
                            with img_col:
                                st.image(thumb, use_container_width=True)
                            with txt_col:
                                st.caption(f"**PDP Title**: {title[:75]}...")
                        else:
                            st.caption(f"**PDP Title**: {title[:90]}...")
                            
                        # Badges
                        if badges:
                            badge_html = " ".join([f'<span class="verified-pill">✓ {b}</span>' for b in badges])
                            st.markdown(badge_html, unsafe_allow_html=True)
                            
                        if is_match:
                            st.markdown(f"[🔗 **Open Direct Product Page**]({url})")
                        else:
                            st.markdown(f"[🔍 **Open 1-Click Search on {p_name}**]({url})")
                        st.code(url, language="text")
                    else:
                        st.markdown(f'<span class="badge-none">⚪ NOT LISTED ON PLATFORM</span>', unsafe_allow_html=True)
                        st.caption("No matching variant listed on this marketplace.")
                        if p_data and p_data.get('notes'):
                            st.caption(f"_{p_data['notes']}_")
                        
                    st.markdown('</div>', unsafe_allow_html=True)
                    
        # 1-Click Open All
        valid_urls = [p['url'] for p in platforms.values() if p and p.get('url')]
        if valid_urls:
            st.markdown("### ⚡ Quick Actions")
            c1, c2 = st.columns(2)
            with c1:
                js_links = [f"window.open('{u}', '_blank');" for u in valid_urls]
                js_script = f"""
                <script>
                function openAllTabs() {{
                    {'; '.join(js_links)}
                }}
                </script>
                <button onclick="openAllTabs()" style="background-color: #2563EB; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                    🚀 Open All {len(valid_urls)} Links in New Tabs
                </button>
                """
                st.components.v1.html(js_script, height=55)
            with c2:
                excel_data = format_excel_export([res])
                st.download_button(
                    "📥 Export This Product to Excel",
                    data=excel_data,
                    file_name=f"SKUScout_{res.get('product_name')[:20]}_{res.get('target_size')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# ----------------- TAB 2: BULK MULTI-LINE PASTE -----------------
with tab_bulk:
    st.markdown("#### Paste Multiple Products (1 per line)")
    st.caption("How many products ever you give, SKUScout will research, visually cross-check, filter out combos, and pull exact single-product links automatically.")
    
    sample_text = """The Derma Co 1% Hyaluronic Sunscreen Aqua Gel 50g
Minimalist 10% Niacinamide Face Serum 30ml
Cetaphil Gentle Skin Cleanser 125ml
Dot & Key Barrier Repair Face Cream 100g
Plum 15% Vitamin C Face Serum 30ml
Simple Kind to Skin Refreshing Facial Wash 150ml"""

    bulk_input = st.text_area(
        "Product List (Include Brand & Size for exact matching):",
        value=sample_text,
        height=180
    )
    
    if st.button("🚀 Scout All Products in Bulk", key="btn_bulk"):
        lines = [line.strip() for line in bulk_input.split("\n") if line.strip()]
        if not lines:
            st.warning("Please paste at least one product.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            batch_results = []
            
            for idx, line in enumerate(lines):
                status_text.text(f"Scouting product {idx+1}/{len(lines)}: {line}...")
                res = skuscout_engine.scout_single_product(
                    raw_product_string=line,
                    include_purplle=include_purplle
                )
                batch_results.append(res)
                st.session_state.results_history.append(res)
                progress_bar.progress((idx + 1) / len(lines))
                time.sleep(0.3)
                
            status_text.success(f"✅ Completed research for {len(lines)} products across all marketplaces!")
            
    if st.session_state.results_history:
        st.markdown("### 📋 Results Summary")
        table_rows = []
        for r in st.session_state.results_history:
            item = {
                'Product Name': r.get('product_name'),
                'Brand': r.get('brand'),
                'Target Size': r.get('target_size'),
            }
            plats = r.get('platforms', {})
            for p in PLATFORM_KEYS:
                p_info = plats.get(p)
                if p_info and p_info.get('url'):
                    if p_info.get('is_exact_match'):
                        item[p] = f"🟢 [PDP Link]({p_info.get('url')})"
                    else:
                        item[p] = f"🟡 [Search Link]({p_info.get('url')})"
                else:
                    item[p] = "⚪ None"
            table_rows.append(item)
            
        st.markdown(format_summary_table(table_rows))
        
        st.download_button(
            "📥 Download Complete Batch Excel Report (.xlsx)",
            data=format_excel_export(st.session_state.results_history),
            file_name="SKUScout_Batch_Results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ----------------- TAB 3: EXCEL / CSV FILE UPLOAD -----------------
with tab_excel:
    st.markdown("#### Upload an Excel (.xlsx) or CSV File")
    uploaded_file = st.file_uploader("Upload Product Master List:", type=["xlsx", "csv"])
    
    if uploaded_file:
        try:
            records = []
            cols = []
            if uploaded_file.name.endswith('.csv'):
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                reader = list(csv.DictReader(io.StringIO(content)))
                records = reader
                cols = list(reader[0].keys()) if reader else []
            else:
                wb = openpyxl.load_workbook(uploaded_file)
                ws = wb.active
                raw_rows = list(ws.iter_rows(values_only=True))
                if raw_rows:
                    cols = [str(h) for h in raw_rows[0]]
                    for r_val in raw_rows[1:]:
                        records.append({cols[i]: r_val[i] for i in range(min(len(cols), len(r_val)))})
                        
            st.markdown("##### Preview Uploaded Data:")
            st.table(records[:5])
            
            name_col = st.selectbox("Select Product Name Column:", cols, index=0)
            
            size_options = ["None (Extract from Product Name)"] + cols
            size_col = st.selectbox("Select Size/Variant Column:", size_options, index=0)
            
            brand_options = ["None (Auto-Detect)"] + cols
            brand_col = st.selectbox("Select Brand Column:", brand_options, index=0)
            
            if st.button("🚀 Process Uploaded File"):
                items_to_process = []
                for row in records:
                    p_name = str(row.get(name_col, '') or "")
                    s_val = str(row.get(size_col, '') or "") if size_col != "None (Extract from Product Name)" else ""
                    b_val = str(row.get(brand_col, '') or "") if brand_col != "None (Auto-Detect)" else ""
                    
                    full_query = f"{b_val} {p_name} {s_val}".strip()
                    items_to_process.append({
                        'name': full_query,
                        'brand': b_val,
                        'size': s_val
                    })
                    
                progress_bar = st.progress(0)
                status_text = st.empty()
                file_results = []
                
                for idx, itm in enumerate(items_to_process):
                    status_text.text(f"Processing row {idx+1}/{len(items_to_process)}: {itm['name']}...")
                    res = skuscout_engine.scout_single_product(
                        raw_product_string=itm['name'],
                        brand_hint=itm['brand'],
                        target_size_hint=itm['size'],
                        include_purplle=include_purplle
                    )
                    file_results.append(res)
                    st.session_state.results_history.append(res)
                    progress_bar.progress((idx + 1) / len(items_to_process))
                    time.sleep(0.3)
                    
                status_text.success(f"✅ Finished processing {len(items_to_process)} products!")
                
                st.download_button(
                    "📥 Download Output Excel Report",
                    data=format_excel_export(file_results),
                    file_name=f"SKUScout_{uploaded_file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ----------------- TAB 4: BRAND D2C CATALOG AUTO-SCOUT -----------------
with tab_d2c:
    st.markdown("#### Auto-Extract Catalog from Brand Website & Find All Marketplace Links")
    st.caption("Give any brand D2C website (e.g. thedermaco.com, mamaearth.in, aqualogica.in). SKUScout pulls the catalog SKUs and their exact sizes, then discovers everywhere they are listed.")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        d2c_url = st.text_input("Brand D2C Website Domain:", value="thedermaco.com")
    with col_d2:
        max_skus = st.number_input("Max Products to Fetch:", min_value=5, max_value=250, value=20, step=5)
        
    if st.button("📥 Fetch Catalog from Brand D2C", key="btn_fetch_catalog"):
        with st.spinner(f"Extracting catalog & variants from {d2c_url}..."):
            catalog = brand_crawler.fetch_brand_catalog(d2c_url, limit=max_skus)
            st.session_state.catalog_cache = catalog
            if catalog:
                st.success(f"Found {len(catalog)} products and variants from {d2c_url}!")
            else:
                st.warning("Could not automatically retrieve products via Shopify API. You can still use the Single or Bulk tabs.")
                
    if st.session_state.catalog_cache:
        cat_items = st.session_state.catalog_cache
        st.table([{
            'Product': it['product_name'],
            'Variant': it['variant_title'],
            'Size': it['size_ml_g'],
            'Price': it['price']
        } for it in cat_items[:15]])
        
        if st.button("🚀 Scout Marketplaces for All Extracted Catalog SKUs"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            cat_results = []
            
            for idx, item in enumerate(cat_items):
                full_name = f"{item['brand']} {item['product_name']} {item['size_ml_g']}"
                status_text.text(f"Scouting SKU {idx+1}/{len(cat_items)}: {item['product_name']} ({item['size_ml_g']})...")
                res = skuscout_engine.scout_single_product(
                    raw_product_string=full_name,
                    brand_hint=item['brand'],
                    brand_domain_hint=item['brand_domain'],
                    target_size_hint=item['target_size'],
                    include_purplle=include_purplle
                )
                cat_results.append(res)
                st.session_state.results_history.append(res)
                progress_bar.progress((idx + 1) / len(cat_items))
                time.sleep(0.3)
                
            status_text.success("✅ Completed catalog cross-marketplace research!")
            
            st.download_button(
                "📥 Download D2C Catalog Cross-Marketplace Report (.xlsx)",
                data=format_excel_export(cat_results),
                file_name=f"SKUScout_{d2c_url}_Catalog_Marketplace_Links.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )