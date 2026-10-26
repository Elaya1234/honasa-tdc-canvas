from typing import Optional, List
from pydantic import BaseModel, Field

class ReelRawMetrics(BaseModel):
    """Raw engagement metrics and metadata extracted for an Instagram Reel."""
    reel_url: str
    shortcode: str
    creator_username: str = "Unknown"
    creator_profile_url: str = ""
    current_views: int = 0
    likes: int = 0
    comments: int = 0
    caption: str = ""
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    upload_date: Optional[str] = None
    status: str = "Pending"
    error_message: Optional[str] = None


class ReelAIAnalysis(BaseModel):
    """AI-inferred analysis from video/audio transcript using Google Gemini."""
    language: str = Field(
        description="Identified primary spoken language (e.g. English, Hindi, Hinglish, Spanish, etc.)"
    )
    whole_script: str = Field(
        description="Verbatim, complete text transcript of all spoken audio/speech in the video"
    )
    hook: str = Field(
        description="The opening statement or first 3-5 seconds of text spoken to capture attention"
    )
    genre_category_subcat: str = Field(
        description="Hierarchical classification based on script content in format 'Genre > Category > Sub Category' (e.g., 'Beauty & Personal Care > Skincare > Anti-Aging Serum')"
    )
    concept_bucketing: str = Field(
        description="Style and format of the video content (e.g., 'Product Review', 'Tutorial / How-To', 'Comedy Skit', 'GRWM', 'Unboxing', 'Transformation / Before-After', 'Informative / Explainer')"
    )
    gender: str = Field(
        description="Inferred gender of the presenter/creator based on voice audio and creator name (e.g., 'Female', 'Male', 'Non-binary', or 'Brand / Neutral')"
    )
    summary_bullet_points: List[str] = Field(
        default_factory=list,
        description="Key takeaways or summary points of the video"
    )


class ReelProcessedRecord(BaseModel):
    """Final unified record combining metrics and AI content analysis."""
    reel_url: str
    channel_standard_name: str
    creator_ig_link: str
    current_views: int
    likes: int
    comments: int
    language: str
    whole_script: str
    hook: str
    genre_category_subcat: str
    concept_bucketing: str
    gender: str
    caption: str = ""
    duration_seconds: Optional[float] = None
    upload_date: Optional[str] = None
    status: str = "Success"
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "Reel URL": self.reel_url,
            "Channel Standard Name": self.channel_standard_name,
            "Creator IG Link": self.creator_ig_link,
            "Current Views": self.current_views,
            "Likes": self.likes,
            "Comments": self.comments,
            "Language": self.language,
            "Whole script extraction": self.whole_script,
            "Hook": self.hook,
            "Genre / Category / Sub Cat": self.genre_category_subcat,
            "Concept Bucketing": self.concept_bucketing,
            "Gender": self.gender,
            "Status": self.status,
            "Caption": self.caption,
        }
