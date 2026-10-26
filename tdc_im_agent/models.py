from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

class ProcessingState(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNAVAILABLE = "UNAVAILABLE"

class VerificationStatus(str, Enum):
    VERIFIED = "Verified"
    CORRECTED = "Corrected"
    NEEDS_REVIEW = "Needs Review"
    UNAVAILABLE = "Unavailable"
    NOT_AVAILABLE = "Not Available"
    FAILED = "Failed"

class ScriptStatus(str, Enum):
    TRANSCRIBED = "Transcribed from Spoken Audio"
    NO_SPEECH = "No spoken speech (Audio track only, only caption available)"
    CAPTION_ONLY = "cant scrap script, only caption"
    UNAVAILABLE = "Unavailable / Cannot Verify"

class DuplicateType(str, Enum):
    UNIQUE = "UNIQUE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    INTENTIONAL_REUSE = "INTENTIONAL_REUSE"

class CanonicalRow(BaseModel):
    """Unified canonical data structure representing a single Reel campaign record."""
    source_row: int
    source_sheet: str = "Sheet1"
    
    # Platform / Creative Metadata
    live_status: str = "Live"
    sub_cat: str = ""
    creator: str = ""
    channel_standard_name: str = ""
    creator_ig_link: str = ""
    product: str = ""
    sku_code: str = ""
    normalized_sku: str = ""
    stage: str = "IG Reel"
    epd_npd: str = ""
    count: int = 1
    range_col: str = ""
    asset: str = ""
    agency: str = ""
    gender: str = "Female"
    follower_base: int = 0
    tier: str = ""
    language: str = "English"
    genre: str = ""
    category: str = "Influencer"
    
    # Financial / Planned Metrics
    er_planned: float = 0.0
    average_views: int = 0
    planned_cpv: float = 0.0
    cost: float = 0.0
    counter: float = 0.0
    final_costs: float = 0.0
    commission: float = 0.0
    total_spends: float = 0.0
    video_status: str = "Live"
    
    # Instagram URLs & Dates
    live_link: str = ""
    normalized_url: str = ""
    shortcode: str = ""
    live_date: Optional[str] = None
    
    # Engagement Metrics
    views_organic: int = 0
    views_brand_collab: int = 0
    video_cpv: float = 0.0
    likes: int = 0
    comments: int = 0
    actual_er: float = 0.0
    
    # Categorization & Creative
    concept_bucketing: str = ""
    bucket: str = "Problem solution"
    
    # Verified Content & Transcripts
    spoken_hook: str = ""
    verified_whole_script: str = ""
    script_scraping_status: str = ScriptStatus.TRANSCRIBED.value
    caption: str = ""
    
    # Live Scraped Metrics
    scraped_views: Optional[int] = None
    scraped_likes: Optional[int] = None
    scraped_comments: Optional[int] = None
    
    # Auditing, State & Verification
    verification_notes: str = ""
    confidence_score: float = 1.0
    processing_state: ProcessingState = ProcessingState.QUEUED
    duplicate_type: DuplicateType = DuplicateType.UNIQUE
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_row_values(self) -> List[Any]:
        """Returns standard 45-column row matching the TDC standardized sheet."""
        return [
            self.live_status,
            self.sub_cat,
            self.creator,
            self.channel_standard_name or f"=LOWER(SUBSTITUTE(C{self.source_row},\" \",\"_\"))",
            self.creator_ig_link,
            self.product,
            self.sku_code,
            self.stage,
            self.epd_npd,
            self.count,
            self.range_col,
            self.asset,
            self.agency,
            self.gender,
            self.follower_base,
            self.tier,
            self.language,
            self.genre,
            self.category,
            self.er_planned,
            self.average_views,
            self.planned_cpv,
            self.cost,
            self.counter,
            self.final_costs,
            self.commission,
            self.total_spends,
            self.video_status,
            self.live_link,
            self.live_date or "",
            self.views_organic,
            self.views_brand_collab,
            self.video_cpv,
            self.likes,
            self.comments,
            self.actual_er,
            self.concept_bucketing,
            self.bucket,
            self.spoken_hook,
            self.verified_whole_script,
            self.script_scraping_status,
            self.scraped_views,
            self.scraped_likes,
            self.scraped_comments,
            self.verification_notes
        ]

class DataQualityRecord(BaseModel):
    reel: str
    field_name: str
    original_value: str
    verified_value: str
    status: VerificationStatus
    confidence: str
    reason: str
    source: str
    timestamp: str

class ProcessingLogRecord(BaseModel):
    timestamp: str
    record_id: str
    operation: str
    status: str
    duration_sec: float
    retry_count: int
    source: str
    error_code: str = ""
    error_message: str = ""

class QAValidationReport(BaseModel):
    file_path: str
    file_exists: bool
    sheets_found: List[str]
    total_reels_input: int
    total_reels_output: int
    reels_reconciled: bool
    total_spend_input: float
    total_spend_output: float
    spend_reconciled: bool
    total_views_input: int
    total_views_output: int
    views_reconciled: bool
    unique_creators: int
    broken_formulas: List[str] = Field(default_factory=list)
    qa_status: str = "PASSED"
    reconciliation_status: str = "PASSED"
    final_completion_state: str = "COMPLETE" # COMPLETE, PARTIAL, FAILED
    discrepancy_reasons: List[str] = Field(default_factory=list)
