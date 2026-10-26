# ARCHITECTURE.md
## TDC - IM Performance Tracking Agent: Architecture & System Design Specification

### 1. System Mission & Philosophy
The **TDC - IM Performance Tracking Agent** is a production-grade, reusable internal analytics application engineered for **The Derma Co (Honasa Consumer Ltd.)**. It automates the end-to-end processing, verification, and performance analysis of Influencer Marketing (IM) campaigns across monthly, quarterly, and annual datasets.

#### Non-Negotiable Operational Principles
1. **Never Silently Guess or Fabricate**: No values (spends, views, transcripts, classifications) are ever manufactured.
2. **Never Silently Overwrite Source Data**: Source values are preserved alongside verified values and audit reasons.
3. **Never Allow One Failure to Terminate the Batch**: Robust failure isolation ensures every Reel is processed independently.
4. **Never Expose Credentials**: Sensitive tokens (Instagram Session IDs, Apify tokens, Gemini API keys) are strictly isolated and redacted.
5. **Deterministic Numerical Computation**: 100% of arithmetic, metric aggregations, CPV, ER, spend percentages, and reconciliation are calculated in deterministic code; LLMs never compute numbers.
6. **Smart Human Review Gates**: The system adheres to **Observe → Understand → Infer → Confirm Only When Necessary → Process → Verify → Validate → Report**. Questions are asked only when data is genuinely ambiguous and materially impacts the report.

---

### 2. High-Level Architectural Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                     TDC - IM PERFORMANCE TRACKING AGENT                            |
|                                       (Streamlit UI / CLI Controller)                              |
+----------------------------------------------------------------------------------------------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    |                                                           |
                    v                                                           v
+---------------------------------------+                   +---------------------------------------+
|          Input Intelligence           |                   |         Security & Sanitization       |
|  - Multi-sheet Excel Parser           |                   |  - Formula Injection Neutralizer      |
|  - Semantic Schema Detection          |                   |  - Untrusted Text Demarcation         |
|  - Period & Campaign Inferencer       |                   |  - Path Traversal Guard               |
+---------------------------------------+                   +---------------------------------------+
                    |                                                           |
                    +-----------------------------+-----------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    Canonical Data Normalization                                    |
|  - SKU Code & Variant Normalizer (8904417319637, 8906087775713, 8904417306248, 8906087775607)      |
|  - Creator Handle & Link Normalizer                                                                |
|  - Reel URL Shortcode Extraction & Deduplication Classifier (Exact / Possible / Intentional)       |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    Execution & State Orchestrator                                  |
|  - Persistent State Machine (QUEUED -> PROCESSING -> SUCCESS / PARTIAL / FAILED / NEEDS_REVIEW)    |
|  - Resumable Versioned Cache (SQLite / JSON)                                                       |
|  - Concurrency & Rate Limit Throttler                                                              |
|  - Circuit Breakers & Bounded Exponential Backoff                                                  |
+----------------------------------------------------------------------------------------------------+
                    |                                                           |
                    v                                                           v
+---------------------------------------+                   +---------------------------------------+
|  Platform Extraction Adapter          |                   |  Multimodal Intelligence Adapter      |
|  (Wraps ig_reel_collector)            |                   |  (Google Gemini Multimodal API)       |
|  - Direct GraphQL Engine              |                   |  - Audio Extraction & Staging         |
|  - Authenticated Media Endpoint       |                   |  - Verbatim Spoken Speech Stt         |
|  - Apify Managed Scraper Fallback     |                   |  - Spoken Hook Identification         |
|  - Embed Public Scraping Fallback     |                   |  - Concept & Style Bucketing          |
|  - TLS Impersonated Media Downloader  |                   |  - Model Version & Prompt Auditing    |
+---------------------------------------+                   +---------------------------------------+
                    |                                                           |
                    +-----------------------------+-----------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                  Verification & Provenance Engine                                  |
|  - Spoken Script vs. Caption Strict Separation                                                     |
|  - Script Scraping Status Assignment (Transcribed / No Spoken Speech / Caption-only / Unavailable) |
|  - Concept & Gender Source vs. Verified Comparison with Confidence Scores                          |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                 Deterministic Analytics & Math Engine                              |
|  - Video CPV = Total Spends / Views                                                                |
|  - Engagement Rate = (Likes + Comments + Shares + Saves) / Views                                   |
|  - Dimension Slicing (Bucket, Language, Category, Gender, Creator, SKU)                            |
|  - Statistical Relationships (Pearson / Spearman when n >= 10, strictly without causal claims)     |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                               Standardized TDC Report Workbook Generator                           |
|  - Executive Summary Sheet                                                                         |
|  - Consolidated All SKUs Sheet (Dynamic =SUMIF, =COUNTIF, =IF Formulas)                           |
|  - SKU-Specific Analytical Sheets (Exact TDC Visual Palette: #C9DAF8 headers, #DFE4EC summaries)  |
|  - Data Quality & Verification Sheet                                                               |
|  - Comprehensive Processing & Security Audit Log Sheet                                             |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                     QA & Reconciliation Gate                                       |
|  - Physical File Save & Independent Re-read                                                        |
|  - Formula Health Check (Assert Zero #REF!, #DIV/0!, #VALUE!)                                      |
|  - Cross-Sheet Numerical Reconciliation (Total Reels, Total Spend, Total Views, Creator Count)     |
|  - Final Completion Status: COMPLETE / PARTIAL / FAILED                                            |
+----------------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Component Architecture

#### 3.1. Input Intelligence & Schema Detection (`input_intelligence.py`)
- **Dynamic Header Identification**: Scans first 10 rows for optimal header row index using keyword density and regex matching.
- **Semantic Field Mapping**: Maps variant column names to the Canonical Schema:
  - `Total Spends` / `Cost` / `Final Costs` / `Budget` → `canonical_spend`
  - `Views Day 10th` / `Views Day 0-5` / `Live Views` → `canonical_views`
  - `Live Link` / `Creative Link` / `Reel URL` → `canonical_reel_url`
  - `Product` / `Sept Product` / `SKU` → `canonical_product_name`
- **Ambiguity Gate**: If multiple columns qualify for the same critical metric with equal confidence, the system raises a single structured clarification prompt rather than silently choosing.

#### 3.2. Period & Scope Inferencer (`period_detector.py`)
- Automatically parses date columns, sheet names, and workbook filenames.
- Maps detected timelines into standard reporting intervals:
  - Monthly (e.g. "September 2026")
  - Quarterly (e.g. "Q3 2026")
  - Yearly / FY (e.g. "FY2026")
  - Custom Date Range (e.g. "01-Aug-2026 to 30-Sep-2026")
- Defaults to single-period consolidated processing without prompting if unambiguous.

#### 3.3. SKU Normalization Engine (`sku_normalizer.py`)
- Maintains canonical TDC SKU registry:
  - `8904417319637` → `2% Sali-Cinamide Anti-Acne Face Wash`
  - `8906087775713` → `1% Hyaluronic Sunscreen Aqua Gel`
  - `8904417306248` → `1% Kojic Acid Face Wash`
  - `8906087775607` → `Benzoyl Peroxide Face Wash`
- Matching Hierarchy:
  1. Exact SKU Barcode match (Tier 1)
  2. Exact Product Title match (Tier 2)
  3. Normalized Token / Keyword match (Tier 3)
  4. Ambiguous / Needs Review (Tier 4)

#### 3.4. Reel Extraction Adapter (`collector_adapter.py`)
- **Preservation Contract**: Wraps `ig_reel_collector` (`InstagramExtractor`, `models.py`) without modifying its internal source files.
- **Fail-Safe Extraction Pipeline**:
  1. Session-authenticated GraphQL direct extraction (if `INSTAGRAM_SESSION_ID` is active).
  2. Apify Actor execution (if `APIFY_TOKEN` is configured).
  3. Public GraphQL Desktop Query with TLS chrome impersonation.
  4. Embed HTML / oEmbed fallback.
- **Authentication State Tracking**:
  - `CONNECTED`, `EXPIRED`, `INVALID`, `NOT CONFIGURED`.
  - When expired, halts authenticated retries immediately and informs user with remaining Reel queue count.

#### 3.5. Verification & Multimodal Intelligence Engine (`verification_engine.py`)
- **Spoken Script vs. Caption Enforcement**:
  - Script = Words actually spoken by the creator in the video.
  - Caption = Instagram post text.
- If audio is available and speech is detected via Gemini multimodal upload, verbatim text is transcribed and `Script Scraping Status` is set to `Transcribed from Spoken Audio`.
- If audio contains music or sound effects only without human speech, status is set to `No spoken speech (Audio track only, only caption available)`.
- If Reel media cannot be retrieved, status is set to `cant scrap script, only caption`.
- If Reel is deleted or private, status is set to `Unavailable / Cannot Verify`.

#### 3.6. Deterministic Analytics Engine (`analytics_engine.py`)
- Computes metrics strictly via IEEE-compliant Python floats/decimals:
  - `Video CPV = Total Spend / Views`
  - `Engagement Rate = (Likes + Comments + Shares + Saves) / Views`
  - `Spend % = Group Spend / Total Spend`
- Dimension Aggregations: Bucket, Language, Category, Gender, Creator, SKU.
- Summary tables reproduce the exact layout of TDC reference reports (`SUM of Total Spends`, `SUM of Views Day 10th`, `COUNTA of Count`, `CPV`, `Spends %`).

#### 3.7. Excel Report Generator (`report_generator.py`)
- Produces a single unified workbook with openpyxl:
  1. `Executive Summary`
  2. `Consolidated All SKUs`
  3. Individual SKU sheets (`1% Hyalu Sunscreen Aqua Gel`, `2% Sali-Cinamide Face Wash`, etc.)
  4. `Data Quality & Verification`
  5. `Processing Log`
- Implements exact TDC styling:
  - Header fill: `#C9DAF8` (Font: Arial, 8.5pt Bold)
  - Summary fill: `#DFE4EC` (Font: Arial, 8.5pt Bold)
  - Borders: Thin `#D0D7DE`
  - Dynamic Excel formulas (`=LOWER(SUBSTITUTE(...))`, `=IF(...)`, `=SUMIF(...)`, `=COUNTIF(...)`, `=SUM(...)`)

#### 3.8. QA, Verification & Reconciliation Gate (`qa_validator.py`)
- Independent verification step:
  - Saves file to disk.
  - Reopens with `openpyxl.load_workbook(data_only=False)` and checks formula validity.
  - Reopens with `data_only=True` (or evaluated state) and reconciles:
    - $\sum \text{Reels}_{\text{SKU}} = \text{Total Reels}$
    - $\sum \text{Spend}_{\text{SKU}} = \text{Total Spend}$
    - $\sum \text{Views}_{\text{SKU}} = \text{Total Views}$
  - Flags any occurrence of `#REF!`, `#DIV/0!`, `#VALUE!`.
  - Determines final job status: `COMPLETE`, `PARTIAL`, or `FAILED`.

---

### 4. Data Flow Architecture

```
[Input Excel File (.xlsx)]
         |
         v
[Input Intelligence] ---> Canonical DataFrame + Mapping Metadata
         |
         v
[Deduplication & SKU Normalizer] ---> Validated Record Queue
         |
         v
[Cache Check (cache.db)] ---> Hits: Return Cached Artifacts
         |                    Misses: Queue for Extraction
         v
[Platform Extraction (ig_reel_collector)] ---> Raw Metrics + Audio/Video Media
         |
         v
[Gemini Multimodal Transcription & Classification] ---> AI Verifications & Spoken Hooks
         |
         v
[Verification & Provenance Engine] ---> Source vs Verified Records + DQ Log
         |
         v
[Deterministic Analytics Engine] ---> Dimensional Pivot Tables & CPV Computations
         |
         v
[OpenPyXL Report Generator] ---> Standardized TDC Excel Workbook (.xlsx)
         |
         v
[QA & Reconciliation Gate] ---> Workbook Validation & Cross-Sheet Balancing
         |
         v
[User Presentation & Audit Export] ---> Completion Report (COMPLETE / PARTIAL / FAILED)
```

---

### 5. Authentication, Failure, and Retry Model
- **Secrets Management**: Credentials loaded from `.env` or system environment variables. Never logged or serialized.
- **Bounded Exponential Backoff**:
  - Attempt 1: Immediate execution.
  - Attempt 2: 2.0s delay.
  - Attempt 3: 4.0s delay with engine fallback.
  - Expiry: If 401/403 session expiration is detected, all authenticated requests halt immediately.
- **Transaction-Safe Resumability**:
  - Cache entries are committed after each Reel. If process is interrupted at Reel 37/46, resumption picks up at Reel 38 with 0 lost work.

---

### 6. AI Usage Boundaries & Governance
- **Strictly Allowed AI Roles**:
  - Spoken audio speech-to-text verbatim transcription.
  - Opening spoken hook extraction.
  - Content concept styling and tone interpretation.
  - Natural language query interpretation for report customization.
- **Strictly Prohibited AI Roles**:
  - LLMs are NEVER permitted to estimate, calculate, interpolate, or adjust numerical metrics (views, likes, comments, spend, CPV, ER).
  - LLMs are NEVER permitted to invent spoken text when audio is unavailable.
  - LLMs are NEVER permitted to overwrite source metadata without an auditable verification trail.
