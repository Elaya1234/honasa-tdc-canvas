# CHANGELOG.md
## TDC - IM Performance Tracking Agent: Release & Revision History

### [1.0.0] - 2026-10-08 — Production Release

#### Added
- **Standalone Compatibility Preservation**: Kept `ig_reel_collector/` 100% operational as an independent utility on `Launch_IG_Collector.bat` without modifying internal source files.
- **Orchestration Layer (`tdc_im_agent`)**:
  - `input_intelligence.py`: Two-pass exact and tokenized column mapper with CSV/Excel formula injection sanitization.
  - `period_detector.py`: Automatic timeline inferencer supporting Monthly, Quarterly, Yearly, and Custom date ranges.
  - `sku_normalizer.py`: 4-tier deterministic SKU matcher grounded in TDC master product barcode catalog (`8904417319637`, `8906087775713`, `8904417306248`, `8906087775607`).
  - `reel_discovery.py`: URL parser, shortcode normalizer, and duplicate classifier (`EXACT_DUPLICATE`, `POSSIBLE_DUPLICATE`, `INTENTIONAL_REUSE`).
  - `collector_adapter.py`: Circuit-breaking extraction wrapper with bounded exponential backoff, rate limiting, and session state tracking.
  - `verification_engine.py`: Strict enforcement of Spoken Script vs Caption with auditable `Script Scraping Status` assignment.
  - `analytics_engine.py`: 100% deterministic arithmetic engine computing spends, views, CPVs, ERs, dimensional pivot tables, and non-causal statistical correlations.
  - `report_generator.py`: OpenPyXL workbook architect producing standardized TDC Excel reports with Executive Summary, Consolidated sheet, individual SKU sheets, Data Quality sheet, and Processing Log.
  - `qa_validator.py`: Independent post-generation inspection gate checking XML health, formula validity, and cross-sheet numerical balancing.
  - `cache_manager.py`: Thread-safe, versioned SQLite caching engine guaranteeing instant crash resumption and idempotency.
  - `app.py`: Streamlit user interface deployed on port 8504 featuring one-click recommended analysis and real-time execution tracking.
  - `cli.py`: Command-line interface for batch processing and automated pipelines.
  - `Launch_TDC_IM_Agent.bat`: 1-click Windows desktop launcher with automatic port check and browser launch.
- **Documentation Suite**:
  - `ARCHITECTURE.md`: Complete system architecture and component designs.
  - `THREAT_MODEL.md`: Security analysis, prompt injection defense, and DPDPA compliance.
  - `DATA_SCHEMA.md`: Canonical schema, aliases, and source-of-truth hierarchy.
  - `USER_GUIDE.md`: Step-by-step user manual and KPI definitions.
  - `TROUBLESHOOTING.md`: Incident resolution and maintenance workflows.
  - `TESTING.md`: Verification protocols and benchmark results.
- **Automated Test Suite**:
  - 16 comprehensive unit, security, adversarial, and golden dataset regression tests in `tests/`, verified at 100% pass rate.
