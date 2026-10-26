# SKUScout ⚡ Autonomous Cross-Marketplace Exact Variant Link Finder

**SKUScout** is an enterprise-grade, 100% free autonomous agent designed for Honasa brand managers, e-commerce specialists, catalog managers, and competitive intelligence teams.

It automatically discovers, cross-checks, and extracts **exact product links with precise ml/g size matching** across all major Indian marketplaces and brand D2C websites.

---

## 🚀 Key Highlights

1. **Exact Variant & Size Verification (ml or g)**:
   - Eliminates wrong variant matches (e.g. if you request `50g`, it will **never** return a `100g` or `30g` variant).
   - Eliminates unwanted combos & multipacks (e.g. rejects "Pack of 2" unless explicitly requested).
   - Normalizes units (`50g`, `50 gm`, `50 grams`, `100ml`, `100 m.l.`, `250 ml`).

2. **Supported Platforms**:
   - 🛒 **Amazon.in**
   - 🛍️ **Flipkart**
   - 💄 **Nykaa**
   - ⚡ **Blinkit** (Quick Commerce)
   - 🛵 **Zepto** (Quick Commerce)
   - 🌐 **Brand D2C Store** (The Derma Co `thedermaco.com`, Mamaearth `mamaearth.in`, Aqualogica `aqualogica.in`, Dr. Sheth's `drsheths.com`, BBlunt, Plum, Minimalist, Dot & Key, etc.)
   - 💜 **Purplle**

3. **100% Completely Free**:
   - Zero paid third-party scraping API subscriptions.
   - Built with resilient direct marketplace suggest APIs + anti-detection TLS impersonation (`curl_cffi` Chrome fingerprints) + DuckDuckGo/Bing site dorks.
   - Immune to frequent HTML/CSS class changes by e-commerce frontends.

4. **1-Click Launch**:
   - Just double click `SKUScout - Cross-Marketplace Link Agent` on your Windows Desktop!
   - Runs locally on **Port 8503** (coexists peacefully with PDP Downloader on 8501 and IG Collector on 8502).

---

## 🛠️ How to Use

### Mode 1: Single SKU Quick Scout
- Enter any product name with variant size (e.g., `The Derma Co 1% Hyaluronic Sunscreen Aqua Gel 50g`).
- Click **Scout Exact Variant Across All Platforms**.
- View real-time status cards with color-coded badges:
  - 🟢 **EXACT MATCH (100%)**: Verified title, brand, and exact ml/g size.
  - 🟡 **VARIANT MISMATCH / DIVERGENCE**: Identifies if only another size (e.g. 100g) is available.
  - ⚪ **NOT LISTED / OUT OF STOCK**: Platform does not stock this SKU.
- Click **Open All Links in New Tabs** to open all product pages at once!

### Mode 2: Bulk Multi-Line Paste
- Paste 5, 20, 50, or 100 products (1 per line).
- Real-time progress bar with live counter.
- Generates a summary table and a 1-click downloadable **Excel Report (.xlsx)** with clickable hyperlinks.

### Mode 3: Excel / CSV File Upload
- Upload your product master list (`.xlsx` or `.csv`).
- Select your columns (Product Name, Brand, Size/Variant).
- Batch processes the entire spreadsheet and outputs a consolidated report.

### Mode 4: Brand D2C Catalog Auto-Scout
- Enter any brand website domain (e.g., `thedermaco.com`, `mamaearth.in`, `aqualogica.in`).
- Pulls the entire catalog and its variants directly from the brand store.
- Cross-scouts all major marketplaces for every single product in the brand's catalog!

---

## 📁 File Structure

- `Launch_SKUScout.bat` - 1-Click Desktop launcher.
- `Stop_SKUScout.bat` - Gracefully stops port 8503.
- `create_skuscout_shortcut.ps1` - Recreates Desktop shortcut if needed.
- `skuscout/app.py` - Streamlit Web UI.
- `skuscout/skuscout_engine.py` - Multi-channel parallel search & resolution engine.
- `skuscout/variant_verifier.py` - Size parsing, unit normalization & negative variant rejection.
- `skuscout/brand_crawler.py` - D2C Shopify/custom catalog & variant search engine.
