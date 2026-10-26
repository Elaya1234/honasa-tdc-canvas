import re
import logging
from typing import Dict, Any, Tuple, Optional
from .config import CANONICAL_SKU_CATALOG

logger = logging.getLogger(__name__)

class SKUNormalizer:
    """
    Deterministic SKU normalization adhering to TDC Master Product Catalog.
    Uses strict 4-tier hierarchy:
    Tier 1: SKU Barcode match (Strongest)
    Tier 2: Exact Product Name match
    Tier 3: Alias / Token match
    Tier 4: Ambiguous / Unmapped
    """

    @classmethod
    def normalize_sku(cls, raw_name: str, raw_code: Optional[str] = None) -> Dict[str, Any]:
        raw_name_clean = str(raw_name or "").strip()
        raw_code_clean = str(raw_code or "").replace(".0", "").strip()

        # Tier 1: Match by exact SKU Code
        if raw_code_clean and raw_code_clean in CANONICAL_SKU_CATALOG:
            meta = CANONICAL_SKU_CATALOG[raw_code_clean]
            return {
                "original_sku": raw_name_clean,
                "normalized_sku": meta["canonical_name"],
                "sheet_title": meta["sheet_title"],
                "sku_code": raw_code_clean,
                "category": meta["category"],
                "normalization_method": "Exact SKU Barcode Match",
                "confidence": "High"
            }

        # Tier 2: Match by exact product name
        for code, meta in CANONICAL_SKU_CATALOG.items():
            if raw_name_clean.lower() == meta["canonical_name"].lower() or raw_name_clean.lower() == meta["sheet_title"].lower():
                return {
                    "original_sku": raw_name_clean,
                    "normalized_sku": meta["canonical_name"],
                    "sheet_title": meta["sheet_title"],
                    "sku_code": code,
                    "category": meta["category"],
                    "normalization_method": "Exact Product Name Match",
                    "confidence": "High"
                }

        # Tier 3: Match by known aliases / keywords
        norm_text = raw_name_clean.lower()
        for code, meta in CANONICAL_SKU_CATALOG.items():
            for alias in meta["aliases"]:
                if alias in norm_text:
                    return {
                        "original_sku": raw_name_clean,
                        "normalized_sku": meta["canonical_name"],
                        "sheet_title": meta["sheet_title"],
                        "sku_code": code,
                        "category": meta["category"],
                        "normalization_method": "Keyword Alias Match",
                        "confidence": "High"
                    }

        # Tier 4: Fallback / Unknown SKU
        safe_sheet_title = re.sub(r'[\\/*?:\[\]]', '', raw_name_clean)[:28] or "Other SKU"
        return {
            "original_sku": raw_name_clean,
            "normalized_sku": raw_name_clean or "Unspecified Product",
            "sheet_title": safe_sheet_title,
            "sku_code": raw_code_clean or "N/A",
            "category": "General",
            "normalization_method": "Unmapped Raw Pass-through",
            "confidence": "Low / Needs Review"
        }
