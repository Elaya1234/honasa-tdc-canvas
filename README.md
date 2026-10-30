# HONASA Consumer — Competitive Intelligence & E-Commerce Suite

A centralized, enterprise-grade intelligence toolkit built for **HONASA Consumer (The Derma Co)** brand managers, catalog specialists, e-commerce managers, and R&D teams.

---

## 🌐 Live Hosted Tools (Direct Browser Links — No Installation Needed)

Share these links directly with team members to open instantly in any web browser on desktop, tablet, or phone:

| Tool Name | What It Does | Live Hosted URL |
| :--- | :--- | :--- |
| 🎙️ **Discussion Intelligence & AudioSuite** | Dual-engine: Customer AudioCRM & In-Person Meeting Minutes with seamless 10-min chunking (by Elaya Narayanan) | [Open Live App ↗](https://elaya1234.github.io/honasa-tdc-canvas/) |
| 🛠️ **Central Tools Hub & Launchpad** | All-in-one directory with status and quick-launch links for all tools | [Open Tools Hub ↗](https://elaya1234.github.io/honasa-tdc-canvas/hub.html) |
| 📊 **Product Page Competitive Canvas** | 334 scraped listings, dual-image comparator, claims matrices, INCI science | [Open Research Canvas ↗](https://elaya1234.github.io/honasa-tdc-canvas/PDP_Competitive_Research_Canvas.html) |
| ☀️ **Sunscreen Multi-Marketplace Board (v3)** | 10 hero products across 8 platforms (Amazon, Nykaa, Blinkit, Flipkart, D2C) | [Open Sunscreen Board ↗](https://elaya1234.github.io/honasa-tdc-canvas/Sunscreen_Comparison_Board_v3.html) |
| 🧼 **South KYC — Face Wash Analysis** | Regional consumer demand, cleansing habits & ingredient preferences | [Open Face Wash Report ↗](https://elaya1234.github.io/honasa-tdc-canvas/TDC_South%20KYC%20%20Analysis/TDC_South_KYC_Face_Wash_FINAL_PERMANENT.html) |
| 🧴 **South KYC — Sunscreen Analysis** | Consumer perception of white cast, aqua gel texture, and daily UV compliance | [Open Sunscreen Report ↗](https://elaya1234.github.io/honasa-tdc-canvas/TDC_South%20KYC%20%20Analysis/TDC_South_KYC_Sunscreen_FINAL_PERMANENT.html) |
| 💧 **South KYC — Serum Analysis** | Actives adoption (Niacinamide, Salicylic, Vitamin C) & packaging formats | [Open Serum Report ↗](https://elaya1234.github.io/honasa-tdc-canvas/TDC_South%20KYC%20%20Analysis/TDC_South_KYC_Serum_Analysis.html) |
| 💆 **South KYC — Shampoo Analysis** | Scalp concern prevalence, sulfate-free adoption & hard-water washing challenges | [Open Shampoo Report ↗](https://elaya1234.github.io/honasa-tdc-canvas/TDC_South%20KYC%20%20Analysis/TDC_South_KYC_Shampoo_FINAL_v5.html) |

---

## 🛠️ The 7 Desktop & Autonomous AI Tools

These tools run locally on Windows machines with 1-click `.bat` launchers:

### 1. **Product Data & Media Downloader**
* **Launcher:** `Launch_Product_Data_Media_Downloader.bat` (or `Launch_PDP_Downloader.bat`) • `http://localhost:8501`
* **What it does:** Scrapes and downloads verbatim Product Detail Page (PDP) specifications, pricing, claims, and all high-resolution images & videos across marketplaces.
* **Input:** Product URL or multi-line link list (Amazon, Flipkart, Nykaa, Blinkit, Brand D2C sites).
* **Output:** Product folder with high-res media, structured `PDP_Data.json`, markdown summary, and 1-click ZIP package.

### 2. **Exact SKU Marketplace Link Finder (SKUScout)**
* **Launcher:** `Launch_Exact_SKU_Marketplace_Link_Finder.bat` (or `Launch_SKUScout.bat`) • `http://localhost:8503`
* **What it does:** Autonomous agent that finds and verifies exact canonical product links matching the exact unit/pack size (ml/g), eliminating unwanted sizes and combo bundles.
* **Input:** Product title with size (e.g. *The Derma Co 1% Hyaluronic Sunscreen Aqua Gel 50g*), text list, or `.xlsx` catalog.
* **Output:** Exact canonical URLs across Amazon, Flipkart, Nykaa, Blinkit, Zepto, Purplle, D2C with match verification badges and Excel report.

### 3. **Instagram Reel Intelligence Analyzer**
* **Launcher:** `Launch_Instagram_Reel_Intelligence_Analyzer.bat` (or `Launch_IG_Collector.bat`) • `http://localhost:8502`
* **What it does:** Extracts video engagement metrics and uses Gemini AI to transcribe spoken audio verbatim, detect hooks, spoken language, concept styles, and creator demographics.
* **Input:** Instagram Reel URL(s).
* **Output:** Engagement metrics, full audio transcript, opening hook breakdown, taxonomy tagging, and exportable Excel/CSV report.

### 4. **Product Page Competitive Comparison**
* **Launcher:** `Launch_Product_Page_Competitive_Comparison.bat` (or `Launch_Research_Canvas.bat`)
* **What it does:** Interactive visual dashboard compiling 334 scraped competitor and hero SKU listings across 4 categories (*Facewash, Sunscreen, Serum, Shampoo*).
* **Output:** Standalone responsive web dashboard (`PDP_Competitive_Research_Canvas.html` / `index.html`) featuring dual-image comparators, claims matrices, and full INCI breakdowns.

### 5. **Marketplace Link Auto-Filler**
* **Launcher:** `Run_Marketplace_Link_Auto_Filler.bat`
* **What it does:** Automatically discovers and populates missing marketplace links directly into Honasa GSO research sheets using multi-engine search and Gemini AI candidate verification.
* **Input:** Honasa GSO Excel spreadsheet with brand and SKU names (`GSO LINKs.xlsx`).
* **Output:** Updated and validated Excel spreadsheet (`GSO_LINKs_AI_Verified.xlsx`) with verified direct links.

### 6. **Product Page Intelligence Extractor**
* **Launcher:** `Run_Product_Page_Intelligence_Extractor.bat`
* **What it does:** Uses Gemini AI to analyze raw product page copy and extract structured formulation science, limitations, texture analysis, target skin types, and contraindications.
* **Input:** Raw PDP details, bullet points, and A+ copy (or path to `PDP_Data.json`).
* **Output:** Clean structured JSON / report covering: key benefits, what it does NOT do, texture & finish, who should use/avoid it, application mistakes, and INCI breakdown.

### 7. **TDC - IM Performance Tracking Agent**
* **Launcher:** `Launch_TDC_IM_Agent.bat` • `http://localhost:8504`
* **What it does:** Enterprise AI-assisted analytics agent that ingests raw TDC Influencer Marketing trackers across monthly, quarterly, yearly, or custom periods; extracts and verifies Instagram Reel metrics; transcribes verbatim spoken audio scripts (strictly separated from captions); computes 100% deterministic Spend, Views, CPV, and ER% metrics; and generates standardized 45-column TDC workbooks with automated executive summaries, SKU sheets, dynamic formulas (`=SUMIF`, `=COUNTIF`, `=IF`), and independent QA balancing.
* **Input:** Raw campaign Excel sheets (e.g. `Sept'26 FW & SS.xlsx`, `Aug'26 SS ( HA) IM analysis .xlsx`).
* **Output:** Standardized multi-tab Excel workbooks matching historical TDC templates, complete with dynamic formulas, QA validation certificates, and reconciliation logs.

### 8. **Discussion Intelligence & AudioCRM Suite (by Elaya Narayanan)**
* **Live Hosted Web Link:** [https://elaya1234.github.io/honasa-tdc-canvas/](https://elaya1234.github.io/honasa-tdc-canvas/)
* **Local Launcher:** `Launch_AudioCRM.bat` • `http://localhost:8510`
* **What it does:** Dual-engine audio intelligence suite featuring:
  1. **Customer AudioCRM & KYC Engine**: SKU-agnostic intake that auto-generates dynamic schemas from any uploaded CSV/Excel spreadsheet, records calls with live Web Audio API waveform visualizers, processes verbatim transcripts & dynamic Q&A answers in parallel background queues with Google Gemini, supports double-click cell overriding, and exports back to formatted Excel/CSV workbooks.
  2. **In-Person Meeting Intelligence & Notes**: Continuous hours-long team/board meeting recording with seamless rolling 10-minute auto-chunking (zero audio dropout), master verbatim transcript concatenation, real-time strategic decisions logging, action items matrices with owners & deadlines, meeting library archive, and 1-click Markdown (`.md`), Plain Text (`.txt`), and Print/PDF export.
* **Architecture:** Dual-mode design — operates 100% standalone directly in modern web browsers on GitHub Pages with SheetJS & Web Audio API, or connects to the local high-concurrency Express/Node.js backend.

---

## ⚡ Quick Start for Local Tools

To launch any tool locally on Windows:
1. Double-click `LAUNCH_ALL_HONASA_TOOLS.bat` to access the master interactive menu.
2. Or double-click any individual tool's launcher (e.g. `Launch_SKUScout.bat` or `Launch_TDC_IM_Agent.bat`).
3. If running Python manually:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 How to Enable GitHub Pages (If not already live)

1. Open your repository settings: [GitHub Pages Settings](https://github.com/Elaya1234/honasa-tdc-canvas/settings/pages)
2. Under **Build and deployment** > **Source**: choose **Deploy from a branch**.
3. Under **Branch**: select **main**, and folder **/ (root)**.
4. Click **Save**. In 1–2 minutes, all web links above will be live for your entire team!
