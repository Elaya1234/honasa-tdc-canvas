import os
import sys
import argparse
import json
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tdc_im_agent.orchestrator import TDCOrchestrator
from tdc_im_agent.config import APP_NAME, APP_VERSION

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("tdc_cli")

def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION} CLI")
    parser.add_argument("--input", "-i", required=True, help="Path to input Excel tracker (.xlsx)")
    parser.add_argument("--sheet", "-s", default=None, help="Campaign sheet name to process (e.g. 'Sept26', 'August26', 'Oct26 ')")
    parser.add_argument("--all-campaigns", action="store_true", help="Process and consolidate all active campaigns across the year")
    parser.add_argument("--list-sheets", action="store_true", help="List all candidate campaign sheets in the workbook")
    parser.add_argument("--inspect", action="store_true", help="Inspect and display recommended analysis")
    parser.add_argument("--run", action="store_true", help="Execute complete analysis and generate workbook")
    parser.add_argument("--engine", default="auto", choices=["auto", "direct", "apify", "demo"], help="Scraping engine")
    parser.add_argument("--reprocess-all", action="store_true", help="Bypass cache and reprocess all reels")

    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    orchestrator = TDCOrchestrator(engine_preference=args.engine)
    target_sheet = "__ALL_CAMPAIGNS__" if args.all_campaigns else args.sheet

    if args.list_sheets:
        from tdc_im_agent.input_intelligence import ExcelInputIntelligence
        parser_tool = ExcelInputIntelligence(input_path)
        sheets = parser_tool.discover_sheets()
        print("\n" + "=" * 60)
        print(f"  {APP_NAME} — DISCOVERED CAMPAIGN SHEETS")
        print("=" * 60)
        for s in sheets:
            print(f"  * {s['display']} [Score: {s['score']}]")
        print("=" * 60 + "\n")
        return

    if args.inspect:
        rec = orchestrator.inspect_and_recommend(input_path, sheet_name=target_sheet)
        print("\n" + "=" * 60)
        print(f"  {APP_NAME} — INSPECTION REPORT")
        print("=" * 60)
        print(f"Active Sheet:           {rec.get('selected_sheet', 'Auto-Selected')}")
        print(f"Reporting Period:       {rec['period_label']} ({rec['period_type']})")
        print(f"Total Reels Found:      {rec['total_reels']}")
        print(f"Active SKUs:            {rec['total_skus']} -> {', '.join(rec['sku_list'])}")
        print(f"Unique Creators:        {rec['total_creators']}")
        print(f"Cached Reels:           {rec['cached_reels_available']} / {rec['total_reels']}")
        print(f"Mapping Confidence:     {rec['mapping_confidence'] * 100:.1f}%")
        print(f"Recommended Output:     {rec['recommended_output']}")
        print(f"Dimensions:             {', '.join(rec['recommended_dimensions'])}")
        print(f"Metrics:                {', '.join(rec['recommended_metrics'])}")
        if rec.get("available_campaign_sheets"):
            print("\nAvailable Campaign Sheets:")
            for s in rec["available_campaign_sheets"][:5]:
                print(f"  - {s['display']}")
        print("=" * 60 + "\n")
        return

    if args.run:
        print("\n" + "=" * 60)
        print(f"  {APP_NAME} — EXECUTING ANALYSIS")
        print("=" * 60)
        
        def progress(curr, total, msg, row):
            print(f"[{curr}/{total}] {msg}")

        result = orchestrator.execute_analysis(
            file_path=input_path,
            sheet_name=target_sheet,
            reprocess_all=args.reprocess_all,
            progress_callback=progress
        )

        print("\n" + "=" * 60)
        print(f"  FINAL ANALYSIS & QA STATUS: {result['completion_status']}")
        print("=" * 60)
        print(f"Output File:            {result['output_file']}")
        print(f"Output Path:            {result['output_path']}")
        print(f"Total Reels:            {result['total_reels']}")
        print(f"Successfully Processed: {result['successfully_processed']}")
        print(f"Verified Spoken Speech: {result['verified_count']}")
        print(f"Instrumental/No Speech: {result['no_speech_count']}")
        print(f"Caption Only:           {result['caption_only_count']}")
        print(f"Failed Records:         {result['failed_count']}")
        print(f"Total Campaign Spend:   Rs. {result['total_spend']:,.0f}")
        print(f"Total Collab Views:     {result['total_views']:,}")
        print(f"Blended CPV:            Rs. {result['avg_cpv']:.2f}")
        print(f"QA Integrity:           {result['qa_status']}")
        print(f"Reconciliation:         {result['reconciliation_status']}")
        print(f"Elapsed Time:           {result['elapsed_seconds']}s")
        if result['discrepancy_reasons']:
            print("Audit Notes:")
            for note in result['discrepancy_reasons']:
                print(f"  * {note}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
