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

class BatchSelection(BaseModel):
    selected_url: str = Field(description="The exact URL matching the target single unit product, or empty string if none match.")
    is_match: bool = Field(description="True if an exact single-unit match was found.")
    reason: str = Field(description="Brief explanation of selection or rejection.")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def clean_nykaa_url(url):
    m = re.search(r'(/p/\d+)', url)
    if m:
        return url.split('?')[0]
    return url.split('?')[0]

def search_nykaa_direct(query):
    clean_q = re.sub(r'[\+\/\—\–\-]+', ' ', query).strip()
    url = f"https://www.nykaa.com/search/result/?q={urllib.parse.quote(clean_q)}"
    candidates = []
    try:
        r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/p/' in href:
                    if not href.startswith('http'):
                        href = 'https://www.nykaa.com' + href
                    clean = clean_nykaa_url(href)
                    title = a.get_text(strip=True)
                    if clean not in [c['url'] for c in candidates]:
                        candidates.append({'url': clean, 'title': title})
    except Exception:
        pass
    return candidates[:6]

def search_nykaa_ddg(query):
    clean_q = re.sub(r'[\+\/\—\–\-]+', ' ', query).strip()
    encoded = urllib.parse.quote_plus(f"site:nykaa.com {clean_q}")
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    results = []
    try:
        r = requests.get(url, impersonate="chrome120", headers=HEADERS, timeout=7)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.find_all("div", class_="result"):
            a_link = div.find("a", class_="result__snippet")
            if not a_link:
                continue
            href = a_link.get("href", "")
            if "uddg=" in href:
                actual = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if "nykaa.com" in actual and "/p/" in actual:
                    title_text = div.find("h2").get_text(strip=True) if div.find("h2") else ""
                    clean = clean_nykaa_url(actual)
                    if clean not in [res["url"] for res in results]:
                        results.append({"url": clean, "title": title_text})
    except Exception:
        pass
    return results[:5]

def enrich_candidate(cand):
    try:
        r = requests.get(cand['url'], impersonate="chrome120", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            if soup.title and soup.title.string:
                cand['page_title'] = soup.title.string.strip()
            meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta:
                cand['page_desc'] = meta.get('content', '').strip()
    except:
        pass
    return cand

def verify_candidates_with_ai(brand, variant, candidates):
    if not candidates:
        return None
        
    cand_lines = []
    for idx, c in enumerate(candidates, 1):
        t = c.get('page_title') or c.get('title', '')
        t_clean = t.encode('ascii', 'ignore').decode('ascii')
        cand_lines.append(f"Candidate {idx}:\n  URL: {c['url']}\n  Title: {t_clean}")
    
    cand_text = "\n".join(cand_lines)
    
    prompt = f"""
You are an expert strict e-commerce data verification agent for Nykaa India.

TARGET PRODUCT:
Brand: {brand}
Variant & Size: {variant} (SINGLE UNIT ONLY)
Store: Nykaa India

CANDIDATES FOUND ON NYKAA:
{cand_text}

VERIFICATION RULES:
1. Exact Brand & Core Variant: The brand and core variant must match. (Ignore retailer marketing fluff like 'For Glowing Skin', 'Broad Spectrum', 'With Vitamin E', 'Clinically Proven').
2. Single Unit Only: Must be a single unit matching target size (e.g. 30ml/50g/100ml/250ml). Strictly REJECT multi-packs, 'Pack of 2', 'Pack of 3', combos, and bundles.
3. Variant Integrity: Different variants (e.g. 'Glow' vs 'Matte', '10%' vs '15%', 'Niacinamide' vs 'Vitamin C', 'Anti-Dandruff' vs 'Hair Fall') must be strictly REJECTED.
4. If a candidate is the exact match for this single unit product, select its URL. If none match, return is_match=False.
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

def scout_single_nykaa(brand, variant):
    clean_v = re.sub(r'[\+\/\—\–\-]+', ' ', variant).strip()
    
    # Pass 1: Direct search on Nykaa
    candidates = search_nykaa_direct(f"{brand} {clean_v}")
    
    # Pass 2: Simplified query without secondary ingredients (e.g. if '2% Kojic Acid + 1% Alpha Arbutin')
    parts = clean_v.split()
    if len(candidates) < 2 and len(parts) > 3:
        core_query = f"{brand} {parts[0]} {parts[1]} {parts[2]}"
        more_cands = search_nykaa_direct(core_query)
        for mc in more_cands:
            if mc['url'] not in [c['url'] for c in candidates]:
                candidates.append(mc)
                
    # Pass 3: Fallback to DuckDuckGo if direct returned nothing
    if not candidates:
        candidates = search_nykaa_ddg(f"{brand} {clean_v}")
        
    if not candidates:
        return None, "No candidates found on Nykaa"
        
    # Quick enrich first 2
    for c in candidates[:2]:
        enrich_candidate(c)
        
    verdict = verify_candidates_with_ai(brand, variant, candidates)
    if verdict and verdict.get("is_match") and verdict.get("selected_url"):
        return verdict["selected_url"], verdict.get("reason", "Approved")
        
    # Pass 4: Alternate concise search
    if len(parts) >= 2:
        concise_q = f"{brand} {parts[0]} {parts[-1]}"
        alt_candidates = search_nykaa_direct(concise_q)
        new_cands = [c for c in alt_candidates if c['url'] not in [x['url'] for x in candidates]]
        if new_cands:
            for c in new_cands[:2]:
                enrich_candidate(c)
            alt_verdict = verify_candidates_with_ai(brand, variant, new_cands)
            if alt_verdict and alt_verdict.get("is_match") and alt_verdict.get("selected_url"):
                return alt_verdict["selected_url"], alt_verdict.get("reason", "Approved on retry")
            
    reason = verdict.get("reason") if verdict else "No match confirmed"
    return None, reason

def run_nykaa_scouting():
    excel_path = r"c:\Users\elaya.n\Documents\HONASA TDC\GSO_LINKs_AI_Verified.xlsx"
    backup_path = r"c:\Users\elaya.n\Documents\HONASA TDC\GSO LINKs.xlsx"
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["Sheet1"]
    
    total_processed = 0
    total_found = 0
    
    print("=== SKUSCOUT MASTER NYKAA RESOLUTION STARTED ===", flush=True)
    
    for r in range(8, ws.max_row + 1):
        c3 = ws.cell(row=r, column=3).value
        c4 = ws.cell(row=r, column=4).value
        if not c3 or not c4:
            continue
        brand = str(c3).strip()
        variant = str(c4).strip()
        
        # Skip placeholders or empty rows
        if variant in ['—', '-', '–'] or len(variant) < 2 or not any(c.isalnum() for c in variant):
            continue
            
        existing_nykaa = ws.cell(row=r, column=8).value
        if existing_nykaa and str(existing_nykaa).strip().startswith("http") and "/p/" in str(existing_nykaa):
            print(f"Row {r:3d} | {brand:15s} | {variant[:30]} -> [ALREADY VERIFIED]", flush=True)
            continue
            
        total_processed += 1
        print(f"\nRow {r:3d} | {brand:15s} | {variant}", flush=True)
        
        url, reason = scout_single_nykaa(brand, variant)
        if url:
            total_found += 1
            ws.cell(row=r, column=8).value = url
            print(f"  [AI APPROVED] {url}", flush=True)
            print(f"  Reason: {reason}", flush=True)
        else:
            print(f"  [NOT FOUND / REJECTED] {reason}", flush=True)
            
        # Incremental save after EVERY product
        try:
            wb.save(excel_path)
            wb.save(backup_path)
        except Exception as e:
            print(f"  [Save error: {e}]", flush=True)
            
        # Pacing: 3.5s to comfortably stay under 15 RPM
        time.sleep(3.5)
        
    try:
        wb.save(excel_path)
        wb.save(backup_path)
        print("\n=== COMPLETE! Saved all verified Nykaa links to Excel! ===", flush=True)
    except Exception as e:
        print(f"Final save error: {e}", flush=True)
        
    print(f"Processed: {total_processed}, Found: {total_found}", flush=True)

if __name__ == "__main__":
    run_nykaa_scouting()
