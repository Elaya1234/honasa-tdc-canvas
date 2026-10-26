import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import CanonicalRow

MONTH_MAP = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "may": "May", "jun": "June", "jul": "July", "aug": "August",
    "sep": "September", "sept": "September", "oct": "October",
    "nov": "November", "dec": "December"
}

class PeriodDetector:
    """
    Intelligently identifies reporting time periods (Monthly, Quarterly, Yearly, Custom)
    without forcing users to answer unnecessary questions.
    """

    @staticmethod
    def detect_period(file_path: str, rows: List[CanonicalRow], sheet_name: Optional[str] = None) -> Dict[str, Any]:
        filename = os.path.basename(file_path).lower()
        sheet_str = (sheet_name or "").lower().strip()
        
        detected_label = ""
        period_type = "Monthly"

        # 0. Check sheet_name if provided
        if sheet_name == "__ALL_CAMPAIGNS__":
            detected_label = "Full Year 2026 (Consolidated)"
            period_type = "Yearly"
        elif sheet_str:
            if "amjja" in sheet_str:
                detected_label = "April - August 2026"
                period_type = "Custom"
            else:
                m_match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[\s'_]*([0-9]{2,4})?", sheet_str)
                if m_match:
                    m_key = m_match.group(1)
                    m_name = MONTH_MAP.get(m_key, m_key.capitalize())
                    yr = m_match.group(2) or "26"
                    yr_full = f"20{yr}" if len(yr) == 2 else yr
                    detected_label = f"{m_name} {yr_full}"
                    period_type = "Monthly"

        # 1. Check filename patterns if not detected from sheet
        if not detected_label:
            # Pattern like: Sept'26 or Sep 2026 or Aug'26
            month_match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[\s'_]*([0-9]{2,4})", filename)
            quarter_match = re.search(r"(q[1-4])[\s'_]*([0-9]{2,4})", filename)
            year_match = re.search(r"(fy|20)([0-9]{2,4})", filename)

            if quarter_match:
                q_num = quarter_match.group(1).upper()
                yr = quarter_match.group(2)
                yr_full = f"20{yr}" if len(yr) == 2 else yr
                detected_label = f"{q_num} {yr_full}"
                period_type = "Quarterly"
            elif month_match:
                m_key = month_match.group(1)
                m_name = MONTH_MAP.get(m_key, m_key.capitalize())
                yr = month_match.group(2)
                yr_full = f"20{yr}" if len(yr) == 2 else yr
                detected_label = f"{m_name} {yr_full}"
                period_type = "Monthly"
        
        # 2. Inspect date values from records
        parsed_dates: List[datetime] = []
        for r in rows:
            d_str = r.live_date or ""
            if not d_str:
                continue
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
                try:
                    parsed_dates.append(datetime.strptime(str(d_str).split()[0], fmt))
                    break
                except ValueError:
                    pass

        if parsed_dates and not detected_label:
            min_date = min(parsed_dates)
            max_date = max(parsed_dates)
            if min_date.month == max_date.month and min_date.year == max_date.year:
                m_name = min_date.strftime("%B")
                detected_label = f"{m_name} {min_date.year}"
                period_type = "Monthly"
            else:
                detected_label = f"{min_date.strftime('%d-%b-%Y')} to {max_date.strftime('%d-%b-%Y')}"
                period_type = "Custom"

        if not detected_label:
            detected_label = "Campaign Period 2026"
            period_type = "General"

        return {
            "period_label": detected_label,
            "period_type": period_type,
            "confidence": "High" if detected_label != "Campaign Period 2026" else "Medium",
            "date_count": len(parsed_dates)
        }
