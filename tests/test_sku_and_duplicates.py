import os
import unittest
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tdc_im_agent.sku_normalizer import SKUNormalizer
from tdc_im_agent.reel_discovery import ReelDiscovery
from tdc_im_agent.models import CanonicalRow, DuplicateType

class TestSKUAndDuplicates(unittest.TestCase):

    def test_sku_normalization_hierarchy(self):
        # Tier 1: SKU Barcode match (Strongest)
        res1 = SKUNormalizer.normalize_sku("Wrong Random Name", "8904417319637")
        self.assertEqual(res1["normalized_sku"], "2% Sali-Cinamide Anti-Acne Face Wash")
        self.assertEqual(res1["normalization_method"], "Exact SKU Barcode Match")

        # Tier 2: Exact Product Name match
        res2 = SKUNormalizer.normalize_sku("1% Hyaluronic Sunscreen Aqua Gel")
        self.assertEqual(res2["normalized_sku"], "1% Hyaluronic Sunscreen Aqua Gel")
        self.assertEqual(res2["sku_code"], "8906087775713")

        # Tier 3: Keyword Alias match
        res3 = SKUNormalizer.normalize_sku("TDC 1% Kojic Acid Face Wash 150ml Promo Pack")
        self.assertEqual(res3["normalized_sku"], "1% Kojic Acid Face Wash")
        self.assertEqual(res3["sku_code"], "8904417306248")

        res4 = SKUNormalizer.normalize_sku("TDC- 2.5% Benzoyl Peroxide Gel Face Wash")
        self.assertEqual(res4["normalized_sku"], "Benzoyl Peroxide Face Wash")
        self.assertEqual(res4["sku_code"], "8906087775607")

    def test_duplicate_classification_engine(self):
        rows = [
            CanonicalRow(
                source_row=2,
                creator="Priya",
                live_link="https://www.instagram.com/reel/C8q_sample1/",
                sku_code="8906087775713"
            ),
            # Exact Duplicate: Same Creator, Same Reel, Same SKU
            CanonicalRow(
                source_row=3,
                creator="Priya",
                live_link="https://www.instagram.com/reel/C8q_sample1/",
                sku_code="8906087775713"
            ),
            # Intentional Reuse: Same Creator, Same Reel, Different SKU
            CanonicalRow(
                source_row=4,
                creator="Priya",
                live_link="https://www.instagram.com/reel/C8q_sample1/",
                sku_code="8904417319637"
            ),
            # Possible Duplicate: Different Creator Listed, Same Reel
            CanonicalRow(
                source_row=5,
                creator="Different Influencer",
                live_link="https://www.instagram.com/reel/C8q_sample1/",
                sku_code="8906087775713"
            ),
            # Unique Reel
            CanonicalRow(
                source_row=6,
                creator="Ananya",
                live_link="https://www.instagram.com/reel/XYZ_unique/",
                sku_code="8906087775713"
            )
        ]

        processed, stats = ReelDiscovery.process_records(rows)

        self.assertEqual(stats["exact_duplicates"], 1)
        self.assertEqual(stats["intentional_reuse"], 1)
        self.assertEqual(stats["possible_duplicates"], 1)
        self.assertEqual(stats["unique_reels"], 2)

        self.assertEqual(processed[0].duplicate_type, DuplicateType.UNIQUE)
        self.assertEqual(processed[1].duplicate_type, DuplicateType.EXACT_DUPLICATE)
        self.assertEqual(processed[2].duplicate_type, DuplicateType.INTENTIONAL_REUSE)
        self.assertEqual(processed[3].duplicate_type, DuplicateType.POSSIBLE_DUPLICATE)
        self.assertEqual(processed[4].duplicate_type, DuplicateType.UNIQUE)

if __name__ == "__main__":
    unittest.main()
