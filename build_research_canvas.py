import os
import json
import sys
import html
import re

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"C:\Users\elaya.n\Documents\HONASA TDC"
FACEWASH_DIR = os.path.join(BASE_DIR, "PDP_Research_Board", "1FACEWASH")
SUNSCREEN_DIR = os.path.join(BASE_DIR, "PDP_Research_Board", "2 SUNSCREEN")
SERUM_DIR = os.path.join(BASE_DIR, "PDP_Research_Board", "3 SERUM")
SHAMPOO_DIR = os.path.join(BASE_DIR, "PDP_Research_Board", "4 SHAMPOO")

OUTPUT_HTML = os.path.join(BASE_DIR, "PDP_Competitive_Research_Canvas.html")
OUTPUT_BAT = os.path.join(BASE_DIR, "Launch_Research_Canvas.bat")

print("Starting Full 4-Category Bright Competitive Research Canvas Generator...")

def process_directory(base_dir, cat_prefix, rel_base_folder):
    if not os.path.exists(base_dir):
        print(f"Warning: Directory not found: {base_dir}")
        return []
        
    entries = sorted(os.listdir(base_dir))
    processed = []
    
    for folder in entries:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
            
        json_path = os.path.join(folder_path, "PDP_Data.json")
        pdp_data = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as jf:
                    pdp_data = json.load(jf)
            except Exception:
                pass
                
        # Scan local images
        imgs_path = os.path.join(folder_path, "images")
        local_images = []
        if os.path.exists(imgs_path):
            for f in sorted(os.listdir(imgs_path)):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    rel_path = f"PDP_Research_Board/{rel_base_folder}/{folder}/images/{f}"
                    local_images.append(rel_path)
                    
        # Scan local videos
        vids_path = os.path.join(folder_path, "videos")
        local_videos = []
        if os.path.exists(vids_path):
            for f in sorted(os.listdir(vids_path)):
                if f.lower().endswith(('.mp4', '.webm', '.mov')):
                    rel_path = f"PDP_Research_Board/{rel_base_folder}/{folder}/videos/{f}"
                    local_videos.append(rel_path)
                    
        title = pdp_data.get('title', '').strip()
        brand = pdp_data.get('brand', '').strip()
        platform = pdp_data.get('platform', '').strip()
        url = pdp_data.get('url', '').strip()
        price = pdp_data.get('price', '').strip()
        mrp = pdp_data.get('mrp', '').strip()
        availability = pdp_data.get('availability', '').strip()
        rating = pdp_data.get('rating', '').strip()
        review_count = str(pdp_data.get('review_count', '')).strip()
        bullets = pdp_data.get('bullets', [])
        overview = pdp_data.get('overview_table', {})
        technical = pdp_data.get('technical_details', {})
        important_info = pdp_data.get('important_info', {})
        
        # DISCARD EMPTY DUMMY / REDIRECT FOLDERS
        is_dummy = False
        comb_text = (folder + " " + title).lower()
        if len(local_images) == 0 and len(local_videos) == 0:
            if not bullets and len(important_info) == 0:
                is_dummy = True
        if any(d in comb_text for d in ['amazon product', 'search', 'just a moment', 'oops!']):
            if len(local_images) == 0 and len(local_videos) == 0:
                is_dummy = True
                
        if is_dummy:
            continue
            
        # Normalize Platform
        plat_norm = "Brand D2C Store"
        p_low = platform.lower()
        if "amazon" in p_low:
            plat_norm = "Amazon"
        elif "nykaa" in p_low:
            plat_norm = "Nykaa"
        elif "flipkart" in p_low:
            plat_norm = "Flipkart"
        elif "blinkit" in p_low:
            plat_norm = "Blinkit"
        elif "d2c" in p_low or ".in" in p_low or ".com" in p_low or "store" in p_low:
            plat_norm = "Brand D2C Store"
            
        # Canonical Brand
        comb = (folder + " " + title + " " + brand).lower()
        can_brand = "Other"
        if "derma" in comb:
            can_brand = "The Derma Co"
        elif "ordinary" in comb:
            can_brand = "The Ordinary"
        elif "minimalist" in comb:
            can_brand = "Minimalist"
        elif "dot" in comb and "key" in comb:
            can_brand = "Dot & Key"
        elif any(k in comb for k in ["l'oreal", "loreal", "loral", "revitalift", "glycolic bright", "crystal", "defender", "fall resist"]):
            can_brand = "L'Oréal Paris"
        elif "foxtale" in comb:
            can_brand = "Foxtale"
        elif any(k in comb for k in ["cetaphil", "चेटाफिल", "सेटाफिल"]):
            can_brand = "Cetaphil"
        elif "himalaya" in comb:
            can_brand = "Himalaya"
        elif "simple" in comb:
            can_brand = "Simple"
            
        # Target SKU assignment across categories
        target_skus = []
        if cat_prefix == "facewash":
            if can_brand == "The Derma Co":
                if "sali-cinamide" in comb or "sali cinamide" in comb:
                    target_skus.append("sku4")
                elif "1%" in comb and "salicylic" in comb:
                    target_skus.append("sku1")
                elif "1%" in comb and "kojic" in comb:
                    target_skus.append("sku2")
                elif "2%" in comb and "salicylic" in comb:
                    target_skus.append("sku3")
                elif "salicylic" in comb:
                    target_skus.extend(["sku1", "sku3"])
                elif "kojic" in comb:
                    target_skus.append("sku2")
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Minimalist":
                if any(k in comb for k in ["salicylic", "anti-acne", "lha"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                elif any(k in comb for k in ["ala", "glycolic", "alpha lipoic", "brightening"]):
                    target_skus.append("sku2")
                elif any(k in comb for k in ["aquaporin", "marula"]):
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Dot & Key":
                if any(k in comb for k in ["cica", "salicylic"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                elif any(k in comb for k in ["strawberry", "vitamin c", "bright", "kojic"]):
                    target_skus.append("sku2")
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "L'Oréal Paris":
                if any(k in comb for k in ["glycolic"]):
                    target_skus.append("sku2")
                elif any(k in comb for k in ["crystal", "salicylic", "micro-essence"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                elif any(k in comb for k in ["hyaluronic", "revitalift"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Foxtale":
                if any(k in comb for k in ["oil & acne", "acne", "true clarity"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                elif any(k in comb for k in ["super glow", "glow", "detan", "tan", "papaya", "kojic"]):
                    target_skus.append("sku2")
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Cetaphil":
                if any(k in comb for k in ["bright", "bhr", "radiance", "creamy"]):
                    target_skus.append("sku2")
                elif any(k in comb for k in ["sa", "exfoliating", "oily", "oil control"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Himalaya":
                if any(k in comb for k in ["clear complexion", "brightening", "dark spot", "turmeric", "kesar", "glow"]):
                    target_skus.append("sku2")
                elif any(k in comb for k in ["neem", "pimple clear"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "Simple":
                if any(k in comb for k in ["vitamin c", "glow"]):
                    target_skus.append("sku2")
                elif any(k in comb for k in ["refreshing", "oil balancing", "clear skin", "kind to skin", "barrier"]):
                    target_skus.extend(["sku1", "sku3", "sku4"])
                else:
                    target_skus.extend(["sku1", "sku2", "sku3", "sku4"])
            elif can_brand == "The Ordinary":
                target_skus.extend(["sku1", "sku2", "sku3", "sku4"])

        elif cat_prefix == "sunscreen":
            if can_brand == "The Derma Co":
                if any(k in comb for k in ["matte", "oil-free"]):
                    target_skus.append("sc_sku2")
                elif any(k in comb for k in ["aqua", "hyaluronic"]):
                    target_skus.append("sc_sku1")
                else:
                    target_skus.extend(["sc_sku1", "sc_sku2"])
            elif can_brand == "Dot & Key":
                if "watermelon" in comb:
                    target_skus.append("sc_sku1")
                elif "cica" in comb or "matte" in comb:
                    target_skus.append("sc_sku2")
                else:
                    target_skus.extend(["sc_sku1", "sc_sku2"])
            elif can_brand == "L'Oréal Paris":
                if "matte" in comb:
                    target_skus.append("sc_sku2")
                else:
                    target_skus.append("sc_sku1")
            elif can_brand == "Foxtale":
                if any(k in comb for k in ["gel", "ice-burst", "oily"]):
                    target_skus.append("sc_sku2")
                elif "dewy" in comb:
                    target_skus.append("sc_sku1")
                else:
                    target_skus.extend(["sc_sku1", "sc_sku2"])
            elif can_brand in ["Cetaphil", "Minimalist"]:
                target_skus.extend(["sc_sku1", "sc_sku2"])
            else:
                target_skus.extend(["sc_sku1", "sc_sku2"])

        elif cat_prefix == "serum":
            if can_brand == "The Derma Co":
                if "vitamin c" in comb or "vit c" in comb: target_skus.append("serum_sku1")
                elif "niacinamide" in comb: target_skus.append("serum_sku2")
                elif "kojic" in comb: target_skus.append("serum_sku3")
                elif "salicylic" in comb: target_skus.append("serum_sku4")
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "Minimalist":
                if "vitamin c" in comb: target_skus.append("serum_sku1")
                elif "niacinamide" in comb: target_skus.append("serum_sku2")
                elif any(k in comb for k in ["arbutin", "tranexamic"]): target_skus.append("serum_sku3")
                elif "salicylic" in comb: target_skus.append("serum_sku4")
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "The Ordinary":
                if any(k in comb for k in ["ascorbic", "vitamin c"]): target_skus.append("serum_sku1")
                elif "niacinamide" in comb: target_skus.append("serum_sku2")
                elif any(k in comb for k in ["alpha arbutin", "arbutin"]): target_skus.append("serum_sku3")
                elif "salicylic" in comb: target_skus.append("serum_sku4")
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "Dot & Key":
                if "vitamin c" in comb or "glow" in comb: target_skus.append("serum_sku1")
                elif "niacinamide" in comb or "clarifying" in comb: target_skus.append("serum_sku2")
                elif "watermelon" in comb or "dark spot" in comb: target_skus.append("serum_sku3")
                elif "cica" in comb or "salicylic" in comb: target_skus.append("serum_sku4")
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "L'Oréal Paris":
                if "vitamin c" in comb: target_skus.append("serum_sku1")
                elif any(k in comb for k in ["glycolic", "dark spot"]): target_skus.append("serum_sku3")
                elif "hyaluronic" in comb or "revitalift" in comb: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3"])
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "Foxtale":
                if any(k in comb for k in ["c for yourself", "vitamin c"]): target_skus.append("serum_sku1")
                elif "niacinamide" in comb: target_skus.append("serum_sku2")
                elif any(k in comb for k in ["rapid spot", "milky way", "brightening", "spot reduction"]): target_skus.append("serum_sku3")
                elif "salicylic" in comb or "acne" in comb: target_skus.append("serum_sku4")
                elif "retinol" in comb: target_skus.append("serum_sku3")
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "Cetaphil":
                if any(k in comb for k in ["bhr", "bright healthy radiance", "perfecting"]): target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3"])
                elif any(k in comb for k in ["blemish", "triple-action", "triple action", "salicylic"]): target_skus.append("serum_sku4")
                elif any(k in comb for k in ["healthy renew", "anti-ageing", "facial serum"]): target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3"])
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            elif can_brand == "Simple":
                if any(k in comb for k in ["vitamin c", "vit c"]): target_skus.append("serum_sku1")
                elif "niacinamide" in comb: target_skus.append("serum_sku2")
                elif "hyaluronic" in comb: target_skus.extend(["serum_sku1", "serum_sku2"])
                else: target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])
            else:
                target_skus.extend(["serum_sku1", "serum_sku2", "serum_sku3", "serum_sku4"])

        elif cat_prefix == "shampoo":
            if can_brand == "The Derma Co":
                if any(k in comb for k in ["dandruff", "triple actives"]): target_skus.append("shampoo_sku1")
                elif any(k in comb for k in ["peptide", "stem cell", "hair fall"]): target_skus.append("shampoo_sku2")
                else: target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
            elif can_brand == "Minimalist":
                if any(k in comb for k in ["dandruff"]): target_skus.append("shampoo_sku1")
                elif any(k in comb for k in ["hair fall", "growth", "actives"]): target_skus.append("shampoo_sku2")
                else: target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
            elif can_brand == "Dot & Key":
                if any(k in comb for k in ["dandruff"]): target_skus.append("shampoo_sku1")
                elif any(k in comb for k in ["hair fall", "hairfall", "moringa", "argan", "peptide"]): target_skus.append("shampoo_sku2")
                else: target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
            elif can_brand == "L'Oréal Paris":
                if any(k in comb for k in ["dandruff", "scalp"]): target_skus.append("shampoo_sku1")
                elif any(k in comb for k in ["fall resist", "hair fall", "density", "hairfall"]): target_skus.append("shampoo_sku2")
                else: target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
            elif can_brand == "Himalaya":
                if any(k in comb for k in ["dandruff", "tea tree"]): target_skus.append("shampoo_sku1")
                elif any(k in comb for k in ["hair fall", "bhringaraja", "protein", "damage"]): target_skus.append("shampoo_sku2")
                else: target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
            elif can_brand == "Foxtale":
                if any(k in comb for k in ["dandruff"]): target_skus.append("shampoo_sku1")
                else: target_skus.append("shampoo_sku2")
            elif can_brand == "Cetaphil":
                target_skus.append("shampoo_sku2")
            else:
                target_skus.extend(["shampoo_sku1", "shampoo_sku2"])
                
        processed.append({
            "folder": folder,
            "category": cat_prefix,
            "title": title if title else folder,
            "brand": can_brand,
            "raw_brand": brand,
            "platform": plat_norm,
            "url": url,
            "price": price,
            "mrp": mrp,
            "availability": availability,
            "rating": rating,
            "review_count": review_count,
            "bullets": bullets,
            "overview": overview,
            "technical": technical,
            "important_info": important_info,
            "images": local_images,
            "videos": local_videos,
            "target_skus": list(set(target_skus))
        })
        
    return processed

facewash_listings = process_directory(FACEWASH_DIR, "facewash", "1FACEWASH")
sunscreen_listings = process_directory(SUNSCREEN_DIR, "sunscreen", "2 SUNSCREEN")
serum_listings = process_directory(SERUM_DIR, "serum", "3 SERUM")
shampoo_listings = process_directory(SHAMPOO_DIR, "shampoo", "4 SHAMPOO")

all_listings = facewash_listings + sunscreen_listings + serum_listings + shampoo_listings
print(f"Total processed valid listings: {len(all_listings)}")
print(f"  Facewash: {len(facewash_listings)}")
print(f"  Sunscreen: {len(sunscreen_listings)}")
print(f"  Serum: {len(serum_listings)}")
print(f"  Shampoo: {len(shampoo_listings)}")

ALL_SKUS = {
    # Facewash SKUs
    "sku1": {
        "id": "sku1",
        "category": "facewash",
        "name": "1% Salicylic Acid Gel Face Wash",
        "size": "100ml",
        "tagline": "Gentle BHA Cleanser with Witch Hazel & Willow Bark for Active Acne & Oil Control",
        "color": "#0d9488",
        "badge": "Active Acne & BHA",
        "icon": "🌿",
        "competitors_map": {
            "The Derma Co": "1% Salicylic Acid Gel Face Wash — 100ml",
            "The Ordinary": "Glucoside / Squalane Cleanser",
            "Minimalist": "Salicylic + LHA 2% Cleanser — 100ml",
            "Dot & Key": "Cica + Salicylic Acid Face Wash — 100ml",
            "L'Oréal Paris": "Revitalift / Salicylic Cleanser — 100ml",
            "Foxtale": "Oil & Acne Control Face Wash — 100ml",
            "Cetaphil": "Gentle Exfoliating SA Cleanser — 118ml",
            "Himalaya": "Neem / Pimple Clear Face Wash — 100ml",
            "Simple": "Clear Skin Oil Balancing Face Wash — 150ml"
        }
    },
    "sku2": {
        "id": "sku2",
        "category": "facewash",
        "name": "1% Kojic Acid Face Wash",
        "size": "100ml",
        "tagline": "Radiance & Pigmentation Cleanser with Niacinamide & Alpha Arbutin for Dark Spots",
        "color": "#e11d48",
        "badge": "Dark Spots & Glow",
        "icon": "✨",
        "competitors_map": {
            "The Derma Co": "1% Kojic Acid Face Wash — 100ml",
            "The Ordinary": "Glucoside / Squalane Cleanser",
            "Minimalist": "Kojic / 7% ALA & AHA Cleanser — 100ml",
            "Dot & Key": "Kojic / Strawberry Bright Face Wash — 100ml",
            "L'Oréal Paris": "Glycolic Bright Daily Foaming Cleanser — 100ml",
            "Foxtale": "Kojic / Super Glow De-Tan Face Wash — 100ml",
            "Cetaphil": "Bright Healthy Radiance Cleanser — 236ml",
            "Himalaya": "Brightening / Turmeric Face Wash — 100ml",
            "Simple": "Vitamin C Glow Facial Wash — 150ml"
        }
    },
    "sku3": {
        "id": "sku3",
        "category": "facewash",
        "name": "2% Salicylic Acid Gel Daily Face Wash",
        "size": "100ml",
        "tagline": "High-Strength 2% BHA Formula with Witch Hazel for Deep Pore Penetration & Exfoliation",
        "color": "#2563eb",
        "badge": "Deep Exfoliation & Oil Control",
        "icon": "🍃",
        "competitors_map": {
            "The Derma Co": "2% Salicylic Acid Gel Daily Face Wash — 100ml",
            "The Ordinary": "Glucoside / Squalane Cleanser",
            "Minimalist": "Salicylic + LHA 2% Cleanser — 100ml",
            "Dot & Key": "Cica + Salicylic Acid Face Wash — 100ml",
            "L'Oréal Paris": "Revitalift Crystal Micro-Foam / SA cleanser — 100ml",
            "Foxtale": "Oil & Acne Control Face Wash — 100ml",
            "Cetaphil": "Gentle Exfoliating SA Cleanser — 118ml",
            "Himalaya": "Pimple Clear Face Wash — 100ml",
            "Simple": "Clear Skin Oil Balancing Face Wash — 150ml"
        }
    },
    "sku4": {
        "id": "sku4",
        "category": "facewash",
        "name": "2% Sali-Cinamide Anti-Acne Face Wash",
        "size": "100ml",
        "tagline": "Dual-Action Acne Defense: 2% Salicylic Acid + 2% Niacinamide with Aquaxyl Barrier Support",
        "color": "#7c3aed",
        "badge": "Anti-Acne & Barrier Defense",
        "icon": "🔬",
        "competitors_map": {
            "The Derma Co": "2% Sali-Cinamide Anti-Acne Face Wash — 100ml",
            "The Ordinary": "Glucoside / Squalane Cleanser",
            "Minimalist": "Salicylic + LHA 2% Cleanser — 100ml",
            "Dot & Key": "Cica + Salicylic Acid Face Wash — 100ml",
            "L'Oréal Paris": "Salicylic / Acne Cleanser — 100ml",
            "Foxtale": "Oil & Acne Control Face Wash — 100ml",
            "Cetaphil": "Gentle Exfoliating SA Cleanser — 118ml",
            "Himalaya": "Pimple Clear Face Wash — 100ml",
            "Simple": "Clear Skin Oil Balancing Face Wash — 150ml"
        }
    },

    # Sunscreen SKUs
    "sc_sku1": {
        "id": "sc_sku1",
        "category": "sunscreen",
        "name": "1% Hyaluronic Sunscreen Aqua Gel (SPF 50 PA++++)",
        "size": "50g / 80g",
        "tagline": "In-Vivo Tested (ISO 24444:2019) Ultra-Lightweight Hydrating Aqua Gel with Titanium Dioxide & Vit E",
        "color": "#0284c7",
        "badge": "Dewy & Hydrating Aqua Gel",
        "icon": "🌊",
        "competitors_map": {
            "The Derma Co": "1% Hyaluronic Sunscreen Aqua Gel (SPF 50 PA++++)",
            "Minimalist": "Multi-Vitamin SPF 50 PA++++ Sunscreen",
            "Dot & Key": "Watermelon Cooling Sunscreen (SPF 50+ PA++++)",
            "L'Oréal Paris": "UV Defender Serum Protector Invisible Resist (SPF 50+)",
            "Foxtale": "Cover Up Dewy Sunscreen (SPF 50 PA++++)",
            "Cetaphil": "Sun SPF 50+ Light Gel Water & Sweat Resistant"
        }
    },
    "sc_sku2": {
        "id": "sc_sku2",
        "category": "sunscreen",
        "name": "1% Hyaluronic Sunscreen Oil-Free Matte Gel (SPF 50 PA++++)",
        "size": "50g",
        "tagline": "In-Vivo Tested (ISO 24444:2019) Zero White Cast Oil-Free Matte Gel for Oily & Acne-Prone Skin",
        "color": "#059669",
        "badge": "Oil-Free & Ultra Matte",
        "icon": "🛡️",
        "competitors_map": {
            "The Derma Co": "1% Hyaluronic Sunscreen Oil-Free Matte Gel (SPF 50 PA++++)",
            "Minimalist": "SPF 50 Lightweight Niacinamide Sunscreen",
            "Dot & Key": "Cica Calming Mattifying Sunscreen (SPF 50+ PA++++)",
            "L'Oréal Paris": "UV Defender Serum Protector Matte & Fresh (SPF 50+)",
            "Foxtale": "Gel Sunscreen for Oily Skin / Ice-Burst (SPF 50 PA++++)",
            "Cetaphil": "Sun SPF 50+ Light Gel"
        }
    },

    # Serum SKUs
    "serum_sku1": {
        "id": "serum_sku1",
        "category": "serum",
        "name": "10% Vitamin C Face Serum",
        "size": "30ml",
        "tagline": "5% Niacinamide & Hyaluronic Acid for Glowing Skin & Dark Spot Reduction",
        "color": "#f59e0b",
        "badge": "Vitamin C Glow Active",
        "icon": "🍊",
        "competitors_map": {
            "The Derma Co": "10% Vitamin C Face Serum — 30ml",
            "Minimalist": "10% Vitamin C Serum — 30ml",
            "Dot & Key": "10% Vitamin C + E Glow Serum — 30ml",
            "The Ordinary": "Ascorbic Acid 8% + Alpha Arbutin 2% — 30ml",
            "L'Oréal Paris": "Revitalift 10% Pure Vitamin C Serum — 30ml",
            "Foxtale": "15% Vitamin C 'C For Yourself' Serum — 30ml",
            "Cetaphil": "Bright Healthy Radiance Perfecting Serum — 30ml",
            "Simple": "10% Vitamin C+E+F Booster Serum — 30ml"
        }
    },
    "serum_sku2": {
        "id": "serum_sku2",
        "category": "serum",
        "name": "10% Niacinamide + 2% Zinc PCA Face Serum",
        "size": "30ml",
        "tagline": "Niacinamide & Zinc PCA for Acne Marks, Blemishes & Sebum Balancing",
        "color": "#3b82f6",
        "badge": "Acne Marks & Sebum Control",
        "icon": "💧",
        "competitors_map": {
            "The Derma Co": "10% Niacinamide Face Serum — 30ml",
            "Minimalist": "10% Niacinamide + Zinc Serum — 30ml",
            "The Ordinary": "Niacinamide 10% + Zinc 1% — 30ml",
            "Dot & Key": "10% Niacinamide Clarifying Serum — 30ml",
            "Foxtale": "Rapid Spot Reduction Drops — 30ml",
            "Cetaphil": "Bright Healthy Radiance Perfecting Serum — 30ml",
            "Simple": "10% Niacinamide Booster Serum — 30ml"
        }
    },
    "serum_sku3": {
        "id": "serum_sku3",
        "category": "serum",
        "name": "2% Kojic Acid Face Serum",
        "size": "30ml",
        "tagline": "Dual Dark Spot Reduction: 2% Kojic Acid + 1% Alpha Arbutin & Niacinamide",
        "color": "#8b5cf6",
        "badge": "Hyperpigmentation Corrector",
        "icon": "💜",
        "competitors_map": {
            "The Derma Co": "2% Kojic Acid Face Serum — 30ml",
            "Minimalist": "2% Alpha Arbutin Serum — 30ml",
            "The Ordinary": "Alpha Arbutin 2% + HA — 30ml",
            "Dot & Key": "10% Niacinamide / Dark Spot Serum — 30ml",
            "L'Oréal Paris": "Glycolic Bright Dark Spot Reduction Serum — 30ml",
            "Foxtale": "Milky Way / Spot Reduction Serum — 30ml",
            "Cetaphil": "BHR Anti-Pigmentation Serum — 30ml"
        }
    },
    "serum_sku4": {
        "id": "serum_sku4",
        "category": "serum",
        "name": "2% Salicylic Acid Face Serum",
        "size": "30ml",
        "tagline": "Active Salicylic Acid & Witch Hazel for Active Acne & Deep Pore Cleansing",
        "color": "#10b981",
        "badge": "Deep Pore Acne Exfoliator",
        "icon": "🌿",
        "competitors_map": {
            "The Derma Co": "2% Salicylic Acid Face Serum — 30ml",
            "Minimalist": "2% Salicylic Acid Serum — 30ml",
            "The Ordinary": "Salicylic Acid 2% Solution — 30ml",
            "Dot & Key": "Cica 2% Salicylic Clarifying Serum — 30ml",
            "Cetaphil": "Triple Action Blemish Serum — 30ml"
        }
    },

    # Shampoo SKUs
    "shampoo_sku1": {
        "id": "shampoo_sku1",
        "category": "shampoo",
        "name": "Triple Actives Anti-Dandruff Shampoo",
        "size": "250ml",
        "tagline": "2% Salicylic Acid + 1% Climbazole + 1% Piroctone Olamine with Menthol for Flake-Free Scalp",
        "color": "#06b6d4",
        "badge": "Triple Actives Scalp Detox",
        "icon": "❄️",
        "competitors_map": {
            "The Derma Co": "Triple Actives Anti-Dandruff Shampoo — 250ml",
            "Minimalist": "Anti-Dandruff Shampoo 3.5% — 250ml",
            "Dot & Key": "Anti-Dandruff Shampoo — 250ml",
            "L'Oréal Paris": "Scalp Advanced / Anti-Dandruff Shampoo — 200ml",
            "Himalaya": "Anti-Dandruff Tea Tree Shampoo — 200ml"
        }
    },
    "shampoo_sku2": {
        "id": "shampoo_sku2",
        "category": "shampoo",
        "name": "Peptide-Stem Cell Hair Fall Control Shampoo",
        "size": "250ml",
        "tagline": "Bio-Peptides & Plant Stem Cells with Rice Water & Pro-Vitamin B5 to Fortify Roots & Reduce Breakage",
        "color": "#84cc16",
        "badge": "Stem Cell Root Fortification",
        "icon": "🌾",
        "competitors_map": {
            "The Derma Co": "Peptide-Stem Cell Hair Fall Control Shampoo — 250ml",
            "Minimalist": "Hair Growth / Hair Fall Control Shampoo — 250ml",
            "Dot & Key": "Peptide Hair Fall Control Shampoo — 250ml",
            "L'Oréal Paris": "Fall Resist 3X Shampoo — 200ml",
            "Himalaya": "Anti-Hair Fall Bhringaraja Shampoo — 200ml"
        }
    }
}

BRANDS_ORDER = [
    "The Derma Co",
    "The Ordinary",
    "Minimalist",
    "Dot & Key",
    "L'Oréal Paris",
    "Foxtale",
    "Cetaphil",
    "Himalaya",
    "Simple"
]

BRAND_ACCENTS = {
    "The Derma Co": {"color": "#0d9488", "bg": "#0d948815", "border": "#0d948840", "tag": "Hero Benchmark"},
    "The Ordinary": {"color": "#475569", "bg": "#47556915", "border": "#47556940", "tag": "Global Direct"},
    "Minimalist": {"color": "#0f172a", "bg": "#0f172a15", "border": "#0f172a40", "tag": "Direct Active"},
    "Dot & Key": {"color": "#db2777", "bg": "#db277715", "border": "#db277740", "tag": "D2C Direct"},
    "L'Oréal Paris": {"color": "#d97706", "bg": "#d9770615", "border": "#d9770640", "tag": "FMCG Prestige"},
    "Foxtale": {"color": "#9333ea", "bg": "#9333ea15", "border": "#9333ea40", "tag": "D2C Direct"},
    "Cetaphil": {"color": "#0284c7", "bg": "#0284c715", "border": "#0284c740", "tag": "Derma Clinical"},
    "Himalaya": {"color": "#16a34a", "bg": "#16a34a15", "border": "#16a34a40", "tag": "Herbal Mass"},
    "Simple": {"color": "#059669", "bg": "#05966915", "border": "#05966940", "tag": "Sensitive Clean"}
}

PLATFORMS_LIST = [
    "Brand D2C Store",
    "Amazon",
    "Nykaa",
    "Flipkart",
    "Blinkit"
]

PLATFORM_COLORS = {
    "Brand D2C Store": {"color": "#0d9488", "icon": "🌿"},
    "Amazon": {"color": "#ea580c", "icon": "📦"},
    "Nykaa": {"color": "#db2777", "icon": "💄"},
    "Flipkart": {"color": "#2563eb", "icon": "🛒"},
    "Blinkit": {"color": "#ca8a04", "icon": "⚡"}
}

# Group listings:
# 1. sku_data: SKU -> Brand -> Listings
# 2. marketplace_data: SKU -> Platform -> Listings for The Derma Co
sku_data = {}
marketplace_data = {}

for sku_id in ALL_SKUS:
    sku_data[sku_id] = {b: [] for b in BRANDS_ORDER}
    marketplace_data[sku_id] = {p: [] for p in PLATFORMS_LIST}

for it in all_listings:
    b = it["brand"]
    p = it["platform"]
    for s in it["target_skus"]:
        if s in sku_data and b in sku_data[s]:
            sku_data[s][b].append(it)
        if b == "The Derma Co" and s in marketplace_data and p in marketplace_data[s]:
            marketplace_data[s][p].append(it)

total_all_imgs = sum(len(it["images"]) for it in all_listings)
total_all_vids = sum(len(it["videos"]) for it in all_listings)

data_payload = {
    "skus": ALL_SKUS,
    "brands": BRANDS_ORDER,
    "brand_accents": BRAND_ACCENTS,
    "platforms": PLATFORMS_LIST,
    "platform_colors": PLATFORM_COLORS,
    "sku_data": sku_data,
    "marketplace_data": marketplace_data,
    "stats": {
        "total_listings": len(all_listings),
        "total_images": total_all_imgs,
        "total_videos": total_all_vids
    }
}

json_payload_str = json.dumps(data_payload, ensure_ascii=False)
print(f"Data payload prepared: {len(all_listings)} listings, {total_all_imgs} images, {total_all_vids} videos.")

# Generate the full bright web app HTML template
html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HONASA TDC • 4-Leaf Competitive Research Canvas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #f8fafc;
  --card: #ffffff;
  --card-border: #e2e8f0;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-sub: #475569;
  --primary: #0d9488;
  --primary-light: #ccfbf1;
  --accent: #2563eb;
  --font: 'Plus Jakarta Sans', sans-serif;
  --mono: 'JetBrains Mono', monospace;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: var(--font);
  background: var(--bg);
  color: var(--text-main);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}}

/* Google Chrome Browser Header */
.browser-chrome {{
  background: #f1f5f9;
  border-bottom: 1px solid #cbd5e1;
  position: sticky;
  top: 0;
  z-index: 500;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}}

.chrome-window-controls {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 4px;
}}
.win-dot {{ width: 11px; height: 11px; border-radius: 50%; display: inline-block; }}
.win-dot.red {{ background: #ff5f56; border: 1px solid #e0443e; }}
.win-dot.yellow {{ background: #ffbd2e; border: 1px solid #dea123; }}
.win-dot.green {{ background: #27c93f; border: 1px solid #1aab29; }}
.chrome-brand-pill {{
  margin-left: 12px;
  background: linear-gradient(135deg, #0d9488, #2563eb);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.5px;
  padding: 2px 10px;
  border-radius: 6px;
  text-transform: uppercase;
}}
.chrome-canvas-title {{
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  margin-left: 6px;
}}

/* Level 1: 4 Category Tabs (Google Chrome Style) */
.category-leaf-bar {{
  display: flex;
  align-items: flex-end;
  padding: 4px 16px 0;
  gap: 3px;
  overflow-x: auto;
  scrollbar-width: none;
}}
.category-leaf-bar::-webkit-scrollbar {{ display: none; }}

.cat-leaf {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px 9px;
  background: #e2e8f0;
  color: #475569;
  border-radius: 10px 10px 0 0;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid #cbd5e1;
  border-bottom: none;
  transition: all 0.15s ease;
  position: relative;
  white-space: nowrap;
  user-select: none;
}}
.cat-leaf:hover {{
  background: #f8fafc;
  color: #0f172a;
}}
.cat-leaf.active {{
  background: #ffffff;
  color: #0f172a;
  border-color: #cbd5e1;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.03);
}}
.cat-leaf.active::after {{
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: #ffffff;
}}
.cat-badge {{
  font-size: 0.65rem;
  padding: 2px 7px;
  border-radius: 10px;
  font-weight: 800;
  background: #e2e8f0;
  color: #475569;
}}
.cat-leaf.active .cat-badge {{
  background: #ccfbf1;
  color: #0d9488;
}}
.cat-icon {{ font-size: 1.05rem; }}

/* Chrome Omnibox / Sub-Header Bar */
.chrome-omnibox-bar {{
  background: #ffffff;
  padding: 8px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  gap: 16px;
}}
.omnibox {{
  flex: 1;
  max-width: 650px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 5px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
  color: #475569;
}}
.omnibox input {{
  border: none;
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: 0.78rem;
  width: 100%;
  color: #0f172a;
}}
.quick-stats {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.stat-tag {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.73rem;
  font-weight: 700;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 4px 10px;
  border-radius: 6px;
  color: #475569;
}}

/* Level 2: SKU Leaf Bar */
.sku-leaf-bar {{
  background: #ffffff;
  padding: 12px 24px;
  display: flex;
  gap: 10px;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
  scrollbar-width: thin;
}}
.sku-leaf {{
  flex: 1;
  min-width: 260px;
  max-width: 380px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}}
.sku-leaf:hover {{
  border-color: #cbd5e1;
  background: #ffffff;
  transform: translateY(-1px);
}}
.sku-leaf.active {{
  background: #ffffff;
  border-color: var(--sku-color, #0d9488);
  box-shadow: 0 4px 14px -3px rgba(13, 148, 136, 0.15);
}}
.sku-leaf-top {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}}
.sku-leaf-badge {{
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 7px;
  border-radius: 4px;
  background: #f1f5f9;
  color: #64748b;
}}
.sku-leaf.active .sku-leaf-badge {{
  background: var(--sku-color, #0d9488);
  color: #ffffff;
}}
.sku-leaf-title {{
  font-size: 0.88rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.3;
}}
.sku-leaf-sub {{
  font-size: 0.72rem;
  color: #64748b;
  margin-top: 3px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

/* Level 3: Dual Sub-Leaves & Mode Toggle */
.subleaf-controls-bar {{
  background: #f8fafc;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 12px;
}}
.subleaf-tabs {{
  display: flex;
  background: #e2e8f0;
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}}
.subleaf-tab {{
  padding: 7px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background: transparent;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 7px;
  transition: all 0.15s ease;
}}
.subleaf-tab:hover {{ color: #0f172a; }}
.subleaf-tab.active {{
  background: #ffffff;
  color: #0d9488;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}}
.subleaf-tab .badge {{
  background: #f1f5f9;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 0.68rem;
}}
.subleaf-tab.active .badge {{
  background: #ccfbf1;
  color: #0d9488;
}}

/* Comparison Mode Switcher (Cross-Marketplace vs Competitor) */
.mode-toggle-group {{
  display: flex;
  background: #ffffff;
  border: 1.5px solid #0d9488;
  padding: 2px;
  border-radius: 8px;
  gap: 2px;
  box-shadow: 0 1px 3px rgba(13, 148, 136, 0.1);
}}
.mode-toggle-btn {{
  padding: 6px 14px;
  font-size: 0.77rem;
  font-weight: 800;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background: transparent;
  color: #0f766e;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.mode-toggle-btn:hover {{ background: #ccfbf130; }}
.mode-toggle-btn.active {{
  background: #0d9488;
  color: #ffffff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}}

.view-options {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}}
.pill-btn {{
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  font-size: 0.74rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s ease;
}}
.pill-btn:hover, .pill-btn.active {{
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}}

/* Main Canvas Content Area */
.canvas-main {{
  padding: 20px 24px 80px;
  max-width: 1800px;
  margin: 0 auto;
}}

/* Brand Row Lanes */
.brand-lane {{
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow 0.2s;
}}
.brand-lane:hover {{
  box-shadow: var(--shadow-md);
}}
.brand-lane.benchmark {{
  border-left: 6px solid #0d9488;
  background: linear-gradient(180deg, #f0fdfa 0%, #ffffff 120px);
}}

.brand-lane-hdr {{
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  background: #fafbfc;
  flex-wrap: wrap;
  gap: 10px;
}}
.brand-lane.benchmark .brand-lane-hdr {{
  background: #f0fdfa;
  border-bottom-color: #ccfbf1;
}}
.brand-lane-title-group {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}}
.brand-badge {{
  font-size: 0.72rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 6px;
  color: #ffffff;
  letter-spacing: 0.4px;
}}
.brand-product-title {{
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}}
.brand-product-sub {{
  font-size: 0.74rem;
  color: #64748b;
  font-weight: 600;
}}

.platform-selector-pills {{
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}}
.plat-pill {{
  padding: 3px 9px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  font-size: 0.7rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s;
}}
.plat-pill:hover, .plat-pill.active {{
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}}

.brand-lane-body {{
  padding: 16px 18px;
}}

.platform-block {{
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e2e8f0;
}}
.platform-block:last-child {{
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}}

.plat-hdr {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}}
.plat-label {{
  font-size: 0.8rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.plat-pricing {{
  font-size: 0.78rem;
  color: #0f172a;
  font-weight: 700;
  background: #f8fafc;
  padding: 3px 9px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}}

/* Horizontal Media Filmstrip */
.media-filmstrip {{
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 10px;
  scrollbar-width: thin;
}}
.media-filmstrip::-webkit-scrollbar {{
  height: 6px;
}}
.media-filmstrip::-webkit-scrollbar-thumb {{
  background: #cbd5e1;
  border-radius: 3px;
}}

/* Image & Video Cards */
.media-card {{
  flex-shrink: 0;
  width: 175px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
  display: flex;
  flex-direction: column;
}}
.media-card:hover {{
  transform: translateY(-2px);
  border-color: #0d9488;
  box-shadow: var(--shadow-md);
}}
.media-card img {{
  width: 100%;
  height: 175px;
  object-fit: contain;
  background: #f8fafc;
  cursor: zoom-in;
  display: block;
}}
.media-card video {{
  width: 100%;
  height: 175px;
  object-fit: cover;
  background: #000;
  display: block;
}}
.media-card-meta {{
  padding: 6px 8px;
  background: #fafbfc;
  border-top: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.67rem;
  color: #64748b;
  font-weight: 600;
}}
.compare-action-btn {{
  background: transparent;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.65rem;
  padding: 1px 5px;
  cursor: pointer;
  color: #475569;
  font-weight: 700;
}}
.compare-action-btn:hover {{
  background: #0d9488;
  color: #fff;
  border-color: #0d9488;
}}

/* Verbatim Product Info Comparison Table */
.table-container {{
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  overflow-x: auto;
  position: relative;
}}
.comparison-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  text-align: left;
  min-width: 1300px;
}}
.comparison-table th, .comparison-table td {{
  padding: 12px 14px;
  border-bottom: 1px solid #e2e8f0;
  border-right: 1px solid #e2e8f0;
  vertical-align: top;
}}
.comparison-table th:last-child, .comparison-table td:last-child {{
  border-right: none;
}}

/* Sticky Benchmark Column */
.comparison-table th:first-child, .comparison-table td:first-child {{
  position: sticky;
  left: 0;
  z-index: 20;
  width: 170px;
  min-width: 170px;
  max-width: 170px;
  background: #f8fafc;
  font-weight: 800;
  color: #0f172a;
  border-right: 2px solid #cbd5e1;
}}
.comparison-table th:nth-child(2), .comparison-table td:nth-child(2) {{
  position: sticky;
  left: 170px;
  z-index: 19;
  width: 280px;
  min-width: 280px;
  max-width: 280px;
  background: #f0fdfa;
  border-right: 3px solid #0d9488;
}}
.comparison-table th:nth-child(2) {{
  background: #ccfbf1 !important;
  color: #0d9488 !important;
}}

.comparison-table thead th {{
  background: #f1f5f9;
  position: sticky;
  top: 100px;
  z-index: 10;
  font-weight: 800;
  color: #0f172a;
  font-size: 0.82rem;
  box-shadow: 0 1px 0 #cbd5e1;
}}
.comparison-table thead th:first-child {{ z-index: 30; }}
.comparison-table thead th:nth-child(2) {{ z-index: 29; }}

.table-brand-hdr {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.table-brand-name {{ font-size: 0.92rem; font-weight: 800; }}
.table-sku-name {{ font-size: 0.72rem; color: #64748b; font-weight: 600; }}

.verbatim-pre {{
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.76rem;
  line-height: 1.5;
  color: #334155;
}}

.verbatim-bullet-list {{
  list-style: none;
  padding: 0;
}}
.verbatim-bullet-list li {{
  position: relative;
  padding-left: 18px;
  margin-bottom: 6px;
  font-size: 0.76rem;
  line-height: 1.45;
}}
.verbatim-bullet-list li::before {{
  content: '•';
  position: absolute;
  left: 4px;
  color: #0d9488;
  font-weight: 800;
  font-size: 1rem;
}}

.tag-item {{
  background: #f1f5f9;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 0.7rem;
  color: #475569;
  font-weight: 600;
}}

.section-row-hdr {{
  background: #f8fafc;
  font-weight: 800;
  color: #0f172a;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

/* Lightbox Modal */
#lb-modal {{
  display: none;
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(8px);
  align-items: center;
  justify-content: center;
  flex-direction: column;
}}
#lb-modal.active {{ display: flex; }}

.lb-toolbar {{
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 6px 16px;
  border-radius: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
  z-index: 10001;
}}
.lb-btn {{
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}}
.lb-btn:hover {{ background: rgba(255, 255, 255, 0.2); }}
.lb-close {{
  position: absolute;
  top: 16px;
  right: 24px;
  color: #ffffff;
  font-size: 2rem;
  cursor: pointer;
  z-index: 10001;
}}

.lb-stage {{
  max-width: 90vw;
  max-height: 85vh;
  overflow: hidden;
  position: relative;
  cursor: grab;
}}
.lb-stage:active {{ cursor: grabbing; }}
.lb-stage img {{
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  transition: transform 0.1s ease;
  user-select: none;
}}

/* Dual Compare Modal */
#dual-compare-modal {{
  display: none;
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(8px);
  flex-direction: column;
  padding: 20px;
}}
#dual-compare-modal.active {{ display: flex; }}

.dual-compare-hdr {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #ffffff;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}}
.dual-slots {{
  display: flex;
  gap: 20px;
  flex: 1;
  margin-top: 16px;
  height: calc(100vh - 120px);
}}
.dual-slot {{
  flex: 1;
  background: rgba(255,255,255,0.05);
  border: 2px dashed rgba(255,255,255,0.2);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}}
.dual-slot.filled {{
  border-style: solid;
  border-color: #0d9488;
}}
.dual-slot img {{
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}}
.dual-slot-label {{
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(0,0,0,0.7);
  color: #ffffff;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
}}

.info-banner {{
  background: #f0fdfa;
  border: 1px solid #ccfbf1;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  font-size: 0.8rem;
  color: #0f766e;
  display: flex;
  align-items: center;
  gap: 10px;
}}
</style>
</head>
<body>

<!-- Lightbox Modal -->
<div id="lb-modal">
  <span class="lb-close" onclick="closeLB()">✕</span>
  <div class="lb-toolbar">
    <button class="lb-btn" onclick="zoomLB(-0.25)">🔍−</button>
    <span id="lb-zoom-level">100%</span>
    <button class="lb-btn" onclick="zoomLB(0.25)">🔍+</button>
    <button class="lb-btn" onclick="resetLB()">⟲ Reset</button>
    <button class="lb-btn" onclick="stageInComparator(currentLBImg)">⚖️ Compare</button>
  </div>
  <div class="lb-stage" id="lb-stage" onmousedown="startDrag(event)">
    <img id="lb-img" src="" alt="">
  </div>
</div>

<!-- Dual Image Compare Modal -->
<div id="dual-compare-modal">
  <div class="dual-compare-hdr">
    <div style="display:flex;align-items:center;gap:10px;">
      <span style="font-size:1.4rem;">⚖️</span>
      <div>
        <h3 style="margin:0;font-size:1.05rem;">Side-by-Side Dual Image Inspector</h3>
        <p style="margin:0;font-size:0.75rem;color:#94a3b8;">Click "Compare" on any image card to stage it here for synchronized visual analysis.</p>
      </div>
    </div>
    <div style="display:flex;gap:10px;">
      <button class="pill-btn" onclick="clearComparator()">Clear Slots</button>
      <button class="pill-btn" onclick="closeComparator()">Close ✕</button>
    </div>
  </div>
  <div class="dual-slots">
    <div class="dual-slot" id="slot-a">
      <div class="dual-slot-label" id="label-a">Slot A (Empty)</div>
      <p style="color:#94a3b8;font-size:0.8rem;">Select an image using the "⚖️ Compare" button</p>
    </div>
    <div class="dual-slot" id="slot-b">
      <div class="dual-slot-label" id="label-b">Slot B (Empty)</div>
      <p style="color:#94a3b8;font-size:0.8rem;">Select a 2nd image using the "⚖️ Compare" button</p>
    </div>
  </div>
</div>

<!-- Browser Chrome / Header -->
<div class="browser-chrome">
  <div class="chrome-window-controls">
    <span class="win-dot red"></span>
    <span class="win-dot yellow"></span>
    <span class="win-dot green"></span>
    <span class="chrome-brand-pill">HONASA TDC</span>
    <span class="chrome-canvas-title">Competitive PDP & Intelligence Board</span>
  </div>

  <!-- Level 1: 4 Category Tabs (Google Style) -->
  <div class="category-leaf-bar" id="category-bar">
    <div class="cat-leaf active" onclick="switchCategory('facewash', this)">
      <span class="cat-icon">🧼</span>
      <span>Facewash</span>
      <span class="cat-badge">4 SKUs • {len(facewash_listings)} listings</span>
    </div>
    <div class="cat-leaf" onclick="switchCategory('sunscreen', this)">
      <span class="cat-icon">☀️</span>
      <span>Sunscreen</span>
      <span class="cat-badge">2 SKUs • {len(sunscreen_listings)} listings</span>
    </div>
    <div class="cat-leaf" onclick="switchCategory('serum', this)">
      <span class="cat-icon">💧</span>
      <span>Serum</span>
      <span class="cat-badge">4 SKUs • {len(serum_listings)} listings</span>
    </div>
    <div class="cat-leaf" onclick="switchCategory('shampoo', this)">
      <span class="cat-icon">🧴</span>
      <span>Shampoo</span>
      <span class="cat-badge">2 SKUs • {len(shampoo_listings)} listings</span>
    </div>
  </div>

  <!-- Chrome Omnibox / Search & Stats Bar -->
  <div class="chrome-omnibox-bar">
    <div class="omnibox">
      <span>🔍</span>
      <input type="text" id="global-search" placeholder="Search keywords, ingredients (e.g. Salicylic, Kojic, Niacinamide, Hyaluronic, Cica, BHR), claims across all listings..." oninput="onGlobalSearch(this.value)">
    </div>
    <div class="quick-stats">
      <div class="stat-tag">📸 <span id="stat-imgs">{total_all_imgs}</span> Images</div>
      <div class="stat-tag">🎥 <span id="stat-vids">{total_all_vids}</span> MP4 Videos</div>
      <div class="stat-tag">🏛️ 9 Brands</div>
      <div class="stat-tag">🌐 5 Platforms</div>
    </div>
  </div>
</div>

<!-- Dynamic Container for Active Category & SKUs -->
<div id="active-category-container">

  <!-- Level 2: SKU Leaves Bar (rendered dynamically per category) -->
  <div class="sku-leaf-bar" id="sku-leaf-bar">
    <!-- Populated by JS -->
  </div>

  <!-- Level 3: Dual Sub-Leaves & Comparison Mode Switcher -->
  <div class="subleaf-controls-bar">
    <!-- Sub-tabs: PDP vs Product Info -->
    <div class="subleaf-tabs">
      <button class="subleaf-tab active" id="btn-pdp-tab" onclick="switchSubLeaf('pdp')">
        <span>🖼️ PDP Media Canvas</span>
        <span class="badge" id="subleaf-pdp-badge">Filmstrip</span>
      </button>
      <button class="subleaf-tab" id="btn-info-tab" onclick="switchSubLeaf('info')">
        <span>📊 Product Info Matrix</span>
        <span class="badge">100% Verbatim</span>
      </button>
    </div>

    <!-- COMPARISON MODE TOGGLE (Cross-Marketplace vs Competitor Benchmark) -->
    <div class="mode-toggle-group">
      <button class="mode-toggle-btn active" id="btn-mode-benchmark" onclick="switchComparisonMode('benchmark')">
        ⚔️ Competitor Benchmark (Derma Co vs Other Brands)
      </button>
      <button class="mode-toggle-btn" id="btn-mode-marketplace" onclick="switchComparisonMode('marketplace')">
        🏢 Cross-Marketplace Channel Audit (Our Own Product Across Channels)
      </button>
    </div>

    <!-- Platform Filter & Dual Inspector Button -->
    <div class="view-options" id="platform-filter-container">
      <span style="font-size:0.72rem;font-weight:700;color:#64748b;">CHANNEL:</span>
      <button class="pill-btn active" onclick="filterPlatform('all', this)">All Channels</button>
      <button class="pill-btn" onclick="filterPlatform('Brand D2C Store', this)">🌿 D2C</button>
      <button class="pill-btn" onclick="filterPlatform('Amazon', this)">📦 Amazon</button>
      <button class="pill-btn" onclick="filterPlatform('Nykaa', this)">💄 Nykaa</button>
      <button class="pill-btn" onclick="filterPlatform('Flipkart', this)">🛒 Flipkart</button>
      <button class="pill-btn" onclick="filterPlatform('Blinkit', this)">⚡ Blinkit</button>
      <div style="width:1px;height:18px;background:#cbd5e1;margin:0 4px;"></div>
      <button class="pill-btn" onclick="openComparator()">⚖️ Dual Inspector</button>
    </div>
  </div>

  <!-- Main Canvas Content Area -->
  <div class="canvas-main">
    <!-- Active SKU Header Banner -->
    <div id="sku-header-banner" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span id="sku-banner-icon" style="font-size:1.3rem;">🌿</span>
          <h2 id="sku-banner-title" style="font-size:1.15rem;font-weight:800;color:#0f172a;">1% Salicylic Acid Gel Face Wash (100ml)</h2>
          <span id="sku-banner-tag" style="background:#ccfbf1;color:#0d9488;font-size:0.7rem;font-weight:800;padding:2px 8px;border-radius:6px;">Hero Benchmark</span>
        </div>
        <p id="sku-banner-desc" style="font-size:0.78rem;color:#64748b;margin-top:2px;">Comparing The Derma Co directly with competitor brands in exact scraped order with all images, videos and verbatim specifications.</p>
      </div>
      <div style="display:flex;gap:8px;" id="sku-competitor-chips">
        <!-- populated dynamically -->
      </div>
    </div>

    <!-- SUBLEAF VIEW 1: PDP Media Canvas -->
    <div id="view-pdp-canvas">
      <div id="pdp-brand-lanes">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- SUBLEAF VIEW 2: Verbatim Product Info Table -->
    <div id="view-info-table" style="display:none;">
      <div class="info-banner" id="table-info-banner">
        <span>🛡️</span>
        <span id="table-info-text"><strong>100% Raw Verbatim Fidelity:</strong> None of the data or statements below are summarized or modified. Every single word, bullet point, description, INCI ingredient list, safety warning, and FAQ is rendered exactly as scraped.</span>
      </div>
      <div class="table-container">
        <table class="comparison-table" id="info-matrix-table">
          <!-- Rendered dynamically -->
        </table>
      </div>
    </div>
  </div>
</div>

<script>
// Complete Dataset Payload
const DATA = {json_payload_str};

let currentCategory = 'facewash';
let currentSKU = 'sku1';
let currentSubLeaf = 'pdp';
let currentComparisonMode = 'benchmark'; // 'benchmark' or 'marketplace'
let currentPlatformFilter = 'all';
let searchQuery = '';

// Lightbox State
let currentLBImg = '';
let currentZoom = 1;
let isDragging = false;
let startX = 0, startY = 0;
let translateX = 0, translateY = 0;

// Dual Comparator State
let slotA = null;
let slotB = null;

// Initialize
window.addEventListener('DOMContentLoaded', () => {{
  renderCategorySKUBar();
  renderActiveSKU();
}});

function switchCategory(cat, el) {{
  currentCategory = cat;
  document.querySelectorAll('.cat-leaf').forEach(e => e.classList.remove('active'));
  if (el) el.classList.add('active');

  const mainContainer = document.getElementById('active-category-container');
  mainContainer.style.display = 'block';

  // Find first SKU belonging to current category
  const skusInCat = Object.values(DATA.skus).filter(s => s.category === currentCategory);
  if (skusInCat.length > 0) {{
    currentSKU = skusInCat[0].id;
  }}

  renderCategorySKUBar();
  renderActiveSKU();
}}

function renderCategorySKUBar() {{
  const bar = document.getElementById('sku-leaf-bar');
  bar.innerHTML = '';

  // Get all SKUs belonging to current category
  const skusInCat = Object.values(DATA.skus).filter(s => s.category === currentCategory);

  skusInCat.forEach(s => {{
    const leaf = document.createElement('div');
    leaf.className = 'sku-leaf' + (s.id === currentSKU ? ' active' : '');
    leaf.style.setProperty('--sku-color', s.color);
    leaf.onclick = () => {{
      document.querySelectorAll('.sku-leaf').forEach(e => e.classList.remove('active'));
      leaf.classList.add('active');
      currentSKU = s.id;
      renderActiveSKU();
    }};

    leaf.innerHTML = `
      <div class="sku-leaf-top">
        <span class="sku-leaf-badge">${{s.badge}}</span>
        <span style="font-size:0.75rem;font-weight:700;color:${{s.color}};">${{s.size}}</span>
      </div>
      <div class="sku-leaf-title">${{s.name}}</div>
      <div class="sku-leaf-sub">${{s.tagline}}</div>
    `;
    bar.appendChild(leaf);
  }});
}}

function switchComparisonMode(mode) {{
  currentComparisonMode = mode;
  document.getElementById('btn-mode-benchmark').classList.toggle('active', mode === 'benchmark');
  document.getElementById('btn-mode-marketplace').classList.toggle('active', mode === 'marketplace');
  
  // Update banner description
  const bannerDesc = document.getElementById('sku-banner-desc');
  const tableText = document.getElementById('table-info-text');

  if (mode === 'marketplace') {{
    bannerDesc.innerText = 'Cross-Marketplace Channel Audit: Comparing The Derma Co\\'s own listings across D2C, Amazon, Nykaa, Flipkart, and Blinkit to identify pricing disparities, asset gaps, and content discrepancies.';
    tableText.innerHTML = '<strong>Cross-Marketplace Consistency Audit:</strong> Comparing The Derma Co across all retail channels. Every word, price, and ingredient statement is 100% verbatim from each marketplace.';
  }} else {{
    bannerDesc.innerText = 'Competitive Benchmark: Comparing The Derma Co directly with competitor brands in exact scraped order with all images, videos and verbatim specifications.';
    tableText.innerHTML = '<strong>100% Raw Verbatim Fidelity:</strong> None of the data or statements below are summarized or modified. Every single word, bullet point, description, INCI ingredient list, safety warning, and FAQ is rendered exactly as scraped.';
  }}

  renderActiveSKU();
}}

function switchSubLeaf(sub) {{
  currentSubLeaf = sub;
  const pdpBtn = document.getElementById('btn-pdp-tab');
  const infoBtn = document.getElementById('btn-info-tab');
  const pdpView = document.getElementById('view-pdp-canvas');
  const infoView = document.getElementById('view-info-table');

  if (sub === 'pdp') {{
    pdpBtn.classList.add('active');
    infoBtn.classList.remove('active');
    pdpView.style.display = 'block';
    infoView.style.display = 'none';
  }} else {{
    infoBtn.classList.add('active');
    pdpBtn.classList.remove('active');
    pdpView.style.display = 'none';
    infoView.style.display = 'block';
  }}
}}

function filterPlatform(plat, el) {{
  currentPlatformFilter = plat;
  el.parentElement.querySelectorAll('.pill-btn').forEach(b => {{
    if (b.innerText.includes('Dual')) return;
    b.classList.remove('active');
  }});
  el.classList.add('active');
  renderActiveSKU();
}}

function onGlobalSearch(query) {{
  searchQuery = query.toLowerCase().trim();
  renderActiveSKU();
}}

function renderActiveSKU() {{
  const skuMeta = DATA.skus[currentSKU];
  if (!skuMeta) return;

  // Update SKU Banner
  document.getElementById('sku-banner-icon').innerText = skuMeta.icon;
  document.getElementById('sku-banner-title').innerText = skuMeta.name + ' (' + skuMeta.size + ')';
  document.getElementById('sku-banner-tag').innerText = skuMeta.badge;

  // Render Competitor chips in header
  const chipsContainer = document.getElementById('sku-competitor-chips');
  chipsContainer.innerHTML = '';
  
  if (currentComparisonMode === 'marketplace') {{
    DATA.platforms.forEach(p => {{
      const pColor = DATA.platform_colors[p] || {{ color: '#0d9488' }};
      const chip = document.createElement('span');
      chip.style.cssText = `font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:4px;background:#f8fafc;color:${{pColor.color}};border:1px solid ${{pColor.color}}40;`;
      chip.innerText = p;
      chipsContainer.appendChild(chip);
    }});
  }} else {{
    DATA.brands.forEach(b => {{
      const acc = DATA.brand_accents[b] || {{ color: '#475569', bg: '#f1f5f9' }};
      const chip = document.createElement('span');
      chip.style.cssText = `font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:4px;background:${{acc.bg}};color:${{acc.color}};border:1px solid ${{acc.color}}30;`;
      chip.innerText = b;
      chipsContainer.appendChild(chip);
    }});
  }}

  // Render PDP View
  renderPDPLanes();

  // Render Info Table View
  renderInfoTable();
}}

function renderPDPLanes() {{
  const container = document.getElementById('pdp-brand-lanes');
  container.innerHTML = '';

  const skuMeta = DATA.skus[currentSKU];

  if (currentComparisonMode === 'marketplace') {{
    // MODE 1: CROSS-MARKETPLACE AUDIT FOR DERMA CO
    const mpMap = DATA.marketplace_data[currentSKU] || {{}};

    DATA.platforms.forEach(plat => {{
      if (currentPlatformFilter !== 'all' && currentPlatformFilter.toLowerCase() !== plat.toLowerCase()) {{
        return; // skip if platform filter does not match
      }}

      const listings = mpMap[plat] || [];
      if (listings.length === 0) return; // REMOVE EMPTY CARDS

      let filtered = listings;
      if (searchQuery) {{
        filtered = listings.filter(l => {{
          const txt = (l.title + ' ' + l.bullets.join(' ') + ' ' + JSON.stringify(l.important_info)).toLowerCase();
          return txt.includes(searchQuery);
        }});
      }}
      if (filtered.length === 0) return; // REMOVE EMPTY CARDS

      const pColor = DATA.platform_colors[plat] || {{ color: '#0d9488', icon: '🌐' }};
      const primary = filtered[0];

      const lane = document.createElement('div');
      lane.className = 'brand-lane benchmark';

      let totalImgs = filtered.reduce((acc, l) => acc + l.images.length, 0);
      let totalVids = filtered.reduce((acc, l) => acc + l.videos.length, 0);

      lane.innerHTML = `
        <div class="brand-lane-hdr" style="background:#f0fdfa;">
          <div class="brand-lane-title-group">
            <span class="brand-badge" style="background:${{pColor.color}};">${{pColor.icon}} ${{plat}}</span>
            <span class="brand-product-title">${{escapeHtml(primary.title)}}</span>
            <span class="stat-tag">📸 ${{totalImgs}} imgs</span>
            ${{totalVids > 0 ? `<span class="stat-tag" style="background:#fef3c7;color:#d97706;border-color:#fde68a;">🎥 ${{totalVids}} vids</span>` : '<span class="stat-tag" style="color:#ef4444;background:#fee2e2;">⚠️ No Video</span>'}}
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            ${{primary.price ? `<span class="plat-pricing" style="background:#fff;font-weight:800;">💰 ${{primary.price}} ${{primary.mrp ? `<s style="color:#94a3b8;font-size:0.7rem;">${{primary.mrp}}</s>` : ''}}</span>` : ''}}
            ${{primary.rating ? `<span class="plat-pricing" style="background:#fff;">⭐ ${{primary.rating}}</span>` : ''}}
            ${{primary.url ? `<a href="${{primary.url}}" target="_blank" style="font-size:0.72rem;font-weight:700;color:${{pColor.color}};text-decoration:none;background:#fff;border:1px solid ${{pColor.color}}40;padding:3px 9px;border-radius:4px;">Open Channel PDP ↗</a>` : ''}}
          </div>
        </div>
        <div class="brand-lane-body">
          <div class="media-filmstrip">
            ${{filtered.map(l => `
              ${{l.videos.map((v, vIdx) => `
                <div class="media-card" style="border-color:#f59e0b;">
                  <video controls playsinline preload="metadata">
                    <source src="${{v}}" type="video/mp4">
                  </video>
                  <div class="media-card-meta">
                    <span style="color:#d97706;font-weight:800;">🎥 Video #${{vIdx + 1}}</span>
                    <span style="font-size:0.6rem;background:#fef3c7;padding:1px 4px;border-radius:3px;">MP4</span>
                  </div>
                </div>
              `).join('')}}
              ${{l.images.map((img, imgIdx) => `
                <div class="media-card">
                  <img src="${{img}}" loading="lazy" alt="${{escapeHtml(l.title)}}" onclick="openLB('${{img}}', '${{escapeHtml(plat)}}', '${{escapeHtml(l.title)}}')" onerror="this.onerror=null;this.src='https://placehold.co/175x175?text=Image+Unavailable';">
                  <div class="media-card-meta">
                    <span>#${{imgIdx + 1}}</span>
                    <button class="compare-action-btn" onclick="event.stopPropagation();stageInComparator('${{img}}', '${{escapeHtml(plat)}} - ${{escapeHtml(l.title)}}')">⚖️ Compare</button>
                  </div>
                </div>
              `).join('')}}
            `).join('')}}
          </div>
        </div>
      `;
      container.appendChild(lane);
    }});

  }} else {{
    // MODE 2: COMPETITOR BENCHMARK
    const skuBrandMap = DATA.sku_data[currentSKU] || {{}};

    DATA.brands.forEach(b => {{
      const isHero = (b === 'The Derma Co');
      const brandListings = skuBrandMap[b] || [];

      // Filter listings by platform if not 'all'
      let filteredListings = brandListings;
      if (currentPlatformFilter !== 'all') {{
        filteredListings = brandListings.filter(l => l.platform.toLowerCase().includes(currentPlatformFilter.toLowerCase()));
      }}

      // Filter listings by search query if present
      if (searchQuery) {{
        filteredListings = filteredListings.filter(l => {{
          const text = (l.title + ' ' + l.bullets.join(' ') + ' ' + JSON.stringify(l.important_info)).toLowerCase();
          return text.includes(searchQuery);
        }});
      }}

      // REMOVE EMPTY CARDS - CRITICAL: IF NO MATCHING LISTINGS, DO NOT RENDER CARD!
      if (filteredListings.length === 0) return;

      const acc = DATA.brand_accents[b] || {{ color: '#475569', bg: '#f1f5f9', border: '#cbd5e1', tag: 'Competitor' }};
      const matchedTitle = (skuMeta.competitors_map && skuMeta.competitors_map[b]) ? skuMeta.competitors_map[b] : 'Direct Competitor';

      const lane = document.createElement('div');
      lane.className = 'brand-lane' + (isHero ? ' benchmark' : '');

      let platsCount = filteredListings.map(l => l.platform).filter((v, i, a) => a.indexOf(v) === i);
      let totalImgsInBrand = filteredListings.reduce((acc, l) => acc + l.images.length, 0);
      let totalVidsInBrand = filteredListings.reduce((acc, l) => acc + l.videos.length, 0);

      let hdrHtml = `
        <div class="brand-lane-hdr">
          <div class="brand-lane-title-group">
            <span class="brand-badge" style="background:${{acc.color}};">${{b}}</span>
            <span class="brand-product-title">${{matchedTitle}}</span>
            <span class="brand-product-sub">• ${{filteredListings.length}} listings across ${{platsCount.length}} platforms</span>
            <span class="stat-tag">📸 ${{totalImgsInBrand}} imgs</span>
            ${{totalVidsInBrand > 0 ? `<span class="stat-tag" style="background:#fef3c7;color:#d97706;border-color:#fde68a;">🎥 ${{totalVidsInBrand}} vids</span>` : ''}}
          </div>
          <div class="platform-selector-pills">
            ${{platsCount.map(p => `<span class="plat-pill" style="border-color:${{acc.color}}30;">${{p}}</span>`).join('')}}
          </div>
        </div>
      `;

      let bodyHtml = '<div class="brand-lane-body">';
      filteredListings.forEach(l => {{
        const pColor = DATA.platform_colors[l.platform] || {{ color: '#475569', icon: '🌐' }};
        bodyHtml += `
          <div class="platform-block">
            <div class="plat-hdr">
              <div class="plat-label" style="color:${{pColor.color}};">
                <span>${{pColor.icon}}</span>
                <span>${{l.platform}}</span>
                <span style="font-weight:500;color:#64748b;font-size:0.75rem;">— ${{escapeHtml(l.title.substring(0, 85))}}...</span>
              </div>
              <div style="display:flex;align-items:center;gap:8px;">
                ${{l.price ? `<span class="plat-pricing">💰 ${{l.price}} ${{l.mrp ? `<s style="color:#94a3b8;font-size:0.7rem;">${{l.mrp}}</s>` : ''}}</span>` : ''}}
                ${{l.rating ? `<span class="plat-pricing">⭐ ${{l.rating}}</span>` : ''}}
                ${{l.url ? `<a href="${{l.url}}" target="_blank" style="font-size:0.72rem;font-weight:700;color:${{pColor.color}};text-decoration:none;border:1px solid ${{pColor.color}}40;padding:2px 8px;border-radius:4px;">Open PDP ↗</a>` : ''}}
              </div>
            </div>

            <div class="media-filmstrip">
              ${{l.videos.map((v, vIdx) => `
                <div class="media-card" style="border-color:#f59e0b;">
                  <video controls playsinline preload="metadata">
                    <source src="${{v}}" type="video/mp4">
                  </video>
                  <div class="media-card-meta">
                    <span style="color:#d97706;font-weight:800;">🎥 Video #${{vIdx + 1}}</span>
                    <span style="font-size:0.6rem;background:#fef3c7;padding:1px 4px;border-radius:3px;">MP4</span>
                  </div>
                </div>
              `).join('')}}

              ${{l.images.map((img, imgIdx) => `
                <div class="media-card">
                  <img src="${{img}}" loading="lazy" alt="${{escapeHtml(l.title)}}" onclick="openLB('${{img}}', '${{escapeHtml(b)}}', '${{escapeHtml(l.title)}}')" onerror="this.onerror=null;this.src='https://placehold.co/175x175?text=Image+Unavailable';">
                  <div class="media-card-meta">
                    <span>#${{imgIdx + 1}}</span>
                    <button class="compare-action-btn" onclick="event.stopPropagation();stageInComparator('${{img}}', '${{escapeHtml(b)}} - ${{escapeHtml(l.title)}}')">⚖️ Compare</button>
                  </div>
                </div>
              `).join('')}}
            </div>
          </div>
        `;
      }});
      bodyHtml += '</div>';

      lane.innerHTML = hdrHtml + bodyHtml;
      container.appendChild(lane);
    }});
  }}
}}

function renderInfoTable() {{
  const table = document.getElementById('info-matrix-table');
  const skuMeta = DATA.skus[currentSKU];

  if (currentComparisonMode === 'marketplace') {{
    // MODE 1: CROSS-MARKETPLACE TABLE FOR THE DERMA CO
    const mpMap = DATA.marketplace_data[currentSKU] || {{}};

    // Active platforms that actually have listings for this SKU
    const activePlatforms = DATA.platforms.filter(p => (mpMap[p] && mpMap[p].length > 0));

    // Build thead
    let theadHtml = '<thead><tr><th>Audit Field</th>';
    activePlatforms.forEach(plat => {{
      const pColor = DATA.platform_colors[plat] || {{ color: '#0d9488', icon: '🌐' }};
      theadHtml += `<th>
        <div class="table-brand-hdr">
          <span class="table-brand-name" style="color:${{pColor.color}};">${{pColor.icon}} ${{plat}}</span>
          <span class="table-sku-name">The Derma Co Official Listing</span>
        </div>
      </th>`;
    }});
    theadHtml += '</tr></thead>';

    function getPlatData(p) {{
      const list = mpMap[p] || [];
      return list.length > 0 ? list[0] : null;
    }}

    let tbodyHtml = '<tbody>';

    // Row 1: Title
    tbodyHtml += '<tr><td class="section-row-hdr">Listing Title</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      tbodyHtml += d ? `<td><strong>${{escapeHtml(d.title)}}</strong><br><a href="${{d.url}}" target="_blank" style="font-size:0.7rem;color:#0d9488;">View Link ↗</a></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 2: Price / MRP
    tbodyHtml += '<tr><td class="section-row-hdr">Price & Discounts</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      tbodyHtml += d ? `<td><div style="font-size:0.9rem;font-weight:800;color:#0f172a;">${{d.price || 'N/A'}}</div>${{d.mrp ? `<div style="font-size:0.75rem;color:#64748b;">MRP: <s>${{d.mrp}}</s></div>` : ''}}</td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 3: Rating & Reviews
    tbodyHtml += '<tr><td class="section-row-hdr">Rating & Reviews</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      tbodyHtml += d ? `<td><div style="font-weight:800;color:#d97706;">⭐ ${{d.rating || 'N/A'}}</div><div style="font-size:0.72rem;color:#64748b;">${{d.review_count ? d.review_count + ' reviews' : ''}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 4: Bullets / Highlights
    tbodyHtml += '<tr><td class="section-row-hdr">Key Bullets (Verbatim)</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      if (d && d.bullets && d.bullets.length > 0) {{
        tbodyHtml += `<td><ul class="verbatim-bullet-list">${{d.bullets.map(b => `<li>${{escapeHtml(b)}}</li>`).join('')}}</ul></td>`;
      }} else {{
        tbodyHtml += '<td class="no-data-cell">—</td>';
      }}
    }});
    tbodyHtml += '</tr>';

    // Row 5: Description
    tbodyHtml += '<tr><td class="section-row-hdr">Description (Verbatim)</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      let desc = d && d.important_info ? (d.important_info['Product Description'] || d.important_info['Description'] || d.important_info['About the product'] || '') : '';
      if (!desc && d && d.bullets && d.bullets.length > 0) desc = d.bullets.join('\\n\\n');
      tbodyHtml += d && desc ? `<td><div class="verbatim-pre">${{escapeHtml(desc)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 6: Key Ingredients
    tbodyHtml += '<tr><td class="section-row-hdr">Key Ingredients (Verbatim)</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      let ings = d && d.important_info ? (d.important_info['Key Ingredients'] || d.important_info['Ingredients'] || '') : '';
      tbodyHtml += d && ings ? `<td><div class="verbatim-pre" style="background:#f0fdf4;border-left:3px solid #16a34a;padding:8px;">${{escapeHtml(ings)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 7: INCI Formula
    tbodyHtml += '<tr><td class="section-row-hdr">Full INCI Formula (Verbatim)</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      let full = d && d.important_info ? (d.important_info['Ingredients List'] || d.important_info['Ingredients:'] || '') : '';
      tbodyHtml += d && full ? `<td><div class="verbatim-pre" style="font-family:var(--mono);font-size:0.71rem;">${{escapeHtml(full)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 8: How to Use
    tbodyHtml += '<tr><td class="section-row-hdr">How to Use (Verbatim)</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      let usage = d && d.important_info ? (d.important_info['How to use'] || d.important_info['Directions'] || '') : '';
      tbodyHtml += d && usage ? `<td><div class="verbatim-pre">${{escapeHtml(usage)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 9: Safety & Patch Test
    tbodyHtml += '<tr><td class="section-row-hdr">Patch Testing & Safety</td>';
    activePlatforms.forEach(p => {{
      const d = getPlatData(p);
      let patch = d && d.important_info ? (d.important_info['Patch testing'] || d.important_info['Disclaimer And Additional Information'] || '') : '';
      tbodyHtml += d && patch ? `<td><div class="verbatim-pre">${{escapeHtml(patch)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    tbodyHtml += '</tbody>';
    table.innerHTML = theadHtml + tbodyHtml;

  }} else {{
    // MODE 2: COMPETITOR BENCHMARK TABLE
    const skuBrandMap = DATA.sku_data[currentSKU] || {{}};

    // Active brands that actually have listings for this SKU
    const activeBrands = DATA.brands.filter(b => (skuBrandMap[b] && skuBrandMap[b].length > 0));

    let theadHtml = '<thead><tr><th>Product Attribute</th>';
    theadHtml += `<th>
      <div class="table-brand-hdr">
        <span class="table-brand-name" style="color:#0d9488;">The Derma Co (Benchmark)</span>
        <span class="table-sku-name">${{(skuMeta.competitors_map && skuMeta.competitors_map['The Derma Co']) ? skuMeta.competitors_map['The Derma Co'] : skuMeta.name}}</span>
      </div>
    </th>`;

    activeBrands.filter(b => b !== 'The Derma Co').forEach(b => {{
      const acc = DATA.brand_accents[b] || {{ color: '#0f172a' }};
      theadHtml += `<th>
        <div class="table-brand-hdr">
          <span class="table-brand-name" style="color:${{acc.color}};">${{b}}</span>
          <span class="table-sku-name">${{(skuMeta.competitors_map && skuMeta.competitors_map[b]) ? skuMeta.competitors_map[b] : 'Competitor SKU'}}</span>
        </div>
      </th>`;
    }});
    theadHtml += '</tr></thead>';

    function getBrandData(b) {{
      const list = skuBrandMap[b] || [];
      if (list.length === 0) return null;
      const d2c = list.find(l => l.platform.toLowerCase().includes('d2c') || l.platform.toLowerCase().includes('brand'));
      const amz = list.find(l => l.platform.toLowerCase().includes('amazon'));
      const primary = d2c || amz || list[0];
      return {{ primary, all: list }};
    }}

    let tbodyHtml = '<tbody>';

    // Row 1: Title & Platforms
    tbodyHtml += '<tr><td class="section-row-hdr">Matched SKU & Platforms</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      const plats = d.all.map(l => l.platform).filter((v,i,a)=>a.indexOf(v)===i);
      tbodyHtml += `<td><strong>${{escapeHtml(d.primary.title)}}</strong><br><div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;">${{plats.map(p => `<span class="tag-item" style="background:#ccfbf1;color:#0f766e;">${{p}}</span>`).join('')}}</div></td>`;
    }});
    tbodyHtml += '</tr>';

    // Row 2: Price & Discounts
    tbodyHtml += '<tr><td class="section-row-hdr">Pricing & Commercials</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      tbodyHtml += `<td><div style="font-size:0.85rem;font-weight:800;color:#0f172a;">${{d.primary.price || 'N/A'}}</div>${{d.primary.mrp ? `<div style="font-size:0.75rem;color:#64748b;">MRP: <s>${{d.primary.mrp}}</s></div>` : ''}}</td>`;
    }});
    tbodyHtml += '</tr>';

    // Row 3: Rating & Reviews
    tbodyHtml += '<tr><td class="section-row-hdr">Ratings & Reviews</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      tbodyHtml += `<td><div style="font-weight:800;color:#d97706;">⭐ ${{d.primary.rating || 'N/A'}}</div><div style="font-size:0.72rem;color:#64748b;">${{d.primary.review_count ? d.primary.review_count + ' reviews' : ''}}</div></td>`;
    }});
    tbodyHtml += '</tr>';

    // Row 4: Bullets / About This Item
    tbodyHtml += '<tr><td class="section-row-hdr">Key Bullets (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      const anyWithBullets = d ? d.all.find(l => l.bullets && l.bullets.length > 0) : null;
      if (anyWithBullets) {{
        tbodyHtml += `<td><ul class="verbatim-bullet-list">${{anyWithBullets.bullets.map(b => `<li>${{escapeHtml(b)}}</li>`).join('')}}</ul></td>`;
      }} else {{
        tbodyHtml += '<td class="no-data-cell">—</td>';
      }}
    }});
    tbodyHtml += '</tr>';

    // Row 5: Product Description
    tbodyHtml += '<tr><td class="section-row-hdr">Full Description (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      let desc = '';
      for (const l of d.all) {{
        if (l.important_info) {{
          desc = l.important_info['Product Description'] || l.important_info['Description'] || l.important_info['About the product'] || '';
          if (desc) break;
        }}
      }}
      if (!desc && d.primary.bullets && d.primary.bullets.length > 0) desc = d.primary.bullets.join('\\n\\n');
      tbodyHtml += desc ? `<td><div class="verbatim-pre">${{escapeHtml(desc)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 6: Key Actives
    tbodyHtml += '<tr><td class="section-row-hdr">Key Actives & Ingredients (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      let ings = '';
      for (const l of d.all) {{
        if (l.important_info) {{
          ings = l.important_info['Key Ingredients'] || l.important_info['Ingredients'] || '';
          if (ings) break;
        }}
        if (l.overview && (l.overview['Active Ingredients'] || l.overview['Active ingredients'])) {{
          ings = l.overview['Active Ingredients'] || l.overview['Active ingredients'];
          break;
        }}
      }}
      tbodyHtml += ings ? `<td><div class="verbatim-pre" style="background:#f0fdf4;border-left:3px solid #16a34a;padding:8px;">${{escapeHtml(ings)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 7: Full INCI Formula
    tbodyHtml += '<tr><td class="section-row-hdr">Full INCI Formula (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      let full = '';
      for (const l of d.all) {{
        if (l.important_info) {{
          full = l.important_info['Ingredients List'] || l.important_info['Ingredients:'] || '';
          if (full) break;
        }}
      }}
      tbodyHtml += full ? `<td><div class="verbatim-pre" style="font-family:var(--mono);font-size:0.71rem;">${{escapeHtml(full)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 8: How to Use
    tbodyHtml += '<tr><td class="section-row-hdr">Directions / How to Use (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      let usage = '';
      for (const l of d.all) {{
        if (l.important_info) {{
          usage = l.important_info['How to use'] || l.important_info['Directions'] || '';
          if (usage) break;
        }}
      }}
      tbodyHtml += usage ? `<td><div class="verbatim-pre">${{escapeHtml(usage)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    // Row 9: FAQs
    tbodyHtml += '<tr><td class="section-row-hdr">FAQs (Verbatim)</td>';
    activeBrands.forEach(b => {{
      const d = getBrandData(b);
      if (!d) {{ tbodyHtml += '<td class="no-data-cell">—</td>'; return; }}
      let faq = '';
      for (const l of d.all) {{
        if (l.important_info && (l.important_info['FAQ'] || l.important_info['FAQs\\n+\\n-'])) {{
          faq = l.important_info['FAQ'] || l.important_info['FAQs\\n+\\n-'];
          break;
        }}
      }}
      tbodyHtml += faq ? `<td><div class="verbatim-pre" style="max-height:280px;overflow-y:auto;">${{escapeHtml(faq)}}</div></td>` : '<td class="no-data-cell">—</td>';
    }});
    tbodyHtml += '</tr>';

    tbodyHtml += '</tbody>';
    table.innerHTML = theadHtml + tbodyHtml;
  }}
}}

// Lightbox Logic
function openLB(src, brand, title) {{
  currentLBImg = src;
  currentZoom = 1;
  translateX = 0;
  translateY = 0;
  const modal = document.getElementById('lb-modal');
  const img = document.getElementById('lb-img');
  img.src = src;
  updateLBTransform();
  modal.classList.add('active');
}}

function closeLB() {{
  document.getElementById('lb-modal').classList.remove('active');
}}

function zoomLB(delta) {{
  currentZoom = Math.max(0.5, Math.min(4, currentZoom + delta));
  updateLBTransform();
}}

function resetLB() {{
  currentZoom = 1;
  translateX = 0;
  translateY = 0;
  updateLBTransform();
}}

function updateLBTransform() {{
  const img = document.getElementById('lb-img');
  img.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{currentZoom}})`;
  document.getElementById('lb-zoom-level').innerText = Math.round(currentZoom * 100) + '%';
}}

function startDrag(e) {{
  isDragging = true;
  startX = e.clientX - translateX;
  startY = e.clientY - translateY;
  window.addEventListener('mousemove', onDrag);
  window.addEventListener('mouseup', stopDrag);
}}

function onDrag(e) {{
  if (!isDragging) return;
  translateX = e.clientX - startX;
  translateY = e.clientY - startY;
  updateLBTransform();
}}

function stopDrag() {{
  isDragging = false;
  window.removeEventListener('mousemove', onDrag);
  window.removeEventListener('mouseup', stopDrag);
}}

// Dual Comparator Logic
function openComparator() {{
  document.getElementById('dual-compare-modal').classList.add('active');
}}

function closeComparator() {{
  document.getElementById('dual-compare-modal').classList.remove('active');
}}

function stageInComparator(imgSrc, label) {{
  if (!slotA) {{
    slotA = {{ src: imgSrc, label: label || 'Image A' }};
  }} else if (!slotB) {{
    slotB = {{ src: imgSrc, label: label || 'Image B' }};
  }} else {{
    slotB = {{ src: imgSrc, label: label || 'Image B' }};
  }}
  updateComparatorSlots();
  openComparator();
}}

function clearComparator() {{
  slotA = null;
  slotB = null;
  updateComparatorSlots();
}}

function updateComparatorSlots() {{
  const sA = document.getElementById('slot-a');
  const sB = document.getElementById('slot-b');

  if (slotA) {{
    sA.classList.add('filled');
    sA.innerHTML = `<div class="dual-slot-label">${{slotA.label}}</div><img src="${{slotA.src}}" alt="Slot A">`;
  }} else {{
    sA.classList.remove('filled');
    sA.innerHTML = `<div class="dual-slot-label">Slot A (Empty)</div><p style="color:#94a3b8;font-size:0.8rem;">Select an image using the "⚖️ Compare" button</p>`;
  }}

  if (slotB) {{
    sB.classList.add('filled');
    sB.innerHTML = `<div class="dual-slot-label">${{slotB.label}}</div><img src="${{slotB.src}}" alt="Slot B">`;
  }} else {{
    sB.classList.remove('filled');
    sB.innerHTML = `<div class="dual-slot-label">Slot B (Empty)</div><p style="color:#94a3b8;font-size:0.8rem;">Select a 2nd image using the "⚖️ Compare" button</p>`;
  }}
}}

function escapeHtml(str) {{
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
}}

window.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape') {{
    closeLB();
    closeComparator();
  }}
}});
</script>
</body>
</html>
'''

with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"Successfully generated complete bright 4-category HTML at: {OUTPUT_HTML}")
print(f"File size: {os.path.getsize(OUTPUT_HTML) / 1024 / 1024:.2f} MB")

# Recreate Launcher batch file
bat_content = f'''@echo off
title HONASA TDC - Competitive Research Canvas
echo Opening Competitive Research Canvas in your default browser...
start "" "{OUTPUT_HTML}"
exit
'''

with open(OUTPUT_BAT, 'w', encoding='utf-8') as bf:
    bf.write(bat_content)

print("Launcher batch file updated.")
print("Bright 4-Category Generation Completed Successfully!")
