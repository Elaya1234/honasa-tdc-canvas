import os
import unittest
import tempfile
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tdc_im_agent.cache_manager import CacheManager
from tdc_im_agent.models import CanonicalRow, ProcessingState, ScriptStatus

class TestResumabilityAndCache(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_cache.db")
        self.cache_mgr = CacheManager(self.db_path)

    def test_cache_save_and_resumption(self):
        # Create a processed row
        row = CanonicalRow(
            source_row=2,
            creator="Ria",
            live_link="https://www.instagram.com/reel/C8q_sample1/",
            shortcode="C8q_sample1",
            spoken_hook="Here is my morning routine",
            verified_whole_script="Here is my morning routine for glowing skin...",
            script_scraping_status=ScriptStatus.TRANSCRIBED.value,
            scraped_views=150000,
            scraped_likes=9000,
            scraped_comments=150,
            concept_bucketing="Tutorial / How-To",
            bucket="Problem solution",
            language="English",
            gender="Female",
            processing_state=ProcessingState.SUCCESS
        )

        # 1. Save to cache
        self.cache_mgr.save_record(row)

        # 2. Simulate application crash & restart: Create fresh row with only basic metadata
        fresh_row = CanonicalRow(
            source_row=2,
            creator="Ria",
            live_link="https://www.instagram.com/reel/C8q_sample1/",
            shortcode="C8q_sample1"
        )

        # 3. Apply cache
        hit = self.cache_mgr.apply_cache_to_row(fresh_row)
        self.assertTrue(hit)
        self.assertEqual(fresh_row.spoken_hook, "Here is my morning routine")
        self.assertEqual(fresh_row.verified_whole_script, "Here is my morning routine for glowing skin...")
        self.assertEqual(fresh_row.scraped_views, 150000)
        self.assertEqual(fresh_row.scraped_likes, 9000)
        self.assertEqual(fresh_row.scraped_comments, 150)
        self.assertEqual(fresh_row.concept_bucketing, "Tutorial / How-To")
        self.assertEqual(fresh_row.processing_state, ProcessingState.SUCCESS)

    def test_cache_miss(self):
        unknown_row = CanonicalRow(
            source_row=10,
            creator="Unknown",
            live_link="https://www.instagram.com/reel/NON_EXISTENT/",
            shortcode="NON_EXISTENT"
        )
        hit = self.cache_mgr.apply_cache_to_row(unknown_row)
        self.assertFalse(hit)

if __name__ == "__main__":
    unittest.main()
