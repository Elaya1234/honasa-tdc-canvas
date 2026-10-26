import os

# Product and Versioning Metadata
APP_NAME = "TDC - IM Performance Tracking Agent"
APP_VERSION = "1.0.0"
COLLECTOR_VERSION = "1.0.0"
ANALYSIS_VERSION = "1.0.0"
REPORT_TEMPLATE_VERSION = "2026.1"
DEFAULT_MODEL_NAME = "gemini-3.5-flash-lite"

# File System Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IG_COLLECTOR_DIR = os.path.join(BASE_DIR, "ig_reel_collector")
CACHE_DIR = os.path.join(BASE_DIR, ".cache_im_agent")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_reports")

# Automatically load environment credentials from ig_reel_collector/.env and workspace .env
for env_candidate in [os.path.join(IG_COLLECTOR_DIR, ".env"), os.path.join(BASE_DIR, ".env")]:
    if os.path.exists(env_candidate):
        try:
            with open(env_candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Styling Constants for TDC Excel Standard
HEADER_FILL_COLOR = "C9DAF8"      # Soft blue header (#C9DAF8)
SUMMARY_FILL_COLOR = "DFE4EC"     # Soft grey summary header (#DFE4EC)
DATA_ALT_FILL_COLOR = "F8FAFC"    # Very subtle zebra row fill
FONT_FAMILY = "Arial"
HEADER_FONT_SIZE = 8.5
DATA_FONT_SIZE = 8.5
BORDER_COLOR = "D0D7DE"

# Maximum File Sizes & Limits
MAX_MEDIA_FILE_BYTES = 50 * 1024 * 1024  # 50 MB safety threshold
MAX_CONCURRENT_REQUESTS = 2
DEFAULT_REQUEST_DELAY = 1.5              # Seconds between Instagram requests
MAX_RETRIES = 3

# Recognized SKU Master Catalog
CANONICAL_SKU_CATALOG = {
    "8904417319637": {
        "canonical_name": "2% Sali-Cinamide Anti-Acne Face Wash",
        "sheet_title": "2% Sali-Cinamide Face Wash",
        "category": "Facewash",
        "aliases": ["2% sali-cinamide", "sali-cinamide", "sali cinamide", "anti acne face wash", "8904417319637"]
    },
    "8906087775713": {
        "canonical_name": "1% Hyaluronic Sunscreen Aqua Gel",
        "sheet_title": "1% Hyalu Sunscreen Aqua Gel",
        "category": "Sunscreen",
        "aliases": ["1% hyaluronic", "1% hyalu sunscreen", "ha sunscreen", "sunscreen aqua gel", "8906087775713"]
    },
    "8904417306248": {
        "canonical_name": "1% Kojic Acid Face Wash",
        "sheet_title": "1% Kojic Acid Face Wash",
        "category": "Facewash",
        "aliases": ["1% kojic acid", "kojic acid face wash", "kojic fw", "kojic face wash", "8904417306248"]
    },
    "8906087775607": {
        "canonical_name": "Benzoyl Peroxide Face Wash",
        "sheet_title": "Benzoyl Peroxide Face Wash",
        "category": "Facewash",
        "aliases": ["benzoyl peroxide", "2.5% benzoyl", "bpo face wash", "8906087775607"]
    }
}
