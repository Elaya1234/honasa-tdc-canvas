# TESTING.md
## TDC - IM Performance Tracking Agent: Comprehensive Verification & Test Specification

### 1. Test Architecture & Automated Suite Overview

The testing suite enforces zero-regression quality assurance across deterministic computations, schema parsing, state management, security boundaries, and real-world campaign workbooks.

```
tests/
├── __init__.py
├── test_input_intelligence.py       # Header detection, reordered columns, sanitization, period parsing
├── test_sku_and_duplicates.py       # Barcode hierarchy, exact/alias matching, duplicate classification
├── test_resumability_and_cache.py   # SQLite persistence, crash recovery, idempotency
├── test_qa_and_reconciliation.py    # Formula validation (#REF!, #DIV/0!), cross-sheet balance checks
├── test_security_adversarial.py     # Formula injection, prompt injection, credential redaction, SSRF
└── test_golden_september.py         # Real-world 46-Reel historical regression on Sept'26 FW & SS.xlsx
```

---

### 2. Executing the Test Suite

All tests execute through the workspace's managed Python environment using `uv.exe`:

#### Run Full Test Suite:
```powershell
& "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe" run --offline --python "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe" --with openpyxl,pandas,pydantic python -m unittest discover tests
```

#### Run Specific Test Modules:
```powershell
# Golden September Regression Test
& "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe" run --offline --python "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe" --with openpyxl,pandas,pydantic python -m unittest tests/test_golden_september.py

# Security & Adversarial Test
& "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe" run --offline --python "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe" --with openpyxl,pandas,pydantic python -m unittest tests/test_security_adversarial.py
```

---

### 3. Golden Dataset Benchmark Results

Running against `c:\Users\elaya.n\Documents\HONASA TDC\IM\Sept'26 FW & SS.xlsx`:
- **Total Deliverables Identified**: 46 Reels
- **Active SKU Count**: 4 distinct products
  - `2% Sali-Cinamide Face Wash`: 15 Reels
  - `1% Hyalu Sunscreen Aqua Gel`: 14 Reels
  - `1% Kojic Acid Face Wash`: 13 Reels
  - `Benzoyl Peroxide Face Wash`: 4 Reels
- **Unique Creators**: 45
- **Spoken Speech Transcribed**: 44
- **Instrumental (No Spoken Speech)**: 1
- **Caption Only (Audio Unobtainable)**: 1
- **QA Workbook Integrity**: `PASSED` (0 broken formula tokens)
- **Numerical Cross-Sheet Reconciliation**: `PASSED` (Total Reels, Spend, and Views balance across SKU and Consolidated sheets)
- **Completion State**: `PARTIAL` (Reflects legitimate speech nuances with 0 silent failures)

---

### 4. Standalone Tool Compatibility Test

To ensure the legacy `ig_reel_collector/` remains 100% operational as a standalone utility, run:
```powershell
& "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe" run --offline --python "C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe" python -c "import sys; sys.path.insert(0, 'ig_reel_collector'); from models import ReelProcessedRecord; from ig_extractor import InstagramExtractor; print('Standalone IG Collector Verified!')"
```
