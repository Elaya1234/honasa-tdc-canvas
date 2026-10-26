# DATA_SCHEMA.md
## TDC - IM Performance Tracking Agent: Canonical Data Schema Specification

### 1. Source of Truth Hierarchy

| Field Type | Primary Authority (Tier 1) | Secondary Authority (Tier 2) | Fallback (Tier 3) | Strictly Prohibited |
| :--- | :--- | :--- | :--- | :--- |
| **Numerical Metrics (Spend, Views, Likes, Comments)** | Direct Verified Platform API (Instagram / Apify) | Source Input Excel (Verified Tracker Columns) | Confirmed Platform Scraping | AI Estimation / Guesswork |
| **Spoken Script (Whole Script)** | Actual Reel Spoken Audio STT (Gemini Multimodal) | Audio Track Transcription Fallback | "Can't scrap script, only caption" / "No spoken speech" | Caption substitution for speech |
| **Spoken Hook** | First 3–5 seconds of verbatim transcribed audio | Leading opening audio statement | Caption opening line (only if explicitly flagged) | Fabricated hook |
| **SKU & Product Code** | Exact 13-digit EAN Barcode (`8904417319637`) | Explicit Product Name Lookup | Semantic Normalized Title | Merging dissimilar variants |
| **Reporting Period** | Explicit Live Date range in row items | Campaign Metadata in Sheet/Filename | User Configuration | Guessing without evidence |

---

### 2. Canonical Column Mapping & Aliases

The input Excel sheets vary across campaigns and months. The system maps incoming headers to the canonical schema dynamically with confidence ratings:

| Canonical Field | Description | Common Source Column Aliases | Data Type | Formula / Origin |
| :--- | :--- | :--- | :--- | :--- |
| `live_status` | Status of creative deployment | `Live`, `Status`, `Post Status` | String | Source Excel |
| `sub_cat` | Product subcategory | `Sub Cat`, `SubCategory`, `Category Group` | String | Source Excel (`Facewash`, `Sunscreen`, etc.) |
| `creator` | Creator display name | `Creator`, `Influencer`, `Influencer Name` | String | Source Excel |
| `channel_standard_name` | Normalized lowercase creator handle | `Channel Standard Name`, `Normalized Handle` | String | `=LOWER(SUBSTITUTE(C2," ","_"))` |
| `creator_ig_link` | Profile link to creator's Instagram | `Creator IG Link`, `Profile URL`, `Instagram Profile` | URL String | Source Excel |
| `product` | Full product commercial name | `Product`, `Sept Product`, `Aug Product`, `SKU Name` | String | Source Excel / Normalized |
| `sku_code` | 13-digit product EAN barcode | `SKU CODE`, `Barcode`, `EAN` | String | Source Excel / Normalized (`8904417319637`, etc.) |
| `stage` | Creative format stage | `Stage`, `Format` | String | `IG Reel`, `IG Reel \| BCA`, etc. |
| `epd_npd` | Existing vs New Product status | `EPD/NPD`, `Product Stage` | String | Source Excel |
| `count` | Unit count per creative | `Count`, `Reel Count` | Integer | Source Excel (typically `1`) |
| `range` | Product line range | `Range`, `Brand Range` | String | Source Excel |
| `asset` | Creative asset identifier | `Assest`, `Asset`, `Creative Asset` | String | Source Excel |
| `agency` | Talent management agency | `Agency`, `Talent Agency` | String | Source Excel |
| `gender` | Presenter / Creator gender | `Gender`, `Creator Gender` | String | Source Excel / Verified Audio (`Female`, `Male`, `Couple`, `AI`) |
| `follower_base` | Creator audience size | `Follower base`, `Followers`, `Audience Size` | Integer | Source Excel |
| `tier` | Influencer tiering | `Tier`, `Creator Tier` | String | `Micro`, `Macro`, `Mid-Tier`, `Celebrity` |
| `language` | Spoken language of creative | `Language`, `Spoken Language` | String | `Hinglish`, `English`, `Hindi`, `Telugu`, `Tamil` |
| `genre` | Top-level content genre | `Genre`, `Content Genre` | String | Source Excel |
| `category` | Influencer archetype / category | `Category`, `Influencer Category` | String | `Influencer`, `Dermatologist`, `AI` |
| `planned_er` | Planned / Historical Engagement Rate | `ER`, `Planned ER` | Float (%) | Source Excel |
| `average_views` | Historical 30-day average views | `Average Views`, `Avg Views` | Integer | Source Excel |
| `planned_cpv` | Planned Cost Per View | `CPV`, `Planned CPV` | Float (₹) | `=IF(U2>0, Y2/U2, 0)` |
| `cost` | Base commercial cost | `Cost`, `Base Cost` | Float (₹) | Source Excel |
| `counter` | Commercial counter-offer | `Counter`, `Counter Cost` | Float (₹) | Source Excel |
| `final_costs` | Agreed commercial compensation | `Final Costs`, `Agreed Cost` | Float (₹) | Source Excel |
| `commission` | Agency commission multiplier | `Commission`, `Agency Fee` | Float | Source Excel (e.g., `1.15`) |
| `total_spends` | Total campaign spend incurred | `Total Spends`, `Spend`, `Total Cost` | Float (₹) | `=IF(Z2>0, Y2*Z2, Y2)` |
| `video_status` | Delivery verification status | `Video Status`, `Asset Status` | String | Source Excel (`Live`) |
| `live_link` | Canonical Instagram Reel URL | `Live Link`, `Reel URL`, `Creative Link` | URL String | Normalized: `https://www.instagram.com/reel/{shortcode}/` |
| `live_date` | Timestamp or date of deployment | `Live Date`, `Posting Date` | Date String | Source Excel |
| `views_organic` | Day 0-5 organic views | `Views Day 0-5 (Organic)` | Integer | Source Excel |
| `views_brand_collab` | Day 10 brand collaboration views | `Views Day 10th (Organic - Brand Collab)` | Integer | Primary Performance Metric |
| `video_cpv` | Actual realized Cost Per View | `Video CPV`, `Actual CPV` | Float (₹) | `=IF(AF2>0, AA2/AF2, 0)` |
| `likes` | Realized likes on Instagram | `Likes` | Integer | Source Excel / Scraped |
| `comments` | Realized comments on Instagram | `Comments` | Integer | Source Excel / Scraped |
| `actual_er` | Realized engagement rate | `ER%`, `Actual ER` | Float (%) | `=IF(AF2>0, (AH2+AI2)/AF2, 0)` |
| `concept_bucketing` | Style and creative treatment | `Concept Bucketing`, `Concept Style` | String | `Transformation`, `Problem solution`, `Tutorial`, etc. |
| `bucket` | Normalized macro content bucket | `Bucket`, `Content Bucket` | String | `Problem solution`, `Educational`, `Lifestyle`, etc. |
| `spoken_hook` | Verbatim opening statement | `Spoken Hook`, `Opening Hook` | String | Audio Speech-to-Text Analysis |
| `verified_whole_script`| Full verbatim spoken speech | `Verified Whole Script (Verbatim Speech)` | String | Audio Speech-to-Text Analysis |
| `script_scraping_status`| Status of audio transcription | `Script Scraping Status` | String | `Transcribed from Spoken Audio` / `No spoken speech` / `cant scrap script` |
| `scraped_views` | Live public scraped views | `Scraped Views` | Integer | Instagram Platform Extraction |
| `scraped_likes` | Live public scraped likes | `Scraped Likes` | Integer | Instagram Platform Extraction |
| `scraped_comments` | Live public scraped comments | `Scraped Comments` | Integer | Instagram Platform Extraction |
| `verification_notes` | Provenance and auditing notes | `Verification Notes`, `Audit Notes` | String | Reconciliation notes |

---

### 3. SKU Master Normalization Registry

| SKU Code (EAN Barcode) | Canonical Product Title | Valid Aliases / Keywords |
| :--- | :--- | :--- |
| `8904417319637` | `2% Sali-Cinamide Anti-Acne Face Wash` | `2% Sali-Cinamide Anti-Acne Face Wash - 150 ml`, `Sali-Cinamide`, `Sali Cinamide`, `Anti Acne Face Wash 150ml` |
| `8906087775713` | `1% Hyaluronic Sunscreen Aqua Gel` | `1% Hyaluronic Sunscreen Aqua Gel 50g`, `1% Hyalu Sunscreen`, `HA Sunscreen`, `Hyaluronic Aqua Gel` |
| `8904417306248` | `1% Kojic Acid Face Wash` | `1% Kojic Acid Face Wash 150ml`, `Kojic Acid FW`, `Kojic FW`, `Kojic Face Wash` |
| `8906087775607` | `Benzoyl Peroxide Face Wash` | `TDC- 2.5% Benzoyl Peroxide Gel Face Wash`, `Benzoyl Peroxide`, `BPO Face Wash` |

---

### 4. Summary Table Structures & Dynamic Formulas

Each SKU analytical sheet and the Consolidated sheet contains four standardized side-by-side analytical tables positioned below the data rows:

#### Table 1: Content Bucket Summary (Columns A to F)
- Header: `Bucket`, `SUM of Total Spends`, `SUM of Views Day 10th (Organic - Brand Collab)`, `COUNTA of Count`, `CPV`, `Spends %`
- Row Items: Distinct content buckets (`Problem solution`, `Educational`, `Lifestyle`, `Entertainment`)
- Spends Formula: `=SUMIF($AL$2:$AL$<N>, A<R>, $AA$2:$AA$<N>)`
- Views Formula: `=SUMIF($AL$2:$AL$<N>, A<R>, $AF$2:$AF$<N>)`
- Count Formula: `=COUNTIF($AL$2:$AL$<N>, A<R>)`
- CPV Formula: `=IF(C<R>>0, B<R>/C<R>, 0)`
- Spends % Formula: `=IF(B$<Total>>0, B<R>/B$<Total>, 0)`
- Grand Total Row: `=SUM(...)` for Spends, Views, Count; `=IF(...)` for CPV, Spends %

#### Table 2: Language Summary (Columns H to M)
- Header: `Language`, `SUM of Total Spends`, `SUM of Views Day 10th (Organic - Brand Collab)`, `COUNTA of Count`, `CPV`, `Spends %`
- Spends Formula: `=SUMIF($Q$2:$Q$<N>, H<R>, $AA$2:$AA$<N>)`
- Views Formula: `=SUMIF($Q$2:$Q$<N>, H<R>, $AF$2:$AF$<N>)`
- Count Formula: `=COUNTIF($Q$2:$Q$<N>, H<R>)`
- CPV Formula: `=IF(J<R>>0, I<R>/J<R>, 0)`
- Spends % Formula: `=IF(I$<Total>>0, I<R>/I$<Total>, 0)`

#### Table 3: Category Summary (Columns A to F, below Table 1)
- Header: `Category`, `SUM of Total Spends`, `SUM of Views Day 10th (Organic - Brand Collab)`, `COUNTA of Count`, `CPV`, `Spends %`
- Scoped to Column S (`$S$2:$S$<N>`)

#### Table 4: Gender Summary (Columns H to M, below Table 2)
- Header: `Gender`, `SUM of Total Spends`, `SUM of Views Day 10th (Organic - Brand Collab)`, `COUNTA of Count`, `CPV`, `Spends %`
- Scoped to Column N (`$N$2:$N$<N>`)
