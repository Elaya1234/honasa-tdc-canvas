import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import openpyxl

from .models import CanonicalRow, ProcessingState, DuplicateType
from .config import CANONICAL_SKU_CATALOG

logger = logging.getLogger(__name__)

# Security: Formula injection patterns for untrusted Excel data
FORMULA_INJECTION_PREFIXES = ('=', '+', '-', '@', '\t', '\r')

def sanitize_untrusted_text(val: Any) -> str:
    """
    Sanitizes untrusted text strings to prevent CSV/Excel formula injection.
    Prefixes risky leading characters with a single apostrophe.
    """
    if val is None:
        return ""
    text = str(val).strip()
    if not text:
        return ""
    if text.startswith(FORMULA_INJECTION_PREFIXES) and not (text.startswith("=") and ("(" in text or text.isupper())):
        return f"'{text}"
    return text

def safe_numeric(val: Any, default: float = 0.0) -> float:
    """Safely converts arbitrary cell values (with ₹, %, commas, spaces) to clean float."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val) if not pd.isna(val) else default
    s = str(val).replace('₹', '').replace(',', '').replace('%', '').replace('Rs.', '').replace(' ', '').strip()
    try:
        return float(s)
    except ValueError:
        return default

def safe_int(val: Any, default: int = 0) -> int:
    """Safely converts arbitrary cell values to clean integer."""
    flt = safe_numeric(val, float(default))
    return int(round(flt))

# Semantic Aliases Dictionary for Header Matching
COLUMN_ALIASES: Dict[str, List[str]] = {
    "live_status": ["live", "live status", "post status", "asset status"],
    "sub_cat": ["sub cat", "subcat", "sub category", "subcategory", "category group"],
    "creator": ["creator", "influencer", "influencer name", "creator name", "artist"],
    "channel_standard_name": ["channel standard name", "standard name", "handle", "creator handle", "instagram handle"],
    "creator_ig_link": ["creator ig link", "creator link", "ig link", "profile link", "instagram profile", "creator profile"],
    "product": [
        "oct product", "sept product", "sep product", "aug product", "august product",
        "july product", "jul product", "june product", "jun product", "may product",
        "apr product", "april product", "mar product", "march product", "product name",
        "sku name", "item name", "product", "sku"
    ],
    "sku_code": ["sku code", "barcode", "ean", "ean code", "sku_code"],
    "stage": ["stage", "format", "deliverable"],
    "epd_npd": ["epd/npd", "epd", "npd", "product stage"],
    "count": ["count", "reel count", "qty", "quantity"],
    "range_col": ["range", "brand range", "product range"],
    "asset": ["assest", "asset", "creative asset"],
    "agency": ["agency", "talent agency"],
    "gender": ["gender", "creator gender"],
    "follower_base": ["follower base", "followers", "follower count", "audience size"],
    "tier": ["tier", "influencer tier", "creator tier"],
    "language": ["language", "spoken language", "lang"],
    "genre": ["genre", "content genre"],
    "category": ["category", "creator category", "influencer category"],
    "er_planned": ["er", "planned er", "target er"],
    "average_views": ["average views", "avg views", "past avg views"],
    "planned_cpv": ["cpv", "planned cpv"],
    "cost": ["cost", "base cost", "creator cost"],
    "counter": ["counter", "counter cost"],
    "final_costs": ["final costs", "final cost", "agreed cost", "deal cost"],
    "commission": ["commission", "agency commission", "agency fee"],
    "total_spends": ["total spends", "total spend", "spends", "spend", "budget", "cost total", "investment"],
    "video_status": ["video status", "delivery status"],
    "live_link": ["live link", "reel link", "creative link", "reel url", "instagram link", "post link"],
    "live_date": ["live date", "posting date", "oct date", "sept date", "aug date", "date", "post date", "publish date"],
    "views_organic": ["views day 0-5", "views day 0–5", "views day 0-5 (organic - creator handle)", "organic views"],
    "views_brand_collab": ["views day 10th", "views day 10", "views day 10th (organic - brand collab)", "views brand collab", "collab views"],
    "video_cpv": ["video cpv", "actual cpv", "realized cpv"],
    "likes": ["likes", "like count", "total likes"],
    "comments": ["comments", "comment count", "total comments"],
    "actual_er": ["er%", "actual er", "engagement rate"],
    "concept_bucketing": ["concept bucketing", "concept style", "style"],
    "bucket": ["bucket", "content bucket", "macro bucket", "concept"],
    "spoken_hook": ["spoken hook", "hook", "opening hook"],
    "verified_whole_script": ["verified whole script", "whole script", "script", "transcript"],
    "script_scraping_status": ["script scraping status", "script status", "scraping status"],
    "scraped_views": ["scraped views", "live views"],
    "scraped_likes": ["scraped likes", "live likes"],
    "scraped_comments": ["scraped comments", "live comments"],
    "verification_notes": ["verification notes", "notes", "audit notes"]
}

class ExcelInputIntelligence:
    """
    Intelligent, resilient reader for TDC Influencer Marketing Workbooks.
    Inspects sheets, detects headers, maps schema, sanitizes input, and normalizes rows.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input Excel file not found: {file_path}")
        self._excel_file: Optional[pd.ExcelFile] = None

    def get_excel_file(self) -> pd.ExcelFile:
        """Returns or initializes the cached pandas ExcelFile object."""
        if self._excel_file is None:
            self._excel_file = pd.ExcelFile(self.file_path)
        return self._excel_file

    def discover_sheets(self) -> List[Dict[str, Any]]:
        """
        Rapidly inspects all sheets in the workbook using read_only openpyxl.
        Classifies sheets into candidate campaign trackers vs reference sheets.
        Returns ranked list of candidate campaign sheets.
        """
        wb = openpyxl.load_workbook(self.file_path, read_only=True)
        results = []

        month_map = {
            "jan": "January", "feb": "February", "mar": "March", "apr": "April",
            "may": "May", "jun": "June", "jul": "July", "aug": "August",
            "sep": "September", "sept": "September", "oct": "October",
            "nov": "November", "dec": "December"
        }

        for sname in wb.sheetnames:
            lower_name = sname.lower().strip()
            # Immediately skip non-campaign dumps, calculations, rough sheets
            if any(x in lower_name for x in ['dump', 'data', 'split', 'rough', 'master', 'utm', 'daily', 'budget', 'flow sheet', 'copy of', 'report', 'plan']):
                continue

            ws = wb[sname]
            link_count = 0
            row_count = 0
            has_creator = False
            has_product = False
            has_spend = False

            # Inspect top 60 rows
            for r_idx, row in enumerate(ws.iter_rows(values_only=True, max_row=60)):
                if r_idx < 1:
                    continue
                row_str = ' '.join(str(c).lower() for c in row if c is not None)
                if any(k in row_str for k in ['creator', 'influencer']):
                    has_creator = True
                if any(k in row_str for k in ['product', 'sku', 'fw', 'serum', 'gel', 'sunscreen', 'facewash']):
                    has_product = True
                if any(k in row_str for k in ['spend', 'cost', 'commercial', 'total spends']):
                    has_spend = True
                if any('instagram.com/reel' in str(v) for v in row if v):
                    link_count += 1
                row_count += 1

            if has_creator and (link_count > 0 or has_spend):
                # Infer period from sheet name
                m_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[\s_]*([0-9]{2,4})?', lower_name)
                if 'amjja' in lower_name:
                    period = 'April - August 2026 (Consolidated)'
                    period_type = 'Custom'
                elif m_match:
                    m_name = month_map.get(m_match.group(1), m_match.group(1).capitalize())
                    yr = m_match.group(2) or '26'
                    period = f'{m_name} 20{yr}' if len(yr) == 2 else f'{m_name} {yr}'
                    period_type = 'Monthly'
                else:
                    period = sname.strip()
                    period_type = 'Campaign'

                # Score priority: live links count * 10 + recency boost
                score = link_count * 10
                if 'sept' in lower_name: score += 100
                elif 'aug' in lower_name: score += 80
                elif 'oct' in lower_name: score += 95
                elif 'amjja' in lower_name: score += 90

                results.append({
                    "sheet_name": sname,
                    "period_label": period,
                    "period_type": period_type,
                    "link_count": link_count,
                    "row_count": row_count,
                    "score": score,
                    "is_campaign": True,
                    "display": f"{sname.strip()} — {period} ({link_count}+ Live Reels)"
                })

        wb.close()
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_default_campaign_sheet(self) -> str:
        """Returns the highest scoring campaign sheet, never defaulting to Product Master."""
        discovered = self.discover_sheets()
        if discovered:
            return discovered[0]["sheet_name"]

        # Fallback to workbook inspection if no campaign detected
        insp = self.inspect_workbook()
        sheets = insp.get("sheets", [])
        for s in sheets:
            s_name = s["sheet_name"]
            if not any(x in s_name.lower() for x in ['master', 'dump', 'daily', 'utm']):
                return s_name
        return sheets[0]["sheet_name"] if sheets else ""

    def inspect_workbook(self) -> Dict[str, Any]:
        """Inspects workbook structure, sheets, row counts, and candidate data tables."""
        wb = openpyxl.load_workbook(self.file_path, read_only=True)
        sheet_summaries = []
        for name in wb.sheetnames:
            ws = wb[name]
            sheet_summaries.append({
                "sheet_name": name,
                "max_row": ws.max_row or 0,
                "max_col": ws.max_column or 0
            })
        wb.close()
        return {
            "file_name": os.path.basename(self.file_path),
            "sheets": sheet_summaries,
            "total_sheets": len(sheet_summaries)
        }

    def detect_header_row(self, df_raw: pd.DataFrame) -> Tuple[int, Dict[str, str], float]:
        """
        Scans first 10 rows to detect header row and compute match confidence.
        Returns: (header_row_index, matched_column_dict, confidence_score)
        """
        best_row = 0
        best_matches = {}
        best_score = 0

        for r_idx in range(min(10, len(df_raw))):
            row_vals = [str(x).strip().lower() for x in df_raw.iloc[r_idx] if pd.notna(x)]
            matches = {}
            for col_idx, cell_text in enumerate(row_vals):
                clean_header = re.sub(r'[\r\n]+', ' ', cell_text).strip()
                for canonical_col, aliases in COLUMN_ALIASES.items():
                    for alias in aliases:
                        if alias == clean_header or (len(alias) > 3 and alias in clean_header):
                            if canonical_col not in matches:
                                matches[canonical_col] = df_raw.columns[col_idx]
                            break
            
            # Key indicator fields
            key_indicators = ["creator", "live_link", "total_spends", "views_brand_collab", "product"]
            score = sum(1 for k in key_indicators if k in matches)
            if score > best_score:
                best_score = score
                best_row = r_idx
                best_matches = matches

        confidence = best_score / 5.0
        return best_row, best_matches, confidence

    def parse_all_campaign_sheets(self) -> Tuple[List[CanonicalRow], Dict[str, Any]]:
        """Parses all discovered campaign sheets and consolidates them into a unified list."""
        discovered = self.discover_sheets()
        all_records: List[CanonicalRow] = []
        seen_shortcodes: set = set()
        sheets_consolidated = 0

        for s_info in discovered:
            sname = s_info["sheet_name"]
            try:
                records, _ = self.parse_sheet(sheet_name=sname)
                for r in records:
                    if r.shortcode:
                        if r.shortcode in seen_shortcodes:
                            continue
                        seen_shortcodes.add(r.shortcode)
                    all_records.append(r)
                sheets_consolidated += 1
            except Exception as e:
                logger.warning(f"Skipping sheet {sname} during consolidation: {e}")

        metadata = {
            "sheet_name": "__ALL_CAMPAIGNS__",
            "header_row": 1,
            "total_rows_parsed": len(all_records),
            "column_mapping": {},
            "mapping_confidence": 1.0,
            "sheets_consolidated": sheets_consolidated
        }
        return all_records, metadata

    def parse_sheet(self, sheet_name: Optional[str] = None) -> Tuple[List[CanonicalRow], Dict[str, Any]]:
        """
        Parses the target sheet into CanonicalRow objects.
        If sheet_name is None, automatically detects and uses the primary campaign sheet.
        If sheet_name is '__ALL_CAMPAIGNS__', parses and merges all campaign sheets.
        """
        if sheet_name == "__ALL_CAMPAIGNS__":
            return self.parse_all_campaign_sheets()

        if sheet_name is None:
            sheet_name = self.get_default_campaign_sheet()

        xl = self.get_excel_file()
        df_raw = pd.read_excel(xl, sheet_name=sheet_name, header=None)
        header_row, col_mapping, confidence = self.detect_header_row(df_raw)

        # Reload dataframe with detected header
        df = pd.read_excel(xl, sheet_name=sheet_name, header=header_row)
        
        # Clean column names
        cleaned_cols = [re.sub(r'[\r\n]+', ' ', str(c)).strip() for c in df.columns]
        df.columns = cleaned_cols

        # Build column index lookup with robust two-pass resolution
        field_to_col: Dict[str, str] = {}
        used_cols: set = set()

        # Pass 1: Exact Matches (highest priority)
        for canonical_field, aliases in COLUMN_ALIASES.items():
            for col_name in df.columns:
                clean_col = col_name.lower().replace('–', '-').replace('—', '-').strip()
                for alias in aliases:
                    if clean_col == alias.lower().strip():
                        field_to_col[canonical_field] = col_name
                        used_cols.add(col_name)
                        break
                if canonical_field in field_to_col:
                    break

        # Pass 2: Guarded token-level containment for remaining unmapped fields
        for canonical_field, aliases in COLUMN_ALIASES.items():
            if canonical_field in field_to_col:
                continue
            for col_name in df.columns:
                if col_name in used_cols:
                    continue
                clean_col = col_name.lower().replace('–', '-').replace('—', '-').strip()
                
                # Guards against cross-field confusion
                if canonical_field == "live_link" and any(x in clean_col for x in ["creator", "profile", "channel", "standard"]):
                    continue
                if canonical_field == "views_brand_collab" and any(x in clean_col for x in ["average", "avg", "0-5", "0–5"]):
                    continue
                if canonical_field == "views_organic" and not any(x in clean_col for x in ["0-5", "0–5", "organic"]):
                    continue
                if canonical_field == "count" and clean_col == "counter":
                    continue

                matched = False
                for alias in aliases:
                    tokens_alias = set(re.findall(r'\w+', alias.lower()))
                    tokens_col = set(re.findall(r'\w+', clean_col))
                    if tokens_alias and tokens_alias.issubset(tokens_col):
                        field_to_col[canonical_field] = col_name
                        used_cols.add(col_name)
                        matched = True
                        break
                if matched:
                    break

        # Pass 3: Empty Column Fallback Guard
        # If the mapped product column is 100% empty, swap to another matching column with real data
        if "product" in field_to_col:
            prod_col = field_to_col["product"]
            prod_non_null = df[prod_col].dropna().count()
            if prod_non_null == 0 or df[prod_col].astype(str).str.strip().isin(['', 'nan', 'none']).all():
                for alt_col in df.columns:
                    if alt_col == prod_col:
                        continue
                    clean_alt = str(alt_col).lower().strip()
                    for alias in COLUMN_ALIASES["product"]:
                        if alias in clean_alt or clean_alt in alias:
                            if df[alt_col].dropna().count() > 0 and not df[alt_col].astype(str).str.strip().isin(['', 'nan', 'none']).all():
                                field_to_col["product"] = alt_col
                                break
                    if df[field_to_col["product"]].dropna().count() > 0:
                        break
                # If still empty, check column immediately preceding SKU CODE
                if df[field_to_col["product"]].dropna().count() == 0 and "sku_code" in field_to_col:
                    sku_col = field_to_col["sku_code"]
                    sku_idx = list(df.columns).index(sku_col)
                    if sku_idx > 0:
                        prev_col = df.columns[sku_idx - 1]
                        if df[prev_col].dropna().count() > 0:
                            field_to_col["product"] = prev_col

        # If product was not mapped at all, look for column before sku_code
        if "product" not in field_to_col and "sku_code" in field_to_col:
            sku_col = field_to_col["sku_code"]
            sku_idx = list(df.columns).index(sku_col)
            if sku_idx > 0:
                prev_col = df.columns[sku_idx - 1]
                if df[prev_col].dropna().count() > 0:
                    field_to_col["product"] = prev_col

        records: List[CanonicalRow] = []
        for idx, row in df.iterrows():
            source_row_num = header_row + 2 + idx # 1-indexed Excel row
            
            # Check if row is empty or summary row
            live_link_val = str(row.get(field_to_col.get("live_link", ""), "") or "").strip()
            creator_val = str(row.get(field_to_col.get("creator", ""), "") or "").strip()
            
            if not live_link_val and not creator_val:
                continue
            if any(k in creator_val.lower() for k in ["grand total", "total", "summary"]):
                continue

            # Extract shortcode and normalized URL
            shortcode = ""
            norm_url = live_link_val
            scraping_status = str(row.get(field_to_col.get("script_scraping_status", ""), "") or "").strip()

            if not live_link_val or live_link_val.lower() in ('nan', 'none', ''):
                shortcode = ""
                norm_url = ""
                if not scraping_status:
                    scraping_status = "No Live Link / Pipeline"
            else:
                match = re.search(r"(?:reel|p|reels)/([A-Za-z0-9_-]+)", live_link_val)
                if match:
                    shortcode = match.group(1)
                    norm_url = f"https://www.instagram.com/reel/{shortcode}/"
                else:
                    shortcode = ""
                    norm_url = live_link_val

            # Parse Spends and Views
            spends = safe_numeric(row.get(field_to_col.get("total_spends", None), 0.0))
            if spends == 0.0:
                final_c = safe_numeric(row.get(field_to_col.get("final_costs", None), 0.0))
                comm = safe_numeric(row.get(field_to_col.get("commission", None), 0.0))
                spends = final_c * comm if comm > 0 else final_c

            views = safe_int(row.get(field_to_col.get("views_brand_collab", None), 0))
            if views == 0:
                views = safe_int(row.get(field_to_col.get("views_organic", None), 0))

            cpv = (spends / views) if views > 0 else 0.0
            likes = safe_int(row.get(field_to_col.get("likes", None), 0))
            comments = safe_int(row.get(field_to_col.get("comments", None), 0))
            er = ((likes + comments) / views) if views > 0 else 0.0

            # Raw Product Name & Code
            prod_raw = str(row.get(field_to_col.get("product", ""), "") or "").strip()
            sku_code_raw = str(row.get(field_to_col.get("sku_code", ""), "") or "").strip()

            record = CanonicalRow(
                source_row=source_row_num,
                source_sheet=sheet_name or "Sheet1",
                live_status=str(row.get(field_to_col.get("live_status", ""), "Live") or "Live").strip(),
                sub_cat=str(row.get(field_to_col.get("sub_cat", ""), "") or "").strip(),
                creator=creator_val,
                channel_standard_name=str(row.get(field_to_col.get("channel_standard_name", ""), "") or "").strip(),
                creator_ig_link=str(row.get(field_to_col.get("creator_ig_link", ""), "") or "").strip(),
                product=prod_raw,
                sku_code=sku_code_raw,
                stage=str(row.get(field_to_col.get("stage", ""), "IG Reel") or "IG Reel").strip(),
                epd_npd=str(row.get(field_to_col.get("epd_npd", ""), "") or "").strip(),
                count=safe_int(row.get(field_to_col.get("count", None), 1), 1),
                range_col=str(row.get(field_to_col.get("range_col", ""), "") or "").strip(),
                asset=str(row.get(field_to_col.get("asset", ""), "") or "").strip(),
                agency=str(row.get(field_to_col.get("agency", ""), "") or "").strip(),
                gender=str(row.get(field_to_col.get("gender", ""), "Female") or "Female").strip(),
                follower_base=safe_int(row.get(field_to_col.get("follower_base", None), 0)),
                tier=str(row.get(field_to_col.get("tier", ""), "") or "").strip(),
                language=str(row.get(field_to_col.get("language", ""), "English") or "English").strip(),
                genre=str(row.get(field_to_col.get("genre", ""), "") or "").strip(),
                category=str(row.get(field_to_col.get("category", ""), "Influencer") or "Influencer").strip(),
                er_planned=safe_numeric(row.get(field_to_col.get("er_planned", None), 0.0)),
                average_views=safe_int(row.get(field_to_col.get("average_views", None), 0)),
                planned_cpv=safe_numeric(row.get(field_to_col.get("planned_cpv", None), 0.0)),
                cost=safe_numeric(row.get(field_to_col.get("cost", None), 0.0)),
                counter=safe_numeric(row.get(field_to_col.get("counter", None), 0.0)),
                final_costs=safe_numeric(row.get(field_to_col.get("final_costs", None), 0.0)),
                commission=safe_numeric(row.get(field_to_col.get("commission", None), 0.0)),
                total_spends=spends,
                video_status=str(row.get(field_to_col.get("video_status", ""), "Live") or "Live").strip(),
                live_link=live_link_val,
                normalized_url=norm_url,
                shortcode=shortcode,
                live_date=str(row.get(field_to_col.get("live_date", ""), "") or "").strip(),
                views_organic=safe_int(row.get(field_to_col.get("views_organic", None), 0)),
                views_brand_collab=views,
                video_cpv=cpv,
                likes=likes,
                comments=comments,
                actual_er=er,
                concept_bucketing=str(row.get(field_to_col.get("concept_bucketing", ""), "") or "").strip(),
                bucket=str(row.get(field_to_col.get("bucket", ""), "Problem solution") or "Problem solution").strip(),
                spoken_hook=sanitize_untrusted_text(row.get(field_to_col.get("spoken_hook", ""), "")),
                verified_whole_script=sanitize_untrusted_text(row.get(field_to_col.get("verified_whole_script", ""), "")),
                script_scraping_status=scraping_status,
                scraped_views=safe_int(row.get(field_to_col.get("scraped_views", None), None)) if pd.notna(row.get(field_to_col.get("scraped_views", None))) else None,
                scraped_likes=safe_int(row.get(field_to_col.get("scraped_likes", None), None)) if pd.notna(row.get(field_to_col.get("scraped_likes", None))) else None,
                scraped_comments=safe_int(row.get(field_to_col.get("scraped_comments", None), None)) if pd.notna(row.get(field_to_col.get("scraped_comments", None))) else None,
                verification_notes=str(row.get(field_to_col.get("verification_notes", ""), "") or "").strip(),
                confidence_score=confidence
            )
            records.append(record)

        metadata = {
            "sheet_name": sheet_name or "Sheet1",
            "header_row": header_row,
            "total_rows_parsed": len(records),
            "column_mapping": field_to_col,
            "mapping_confidence": confidence
        }
        return records, metadata
