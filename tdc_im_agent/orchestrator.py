import os
import time
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from .config import OUTPUT_DIR, APP_NAME, APP_VERSION
from .models import (
    CanonicalRow, ProcessingState, ScriptStatus, VerificationStatus,
    DataQualityRecord, ProcessingLogRecord, QAValidationReport
)
from .input_intelligence import ExcelInputIntelligence
from .period_detector import PeriodDetector
from .sku_normalizer import SKUNormalizer
from .reel_discovery import ReelDiscovery
from .collector_adapter import CollectorAdapter
from .verification_engine import VerificationEngine
from .analytics_engine import AnalyticsEngine
from .report_generator import TDCReportGenerator
from .qa_validator import QAValidator
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class TDCOrchestrator:
    """
    Main execution coordinator for TDC - IM Performance Tracking Agent.
    Implements the core operating principle:
    OBSERVE -> UNDERSTAND -> INFER -> CONFIRM ONLY WHEN NECESSARY -> PROCESS -> VERIFY -> VALIDATE -> REPORT
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        apify_token: Optional[str] = None,
        session_id: Optional[str] = None,
        engine_preference: str = "auto",
        cache_db_path: Optional[str] = None
    ):
        self.collector_adapter = CollectorAdapter(
            gemini_api_key=gemini_api_key,
            apify_token=apify_token,
            session_id=session_id,
            engine_preference=engine_preference
        )
        self.cache_manager = CacheManager(cache_db_path)
        self.is_paused = False
        self.is_cancelled = False

    def inspect_and_recommend(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Observes the workbook, discovers candidate campaign sheets, infers schema, period, SKUs,
        and produces the instant recommendation with minimum questions.
        """
        parser = ExcelInputIntelligence(file_path)
        discovered = parser.discover_sheets()

        if sheet_name is None:
            sheet_name = parser.get_default_campaign_sheet()

        rows, meta = parser.parse_sheet(sheet_name=sheet_name)

        # Infer period
        period_info = PeriodDetector.detect_period(file_path, rows, sheet_name=sheet_name)

        # SKU normalization
        sku_set = set()
        for r in rows:
            norm_res = SKUNormalizer.normalize_sku(r.product, r.sku_code)
            r.normalized_sku = norm_res["normalized_sku"]
            sku_set.add(norm_res["normalized_sku"])

        # Creator count
        creators = set(r.creator.strip() for r in rows if r.creator.strip())

        # Check existing cached count
        cached_count = sum(1 for r in rows if r.shortcode and self.cache_manager.get_cached_record(r.shortcode) is not None)

        recommendation = {
            "period_label": period_info["period_label"],
            "period_type": period_info["period_type"],
            "total_reels": len(rows),
            "total_skus": len(sku_set),
            "sku_list": sorted(list(sku_set)),
            "total_creators": len(creators),
            "cached_reels_available": cached_count,
            "mapping_confidence": meta["mapping_confidence"],
            "available_campaign_sheets": discovered,
            "selected_sheet": sheet_name,
            "recommended_output": "SKU-wise + Consolidated",
            "recommended_dimensions": ["Language", "Gender", "Content Bucket", "Content Category", "Creator"],
            "recommended_metrics": ["Spend", "Views", "Likes", "Comments", "Engagement", "CPV"],
            "relationships": ["Spend vs Views", "Spend vs Engagement"]
        }
        return recommendation

    def execute_analysis(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        download_media: bool = True,
        reprocess_all: bool = False,
        progress_callback: Optional[Callable[[int, int, str, CanonicalRow], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end processing pipeline with failure isolation,
        caching, verification, deterministic report generation, and QA validation.
        """
        start_time = time.time()
        parser = ExcelInputIntelligence(file_path)
        if sheet_name is None:
            sheet_name = parser.get_default_campaign_sheet()

        rows, meta = parser.parse_sheet(sheet_name=sheet_name)

        # Step 1: Detect reporting period
        period_info = PeriodDetector.detect_period(file_path, rows, sheet_name=sheet_name)
        period_label = period_info["period_label"]

        # Step 2: Normalize SKUs
        for r in rows:
            norm_meta = SKUNormalizer.normalize_sku(r.product, r.sku_code)
            r.normalized_sku = norm_meta["normalized_sku"]
            r.sub_cat = norm_meta.get("category", r.sub_cat)

        # Step 3: Discover Reels and Deduplicate
        rows, dupe_stats = ReelDiscovery.process_records(rows)

        # Staging directory for temporary audio/video downloads
        temp_dir = tempfile.mkdtemp(prefix="tdc_im_media_")

        processing_logs: List[ProcessingLogRecord] = []
        data_quality_records: List[DataQualityRecord] = []

        total_reels = len(rows)

        # Step 4: Process Reels via Cache or Collector Adapter
        for idx, row in enumerate(rows):
            if self.is_cancelled:
                logger.info("Processing cancelled by user; committing completed records.")
                break

            record_id = row.shortcode or f"Row_{row.source_row}"
            op_start = time.time()

            # Guard: If row has no live link or shortcode, skip external scraping
            if not row.live_link or not row.shortcode:
                row.script_scraping_status = "No Live Link / Pipeline"
                row.verification_notes = "Skipped extraction - No live Reel URL in source row"
                data_quality_records.append(DataQualityRecord(
                    reel=record_id,
                    field_name="live_link",
                    original_value="",
                    verified_value="Pipeline / No Link",
                    status=VerificationStatus.NEEDS_REVIEW,
                    confidence="High",
                    reason="Row does not contain live Instagram Reel URL",
                    source="Source Sheet Metadata",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                continue

            # Check cache unless reprocess_all is requested
            cache_hit = False
            if not reprocess_all:
                cache_hit = self.cache_manager.apply_cache_to_row(row)

            if cache_hit:
                status_str = "SUCCESS (Cache Hit)"
                if progress_callback:
                    progress_callback(idx + 1, total_reels, f"Cached: @{row.creator} ({record_id})", row)
            else:
                # Process via Collector Adapter with failure isolation
                if progress_callback:
                    progress_callback(idx + 1, total_reels, f"Processing @{row.creator} ({record_id})...", row)

                try:
                    self.collector_adapter.process_single_reel(
                        row=row,
                        download_media=download_media,
                        temp_dir=temp_dir
                    )
                    status_str = row.processing_state.value
                    # Commit to persistent cache
                    self.cache_manager.save_record(row)
                except Exception as e:
                    row.processing_state = ProcessingState.FAILED
                    status_str = "FAILED"
                    row.verification_notes += f"Processing exception: {str(e)[:80]}; "
                    logger.error(f"Error processing {record_id}: {e}")

            duration = round(time.time() - op_start, 2)

            # Processing log entry (Secrets strictly scrubbed)
            processing_logs.append(ProcessingLogRecord(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                record_id=record_id,
                operation="Reel Analysis & STT",
                status=status_str,
                duration_sec=duration,
                retry_count=0 if cache_hit else 1,
                source="Cache" if cache_hit else "Collector/Gemini"
            ))

            # Step 5: Verification & Data Quality Records
            dq_items = VerificationEngine.verify_record(row)
            data_quality_records.extend(dq_items)

        # Clean up temporary staging directory
        try:
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
        except Exception:
            pass

        # Step 6: Compute Executive Summary KPIs deterministically
        exec_metrics = AnalyticsEngine.compute_executive_metrics(rows)

        # Step 7: Generate Standardized TDC Excel Workbook
        safe_period_slug = period_label.replace(" ", "_").replace("'", "")
        output_filename = f"TDC - IM Performance Tracking - {safe_period_slug}.xlsx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)

        report_gen = TDCReportGenerator(period_label=period_label)
        report_gen.build_full_workbook(
            rows=rows,
            dq_records=data_quality_records,
            log_records=processing_logs,
            exec_summary_metrics=exec_metrics,
            output_path=output_filepath
        )

        # Step 8: QA & Reconciliation Gate (Re-open file and inspect)
        qa_report = QAValidator.validate_workbook(
            file_path=output_filepath,
            input_rows=rows
        )

        total_elapsed = round(time.time() - start_time, 2)

        return {
            "period": period_label,
            "input_file": os.path.basename(file_path),
            "output_file": output_filename,
            "output_path": output_filepath,
            "total_reels": total_reels,
            "successfully_processed": sum(1 for r in rows if r.processing_state in [ProcessingState.SUCCESS, ProcessingState.PARTIAL]),
            "verified_count": sum(1 for r in rows if "Transcribed" in str(r.script_scraping_status)),
            "no_speech_count": sum(1 for r in rows if "no spoken" in str(r.script_scraping_status).lower()),
            "caption_only_count": sum(1 for r in rows if "cant scrap" in str(r.script_scraping_status).lower() or ("caption" in str(r.script_scraping_status).lower() and "no spoken" not in str(r.script_scraping_status).lower())),
            "failed_count": sum(1 for r in rows if r.processing_state == ProcessingState.FAILED),
            "qa_status": qa_report.qa_status,
            "reconciliation_status": qa_report.reconciliation_status,
            "completion_status": qa_report.final_completion_state,
            "discrepancy_reasons": qa_report.discrepancy_reasons,
            "total_spend": exec_metrics["total_spend"],
            "total_views": exec_metrics["total_views"],
            "avg_cpv": exec_metrics["avg_cpv"],
            "elapsed_seconds": total_elapsed
        }
