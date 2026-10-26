import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import os
import re
import time
import json
import urllib.parse
import openpyxl
from curl_cffi import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Load API key
env_path = r"c:\Users\elaya.n\Documents\HONASA TDC\.env"
api_key = None
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.strip().split("=", 1)[1]

if not api_key:
    raise ValueError("GEMINI_API_KEY not found!")

client = genai.Client(api_key=api_key)

# Load full Blinkit catalog
catalog_path = r"c:\Users\elaya.n\Documents\HONASA TDC\skuscout\blinkit_catalog.json"
with open(catalog_path, "r", encoding="utf-8") as f:
    catalog = json.load(f)

class BatchSelection(BaseModel):
    selected_url: str = Field(description="The exact URL from candidates matching target single unit, or empty string if none match.")
    is_match: bool = Field(description="True if an exact single-unit match was found.")
    reason: str = Field(description="Brief explanation of selection or rejection.")

def get_brand_key(brand):
    clean = re.sub(r"[^a-z0-9]+", "", str(brand).lower())
    if "derma" in clean: return "derma-co"
    if "ordinary" in clean: return "ordinary"
    if "minimalist" in clean: return "minimalist"
    if "dot" in clean: return "dot-key"
    if "lor" in clean and "al" in clean: return "loreal"
    if "foxtale" in clean: return "foxtale"
    if "cetaphil" in clean: return "cetaphil"
    if "himalaya" in clean: return "himalaya"
    if "simple" in clean: return "simple"
    return clean

def find_catalog_candidates(brand, variant, category):
    b_key = get_brand_key(brand)
    clean_v = re.sub(r"[—–\-+]+", " ", variant).lower()
    
    numbers = re.findall(r"\b\d+\b", clean_v)
    v_words = [w for w in re.findall(r"\w+", clean_v) if len(w) > 2 and w not in ["face", "serum", "wash", "gel", "cream", "daily", "skin", "pure", "with", "and", "for", "cleanser", "shampoo"]]
    
    cat_keywords = []
    forbidden_keywords = []
    if category == "SERUM":
        cat_keywords = ["serum"]
        forbidden_keywords = ["wash", "cleanser", "cream", "shampoo", "body-wash", "sunscreen", "patches", "toner"]
    elif category == "FACEWASH":
        cat_keywords = ["wash", "cleanser", "facewash"]
        forbidden_keywords = ["body-wash", "shampoo", "serum", "patches", "cream", "toner", "sunscreen"]
    elif category == "SHAMPOO":
        cat_keywords = ["shampoo"]
        forbidden_keywords = ["body-wash", "face", "serum", "cream", "wash", "facewash"]
    elif category == "SUNSCREEN":
        cat_keywords = ["sunscreen", "spf", "aqua-gel"]
        forbidden_keywords = ["shampoo", "face-wash", "body-wash", "serum"]

    candidates = []
    for item in catalog:
        slug = item.get("slug", "").lower()
        title = item.get("title", "").lower()
        
        # Exact brand check
        if b_key == "derma-co":
            if not ("derma-co" in slug or "derma co" in title):
                continue
        elif b_key == "dot-key":
            if not ("dot-key" in slug or "dot key" in title or "dot and key" in title):
                continue
        elif b_key == "loreal":
            if not ("loreal" in slug or "l-oreal" in slug or "l oreal" in slug):
                continue
        elif b_key == "ordinary":
            if not (re.search(r"\bordinary\b", slug) or re.search(r"\bordinary\b", title)):
                continue
            if "extraordinary" in slug or "extraordinary" in title:
                continue
        else:
            if not (b_key in slug or b_key in title):
                continue
                
        is_combo = any(k in slug for k in ["combo", "pack-of-2", "pack-of-3", "pack-of-4", "pack-of-5", "bogo"])
        
        score = 0
        if any(ck in slug for ck in cat_keywords):
            score += 15
        elif any(ck in title for ck in cat_keywords):
            score += 10
            
        if any(fk in slug for fk in forbidden_keywords):
            score -= 25
            
        if is_combo:
            score -= 15
            
        for w in v_words:
            if w in slug:
                score += 5
            elif w in title:
                score += 3
                
        for n in numbers:
            if f"-{n}-" in slug or f" {n}%" in title or f" {n} " in title:
                score += 8
                
        if score > 0:
            candidates.append((score, is_combo, item))
            
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[2] for c in candidates[:6]]

def search_ddg_blinkit(brand, variant):
    clean_v = re.sub(r"[—–\-+]+", " ", variant).strip()
    query = f"Blinkit {brand} {clean_v}"
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    results = []
    try:
        r = requests.get(url, impersonate="chrome120", headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.find_all("div", class_="result"):
            a_link = div.find("a", class_="result__snippet")
            if not a_link: continue
            href = a_link.get("href", "")
            if "uddg=" in href:
                actual = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if "blinkit.com" in actual and ("/prn/" in actual or "/prid/" in actual):
                    h2 = div.find("h2").get_text(strip=True) if div.find("h2") else ""
                    clean_u = actual.split("?")[0]
                    results.append({"url": clean_u, "title": h2})
    except Exception:
        pass
    return results[:3]

def verify_candidates_with_ai(brand, variant, category, candidates):
    if not candidates:
        return None
        
    cand_lines = []
    for idx, c in enumerate(candidates, 1):
        t = c.get("title", "")
        t_clean = t.encode("ascii", "ignore").decode("ascii")
        cand_lines.append(f"Candidate {idx}:\n  URL: {c['url']}\n  Title: {t_clean}")
    
    cand_text = "\n".join(cand_lines)
    
    prompt = f"""
You are an expert strict e-commerce data verification agent for Blinkit India (quick commerce).

TARGET PRODUCT:
Category: {category}
Brand: {brand}
Variant & Target Size: {variant} (SINGLE UNIT ONLY)
Store: Blinkit India

CANDIDATES FOUND ON BLINKIT:
{cand_text}

STRICT VERIFICATION RULES:
1. Exact Brand & Core Variant: The brand and core variant must match. Ignore marketing fluff like '3X', 'For Glowing Skin', 'Broad Spectrum', 'With Vitamin E', 'Clinically Proven'.
2. Single Unit Only: Must be a SINGLE unit matching the product variant. Standard retail single-unit bottles or tubes are expected (e.g. ~30ml for serums, ~50g for sunscreens, ~100ml for cleansers, ~180ml-250ml for shampoos). Strictly REJECT combos, 'Pack of 2', 'Pack of 3', BOGO, and bundles. If a candidate is a single bottle/tube matching the variant, it is acceptable even if the exact ml is omitted from the title.
3. Category Integrity: 
   - If target is SERUM: Must be a Face Serum. Strictly REJECT face washes, creams, toners, patches, hair serums.
   - If target is FACEWASH: Must be a Face Wash / Cleanser. Strictly REJECT body washes, face serums, creams, patches.
   - If target is SHAMPOO: Must be a Shampoo. Strictly REJECT conditioners, face washes, hair serums.
   - If target is SUNSCREEN: Must be a Sunscreen. Strictly REJECT moisturizers without SPF, body washes.
4. Variant Discrepancy: Different active ingredients or product lines (e.g. 10% vs 2%, Niacinamide vs Vitamin C, Salicylic vs Kojic, Fall Resist vs Extraordinary Oil) must be strictly REJECTED.
5. If an exact match for this single unit product is found, return its URL. If NO candidate matches all rules, return is_match=False and selected_url="".
"""
    for attempt in range(5):
        try:
            resp = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=BatchSelection,
                    temperature=0.1
                )
            )
            return json.loads(resp.text)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_s = 4.0 * (attempt + 1)
                print(f"    [Rate limit hit: pausing {wait_s}s before retry {attempt+1}...]", flush=True)
                time.sleep(wait_s)
            else:
                print(f"    [!] Gemini error: {e}", flush=True)
                return None
    return None

def scout_single_blinkit(brand, variant, category):
    candidates = find_catalog_candidates(brand, variant, category)
    
    ddg_cands = search_ddg_blinkit(brand, variant)
    for d in ddg_cands:
        if d["url"] not in [c["url"] for c in candidates]:
            candidates.append(d)
            
    if not candidates:
        return None, "No candidates found on Blinkit"
        
    verdict = verify_candidates_with_ai(brand, variant, category, candidates)
    if verdict and verdict.get("is_match") and verdict.get("selected_url"):
        return verdict["selected_url"], verdict.get("reason", "Approved")
        
    reason = verdict.get("reason") if verdict else "No match confirmed"
    return None, reason

def run_blinkit_scouting():
    excel_path = r"c:\Users\elaya.n\Documents\HONASA TDC\GSO_LINKs_AI_Verified.xlsx"
    backup_path = r"c:\Users\elaya.n\Documents\HONASA TDC\GSO LINKs.xlsx"
    
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["Sheet1"]
    
    total_processed = 0
    total_found = 0
    total_rejected = 0
    
    print("=== SKUSCOUT MASTER BLINKIT CANONICAL RESOLUTION STARTED ===", flush=True)
    
    current_category = "SERUM"
    
    for r in range(6, ws.max_row + 1):
        c2 = ws.cell(row=r, column=2).value
        c3 = ws.cell(row=r, column=3).value
        c4 = ws.cell(row=r, column=4).value
        
        if c2 in ["SERUM", "SHAMPOO", "SUNSCREEN", "FACEWASH"]:
            current_category = c2
            continue
            
        if not c3 or not c4:
            continue
            
        brand = str(c3).strip()
        variant = str(c4).strip()
        
        if brand == "Brand" or variant == "Product Variant & Size":
            continue
            
        if variant in ["—", "-", "–", "None"] or len(variant) < 2 or not any(c.isalnum() for c in variant):
            continue
            
        existing_blinkit = ws.cell(row=r, column=9).value
        if existing_blinkit and str(existing_blinkit).strip().startswith("http") and "/prn/" in str(existing_blinkit):
            print(f"Row {r:3d} [{current_category:9s}] {brand:15s} | {variant[:30]} -> [ALREADY VERIFIED]", flush=True)
            continue
            
        total_processed += 1
        print(f"\nRow {r:3d} [{current_category:9s}] {brand:15s} | {variant}", flush=True)
        
        url, reason = scout_single_blinkit(brand, variant, current_category)
        if url:
            total_found += 1
            ws.cell(row=r, column=9).value = url
            print(f"  [AI APPROVED] {url}", flush=True)
            print(f"  Reason: {reason}", flush=True)
        else:
            total_rejected += 1
            print(f"  [NOT FOUND / REJECTED] {reason}", flush=True)
            
        # Incremental save after EVERY product
        try:
            wb.save(excel_path)
        except Exception as e:
            print(f"  [Save error on {excel_path}: {e}]", flush=True)
        try:
            wb.save(backup_path)
        except Exception as e:
            print(f"  [Save error on {backup_path}: {e}]", flush=True)
            
        # Pacing: 3.5s to stay under 15 RPM
        time.sleep(3.5)
        
    try:
        wb.save(excel_path)
        wb.save(backup_path)
        print("\n=== COMPLETE! Saved all verified Blinkit links to Excel! ===", flush=True)
    except Exception as e:
        print(f"Final save error: {e}", flush=True)
        
    print(f"\nSummary: Processed {total_processed} items. Found & Approved: {total_found}. Not on Blinkit / Rejected: {total_rejected}.", flush=True)

if __name__ == "__main__":
    run_blinkit_scouting()
