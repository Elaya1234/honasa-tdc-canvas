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
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env or environment!")

client = genai.Client(api_key=api_key)

class VerificationResult(BaseModel):
    is_exact_match: bool = Field(description="True if the scraped product is exactly the same as the target product (brand, variant, size) and is NOT a combo pack.")
    confidence: int = Field(description="Confidence score 0-100")
    reason: str = Field(description="Brief explanation of approval or rejection.")

def clean_url(url, domain):
    try:
        parsed = urllib.parse.urlparse(url)
        if "amazon.in" in domain:
            m = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
            if m:
                return f"https://www.amazon.in/dp/{m.group(1)}"
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        elif "flipkart.com" in domain:
            m = re.search(r'(/p/itm[a-zA-Z0-9]+)', url)
            if m:
                return url.split("?")[0]
            return url.split("?")[0]
        elif "nykaa.com" in domain:
            m = re.search(r'(/p/\d+)', url)
            if m:
                return url.split("?")[0]
            return url.split("?")[0]
        else:
            return url.split("?")[0]
    except:
        return url

def search_ddg(query, domain=None):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    links = []
    try:
        r = requests.get(url, impersonate="chrome120", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", class_="result__snippet", href=True):
            href = a["href"]
            if "uddg=" in href:
                actual = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if "y.js" not in actual and "ad_domain" not in actual and "bing.com" not in actual:
                    if domain is None or domain in actual:
                        cleaned = clean_url(actual, domain or "")
                        if cleaned not in links:
                            links.append(cleaned)
    except Exception as e:
        pass
    return links[:5]

def quick_scrape(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    try:
        r = requests.get(url, impersonate="chrome120", headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Title
        title = ""
        az_title = soup.find(id="productTitle")
        if az_title:
            title = az_title.get_text(strip=True)
        elif soup.title:
            title = soup.title.string or ""
            
        desc = ""
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_desc:
            desc = meta_desc.get("content", "")
            
        return {"url": url, "title": title.strip(), "description": desc.strip()}
    except:
        return None

def verify_with_gemini(target_brand, target_variant, scraped):
    prompt = f"""
You are an expert strict e-commerce data verification agent for Indian beauty & personal care marketplaces (Amazon, Nykaa, Flipkart, Blinkit, Zepto, D2C).

TARGET PRODUCT:
Brand: {target_brand}
Target Variant & Size: {target_variant}

FOUND ON STORE:
URL: {scraped['url']}
Page Title: {scraped['title']}
Description: {scraped['description']}

STRICT RULES:
1. Exact Brand Match: Brand must match {target_brand}.
2. Core Variant Match: The core product variant must match. (Ignore marketing claims like 'SPF 50 PA++++', 'with Vitamin E', 'Broad Spectrum', 'For Glowing Skin' appended by retailers).
3. Unit / Pack Match: MUST be a single individual unit matching the specified size. Strictly REJECT combos, bundles, packs of 2/3/4, or travel sizes.
4. Competitor / Sponsored: Strictly REJECT if it is a different product.

Evaluate carefully and output structured JSON.
"""
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VerificationResult,
                temperature=0.1
            )
        )
        data = json.loads(resp.text)
        return data
    except Exception as e:
        print(f"    [!] Gemini call failed: {e}")
        return {"is_exact_match": False, "confidence": 0, "reason": str(e)}

D2C_DOMAINS = {
    "The Derma Co": "thedermaco.com",
    "Minimalist": "beminimalist.co",
    "Dot & Key": "dotandkey.com",
    "L'Oreal Paris": "lorealparis.co.in",
    "L'Oral Paris": "lorealparis.co.in",
    "Foxtale": "foxtale.in",
    "Cetaphil": "cetaphil.in",
    "The Ordinary": "theordinary.com",
    "Himalaya": "himalayawellness.in",
    "Simple": "simpleskincare.in"
}

MARKETPLACE_CONFIG = [
    {"col": 5, "name": "Brand D2C", "domain_fn": lambda b: D2C_DOMAINS.get(b, ""), "query_fn": lambda b, v: f"site:{D2C_DOMAINS.get(b, '')} {v}" if D2C_DOMAINS.get(b) else ""},
    {"col": 6, "name": "Amazon", "domain_fn": lambda b: "amazon.in", "query_fn": lambda b, v: f"site:amazon.in {b} {v}"},
    {"col": 7, "name": "Flipkart", "domain_fn": lambda b: "flipkart.com", "query_fn": lambda b, v: f"Flipkart {b} {v}"},
    {"col": 8, "name": "Nykaa", "domain_fn": lambda b: "nykaa.com", "query_fn": lambda b, v: f"Nykaa {b} {v}"},
    {"col": 9, "name": "Blinkit", "domain_fn": lambda b: "blinkit.com", "query_fn": lambda b, v: f"Blinkit {b} {v}"},
    {"col": 10, "name": "Zepto", "domain_fn": lambda b: "zepto.com", "query_fn": lambda b, v: f"Zepto {b} {v}"},
    {"col": 11, "name": "Instamart", "domain_fn": lambda b: "swiggy.com", "query_fn": lambda b, v: f"Swiggy Instamart {b} {v}"},
]

def resolve_and_verify_single(brand, variant, mp):
    domain = mp["domain_fn"](brand)
    if not domain:
        return None
    query = mp["query_fn"](brand, variant)
    print(f"  Searching {mp['name']}: '{query}'")
    candidates = search_ddg(query, domain)
    if not candidates:
        fallback_query = f"{mp['name']} {brand} {variant}"
        candidates = search_ddg(fallback_query, domain)
        
    print(f"    Found {len(candidates)} candidate links.")
    for idx, url in enumerate(candidates, 1):
        print(f"    [{idx}/{len(candidates)}] Checking: {url}")
        scraped = quick_scrape(url)
        if not scraped or not scraped["title"]:
            print("      [x] Could not fetch page content.")
            continue
        clean_title = scraped['title'][:75].encode('ascii', 'ignore').decode('ascii')
        print(f"      Title: {clean_title}...")
        verdict = verify_with_gemini(brand, variant, scraped)
        status = "[APPROVED]" if verdict.get("is_exact_match") else "[REJECTED]"
        clean_reason = verdict.get('reason', '').encode('ascii', 'ignore').decode('ascii')
        print(f"      AI: {status} ({verdict.get('confidence')}%) -> {clean_reason}")
        if verdict.get("is_exact_match"):
            return url
    return None

def test_row_72():
    print("Testing Row 72: The Derma Co 1% Hyaluronic Sunscreen Aqua Gel - 50g")
    brand = "The Derma Co"
    variant = "1% Hyaluronic Sunscreen Aqua Gel 50g"
    results = {}
    for mp in MARKETPLACE_CONFIG:
        url = resolve_and_verify_single(brand, variant, mp)
        results[mp["name"]] = url
        print(f"=== RESULT {mp['name']}: {url} ===\n")
    return results

if __name__ == "__main__":
    test_row_72()
