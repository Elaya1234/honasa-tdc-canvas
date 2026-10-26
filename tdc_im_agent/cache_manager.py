import os
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from .config import CACHE_DIR, COLLECTOR_VERSION, ANALYSIS_VERSION, DEFAULT_MODEL_NAME
from .models import CanonicalRow, ProcessingState, ScriptStatus

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Persistent, versioned, thread-safe SQLite cache for Reel analysis.
    Ensures idempotency, zero wasted re-transcription, and instant crash recovery.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(CACHE_DIR, "im_cache.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS reel_cache (
                    shortcode TEXT PRIMARY KEY,
                    normalized_url TEXT,
                    collector_version TEXT,
                    analysis_version TEXT,
                    model_version TEXT,
                    processing_state TEXT,
                    spoken_hook TEXT,
                    verified_whole_script TEXT,
                    script_scraping_status TEXT,
                    scraped_views INTEGER,
                    scraped_likes INTEGER,
                    scraped_comments INTEGER,
                    concept_bucketing TEXT,
                    bucket TEXT,
                    language TEXT,
                    gender TEXT,
                    verification_notes TEXT,
                    confidence_score REAL,
                    raw_payload TEXT,
                    last_updated TEXT
                )
                """)
                # Self-healing purge: Remove any previously corrupted cache rows where captions were stored as audio transcripts
                conn.execute("""
                DELETE FROM reel_cache
                WHERE (script_scraping_status = 'Transcribed from Spoken Audio' OR script_scraping_status = 'TRANSCRIBED')
                  AND (verified_whole_script LIKE '%#%' OR verified_whole_script LIKE '%[AI Audio Note%' OR verified_whole_script LIKE 'Check out this reel by @%')
                """)
        finally:
            conn.close()

    def get_cached_record(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached analysis for a given shortcode if available."""
        if not shortcode:
            return None
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM reel_cache WHERE shortcode = ?", (shortcode,)).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def save_record(self, row: CanonicalRow):
        """Persists or updates a processed CanonicalRow in the cache."""
        if not row.shortcode:
            return
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                INSERT OR REPLACE INTO reel_cache (
                    shortcode, normalized_url, collector_version, analysis_version, model_version,
                    processing_state, spoken_hook, verified_whole_script, script_scraping_status,
                    scraped_views, scraped_likes, scraped_comments, concept_bucketing, bucket,
                    language, gender, verification_notes, confidence_score, raw_payload, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.shortcode,
                    row.normalized_url or row.live_link,
                    COLLECTOR_VERSION,
                    ANALYSIS_VERSION,
                    DEFAULT_MODEL_NAME,
                    row.processing_state.value,
                    row.spoken_hook,
                    row.verified_whole_script,
                    row.script_scraping_status,
                    row.scraped_views,
                    row.scraped_likes,
                    row.scraped_comments,
                    row.concept_bucketing,
                    row.bucket,
                    row.language,
                    row.gender,
                    row.verification_notes,
                    row.confidence_score,
                    json.dumps(row.provenance_metadata),
                    now_str
                ))
        finally:
            conn.close()

    def apply_cache_to_row(self, row: CanonicalRow) -> bool:
        """
        Populates a row from cache if a valid cached entry exists.
        Strictly rejects corrupted records where captions or hashtags were cached as scripts.
        Returns True if cache hit was applied.
        """
        cached = self.get_cached_record(row.shortcode)
        if cached and cached.get("processing_state") in [ProcessingState.SUCCESS.value, ProcessingState.PARTIAL.value]:
            script = (cached.get("verified_whole_script") or "").strip()
            status = cached.get("script_scraping_status") or ""

            # Strict cache integrity check: Never load captions or hashtag dumps as transcribed speech
            if status in [ScriptStatus.TRANSCRIBED.value, "Transcribed from Spoken Audio"]:
                if "#" in script or "[AI Audio Note" in script or script.startswith("Check out this reel by @"):
                    logger.info(f"Invalidating corrupted cache record for {row.shortcode} (caption falsely stored as script)")
                    return False

            row.spoken_hook = cached.get("spoken_hook") or ""
            row.verified_whole_script = script
            row.script_scraping_status = status or row.script_scraping_status
            if cached.get("scraped_views") is not None:
                row.scraped_views = cached.get("scraped_views")
            if cached.get("scraped_likes") is not None:
                row.scraped_likes = cached.get("scraped_likes")
            if cached.get("scraped_comments") is not None:
                row.scraped_comments = cached.get("scraped_comments")
            if cached.get("concept_bucketing"):
                row.concept_bucketing = cached.get("concept_bucketing")
            if cached.get("bucket"):
                row.bucket = cached.get("bucket")
            if cached.get("language"):
                row.language = cached.get("language")
            if cached.get("gender"):
                row.gender = cached.get("gender")
            row.processing_state = ProcessingState(cached.get("processing_state"))
            row.verification_notes += "[Cached Analysis Applied]; "
            return True
        return False
