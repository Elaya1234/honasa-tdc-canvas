# ======================================================================
# PRODUCT PAGE INTELLIGENCE EXTRACTOR
# Deep LLM-Powered Product Formulation, Claim & Consumer Insight Extractor
# ======================================================================

import os
import re
import sys
import json

try:
    from google import genai
except ImportError:
    genai = None

# Load API key from workspace .env or environment
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    env_paths = [
        r"C:\Users\elaya.n\Documents\HONASA TDC\.env",
        r"C:\Users\elaya.n\Documents\HONASA TDC\ig_reel_collector\.env"
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            API_KEY = line.strip().split("=", 1)[1].strip("\"' ")
                            break
            except Exception:
                pass
        if API_KEY:
            break

def extract_structured_intelligence(pdp_data):
    """
    Analyzes raw PDP details (title, bullets, description, A+ content, specifications)
    and formats them into the exact structured sections requested by Honasa researchers:
      - description
      - key_benefits
      - what_it_does_not_do
      - texture_and_finish
      - who_should_use_it
      - who_should_avoid_it
      - common_mistakes_to_avoid
      - common_questions
      - ingredients_breakdown
      - extra_brand_info
    """
    # Prepare text summary of the product
    title = pdp_data.get('title', '')
    brand = pdp_data.get('brand', '')
    platform = pdp_data.get('platform', '')
    bullets = "\n".join([f"- {b}" for b in pdp_data.get('bullets', [])])
    specs = "\n".join([f"- {k}: {v}" for k, v in pdp_data.get('specifications', {}).items()])
    aplus = "\n".join([f"> {t}" for t in pdp_data.get('aplus_text', [])])
    
    raw_context = f"""
PRODUCT TITLE: {title}
BRAND: {brand}
PLATFORM: {platform}
PRICE: {pdp_data.get('price', '')} (MRP: {pdp_data.get('mrp', '')})
RATING: {pdp_data.get('rating', '')}

BULLETS & HIGHLIGHTS:
{bullets}

SPECIFICATIONS & ATTRIBUTES:
{specs}

A+ & DETAILED COPY:
{aplus}
"""

    if not API_KEY or genai is None:
        return fallback_heuristics(pdp_data)

    prompt = f"""
You are an expert cosmetic formulation scientist and e-commerce competitive intelligence analyst for Honasa Consumer (The Derma Co, Mamaearth, Aqualogica).
Analyze the following e-commerce product detail page (PDP) content and extract high-precision, structured intelligence.

{raw_context}

Return a STRICT JSON object with these EXACT keys (do not include markdown ticks around json, just the raw valid json):
{{
  "description": "Comprehensive product overview and clinical positioning.",
  "key_benefits": ["Benefit 1 with active ingredient mechanism", "Benefit 2...", "..."],
  "what_it_does_not_do": ["Clear limitation 1 (e.g. what this product/sunscreen does NOT do)", "Limitation 2...", "..."],
  "texture_and_finish": "Detailed breakdown of texture (e.g. watery gel, rich cream, mousse), skin feel, absorption speed, white cast, and finish (e.g. matte, dewy, invisible, non-greasy).",
  "who_should_use_it": ["Target skin type 1 (e.g. Oily / Acne-prone)", "Key concerns addressed (e.g. clogged pores, blackheads)", "..."],
  "who_should_avoid_it": ["Who should avoid or exercise caution (e.g. extremely dry/compromised barrier, open active cystic lesions, known active allergies)", "..."],
  "common_mistakes_to_avoid": ["Application mistake 1 (e.g. using on damp skin if it causes irritation, skipping patch test, not reapplying)", "Mistake 2...", "..."],
  "common_questions": [
    {{"question": "Frequent question 1", "answer": "Clear factual answer based on product formulation"}},
    {{"question": "Frequent question 2", "answer": "Clear factual answer"}}
  ],
  "ingredients_breakdown": ["Key active 1: role & percentage if known", "Key active 2...", "Full INCI base if provided"],
  "extra_brand_info": ["Certifications (e.g. Dermatologically tested, Cruelty-free)", "Clinical claims", "Packaging & origin"]
}}
"""

    models_to_try = ['gemini-2.5-flash', 'gemini-3.6-flash', 'gemini-flash-lite-latest', 'gemini-2.0-flash']
    last_error = None

    for m in models_to_try:
        try:
            client = genai.Client(api_key=API_KEY)
            response = client.models.generate_content(
                model=m,
                contents=prompt,
            )
            text = response.text.strip()
            # Clean any markdown code fences if present
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            structured = json.loads(text)
            return structured
        except Exception as e:
            last_error = e
            continue

    print("All Gemini models failed for PDP intelligence:", last_error)
    return fallback_heuristics(pdp_data)

def fallback_heuristics(pdp_data):
    """Fallback rule-based intelligence generator if API is unavailable."""
    title = pdp_data.get('title', 'Product')
    bullets = pdp_data.get('bullets', [])
    specs = pdp_data.get('specifications', {})
    
    return {
        "description": " ".join(bullets[:2]) if bullets else title,
        "key_benefits": bullets if bullets else ["Deep cleansing and nourishment", "Gentle everyday formulation"],
        "what_it_does_not_do": [
            "Does not replace a complete clinical dermatological treatment for severe chronic conditions",
            "Does not provide instant overnight results without regular consistent usage",
            "Does not offer sun protection unless SPF rating is specifically stated"
        ],
        "texture_and_finish": specs.get("Item Form", "Lightweight foaming / gel formulation designed for rapid absorption without heavy residue."),
        "who_should_use_it": [specs.get("Skin Type", "Suitable for all skin types, especially oily and acne-prone skin"), "Individuals looking for active pore care"],
        "who_should_avoid_it": ["Individuals with known allergies to active ingredients", "Skin with broken or severely irritated barriers without patch test"],
        "common_mistakes_to_avoid": [
            "Skipping a patch test before first use",
            "Over-using or combining with too many strong exfoliating actives simultaneously",
            "Failing to follow up with sunscreen during daytime use"
        ],
        "common_questions": [
            {"question": "Can this be used daily?", "answer": "Yes, as per brand directions for daily morning and evening skincare routines."},
            {"question": "Is it dermatologically tested?", "answer": "Formulated following brand clinical safety and testing standards."}
        ],
        "ingredients_breakdown": [specs.get("Special Ingredients", "Key active formulation")],
        "extra_brand_info": [f"Platform: {pdp_data.get('platform', '')}", f"Price: {pdp_data.get('price', '')}"]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("   PRODUCT PAGE INTELLIGENCE EXTRACTOR")
    print("   AI-Powered Formulation, Claim & Consumer Insight Extractor")
    print("=" * 60)
    
    # Check if a JSON file was passed
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as jf:
            sample_data = json.load(jf)
        print(f"\n[INFO] Loaded product: {sample_data.get('title', 'Unknown')}")
    else:
        # Default demo product
        print("\n[INFO] Running demo test product extraction...")
        sample_data = {
            "title": "The Derma Co 1% Hyaluronic Sunscreen Aqua Gel SPF 50 PA++++ (50g)",
            "brand": "The Derma Co",
            "platform": "The Derma Co D2C",
            "price": "₹499",
            "mrp": "₹499",
            "rating": "4.6",
            "bullets": [
                "Protects against UVA & UVB rays with SPF 50 & PA++++",
                "Non-greasy, lightweight texture with zero white cast",
                "Formulated with 1% Hyaluronic Acid & Vitamin E for hydration"
            ],
            "specifications": {
                "Item Form": "Aqua Gel",
                "Skin Type": "All Skin Types, Oily, Normal",
                "Special Ingredients": "1% Hyaluronic Acid, Vitamin E, Titanium Dioxide"
            },
            "aplus_text": [
                "Broad Spectrum Protection with Blue Light defense for screen-heavy daily work.",
                "Safe dermatological formulation tested by certified cosmetic labs."
            ]
        }
    
    print("[INFO] Extracting structured intelligence via Gemini AI...")
    result = extract_structured_intelligence(sample_data)
    print("\n" + json.dumps(result, indent=2))
    print("\n[SUCCESS] Extraction completed successfully!")
