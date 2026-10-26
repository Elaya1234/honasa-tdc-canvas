# USER_GUIDE.md
## TDC - IM Performance Tracking Agent: End-User Operational Manual

### 1. Introduction
The **TDC - IM Performance Tracking Agent** is an enterprise analytics platform designed specifically for the Influencer Marketing (IM) team at **The Derma Co (Honasa Consumer Ltd.)**. It automates the intake, verification, multi-dimensional performance analysis, and standardized executive reporting of influencer campaigns across monthly, quarterly, and annual datasets.

---

### 2. Quick-Start Guide (3 Steps)

#### Step 1: Launch the Agent
Double-click `Launch_TDC_IM_Agent.bat` in the project root directory, or execute in terminal:
```bash
Launch_TDC_IM_Agent.bat
```
Your default web browser will automatically open to:
`http://localhost:8504`

#### Step 2: Upload or Select Campaign Tracker
1. Click **Browse files** and select your Influencer Marketing Excel Tracker (`.xlsx`), or click **Load Sept'26 FW & SS (Golden Set)** for immediate demonstration.
2. The agent automatically executes the **Observe → Understand → Infer** sequence:
   - Identifies reporting period (e.g. *September 2026* or *Q3 2026*).
   - Tallies deliverables, SKUs, and creator partners.
   - Evaluates cache readiness.
   - Proposes the **Recommended Output Configuration**.

#### Step 3: Run the Analysis
- Click **🚀 START RECOMMENDED ANALYSIS**.
- The progress dashboard tracks extraction, speech-to-text audio transcription, and deterministic KPI computations in real time.
- Upon completion, download the verified executive report:
  `TDC - IM Performance Tracking - <Period>.xlsx`

---

### 3. Understanding the Standardized Output Report

The generated Excel file contains five specialized analytical sheets:

| Sheet Name | Content & Purpose |
| :--- | :--- |
| **`Executive Summary`** | Top-level KPI dashboard: Total Spend, Total Views, Blended CPV, Blended ER, top-performing SKUs/creators, and comprehensive Data Quality audit summary. |
| **`Consolidated All SKUs`** | Complete 45-column campaign ledger encompassing all deliverables, equipped with dynamic `=SUMIF`, `=COUNTIF`, and `=IF` summary tables for Bucket, Language, Category, and Gender. |
| **Individual SKU Sheets** | Dedicated analytical sheets per active product line (e.g., `1% Hyalu Sunscreen Aqua Gel`, `2% Sali-Cinamide Face Wash`, `1% Kojic Acid Face Wash`, `Benzoyl Peroxide Face Wash`), formatted in official TDC palette (`#C9DAF8` headers, `#DFE4EC` summaries). |
| **`Data Quality & Verification`** | Field-level audit trail documenting every verification decision, confidence rating, source attribution, and correction reason. |
| **`Processing Log`** | Security-hardened timestamped execution ledger with sanitized, credential-scrubbed system messages. |

---

### 4. Key Rules & System Behaviors

#### A. Spoken Script vs. Post Caption
- **Spoken Script**: Verbatim words actually spoken aloud by the creator in the video, extracted via speech-to-text.
- **Caption**: The written Instagram post text and hashtags.
- If a Reel has only background music without spoken dialogue, the status is explicitly set to:
  `No spoken speech (Audio track only, only caption available)`
- Captions are **never** substituted for spoken scripts.

#### B. 100% Deterministic Arithmetic
- All calculations for Spend, Views, CPV, ER%, and dimension summaries are computed in deterministic Python code and dynamic Excel formulas.
- Artificial Intelligence is **never** permitted to estimate, invent, or guess numerical values.

#### C. Instant Crash Resumption
- The agent persists processing state to a local SQLite database after every individual deliverable.
- If power is lost or processing is interrupted, re-launching the tool will resume from the exact unfinished record without re-transcribing completed items.
