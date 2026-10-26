import re
from typing import List, Dict, Tuple, Any
from .models import CanonicalRow, DuplicateType

def extract_shortcode(url: str) -> str:
    """Extracts shortcode from Instagram link."""
    clean = str(url or "").strip()
    match = re.search(r"(?:reel|p|reels)/([A-Za-z0-9_-]+)", clean)
    return match.group(1) if match else ""

def normalize_url(url: str) -> str:
    """Normalizes URL to standard canonical format."""
    sc = extract_shortcode(url)
    if sc:
        return f"https://www.instagram.com/reel/{sc}/"
    return str(url or "").strip()

class ReelDiscovery:
    """
    Handles Reel URL discovery, extraction, normalization, and duplicate classification.
    Adheres strictly to the rule: NEVER silently drop duplicates.
    """

    @classmethod
    def process_records(cls, rows: List[CanonicalRow]) -> Tuple[List[CanonicalRow], Dict[str, Any]]:
        seen_shortcodes: Dict[str, List[int]] = {}
        seen_urls: Dict[str, List[int]] = {}

        for idx, r in enumerate(rows):
            sc = extract_shortcode(r.live_link)
            norm = normalize_url(r.live_link)
            r.shortcode = sc
            r.normalized_url = norm

            if sc:
                seen_shortcodes.setdefault(sc, []).append(idx)
            if norm:
                seen_urls.setdefault(norm, []).append(idx)

        exact_dupes = 0
        possible_dupes = 0
        reuse_dupes = 0

        for sc, indices in seen_shortcodes.items():
            if len(indices) > 1:
                # Multiple rows with identical shortcode
                first_idx = indices[0]
                first_creator = rows[first_idx].creator.strip().lower()
                first_sku = rows[first_idx].sku_code

                for dup_idx in indices[1:]:
                    curr_creator = rows[dup_idx].creator.strip().lower()
                    curr_sku = rows[dup_idx].sku_code
                    if curr_creator == first_creator and curr_sku == first_sku:
                        rows[dup_idx].duplicate_type = DuplicateType.EXACT_DUPLICATE
                        rows[dup_idx].verification_notes += f"Exact duplicate of Row {rows[first_idx].source_row}; "
                        exact_dupes += 1
                    elif curr_creator == first_creator and curr_sku != first_sku:
                        rows[dup_idx].duplicate_type = DuplicateType.INTENTIONAL_REUSE
                        rows[dup_idx].verification_notes += f"Intentional creative reuse across SKUs (Row {rows[first_idx].source_row}); "
                        reuse_dupes += 1
                    else:
                        rows[dup_idx].duplicate_type = DuplicateType.POSSIBLE_DUPLICATE
                        rows[dup_idx].verification_notes += f"Possible duplicate Reel with Row {rows[first_idx].source_row}; "
                        possible_dupes += 1

        stats = {
            "total_records": len(rows),
            "unique_reels": len(seen_shortcodes),
            "exact_duplicates": exact_dupes,
            "possible_duplicates": possible_dupes,
            "intentional_reuse": reuse_dupes
        }
        return rows, stats
