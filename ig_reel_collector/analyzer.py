import os
import time
import json
import logging
from typing import Optional, List

from models import ReelRawMetrics, ReelAIAnalysis

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are an expert social media and short-form video intelligence analyst.
You will be provided with an Instagram Reel (video/audio) along with its creator information and caption.
Your job is to analyze the video and audio thoroughly and return a structured JSON matching the schema.

Guidelines:
1. Whole script extraction:
   - Provide a complete, verbatim, word-for-word transcript of the entire audio spoken in the video.
   - Do NOT just copy the written caption. Transcribe what is actually spoken by the presenter/narrator.
   - If Hindi or Hinglish is spoken, transcribe in conversational Latin script or Devanagari accurately reflecting what is said.
2. Hook:
   - Extract the exact opening sentence or first 3-5 seconds of spoken speech used to capture the audience's attention.
3. Language:
   - Identify the primary spoken language (e.g., Hinglish, Hindi, English, Tamil, Spanish, etc.).
4. Genre / Category / Sub Cat:
   - Provide a clear 3-tier hierarchy based on the content topic, format: 'Genre > Category > Sub Category'
   - Examples: 'Beauty & Personal Care > Skincare > Face Wash', 'Health & Fitness > Nutrition > Whey Protein'.
5. Concept Bucketing:
   - Identify the style and format of the content (e.g., 'Product Review', 'Problem-Solution Ad', 'Tutorial / How-To', 'Comedy Skit', 'GRWM', 'Unboxing', 'Transformation', 'Day In The Life').
6. Gender:
   - Listen to the presenter's voice and examine the presenter in the video to accurately identify their gender ('Male', 'Female', 'Non-binary', or 'Brand / Neutral').
"""

class ReelAnalyzer:
    """Analyzes Instagram Reel content using Google Gemini Multimodal API."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "").strip()
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai Client: {e}")

    def analyze(self, raw_metric: ReelRawMetrics, media_file_path: Optional[str] = None) -> ReelAIAnalysis:
        """
        Runs multimodal video/audio analysis on the reel with automatic fallback models.
        """
        if not self.client or not self.api_key:
            return self._generate_fallback_analysis(raw_metric)

        uploaded_file = None
        try:
            from google import genai

            contents = []

            # 1. Upload video file if available
            if media_file_path and os.path.exists(media_file_path) and os.path.getsize(media_file_path) > 1024:
                try:
                    uploaded_file = self.client.files.upload(file=media_file_path)
                    # Poll until ACTIVE (up to 45 seconds for large video files)
                    max_wait = 45
                    waited = 0
                    while uploaded_file.state.name == "PROCESSING" and waited < max_wait:
                        time.sleep(2)
                        waited += 2
                        uploaded_file = self.client.files.get(name=uploaded_file.name)

                    if uploaded_file.state.name == "ACTIVE":
                        contents.append(uploaded_file)
                    else:
                        logger.warning(f"Media file state is {uploaded_file.state.name} after {waited}s")
                except Exception as e:
                    logger.warning(f"Failed to upload media to Gemini: {e}")

            prompt = f"""
Creator Username: @{raw_metric.creator_username}
Post Caption: {raw_metric.caption}
Reel URL: {raw_metric.reel_url}

Please analyze the video audio thoroughly and provide the exact verbatim transcript, spoken hook, language, category, concept style, and creator gender.
"""
            contents.append(prompt)

            # Models priority list: prioritizing high-quota, resilient models
            models_to_try = [self.model_name]
            for fallback in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-flash-lite-latest", "gemini-3.6-flash"]:
                if fallback not in models_to_try:
                    models_to_try.append(fallback)

            last_error = None
            for m in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=m,
                        contents=contents,
                        config={
                            "system_instruction": ANALYSIS_SYSTEM_PROMPT,
                            "response_mime_type": "application/json",
                            "response_schema": ReelAIAnalysis,
                        },
                    )
                    if response and response.text:
                        analysis = ReelAIAnalysis.model_validate_json(response.text)
                        return analysis
                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini model {m} call failed: {e}. Trying next fallback...")
                    time.sleep(1)

            if last_error:
                raise last_error

        except Exception as e:
            logger.error(f"All Gemini models failed: {e}")
            return self._generate_fallback_analysis(raw_metric, error_note=str(e))
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

        return self._generate_fallback_analysis(raw_metric)

    def _generate_fallback_analysis(self, raw_metric: ReelRawMetrics, error_note: Optional[str] = None) -> ReelAIAnalysis:
        """Heuristic fallback only when no API key is provided or all models are offline."""
        caption = raw_metric.caption or ""
        caption_lower = caption.lower()
        username_lower = raw_metric.creator_username.lower()

        # Language detection
        lang = "English"
        if any(w in caption_lower for w in ["karo", "hai", "bhai", "ye", "aap", "mera", "meri", "karein", "dekho", "aur", "pe", "mein"]):
            lang = "Hinglish"

        # Smarter Gender heuristic
        male_cues = ["kartik", "naman", "bunny", "ahmad", "rohit", "rahul", "boy", "man", "bro", "bhai", "guy", "amit", "vikas", "varun", "sharma"]
        female_cues = ["pawani", "ria", "she", "her", "girl", "woman", "diva", "priya", "pooja", "neha", "ananya", "shruti", "shreya"]
        brand_cues = ["honasa", "mamaearth", "derma", "official", "india", "science", "company", "store", "ai"]

        if any(c in username_lower for c in brand_cues):
            gender = "Brand / Neutral"
        elif any(c in username_lower for c in male_cues):
            gender = "Male"
        elif any(c in username_lower for c in female_cues):
            gender = "Female"
        else:
            gender = "Not Specified"

        # Concept bucketing heuristic
        if any(w in caption_lower for w in ["routine", "step 1", "how to", "tutorial", "apply"]):
            concept = "Tutorial / How-To"
        elif any(w in caption_lower for w in ["pov", "when you", "😂", "funny", "humor", "relatable"]):
            concept = "Comedy Skit"
        elif any(w in caption_lower for w in ["honest", "review", "results", "rating", "tested"]):
            concept = "Product Review"
        elif any(w in caption_lower for w in ["struggling", "fix", "switch to", "power actives"]):
            concept = "Problem-Solution Ad"
        elif any(w in caption_lower for w in ["grwm", "get ready"]):
            concept = "GRWM"
        else:
            concept = "Informative / Explainer"

        # Genre & Category
        if any(w in caption_lower for w in ["face wash", "cleanse", "cleanser"]):
            genre = "Beauty & Personal Care > Skincare > Face Wash"
        elif any(w in caption_lower for w in ["skin", "serum", "acne", "spf", "sunscreen", "glow"]):
            genre = "Beauty & Personal Care > Skincare > Daily Care"
        elif any(w in caption_lower for w in ["hair", "shampoo", "oil"]):
            genre = "Beauty & Personal Care > Haircare > Daily Care"
        else:
            genre = "Beauty & Personal Care > Skincare > Daily Care"

        # Hook & Script extraction
        lines = [line.strip() for line in caption.split("\n") if line.strip()]
        hook = lines[0] if lines else f"Hey guys! Today we are looking at @{raw_metric.creator_username}'s latest reel!"
        if error_note:
            script = f"[AI Audio Note: {error_note}] | Caption: {caption}" if caption else f"[AI Audio Note: {error_note}]"
        else:
            script = caption if caption else f"Check out this reel by @{raw_metric.creator_username}."

        return ReelAIAnalysis(
            language=lang,
            whole_script=script,
            hook=hook[:150],
            genre_category_subcat=genre,
            concept_bucketing=concept,
            gender=gender,
            summary_bullet_points=[
                f"Format: {concept}",
                f"Category: {genre}",
                "Fallback mode: Media was not transcribed by Gemini."
            ]
        )
