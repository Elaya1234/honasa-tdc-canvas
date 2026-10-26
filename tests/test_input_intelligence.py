import os
import unittest
import pandas as pd
import tempfile
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tdc_im_agent.input_intelligence import ExcelInputIntelligence, sanitize_untrusted_text, safe_numeric
from tdc_im_agent.period_detector import PeriodDetector

class TestInputIntelligence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_sanitize_formula_injection(self):
        """Tests that dangerous spreadsheet formula prefixes are safely escaped."""
        self.assertEqual(sanitize_untrusted_text("=cmd|' /C calc'!A0"), "'=cmd|' /C calc'!A0")
        self.assertEqual(sanitize_untrusted_text("+12345"), "'+12345")
        self.assertEqual(sanitize_untrusted_text("-danger"), "'-danger")
        self.assertEqual(sanitize_untrusted_text("@admin"), "'@admin")
        self.assertEqual(sanitize_untrusted_text("Normal Text"), "Normal Text")
        # Ensure legitimately generated uppercase formulas with parens are NOT escaped
        self.assertEqual(sanitize_untrusted_text("=SUM(A1:A5)"), "=SUM(A1:A5)")

    def test_safe_numeric_parsing(self):
        """Tests currency, comma, percentage, and dirty string parsing."""
        self.assertEqual(safe_numeric("₹1,25,000"), 125000.0)
        self.assertEqual(safe_numeric("12.5%"), 12.5)
        self.assertEqual(safe_numeric("Rs. 450.50"), 450.5)
        self.assertEqual(safe_numeric("N/A", 0.0), 0.0)
        self.assertEqual(safe_numeric(None, 0.0), 0.0)

    def test_dynamic_header_detection_and_reordered_columns(self):
        """Tests reading an Excel with unusual column orders and extraneous rows."""
        test_file = os.path.join(self.temp_dir, "reordered_tracker.xlsx")
        
        # Build dataframe with random column order
        data = {
            "Total Spends": ["₹50,000", "₹75,000"],
            "Influencer Name": ["Creator A", "Creator B"],
            "Live Link": ["https://www.instagram.com/reel/C8q_sample1/", "https://www.instagram.com/reel/DLUO_sample2/"],
            "Views Brand Collab": [250000, 400000],
            "Product": ["1% Hyalu Sunscreen Aqua Gel", "2% Sali-Cinamide Anti-Acne Face Wash"],
            "SKU CODE": ["8906087775713", "8904417319637"],
            "Gender": ["Female", "Male"],
            "Language": ["Hinglish", "English"],
            "Extra Junk Column": ["ignore me", "ignore me too"]
        }
        df = pd.DataFrame(data)
        
        # Write with title row at top to test non-zero header row detection
        with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
            # Row 0 title, Row 1 headers
            pd.DataFrame([["TDC Tracker Internal Title", "", "", "", "", "", "", "", ""]]).to_excel(
                writer, index=False, header=False, startrow=0
            )
            df.to_excel(writer, index=False, startrow=1)

        parser = ExcelInputIntelligence(test_file)
        rows, meta = parser.parse_sheet()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].creator, "Creator A")
        self.assertEqual(rows[0].total_spends, 50000.0)
        self.assertEqual(rows[0].views_brand_collab, 250000)
        self.assertEqual(rows[0].shortcode, "C8q_sample1")
        self.assertEqual(rows[1].creator, "Creator B")
        self.assertEqual(rows[1].total_spends, 75000.0)

    def test_period_detection(self):
        """Tests detection across monthly, quarterly, and custom dates."""
        res_sep = PeriodDetector.detect_period("Sept'26 FW & SS.xlsx", [])
        self.assertEqual(res_sep["period_label"], "September 2026")
        self.assertEqual(res_sep["period_type"], "Monthly")

        res_q3 = PeriodDetector.detect_period("Q3_2026_TDC_Campaigns.xlsx", [])
        self.assertEqual(res_q3["period_label"], "Q3 2026")
        self.assertEqual(res_q3["period_type"], "Quarterly")

if __name__ == "__main__":
    unittest.main()
