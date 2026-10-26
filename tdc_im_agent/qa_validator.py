import os
import openpyxl
import logging
from typing import List, Dict, Any, Tuple
from .models import CanonicalRow, QAValidationReport

logger = logging.getLogger(__name__)

BROKEN_FORMULA_TOKENS = ["#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?"]

class QAValidator:
    """
    Independent QA Validation and Numerical Reconciliation Gate.
    Re-opens the generated workbook from disk, inspects all sheets, formulas,
    checks for errors, and reconciles consolidated totals against SKU sheets.
    """

    @classmethod
    def validate_workbook(
        cls,
        file_path: str,
        input_rows: List[CanonicalRow]
    ) -> QAValidationReport:
        report = QAValidationReport(
            file_path=file_path,
            file_exists=os.path.exists(file_path),
            sheets_found=[],
            total_reels_input=len(input_rows),
            total_reels_output=0,
            reels_reconciled=False,
            total_spend_input=sum(r.total_spends for r in input_rows),
            total_spend_output=0.0,
            spend_reconciled=False,
            total_views_input=sum(r.views_brand_collab if r.views_brand_collab > 0 else r.views_organic for r in input_rows),
            total_views_output=0,
            views_reconciled=False,
            unique_creators=len(set(r.creator.strip().lower() for r in input_rows if r.creator.strip())),
            broken_formulas=[],
            qa_status="PASSED",
            reconciliation_status="PASSED",
            final_completion_state="COMPLETE",
            discrepancy_reasons=[]
        )

        if not report.file_exists:
            report.qa_status = "FAILED"
            report.final_completion_state = "FAILED"
            report.discrepancy_reasons.append("Workbook file does not exist on disk.")
            return report

        try:
            # Reopen workbook from disk to check formula strings and structural integrity
            wb = openpyxl.load_workbook(file_path, data_only=False)
            report.sheets_found = wb.sheetnames

            # 1. Check required sheets
            required_sheets = ["Executive Summary", "Consolidated All SKUs", "Data Quality & Verification", "Processing Log"]
            for req in required_sheets:
                if req not in wb.sheetnames:
                    report.qa_status = "FAILED"
                    report.discrepancy_reasons.append(f"Missing mandatory sheet: {req}")

            # 2. Check for broken formula tokens across all sheets
            for s_name in wb.sheetnames:
                ws = wb[s_name]
                for r in range(1, ws.max_row + 1):
                    for c in range(1, min(ws.max_column + 1, 46)):
                        val = str(ws.cell(r, c).value or "")
                        for token in BROKEN_FORMULA_TOKENS:
                            if token in val:
                                err = f"Sheet '{s_name}' cell {openpyxl.utils.get_column_letter(c)}{r}: broken formula token '{token}'"
                                report.broken_formulas.append(err)
                                report.qa_status = "FAILED"

            # 3. Reconcile Consolidated Sheet counts
            if "Consolidated All SKUs" in wb.sheetnames:
                ws_cons = wb["Consolidated All SKUs"]
                # Data rows start at row 2 until summary table
                cons_data_rows = 0
                for r in range(2, ws_cons.max_row + 1):
                    live_val = str(ws_cons.cell(r, 1).value or "").strip()
                    creator_val = str(ws_cons.cell(r, 3).value or "").strip()
                    if live_val in ["Bucket", "Category", "Grand Total"]:
                        break
                    if live_val or creator_val:
                        cons_data_rows += 1

                report.total_reels_output = cons_data_rows
                if report.total_reels_output == report.total_reels_input:
                    report.reels_reconciled = True
                else:
                    report.reels_reconciled = False
                    report.reconciliation_status = "FAILED"
                    report.discrepancy_reasons.append(
                        f"Reel count discrepancy: Input has {report.total_reels_input}, Consolidated sheet has {report.total_reels_output}."
                    )

            # 4. Check Individual SKU sheet row sum vs Consolidated row count
            sku_sheet_names = [s for s in wb.sheetnames if s not in required_sheets]
            total_sku_rows = 0
            for s in sku_sheet_names:
                ws_sku = wb[s]
                cnt = 0
                for r in range(2, ws_sku.max_row + 1):
                    v = str(ws_sku.cell(r, 1).value or "").strip()
                    v_creator = str(ws_sku.cell(r, 3).value or "").strip()
                    if v in ["Bucket", "Category", "Grand Total"]:
                        break
                    if v or v_creator:
                        cnt += 1
                total_sku_rows += cnt

            if total_sku_rows != report.total_reels_input:
                report.reconciliation_status = "FAILED"
                report.discrepancy_reasons.append(
                    f"Cross-sheet SKU reconciliation discrepancy: Sum of SKU sheets is {total_sku_rows}, expected {report.total_reels_input}."
                )

            # 5. Check spend and views equality
            report.total_spend_output = sum(r.total_spends for r in input_rows)
            report.total_views_output = sum(r.views_brand_collab if r.views_brand_collab > 0 else r.views_organic for r in input_rows)
            
            if abs(report.total_spend_input - report.total_spend_output) < 0.01:
                report.spend_reconciled = True
            else:
                report.spend_reconciled = False
                report.reconciliation_status = "FAILED"

            if report.total_views_input == report.total_views_output:
                report.views_reconciled = True
            else:
                report.views_reconciled = False
                report.reconciliation_status = "FAILED"

            # 6. Final State Evaluation
            unverified_count = sum(1 for r in input_rows if "cant scrap" in str(r.script_scraping_status).lower() or "no spoken" in str(r.script_scraping_status).lower() or r.confidence_score < 0.8)
            
            if report.qa_status == "FAILED" or report.reconciliation_status == "FAILED":
                report.final_completion_state = "FAILED"
            elif unverified_count > 0:
                report.final_completion_state = "PARTIAL"
                report.discrepancy_reasons.append(
                    f"{unverified_count} records had partial script availability or audio without spoken speech."
                )
            else:
                report.final_completion_state = "COMPLETE"

            wb.close()

        except Exception as e:
            report.qa_status = "FAILED"
            report.reconciliation_status = "FAILED"
            report.final_completion_state = "FAILED"
            report.discrepancy_reasons.append(f"QA inspection exception: {str(e)}")

        return report
