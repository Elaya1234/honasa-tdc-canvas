import os
import sys
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Tuple

from .config import IG_COLLECTOR_DIR, DEFAULT_REQUEST_DELAY, MAX_RETRIES
from .models import CanonicalRow, ProcessingState, ScriptStatus, VerificationStatus

logger = logging.getLogger(__name__)

# Safely expose ig_reel_collector components without modifying them
if IG_COLLECTOR_DIR not in sys.path:
    sys.path.insert(0, IG_COLLECTOR_DIR)

try:
    from ig_extractor import InstagramExtractor, extract_shortcode
    from analyzer import ReelAnalyzer
    from models import ReelRawMetrics, ReelAIAnalysis
except ImportError:
    from extractor import InstagramExtractor, extract_shortcode
    from analyzer import ReelAnalyzer
    from models import ReelRawMetrics, ReelAIAnalysis


class AuthState:
    NOT_CONFIGURED = "NOT CONFIGURED"
    CONNECTED = "CONNECTED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


class CollectorAdapter:
    """
    Safely wraps ig_reel_collector with:
    - Bounded retries and exponential backoff
    - Session expiration trap & circuit breaker
    - Rate-limiting throttler
    - Credential isolation (never leaks session IDs or tokens)
    - Reel failure isolation (one failure never terminates batch)
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        apify_token: Optional[str] = None,
        session_id: Optional[str] = None,
        engine_preference: str = "auto",
        delay_seconds: float = DEFAULT_REQUEST_DELAY
    ):
        self.gemini_api_key = (gemini_api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        self.apify_token = (apify_token or os.environ.get("APIFY_TOKEN", "")).strip()
        self.session_id = (session_id or os.environ.get("INSTAGRAM_SESSION_ID", "")).strip()
        self.engine_preference = engine_preference
        self.delay_seconds = delay_seconds

        self._auth_state = AuthState.CONNECTED if self.session_id else AuthState.NOT_CONFIGURED
        self._lock = threading.Lock()
        self._last_request_time = 0.0

        # Initialize underlying collector components
        self.extractor = InstagramExtractor(
            apify_token=self.apify_token if self.apify_token else None,
            session_id=self.session_id if self.session_id else None
        )
        self.analyzer = ReelAnalyzer(api_key=self.gemini_api_key)

    @property
    def auth_state(self) -> str:
        return self._auth_state

    def update_session_id(self, new_session_id: str):
        with self._lock:
            self.session_id = (new_session_id or "").strip()
            self._auth_state = AuthState.CONNECTED if self.session_id else AuthState.NOT_CONFIGURED
            self.extractor = InstagramExtractor(
                apify_token=self.apify_token if self.apify_token else None,
                session_id=self.session_id if self.session_id else None
            )

    def _throttle(self):
        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay_seconds:
                time.sleep(self.delay_seconds - elapsed)
            self._last_request_time = time.time()

    def process_single_reel(
        self,
        row: CanonicalRow,
        download_media: bool = True,
        temp_dir: Optional[str] = None
    ) -> CanonicalRow:
        """
        Processes a single Reel with full failure isolation and bounded retries.
        """
        if not row.live_link or not row.shortcode:
            row.processing_state = ProcessingState.FAILED
            row.script_scraping_status = ScriptStatus.UNAVAILABLE.value
            row.verification_notes += "Missing Reel URL or shortcode; "
            return row

        self._throttle()
        row.processing_state = ProcessingState.PROCESSING

        raw_metrics: Optional[ReelRawMetrics] = None
        media_path: Optional[str] = None

        # 1. Extraction with Bounded Retry
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # If session was detected as expired, do not retry authenticated requests
                if self._auth_state == AuthState.EXPIRED:
                    self.extractor.session_id = ""

                batch_res = self.extractor.extract_batch(
                    urls=[row.live_link],
                    engine_preference=self.engine_preference
                )
                if batch_res:
                    raw_metrics = batch_res[0]
                    # Check for auth expiry signal
                    if "login" in str(raw_metrics.error_message or "").lower() or "checkpoint" in str(raw_metrics.error_message or "").lower():
                        with self._lock:
                            self._auth_state = AuthState.EXPIRED
                        logger.warning(f"Instagram session expired during Reel {row.shortcode}")
                    break
            except Exception as e:
                err_str = str(e)
                if attempt == MAX_RETRIES:
                    logger.warning(f"All extraction retries failed for {row.live_link}: {err_str}")
                    row.verification_notes += f"Extraction retry failed: {err_str[:80]}; "
                time.sleep(attempt * 1.5)

        if not raw_metrics:
            raw_metrics = ReelRawMetrics(
                reel_url=row.normalized_url or row.live_link,
                shortcode=row.shortcode,
                creator_username=row.creator or "Unknown",
                status="Failed"
            )

        # Update Scraped Metrics if available (Preserving source of truth)
        if raw_metrics.current_views > 0:
            row.scraped_views = raw_metrics.current_views
        if raw_metrics.likes > 0:
            row.scraped_likes = raw_metrics.likes
        if raw_metrics.comments > 0:
            row.scraped_comments = raw_metrics.comments
        if raw_metrics.caption:
            row.caption = raw_metrics.caption

        # 2. Media Download & Audio Extraction (if enabled and not demo mode)
        if download_media and temp_dir and os.path.exists(temp_dir) and self.engine_preference != "demo":
            try:
                media_path = self.extractor.download_video_or_audio(raw_metrics, temp_dir)
            except Exception as e:
                logger.debug(f"Media download error for {row.shortcode}: {e}")

        # 3. Multimodal Analysis via Gemini
        ai_analysis: Optional[ReelAIAnalysis] = None
        try:
            ai_analysis = self.analyzer.analyze(raw_metrics, media_file_path=media_path)
        except Exception as e:
            logger.warning(f"Gemini analysis exception for {row.shortcode}: {e}")

        # 4. Strict Spoken Script vs Caption Separation
        if ai_analysis:
            has_real_media = media_path and os.path.exists(media_path) and os.path.getsize(media_path) > 1024
            
            raw_cap = (raw_metrics.caption or "").strip()
            script_text = (ai_analysis.whole_script or "").strip()
            
            # Check if this analysis was a heuristic fallback or caption reuse
            is_fallback = (
                any("fallback mode" in str(s).lower() for s in (ai_analysis.summary_bullet_points or []))
                or (bool(raw_cap) and script_text == raw_cap)
                or (bool(raw_cap) and "#" in script_text and "#" in raw_cap and script_text.startswith(raw_cap[:min(30, len(raw_cap))]))
                or script_text.startswith("[AI Audio Note")
                or script_text.startswith("Check out this reel by @")
            )

            is_no_speech = (
                "no spoken" in script_text.lower()
                or "instrumental" in script_text.lower()
                or "music only" in script_text.lower()
                or not script_text
            )

            if has_real_media and script_text and not is_fallback and not is_no_speech:
                # Real speech transcribed from audio
                row.spoken_hook = ai_analysis.hook or ""
                row.verified_whole_script = ai_analysis.whole_script
                row.script_scraping_status = ScriptStatus.TRANSCRIBED.value
                row.language = ai_analysis.language or row.language
                row.processing_state = ProcessingState.SUCCESS
            elif has_real_media and is_no_speech:
                row.spoken_hook = ""
                row.verified_whole_script = ""
                row.script_scraping_status = ScriptStatus.NO_SPEECH.value
                row.processing_state = ProcessingState.PARTIAL
                row.verification_notes += "Audio track contains only music/effects without spoken speech; "
            else:
                # Video media was not obtainable or script could not be transcribed
                row.spoken_hook = ""
                row.verified_whole_script = ""
                # Retain caption separately in row.caption, NEVER substitute for script
                row.script_scraping_status = ScriptStatus.CAPTION_ONLY.value
                row.processing_state = ProcessingState.PARTIAL
                row.verification_notes += "Spoken audio unavailable; caption preserved separately; "

            # Update verified style/concept if confident
            if ai_analysis.concept_bucketing:
                row.concept_bucketing = ai_analysis.concept_bucketing
        else:
            row.spoken_hook = ""
            row.verified_whole_script = ""
            row.script_scraping_status = ScriptStatus.CAPTION_ONLY.value
            row.processing_state = ProcessingState.PARTIAL

        # Clean up temporary media file to prevent disk exhaustion
        if media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception:
                pass

        return row
