import unittest
import os
from tdc_im_agent.input_intelligence import ExcelInputIntelligence
from tdc_im_agent.orchestrator import TDCOrchestrator
from tdc_im_agent.period_detector import PeriodDetector

class TestMultiSheetMaster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master_file = r"C:\Users\elaya.n\Downloads\IM 2026 - TDC (1).xlsx"
        cls.has_master = os.path.exists(cls.master_file)

    def test_multisheet_discovery(self):
        if not self.has_master:
            self.skipTest("Master workbook not found in Downloads")
        parser = ExcelInputIntelligence(self.master_file)
        sheets = parser.discover_sheets()
        sheet_names = [s["sheet_name"] for s in sheets]
        
        # Verify campaign sheets are present
        self.assertIn("Sept26", sheet_names)
        self.assertIn("August26", sheet_names)
        self.assertIn("AMJJA26", sheet_names)
        
        # Verify non-campaign dumps and master catalogs are excluded
        self.assertNotIn("Product Master", sheet_names)
        self.assertNotIn("daily update ", sheet_names)
        self.assertNotIn("june- aug data", sheet_names)

    def test_default_campaign_sheet_never_product_master(self):
        if not self.has_master:
            self.skipTest("Master workbook not found in Downloads")
        parser = ExcelInputIntelligence(self.master_file)
        default_sheet = parser.get_default_campaign_sheet()
        self.assertNotEqual(default_sheet, "Product Master")
        self.assertTrue(len(default_sheet) > 0)

    def test_inspect_and_recommend_multisheet(self):
        if not self.has_master:
            self.skipTest("Master workbook not found in Downloads")
        orch = TDCOrchestrator()
        rec = orch.inspect_and_recommend(self.master_file, sheet_name="Sept26")
        self.assertEqual(rec["period_label"], "September 2026")
        self.assertGreater(rec["total_reels"], 100)
        self.assertGreater(rec["total_skus"], 5)
        self.assertGreater(rec["total_creators"], 50)

    def test_period_detector_with_sheet_name(self):
        res_sep = PeriodDetector.detect_period("dummy.xlsx", [], sheet_name="Sept26")
        self.assertEqual(res_sep["period_label"], "September 2026")
        self.assertEqual(res_sep["period_type"], "Monthly")

        res_aug = PeriodDetector.detect_period("dummy.xlsx", [], sheet_name="August26")
        self.assertEqual(res_aug["period_label"], "August 2026")
        self.assertEqual(res_aug["period_type"], "Monthly")

        res_all = PeriodDetector.detect_period("dummy.xlsx", [], sheet_name="__ALL_CAMPAIGNS__")
        self.assertEqual(res_all["period_label"], "Full Year 2026 (Consolidated)")
        self.assertEqual(res_all["period_type"], "Yearly")

if __name__ == "__main__":
    unittest.main()
