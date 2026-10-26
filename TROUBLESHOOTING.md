# TROUBLESHOOTING.md
## TDC - IM Performance Tracking Agent: Troubleshooting & Diagnostics Guide

### 1. Instagram Session & Authentication Issues

#### Symptom: "Instagram authentication expired. X Reels remain."
- **Root Cause**: Instagram browser `sessionid` cookies typically expire after 30 to 90 days or when logged out in the browser.
- **Remedy**:
  1. Open Chrome or Edge and navigate to [instagram.com](https://www.instagram.com).
  2. Press `F12` to open Developer Tools → Navigate to **Application** (or Storage) tab.
  3. Expand **Cookies** → Click `https://www.instagram.com`.
  4. Find the cookie named **`sessionid`**, copy its alphanumeric value.
  5. In the Agent UI sidebar, expand **Manage Credentials** → Paste into **Instagram sessionid Cookie** → Click **Update Instagram Session**.
  6. Click **Resume**. The agent will immediately continue without reprocessing completed Reels.

---

### 2. Scraping & Network Diagnostics

#### Symptom: Reel marked as "cant scrap script, only caption"
- **Root Cause**: The creator's Reel media could not be fetched due to Instagram CDN temporary throttling, or the Reel is age-restricted / private.
- **System Safeguard**: The agent isolates the failure, preserves the written caption separately, flags the record in the Data Quality audit sheet, and proceeds with the rest of the campaign deliverables without crashing.

#### Symptom: Rate Limiting (HTTP 429)
- **Remedy**: Increase the inter-request throttle in the sidebar (e.g. from 1.5s to 3.0s), or switch the Extraction Engine from `direct` to `apify` (Managed Actor).

---

### 3. Excel Input & Schema Diagnostics

#### Symptom: "Mapping Confidence < 70%" or Column Discrepancy
- **Root Cause**: An uploaded tracker used completely novel column headers (e.g. *"Campaign Expenditure (INR)"* instead of *"Total Spends"*).
- **Remedy**: Verify the column names against `DATA_SCHEMA.md`. The agent supports dozens of common aliases, but critical metrics (Creator, Link, Spends, Views) must have identifiable keywords.

#### Symptom: Discrepancy Flagged in Cross-Sheet Reconciliation
- **Root Cause**: One or more deliverables in the input file had missing or corrupted SKU codes.
- **Remedy**: Check the `Data Quality & Verification` sheet. Unmapped products are grouped into an `Other SKU` sheet to ensure no deliverable is discarded silently.

---

### 4. Cache & Resumption Maintenance

#### Location of Persistent Cache:
`c:\Users\elaya.n\Documents\HONASA TDC\.cache_im_agent\im_cache.db`

#### To Reset or Clear Cache:
- To reprocess an entire workbook from scratch without deleting previous historical data, check the **Force Reprocess All (Bypass Cache)** checkbox in the sidebar.
- To completely purge cached artifacts:
  ```powershell
  Remove-Item -Path "c:\Users\elaya.n\Documents\HONASA TDC\.cache_im_agent\im_cache.db" -Force
  ```
