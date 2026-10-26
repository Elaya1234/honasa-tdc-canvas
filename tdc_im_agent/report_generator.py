import os
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any, Optional

from .config import (
    HEADER_FILL_COLOR, SUMMARY_FILL_COLOR, DATA_ALT_FILL_COLOR,
    FONT_FAMILY, HEADER_FONT_SIZE, DATA_FONT_SIZE, BORDER_COLOR
)
from .models import CanonicalRow, DataQualityRecord, ProcessingLogRecord
from .sku_normalizer import SKUNormalizer

EXCEL_COLUMNS_45 = [
    "Live",
    "Sub Cat",
    "Creator",
    "Channel Standard Name",
    "Creator IG Link",
    "Product",
    "SKU CODE",
    "Stage",
    "EPD/NPD",
    "Count",
    "Range",
    "Assest",
    "Agency",
    "Gender",
    "Follower base",
    "Tier",
    "Language",
    "Genre",
    "Category",
    "ER",
    "Average Views",
    "CPV",
    "Cost",
    "Counter",
    "Final Costs",
    "Commission",
    "Total Spends",
    "Video Status",
    "Live Link",
    "Live Date",
    "Views Day 0-5 (Organic)",
    "Views Day 10th (Organic - Brand Collab)",
    "Video CPV",
    "Likes",
    "Comments",
    "ER%",
    "Concept Bucketing",
    "Bucket",
    "Spoken Hook",
    "Verified Whole Script (Verbatim Speech)",
    "Script Scraping Status",
    "Scraped Views",
    "Scraped Likes",
    "Scraped Comments",
    "Verification Notes"
]

class TDCReportGenerator:
    """
    Generates standardized, formula-rich, visually compliant Excel workbooks
    matching the official The Derma Co Influencer Marketing analytical standard.
    """

    def __init__(self, period_label: str = "Campaign Period 2026"):
        self.period_label = period_label
        self.wb = openpyxl.Workbook()
        # Remove default sheet
        self.wb.remove(self.wb.active)

        # Style objects
        self.header_font = Font(name=FONT_FAMILY, size=HEADER_FONT_SIZE, bold=True, color="000000")
        self.header_fill = PatternFill(start_color=HEADER_FILL_COLOR, end_color=HEADER_FILL_COLOR, fill_type="solid")
        self.summary_fill = PatternFill(start_color=SUMMARY_FILL_COLOR, end_color=SUMMARY_FILL_COLOR, fill_type="solid")
        self.body_font = Font(name=FONT_FAMILY, size=DATA_FONT_SIZE, bold=False, color="000000")
        self.body_bold_font = Font(name=FONT_FAMILY, size=DATA_FONT_SIZE, bold=True, color="000000")
        
        self.thin_border = Border(
            left=Side(style="thin", color=BORDER_COLOR),
            right=Side(style="thin", color=BORDER_COLOR),
            top=Side(style="thin", color=BORDER_COLOR),
            bottom=Side(style="thin", color=BORDER_COLOR)
        )

    def _sanitize_cell_value(self, val: Any) -> Any:
        if val is None:
            return ""
        if isinstance(val, (int, float)):
            return val
        s = str(val)
        if s.startswith(('+', '-', '@')) or (s.startswith('=') and not (s.startswith('=IF(') or s.startswith('=SUM(') or s.startswith('=LOWER(') or s.startswith('=COUNTIF(') or s.startswith('=SUMIF('))):
            return f"'{s}"
        return s

    def build_full_workbook(
        self,
        rows: List[CanonicalRow],
        dq_records: List[DataQualityRecord],
        log_records: List[ProcessingLogRecord],
        exec_summary_metrics: Dict[str, Any],
        output_path: str
    ):
        # 1. Executive Summary Sheet
        self._create_executive_summary_sheet(rows, exec_summary_metrics)

        # 2. Consolidated All SKUs Sheet
        self._create_data_and_summary_sheet("Consolidated All SKUs", rows)

        # 3. Individual SKU Sheets
        sku_groups: Dict[str, List[CanonicalRow]] = {}
        for r in rows:
            meta = SKUNormalizer.normalize_sku(r.product, r.sku_code)
            sheet_title = meta.get("sheet_title", "Other SKU")
            sku_groups.setdefault(sheet_title, []).append(r)

        for sheet_title, group_rows in sku_groups.items():
            self._create_data_and_summary_sheet(sheet_title, group_rows)

        # 4. Data Quality & Verification Sheet
        self._create_data_quality_sheet(dq_records)

        # 5. Processing Log Sheet
        self._create_processing_log_sheet(log_records)

        # Save workbook
        self.wb.save(output_path)

    def _create_data_and_summary_sheet(self, title: str, rows: List[CanonicalRow]):
        ws = self.wb.create_sheet(title=title[:31])
        ws.views.sheetView[0].showGridLines = True

        # Write Header Row (Row 1)
        ws.append(EXCEL_COLUMNS_45)
        ws.row_dimensions[1].height = 28

        for col_idx in range(1, len(EXCEL_COLUMNS_45) + 1):
            c = ws.cell(1, col_idx)
            c.font = self.header_font
            c.fill = self.header_fill
            c.border = self.thin_border
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Write Data Rows
        start_row = 2
        for idx, r in enumerate(rows):
            curr_row = start_row + idx
            
            # Formulas for calculated columns
            chan_std_formula = f'=LOWER(SUBSTITUTE(C{curr_row}," ","_"))'
            plan_cpv_formula = f'=IF(U{curr_row}>0, Y{curr_row}/U{curr_row}, 0)'
            spends_formula = f'=IF(Z{curr_row}>0, Y{curr_row}*Z{curr_row}, Y{curr_row})'
            vid_cpv_formula = f'=IF(AF{curr_row}>0, AA{curr_row}/AF{curr_row}, 0)'
            er_pct_formula = f'=IF(AF{curr_row}>0, (AH{curr_row}+AI{curr_row})/AF{curr_row}, 0)'

            row_data = [
                self._sanitize_cell_value(r.live_status),
                self._sanitize_cell_value(r.sub_cat),
                self._sanitize_cell_value(r.creator),
                chan_std_formula,
                self._sanitize_cell_value(r.creator_ig_link),
                self._sanitize_cell_value(r.product),
                self._sanitize_cell_value(r.sku_code),
                self._sanitize_cell_value(r.stage),
                self._sanitize_cell_value(r.epd_npd),
                r.count,
                self._sanitize_cell_value(r.range_col),
                self._sanitize_cell_value(r.asset),
                self._sanitize_cell_value(r.agency),
                self._sanitize_cell_value(r.gender),
                r.follower_base,
                self._sanitize_cell_value(r.tier),
                self._sanitize_cell_value(r.language),
                self._sanitize_cell_value(r.genre),
                self._sanitize_cell_value(r.category),
                r.er_planned,
                r.average_views,
                plan_cpv_formula,
                r.cost,
                r.counter,
                r.final_costs,
                r.commission,
                spends_formula,
                self._sanitize_cell_value(r.video_status),
                self._sanitize_cell_value(r.live_link),
                self._sanitize_cell_value(r.live_date or ""),
                r.views_organic,
                r.views_brand_collab,
                vid_cpv_formula,
                r.likes,
                r.comments,
                er_pct_formula,
                self._sanitize_cell_value(r.concept_bucketing),
                self._sanitize_cell_value(r.bucket),
                self._sanitize_cell_value(r.spoken_hook),
                self._sanitize_cell_value(r.verified_whole_script),
                self._sanitize_cell_value(r.script_scraping_status),
                r.scraped_views or "",
                r.scraped_likes or "",
                r.scraped_comments or "",
                self._sanitize_cell_value(r.verification_notes)
            ]

            ws.append(row_data)
            ws.row_dimensions[curr_row].height = 20

            # Style data cells
            for col_idx in range(1, len(EXCEL_COLUMNS_45) + 1):
                cell = ws.cell(curr_row, col_idx)
                cell.font = self.body_font
                cell.border = self.thin_border
                
                # Format alignments and numbers
                col_name = EXCEL_COLUMNS_45[col_idx - 1]
                if col_name in ["Cost", "Counter", "Final Costs", "Total Spends"]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col_name in ["Count", "Follower base", "Average Views", "Views Day 0-5 (Organic)", "Views Day 10th (Organic - Brand Collab)", "Likes", "Comments", "Scraped Views", "Scraped Likes", "Scraped Comments"]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col_name in ["CPV", "Video CPV"]:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col_name in ["ER", "ER%"]:
                    cell.number_format = "0.00%"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif col_name in ["Live", "Gender", "Language", "Script Scraping Status", "Video Status", "Sub Cat"]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        data_end_row = start_row + len(rows) - 1

        # Summary tables start 3 rows after data
        summary_start_row = data_end_row + 3

        # Distinct dimensions
        buckets = sorted(list(set(r.bucket for r in rows if r.bucket))) or ["Problem solution"]
        languages = sorted(list(set(r.language for r in rows if r.language))) or ["English"]
        categories = sorted(list(set(r.category for r in rows if r.category))) or ["Influencer"]
        genders = sorted(list(set(r.gender for r in rows if r.gender))) or ["Female"]

        # Table 1 (Left): Bucket Summary (Cols A to F)
        # Table 2 (Right): Language Summary (Cols H to M)
        self._write_side_by_side_summary(
            ws=ws,
            start_row=summary_start_row,
            data_start=start_row,
            data_end=data_end_row,
            left_title="Bucket",
            left_col_letter="AL", # Bucket column
            left_items=buckets,
            right_title="Language",
            right_col_letter="Q",  # Language column
            right_items=languages
        )

        # Table 3 (Left) & Table 4 (Right): Category & Gender Summary
        offset = max(len(buckets), len(languages)) + 4
        cat_start_row = summary_start_row + offset
        self._write_side_by_side_summary(
            ws=ws,
            start_row=cat_start_row,
            data_start=start_row,
            data_end=data_end_row,
            left_title="Category",
            left_col_letter="S", # Category column
            left_items=categories,
            right_title="Gender",
            right_col_letter="N", # Gender column
            right_items=genders
        )

        # Set readable column widths
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            col_header = str(ws.cell(1, col[0].column).value or "")
            max_len = min(max(len(col_header), 12), 40)
            ws.column_dimensions[col_letter].width = max_len + 3

    def _write_side_by_side_summary(
        self,
        ws,
        start_row: int,
        data_start: int,
        data_end: int,
        left_title: str,
        left_col_letter: str,
        left_items: List[str],
        right_title: str,
        right_col_letter: str,
        right_items: List[str]
    ):
        # Header Row
        # Left (Cols 1-6 / A-F): Dimension, SUM of Total Spends, SUM of Views, COUNTA of Count, CPV, Spends
        left_headers = [left_title, "SUM of Total Spends", "SUM of Views Day 10th\n(Organic - Brand Collab)", "COUNTA of Count", "CPV", "Spends"]
        # Right (Cols 8-13 / H-M): Dimension, SUM of Total Spends, SUM of Views, COUNTA of Count, CPV, Spends
        right_headers = [right_title, "SUM of Total Spends", "SUM of Views Day 10th\n(Organic - Brand Collab)", "COUNTA of Count", "CPV", "Spends"]

        ws.row_dimensions[start_row].height = 24
        for idx, h in enumerate(left_headers):
            cell = ws.cell(start_row, idx + 1, h)
            cell.font = self.header_font
            cell.fill = self.summary_fill
            cell.border = self.thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for idx, h in enumerate(right_headers):
            cell = ws.cell(start_row, idx + 8, h)
            cell.font = self.header_font
            cell.fill = self.summary_fill
            cell.border = self.thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Rows
        max_rows = max(len(left_items), len(right_items))
        left_total_row = start_row + len(left_items) + 1
        right_total_row = start_row + len(right_items) + 1

        for i in range(max_rows):
            curr_r = start_row + 1 + i
            ws.row_dimensions[curr_r].height = 20

            # Left Table Row
            if i < len(left_items):
                item = left_items[i]
                ws.cell(curr_r, 1, item).alignment = Alignment(horizontal="left", vertical="center")
                # Spends
                c_sp = ws.cell(curr_r, 2, f'=SUMIF(${left_col_letter}${data_start}:${left_col_letter}${data_end}, A{curr_r}, $AA${data_start}:$AA${data_end})')
                c_sp.number_format = "#,##0"
                # Views
                c_vw = ws.cell(curr_r, 3, f'=SUMIF(${left_col_letter}${data_start}:${left_col_letter}${data_end}, A{curr_r}, $AF${data_start}:$AF${data_end})')
                c_vw.number_format = "#,##0"
                # Count
                c_cnt = ws.cell(curr_r, 4, f'=COUNTIF(${left_col_letter}${data_start}:${left_col_letter}${data_end}, A{curr_r})')
                c_cnt.number_format = "#,##0"
                # CPV
                c_cpv = ws.cell(curr_r, 5, f'=IF(C{curr_r}>0, B{curr_r}/C{curr_r}, 0)')
                c_cpv.number_format = "0.00"
                # Spends %
                c_pct = ws.cell(curr_r, 6, f'=IF(B${left_total_row}>0, B{curr_r}/B${left_total_row}, 0)')
                c_pct.number_format = "0.00%"

                for col_idx in range(1, 7):
                    c = ws.cell(curr_r, col_idx)
                    c.font = self.body_font
                    c.border = self.thin_border

            # Right Table Row
            if i < len(right_items):
                item = right_items[i]
                ws.cell(curr_r, 8, item).alignment = Alignment(horizontal="left", vertical="center")
                # Spends
                c_sp = ws.cell(curr_r, 9, f'=SUMIF(${right_col_letter}${data_start}:${right_col_letter}${data_end}, H{curr_r}, $AA${data_start}:$AA${data_end})')
                c_sp.number_format = "#,##0"
                # Views
                c_vw = ws.cell(curr_r, 10, f'=SUMIF(${right_col_letter}${data_start}:${right_col_letter}${data_end}, H{curr_r}, $AF${data_start}:$AF${data_end})')
                c_vw.number_format = "#,##0"
                # Count
                c_cnt = ws.cell(curr_r, 11, f'=COUNTIF(${right_col_letter}${data_start}:${right_col_letter}${data_end}, H{curr_r})')
                c_cnt.number_format = "#,##0"
                # CPV
                c_cpv = ws.cell(curr_r, 12, f'=IF(J{curr_r}>0, I{curr_r}/J{curr_r}, 0)')
                c_cpv.number_format = "0.00"
                # Spends %
                c_pct = ws.cell(curr_r, 13, f'=IF(I${right_total_row}>0, I{curr_r}/I${right_total_row}, 0)')
                c_pct.number_format = "0.00%"

                for col_idx in range(8, 14):
                    c = ws.cell(curr_r, col_idx)
                    c.font = self.body_font
                    c.border = self.thin_border

        # Write Grand Total Rows
        # Left Total
        left_start_i = start_row + 1
        left_end_i = start_row + len(left_items)
        ws.cell(left_total_row, 1, "Grand Total").alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(left_total_row, 2, f'=SUM(B{left_start_i}:B{left_end_i})').number_format = "#,##0"
        ws.cell(left_total_row, 3, f'=SUM(C{left_start_i}:C{left_end_i})').number_format = "#,##0"
        ws.cell(left_total_row, 4, f'=SUM(D{left_start_i}:D{left_end_i})').number_format = "#,##0"
        ws.cell(left_total_row, 5, f'=IF(C{left_total_row}>0, B{left_total_row}/C{left_total_row}, 0)').number_format = "0.00"
        ws.cell(left_total_row, 6, f'=IF(B{left_total_row}>0, B{left_total_row}/B${left_total_row}, 0)').number_format = "0.00%"

        for col_idx in range(1, 7):
            c = ws.cell(left_total_row, col_idx)
            c.font = self.body_bold_font
            c.border = self.thin_border

        # Right Total
        right_start_i = start_row + 1
        right_end_i = start_row + len(right_items)
        ws.cell(right_total_row, 8, "Grand Total").alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(right_total_row, 9, f'=SUM(I{right_start_i}:I{right_end_i})').number_format = "#,##0"
        ws.cell(right_total_row, 10, f'=SUM(J{right_start_i}:J{right_end_i})').number_format = "#,##0"
        ws.cell(right_total_row, 11, f'=SUM(K{right_start_i}:K{right_end_i})').number_format = "#,##0"
        ws.cell(right_total_row, 12, f'=IF(J{right_total_row}>0, I{right_total_row}/J{right_total_row}, 0)').number_format = "0.00"
        ws.cell(right_total_row, 13, f'=IF(I{right_total_row}>0, I{right_total_row}/I${right_total_row}, 0)').number_format = "0.00%"

        for col_idx in range(8, 14):
            c = ws.cell(right_total_row, col_idx)
            c.font = self.body_bold_font
            c.border = self.thin_border

    def _create_executive_summary_sheet(self, rows: List[CanonicalRow], m: Dict[str, Any]):
        ws = self.wb.create_sheet(title="Executive Summary")
        ws.views.sheetView[0].showGridLines = True

        # Header Title Banner
        ws.merge_cells("A1:G1")
        banner = ws.cell(1, 1, f"THE DERMA CO — INFLUENCER MARKETING PERFORMANCE DASHBOARD ({self.period_label})")
        banner.font = Font(name=FONT_FAMILY, size=12, bold=True, color="1E3A8A")
        banner.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[1].height = 32

        # Section 1: Campaign Overview KPIs
        kpi_headers = ["Metric", "Value", "Notes"]
        for c_idx, h in enumerate(kpi_headers, 1):
            c = ws.cell(3, c_idx, h)
            c.font = self.header_font
            c.fill = self.header_fill
            c.border = self.thin_border

        kpis = [
            ("Reporting Period", self.period_label, "Analyzed campaign timeframe"),
            ("Total SKUs Active", m.get("unique_skus", 0), "Distinct product lines"),
            ("Total Reels Deployed", m.get("total_reels", 0), "Processed creative deliverables"),
            ("Total Creators", m.get("unique_creators", 0), "Unique influencer partners"),
            ("Total Campaign Spend", m.get("total_spend", 0.0), "₹ Total commercial investment"),
            ("Total Realized Views", m.get("total_views", 0), "Audience reach (Day 10 Brand Collab)"),
            ("Total Realized Likes", m.get("total_likes", 0), "Audience approval signal"),
            ("Total Realized Comments", m.get("total_comments", 0), "Direct audience conversations"),
            ("Blended CPV", m.get("avg_cpv", 0.0), "₹ Cost per view (Spend / Views)"),
            ("Blended Engagement Rate", m.get("avg_er", 0.0), "(Likes + Comments) / Views")
        ]

        for idx, (label, val, note) in enumerate(kpis, 4):
            ws.cell(idx, 1, label).font = self.body_bold_font
            val_cell = ws.cell(idx, 2, val)
            val_cell.font = self.body_font
            if isinstance(val, float) and "CPV" in label:
                val_cell.number_format = "₹0.00"
            elif isinstance(val, float) and "Rate" in label:
                val_cell.number_format = "0.00%"
            elif isinstance(val, (int, float)) and "Spend" in label:
                val_cell.number_format = "₹#,##0"
            elif isinstance(val, int):
                val_cell.number_format = "#,##0"
            ws.cell(idx, 3, note).font = self.body_font
            for c_i in range(1, 4):
                ws.cell(idx, c_i).border = self.thin_border

        # Section 2: Data Quality Verification Audit
        dq_start = len(kpis) + 6
        ws.cell(dq_start, 1, "DATA QUALITY & VERIFICATION AUDIT").font = Font(name=FONT_FAMILY, size=10, bold=True, color="1E3A8A")
        dq_headers = ["Audit Dimension", "Count", "Verification Status"]
        for c_idx, h in enumerate(dq_headers, 1):
            c = ws.cell(dq_start + 1, c_idx, h)
            c.font = self.header_font
            c.fill = self.summary_fill
            c.border = self.thin_border

        dq_kpis = [
            ("Total Deliverables Identified", m.get("total_reels", 0), "Verified"),
            ("Transcribed from Spoken Audio", m.get("transcribed_count", 0), "Verbatim Speech Verified"),
            ("Audio Only (No Spoken Speech)", m.get("no_speech_count", 0), "Instrumental Verified"),
            ("Caption Only (Audio Unobtainable)", m.get("caption_only_count", 0), "Needs Review"),
            ("Flagged for Review / Discrepancy", m.get("needs_review_count", 0), "Audit Flagged")
        ]

        for idx, (dim, cnt, st) in enumerate(dq_kpis, dq_start + 2):
            ws.cell(idx, 1, dim).font = self.body_bold_font
            c_cnt = ws.cell(idx, 2, cnt)
            c_cnt.font = self.body_font
            c_cnt.number_format = "#,##0"
            ws.cell(idx, 3, st).font = self.body_font
            for c_i in range(1, 4):
                ws.cell(idx, c_i).border = self.thin_border

        ws.column_dimensions["A"].width = 38
        ws.column_dimensions["B"].width = 24
        ws.column_dimensions["C"].width = 35

    def _create_data_quality_sheet(self, dq_records: List[DataQualityRecord]):
        ws = self.wb.create_sheet(title="Data Quality & Verification")
        ws.views.sheetView[0].showGridLines = True
        headers = ["Reel", "Field", "Original Value", "Verified Value", "Status", "Confidence", "Reason", "Source", "Timestamp"]
        ws.append(headers)
        ws.row_dimensions[1].height = 26

        for c_idx in range(1, len(headers) + 1):
            c = ws.cell(1, c_idx)
            c.font = self.header_font
            c.fill = self.header_fill
            c.border = self.thin_border
            c.alignment = Alignment(horizontal="center", vertical="center")

        for idx, r in enumerate(dq_records, 2):
            ws.append([
                r.reel,
                r.field_name,
                r.original_value,
                r.verified_value,
                r.status.value,
                r.confidence,
                r.reason,
                r.source,
                r.timestamp
            ])
            for col_i in range(1, len(headers) + 1):
                cell = ws.cell(idx, col_i)
                cell.font = self.body_font
                cell.border = self.thin_border

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = 20

    def _create_processing_log_sheet(self, log_records: List[ProcessingLogRecord]):
        ws = self.wb.create_sheet(title="Processing Log")
        ws.views.sheetView[0].showGridLines = True
        headers = ["Timestamp", "Record ID", "Operation", "Status", "Duration (s)", "Retry Count", "Source", "Error Code", "Error Message"]
        ws.append(headers)
        ws.row_dimensions[1].height = 26

        for c_idx in range(1, len(headers) + 1):
            c = ws.cell(1, c_idx)
            c.font = self.header_font
            c.fill = self.summary_fill
            c.border = self.thin_border
            c.alignment = Alignment(horizontal="center", vertical="center")

        for idx, r in enumerate(log_records, 2):
            # Strict safety: ensure error_message and other fields never contain leaked credentials
            safe_err = re.sub(r'(sessionid|session_id|api_key|token)=[A-Za-z0-9_.-]+', r'\1=***', str(r.error_message), flags=re.IGNORECASE)
            ws.append([
                r.timestamp,
                r.record_id,
                r.operation,
                r.status,
                r.duration_sec,
                r.retry_count,
                r.source,
                r.error_code,
                safe_err
            ])
            for col_i in range(1, len(headers) + 1):
                cell = ws.cell(idx, col_i)
                cell.font = self.body_font
                cell.border = self.thin_border

        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = 18
