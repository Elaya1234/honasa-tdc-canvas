import re
import os
import json
import base64
import urllib.parse
import concurrent.futures
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests
import variant_verifier
import brand_crawler

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'DNT': '1',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
}

_GENAI_CLIENT = None
def get_genai_client():
    global _GENAI_CLIENT
    if _GENAI_CLIENT is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            key = line.strip().split("=", 1)[1]
        if key:
            try:
                from google import genai
                _GENAI_CLIENT = genai.Client(api_key=key)
            except Exception:
                _GENAI_CLIENT = None
    return _GENAI_CLIENT

CRAWLER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Google-Extended; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# ----------------- CACHED QUICK-COMMERCE CATALOGS -----------------

_BLINKIT_CATALOG = None
_ZEPTO_CATALOG = None

def get_blinkit_catalog() -> List[Dict[str, str]]:
    global _BLINKIT_CATALOG
    if _BLINKIT_CATALOG is None:
        cat_path = os.path.join(os.path.dirname(__file__), "blinkit_catalog.json")
        if os.path.exists(cat_path):
            try:
                with open(cat_path, encoding="utf-8") as f:
                    _BLINKIT_CATALOG = json.load(f)
            except Exception:
                _BLINKIT_CATALOG = []
        else:
            _BLINKIT_CATALOG = []
    return _BLINKIT_CATALOG

def get_zepto_catalog() -> List[Dict[str, str]]:
    global _ZEPTO_CATALOG
    if _ZEPTO_CATALOG is None:
        cat_path = os.path.join(os.path.dirname(__file__), "zepto_catalog.json")
        if os.path.exists(cat_path):
            try:
                with open(cat_path, encoding="utf-8") as f:
                    _ZEPTO_CATALOG = json.load(f)
            except Exception:
                _ZEPTO_CATALOG = []
        else:
            _ZEPTO_CATALOG = []
    return _ZEPTO_CATALOG

# ----------------- UNIVERSAL SEARCH DORK ENGINE -----------------

def decode_bing_url(href: str) -> str:
    if '/ck/a?' in href and 'u=' in href:
        try:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'u' in qs:
                val = qs['u'][0]
                if val.startswith('a1'):
                    val = val[2:]
                val += '=' * (-len(val) % 4)
                return base64.b64decode(val).decode('utf-8', errors='ignore')
        except Exception:
            pass
    return href

def dork_search(site_domain: str, query: str, max_results: int = 5) -> List[Dict[str, str]]:
    clean_query = re.sub(r'["\']', '', query).strip()
    dork = f"site:{site_domain} {clean_query}"
    results = []
    
    try:
        bing_url = f"https://www.bing.com/search?q={urllib.parse.quote(dork)}"
        resp = requests.get(
            bing_url,
            headers=HEADERS,
            impersonate="chrome120",
            timeout=10
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for li in soup.select("li.b_algo"):
                a = li.select_one("h2 a")
                if a:
                    raw_href = a.get("href", "")
                    title = a.get_text(separator=" ", strip=True)
                    clean_url = decode_bing_url(raw_href)
                    if site_domain in clean_url and clean_url.startswith("http"):
                        results.append({"title": title, "url": clean_url})
                        if len(results) >= max_results:
                            return results
    except Exception:
        pass

    return results

# ----------------- CANONICAL URL CLEANERS -----------------

def clean_amazon_url(url: str) -> str:
    asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
    if asin_match:
        return f"https://www.amazon.in/dp/{asin_match.group(1)}"
    return url.split("?")[0]

def clean_flipkart_url(url: str) -> str:
    match = re.search(r'(https://www\.flipkart\.com/[^?]+(?:/p/[a-zA-Z0-9]+))', url)
    if match:
        return match.group(1)
    return url.split("?")[0]

def clean_nykaa_url(url: str) -> str:
    match = re.search(r'(https://www\.nykaa\.com/[^?]+(?:/p/\d+))', url)
    if match:
        return match.group(1)
    return url.split("?")[0]

def clean_blinkit_url(url: str) -> str:
    match = re.search(r'(https://blinkit\.com/prn/[^?]+/prid/\d+)', url)
    if match:
        return match.group(1)
    return url.split("?")[0]

def clean_zepto_url(url: str) -> str:
    match = re.search(r'(https://(?:www\.)?zepto\.com/pn/[^?]+)', url)
    if match:
        return match.group(1)
    return url.split("?")[0]

def build_search_query(product_name: str, brand: str = "", target_size: str = "") -> str:
    parts = []
    clean_p = product_name.strip()
    if brand and brand.lower() not in clean_p.lower():
        parts.append(brand)
    parts.append(clean_p)
    if target_size and target_size.lower() not in clean_p.lower():
        parts.append(target_size)
    return " ".join(parts).strip()

def compute_word_overlap(text1: str, text2: str) -> int:
    w1 = set(re.findall(r'\w+', text1.lower()))
    w2 = set(re.findall(r'\w+', text2.lower()))
    return len(w1 & w2)

# ----------------- PLATFORM RESOLVERS -----------------

def resolve_amazon(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Amazon India with deep verification and search fallback."""
    query = build_search_query(product_name, brand, target_size)
    target_full = f"{brand} {product_name} {target_size}".strip()
    search_url = f"https://www.amazon.in/s?k={urllib.parse.quote_plus(query)}"
    candidates = []
    
    # 1. Direct Amazon Catalog Search
    try:
        url = f"https://www.amazon.in/s?k={urllib.parse.quote(query)}"
        resp = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for item in soup.select('div[data-asin]'):
                asin = item.get('data-asin')
                if not asin or len(asin) != 10:
                    continue
                
                title = ""
                thumbnail_url = ""
                
                # Check rich title elements first to get full unabbreviated title
                title_elem = item.select_one('h2.a-size-base-plus, h2 a span, span.a-text-normal')
                if title_elem:
                    title = title_elem.get_text(separator=' ', strip=True)
                if not title or len(title) < 10:
                    img = item.select_one('img[alt]')
                    if img:
                        title = img.get('alt', '').strip()
                if not title:
                    h2 = item.select_one('h2')
                    if h2:
                        title = h2.get_text(separator=' ', strip=True)
                        
                brand_elem = item.select_one('h2.a-size-mini')
                brand_txt = brand_elem.get_text(strip=True) if brand_elem else ""
                img_elem = item.select_one('img[alt]')
                img_alt_txt = img_elem.get('alt', '').strip() if img_elem else ''
                if not brand_txt:
                    brand_txt = variant_verifier.detect_brand(img_alt_txt) or ""
                if brand_txt and brand_txt.lower() not in title.lower():
                    title = f"{brand_txt} {title}"
                        
                img_src = item.select_one('img[src]')
                if img_src:
                    thumbnail_url = img_src.get('src', '')

                # Check combo in title, alt text, and explicit pack declarations in card text
                is_combo_title, _ = variant_verifier.is_combo_or_multipack(title)
                is_combo_alt, _ = variant_verifier.is_combo_or_multipack(img_alt_txt)
                
                card_text = item.get_text(separator=' ', strip=True)
                has_pack = bool(re.search(r'\b(?:pack\s+of\s+[2-9]\d*|\(pack\s+of\s+[2-9]\d*\)|set\s+of\s+[2-9]\d*)\b', card_text, re.I))
                
                if is_combo_title or is_combo_alt or has_pack:
                    continue

                if title and len(title) > 5:
                    clean_url = f"https://www.amazon.in/dp/{asin}"
                    v_res = variant_verifier.verify_product_identity(target_full, title, clean_url, "")
                    if v_res['is_match']:
                        score = v_res['confidence']
                        if 'sponsored' in title.lower():
                            score -= 20
                        overlap = compute_word_overlap(target_full, title)
                        score += overlap * 3
                        candidates.append((score, asin, title, thumbnail_url, v_res))
    except Exception:
        pass

    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates:
        top = candidates[0]
        return {
            'platform': 'Amazon.in',
            'title': top[2],
            'url': f"https://www.amazon.in/dp/{top[1]}",
            'thumbnail_url': top[3],
            'variant_found': top[4].get('found_variant', ''),
            'is_exact_match': True,
            'confidence': top[4]['confidence'],
            'verified_badges': top[4]['verified_badges'],
            'notes': top[4]['notes']
        }
        
    # 2. Dork Search Fallback
    try:
        d_candidates = dork_search("amazon.in", query, max_results=5)
        for c in d_candidates:
            raw_url = c['url']
            if '/dp/' in raw_url or '/gp/product/' in raw_url:
                clean_url = clean_amazon_url(raw_url)
                v_res = variant_verifier.verify_product_identity(target_full, c['title'], clean_url, "")
                if v_res['is_match']:
                    return {
                        'platform': 'Amazon.in',
                        'title': c['title'],
                        'url': clean_url,
                        'thumbnail_url': "",
                        'variant_found': v_res.get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': v_res['confidence'],
                        'verified_badges': v_res['verified_badges'],
                        'notes': v_res['notes']
                    }
    except Exception:
        pass
        
    # Guaranteed 1-Click Search Fallback
    return {
        'platform': 'Amazon.in',
        'title': f"Amazon Search: {query}",
        'url': search_url,
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 50,
        'verified_badges': ['Search & Choose'],
        'notes': 'Exact PDP not auto-verified; 1-Click Search link provided to choose product directly'
    }

def resolve_flipkart(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Flipkart with deep verification and search fallback."""
    query = build_search_query(product_name, brand, target_size)
    target_full = f"{brand} {product_name} {target_size}".strip()
    search_url = f"https://www.flipkart.com/search?q={urllib.parse.quote_plus(query)}"
    candidates = []
    
    try:
        url = f"https://www.flipkart.com/search?q={urllib.parse.quote(query)}"
        resp = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.select('a[href*="/p/"]'):
                href = a.get('href', '')
                title = a.get_text(separator=' ', strip=True)
                thumbnail_url = ""
                img = a.select_one('img')
                if img:
                    thumbnail_url = img.get('src', '')
                    
                if len(title) > 8:
                    clean_url = clean_flipkart_url("https://www.flipkart.com" + href if href.startswith('/') else href)
                    v_res = variant_verifier.verify_product_identity(target_full, title, clean_url, "")
                    if v_res['is_match']:
                        score = v_res['confidence'] + compute_word_overlap(target_full, title) * 2
                        candidates.append((score, title, clean_url, thumbnail_url, v_res))
    except Exception:
        pass

    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates:
        top = candidates[0]
        return {
            'platform': 'Flipkart',
            'title': top[1],
            'url': top[2],
            'thumbnail_url': top[3],
            'variant_found': top[4].get('found_variant', ''),
            'is_exact_match': True,
            'confidence': top[4]['confidence'],
            'verified_badges': top[4]['verified_badges'],
            'notes': top[4]['notes']
        }

    try:
        d_candidates = dork_search("flipkart.com", query, max_results=5)
        for c in d_candidates:
            if '/p/' in c['url']:
                clean_url = clean_flipkart_url(c['url'])
                v_res = variant_verifier.verify_product_identity(target_full, c['title'], clean_url, "")
                if v_res['is_match']:
                    return {
                        'platform': 'Flipkart',
                        'title': c['title'],
                        'url': clean_url,
                        'thumbnail_url': "",
                        'variant_found': v_res.get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': v_res['confidence'],
                        'verified_badges': v_res['verified_badges'],
                        'notes': v_res['notes']
                    }
    except Exception:
        pass

    # Guaranteed 1-Click Search Fallback
    return {
        'platform': 'Flipkart',
        'title': f"Flipkart Search: {query}",
        'url': search_url,
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 50,
        'verified_badges': ['Search & Choose'],
        'notes': 'Exact PDP not auto-verified; 1-Click Search link provided to choose product directly'
    }

def resolve_nykaa(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Nykaa with deep AI verification and multi-pass search."""
    clean_v = re.sub(r'[—–\-+]+', ' ', f"{brand} {product_name} {target_size}").strip()
    target_full = f"{brand} {product_name} {target_size}".strip()
    search_url = f"https://www.nykaa.com/search/result/?q={urllib.parse.quote_plus(clean_v)}"
    candidates = []
    
    # Pass 1: Direct Nykaa search
    try:
        url = f"https://www.nykaa.com/search/result/?q={urllib.parse.quote(clean_v)}"
        resp = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
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

    # Pass 2: DDG fallback if direct search returned empty
    if not candidates:
        try:
            d_candidates = dork_search("nykaa.com", clean_v, max_results=5)
            for c in d_candidates:
                if '/p/' in c['url']:
                    clean = clean_nykaa_url(c['url'])
                    if clean not in [x['url'] for x in candidates]:
                        candidates.append({'url': clean, 'title': c['title']})
        except Exception:
            pass

    # AI Verification Pass
    ai_client = get_genai_client()
    if ai_client and candidates:
        try:
            from pydantic import BaseModel, Field
            from google.genai import types
            
            class BatchSelection(BaseModel):
                selected_url: str = Field(description="Exact URL matching single unit product, or empty string.")
                is_match: bool = Field(description="True if exact match found.")
                reason: str = Field(description="Explanation.")

            cand_text = "\n".join([f"Candidate {i+1}: {c['url']} | Title: {c['title']}" for i, c in enumerate(candidates[:5])])
            prompt = f"""
TARGET: Brand: {brand} | Variant & Size: {product_name} {target_size} (SINGLE UNIT ONLY)
Store: Nykaa India
CANDIDATES:
{cand_text}
RULES: Exact brand and core variant. Single unit only (no combos, no packs of 2/3). Reject conflicting sizes.
Select the single matching URL, or is_match=False if none match.
"""
            resp = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=BatchSelection,
                    temperature=0.1
                )
            )
            v_data = json.loads(resp.text)
            if v_data.get("is_match") and v_data.get("selected_url"):
                sel_url = v_data["selected_url"]
                sel_title = next((c['title'] for c in candidates if c['url'] == sel_url), f"{brand} {product_name}")
                return {
                    'platform': 'Nykaa',
                    'title': sel_title,
                    'url': sel_url,
                    'thumbnail_url': "",
                    'variant_found': target_size,
                    'is_exact_match': True,
                    'confidence': 100,
                    'verified_badges': ['AI Verified', 'Exact Variant', 'Single Unit'],
                    'notes': v_data.get('reason', 'AI verified exact single-product match')
                }
        except Exception:
            pass

    # Fallback to heuristic verification
    for c in candidates:
        v_res = variant_verifier.verify_product_identity(target_full, c['title'], c['url'], "")
        if v_res['is_match']:
            return {
                'platform': 'Nykaa',
                'title': c['title'],
                'url': c['url'],
                'thumbnail_url': "",
                'variant_found': v_res.get('found_variant', ''),
                'is_exact_match': True,
                'confidence': v_res['confidence'],
                'verified_badges': v_res['verified_badges'],
                'notes': v_res['notes']
            }

    # Guaranteed 1-Click Search Fallback
    return {
        'platform': 'Nykaa',
        'title': f"Nykaa Search: {clean_v}",
        'url': search_url,
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 50,
        'verified_badges': ['Search & Choose'],
        'notes': 'Exact PDP not auto-verified; 1-Click Search link provided to choose product directly'
    }

def resolve_blinkit(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Blinkit with canonical /prn/ URLs only (zero combos or search URLs)."""
    clean_v = re.sub(r'[—–\-+]+', ' ', f"{product_name} {target_size}").strip()
    target_full = f"{brand} {product_name} {target_size}".strip()
    
    # Infer Category
    clean_lower = target_full.lower()
    category = "SERUM"
    if any(w in clean_lower for w in ["shampoo", "hair fall", "dandruff", "bhringaraja"]):
        category = "SHAMPOO"
    elif any(w in clean_lower for w in ["wash", "cleanser", "facewash", "foam"]):
        category = "FACEWASH"
    elif any(w in clean_lower for w in ["sunscreen", "spf", "aqua-gel", "matte gel"]):
        category = "SUNSCREEN"
        
    def get_brand_key(b):
        c = re.sub(r"[^a-z0-9]+", "", str(b).lower())
        if "derma" in c: return "derma-co"
        if "ordinary" in c: return "ordinary"
        if "minimalist" in c: return "minimalist"
        if "dot" in c: return "dot-key"
        if "lor" in c and "al" in c: return "loreal"
        if "foxtale" in c: return "foxtale"
        if "cetaphil" in c: return "cetaphil"
        if "himalaya" in c: return "himalaya"
        if "simple" in c: return "simple"
        return c

    catalog = get_blinkit_catalog()
    b_key = get_brand_key(brand)
    numbers = re.findall(r"\b\d+\b", clean_v.lower())
    v_words = [w for w in re.findall(r"\w+", clean_v.lower()) if len(w) > 2 and w not in ["face", "serum", "wash", "gel", "cream", "daily", "skin", "pure", "with", "and", "for", "cleanser", "shampoo"]]
    
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
        
        if b_key == "derma-co":
            if not ("derma-co" in slug or "derma co" in title): continue
        elif b_key == "dot-key":
            if not ("dot-key" in slug or "dot key" in title or "dot and key" in title): continue
        elif b_key == "loreal":
            if not ("loreal" in slug or "l-oreal" in slug or "l oreal" in slug): continue
        elif b_key == "ordinary":
            if not (re.search(r"\bordinary\b", slug) or re.search(r"\bordinary\b", title)): continue
            if "extraordinary" in slug or "extraordinary" in title: continue
        else:
            if not (b_key in slug or b_key in title): continue
                
        is_combo = any(k in slug for k in ["combo", "pack-of-2", "pack-of-3", "pack-of-4", "pack-of-5", "bogo"])
        score = 0
        if any(ck in slug for ck in cat_keywords): score += 15
        elif any(ck in title for ck in cat_keywords): score += 10
        if any(fk in slug for fk in forbidden_keywords): score -= 25
        if is_combo: score -= 15
        for w in v_words:
            if w in slug: score += 5
            elif w in title: score += 3
        for n in numbers:
            if f"-{n}-" in slug or f" {n}%" in title or f" {n} " in title: score += 8
        if score > 0:
            candidates.append((score, is_combo, item))
            
    candidates.sort(key=lambda x: x[0], reverse=True)
    cands = [c[2] for c in candidates[:6]]

    # Pass 2: Dork search complement
    try:
        d_candidates = dork_search("blinkit.com", target_full, max_results=4)
        for c in d_candidates:
            if '/prn/' in c['url'] or '/prid/' in c['url']:
                clean_url = clean_blinkit_url(c['url'])
                if clean_url not in [x['url'] for x in cands]:
                    cands.append({'url': clean_url, 'title': c['title']})
    except Exception:
        pass

    # AI Verification Pass
    ai_client = get_genai_client()
    if ai_client and cands:
        try:
            from pydantic import BaseModel, Field
            from google.genai import types
            class BatchSelection(BaseModel):
                selected_url: str = Field(description="The exact URL from candidates matching target single unit, or empty string if none match.")
                is_match: bool = Field(description="True if an exact single-unit match was found.")
                reason: str = Field(description="Brief reason.")

            cand_lines = [f"Candidate {idx}:\n  URL: {c['url']}\n  Title: {c.get('title','')}" for idx, c in enumerate(cands, 1)]
            cand_text = "\n".join(cand_lines)
            prompt = f"""
You are an expert strict e-commerce data verification agent for Blinkit India (quick commerce).
TARGET: Category: {category} | Brand: {brand} | Variant & Size: {product_name} {target_size} (SINGLE UNIT ONLY)
CANDIDATES:
{cand_text}
RULES:
1. Exact brand and core variant match.
2. Single unit only (strictly reject combos, pack of 2/3, bundles).
3. Category integrity (e.g. shampoo must be shampoo, face wash must be face wash).
4. If exact single unit match is found, return its URL. Otherwise return is_match=False.
"""
            resp = ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=BatchSelection,
                    temperature=0.1
                )
            )
            v_data = json.loads(resp.text)
            if v_data.get("is_match") and v_data.get("selected_url"):
                sel_url = v_data["selected_url"]
                sel_title = next((c['title'] for c in cands if c['url'] == sel_url), f"{brand} {product_name}")
                return {
                    'platform': 'Blinkit',
                    'title': sel_title,
                    'url': sel_url,
                    'thumbnail_url': "",
                    'variant_found': target_size,
                    'is_exact_match': True,
                    'confidence': 100,
                    'verified_badges': ['AI Verified', 'Canonical PDP', 'Single Unit'],
                    'notes': v_data.get('reason', 'AI verified exact single-product match')
                }
        except Exception:
            pass

    # Heuristic verification fallback
    for c in cands:
        v_res = variant_verifier.verify_product_identity(target_full, c['title'], c['url'], "")
        if v_res['is_match']:
            return {
                'platform': 'Blinkit',
                'title': c['title'],
                'url': c['url'],
                'thumbnail_url': "",
                'variant_found': v_res.get('found_variant', ''),
                'is_exact_match': True,
                'confidence': v_res['confidence'],
                'verified_badges': v_res['verified_badges'],
                'notes': v_res['notes']
            }

    # Strict: No search fallback, explicitly mark unavailable
    return {
        'platform': 'Blinkit',
        'title': '',
        'url': '',
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 0,
        'verified_badges': ['Not Found on Blinkit'],
        'notes': 'Product not listed as a single unit on Blinkit'
    }


def resolve_zepto(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Zepto with direct /pn/.../pvid/... canonical URLs or search fallback."""
    query = build_search_query(product_name, brand, target_size)
    target_query = f"{brand} {product_name} {target_size}".strip()
    search_url = f"https://www.zepto.com/search?q={urllib.parse.quote_plus(query)}"
    catalog = get_zepto_catalog()
    clean_brand = brand.lower().replace("'", "").replace("’", "").replace(".", "").replace(" ", "")
    
    candidates = []
    for item in catalog:
        slug = item.get('slug', '').lower()
        title = item.get('title', '')
        if clean_brand and clean_brand not in slug.replace('-', ''):
            continue
        overlap = compute_word_overlap(target_query, f"{title} {slug}")
        if overlap >= 2:
            candidates.append((overlap, item))
            
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    for _, item in candidates[:6]:
        url = item['url']
        try:
            r = requests.get(url, headers=CRAWLER_HEADERS, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                cand_title = item.get('title', '')
                thumbnail_url = ""
                for s in soup.find_all('script', type='application/ld+json'):
                    try:
                        d = json.loads(s.string)
                        if d.get('@type') == 'Product':
                            cand_title = d.get('name', cand_title)
                            imgs = d.get('image', [])
                            if isinstance(imgs, list) and imgs:
                                thumbnail_url = imgs[0]
                            elif isinstance(imgs, str):
                                thumbnail_url = imgs
                            break
                    except Exception:
                        pass
                        
                pdp_sizes = []
                for tag in soup.find_all(string=re.compile(r'\d+\s*(?:ml|g|gm)\b', re.IGNORECASE)):
                    t_str = tag.strip()
                    if len(t_str) < 40:
                        pdp_sizes.append(t_str)
                pdp_size_text = " ".join(pdp_sizes)
                
                v_res = variant_verifier.verify_product_identity(
                    target_query,
                    f"{cand_title} {pdp_size_text}",
                    url,
                    ""
                )
                
                if v_res['is_match']:
                    return {
                        'platform': 'Zepto',
                        'title': cand_title,
                        'url': url,
                        'thumbnail_url': thumbnail_url,
                        'variant_found': v_res.get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': v_res['confidence'],
                        'verified_badges': v_res['verified_badges'],
                        'notes': v_res['notes']
                    }
        except Exception:
            continue
            
    try:
        d_candidates = dork_search("zepto.com", target_query, max_results=4)
        for c in d_candidates:
            if '/pn/' in c['url']:
                clean_url = clean_zepto_url(c['url'])
                v_res = variant_verifier.verify_product_identity(target_query, c['title'], clean_url, "")
                if v_res['is_match']:
                    return {
                        'platform': 'Zepto',
                        'title': c['title'],
                        'url': clean_url,
                        'thumbnail_url': "",
                        'variant_found': v_res.get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': v_res['confidence'],
                        'verified_badges': v_res['verified_badges'],
                        'notes': v_res['notes']
                    }
    except Exception:
        pass

    # Guaranteed 1-Click Search Fallback
    return {
        'platform': 'Zepto',
        'title': f"Zepto Search: {query}",
        'url': search_url,
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 50,
        'verified_badges': ['Search & Choose'],
        'notes': 'Exact PDP not auto-verified; 1-Click Search link provided to choose product directly'
    }

def resolve_purplle(product_name: str, brand: str = "", target_size: str = "") -> Dict[str, Any]:
    """Resolves exact product variant on Purplle with direct /product/... links or search fallback."""
    query = build_search_query(product_name, brand, target_size)
    target_query = f"{brand} {product_name} {target_size}".strip()
    search_url = f"https://www.purplle.com/search?q={urllib.parse.quote_plus(query)}"
    clean_brand = brand.lower().replace("'", "").replace("’", "").replace(".", "").replace(" ", "-")
    
    brand_slugs = [
        clean_brand,
        clean_brand.replace("-cosmetics", "").replace("-wellness", ""),
        "the-derma-co" if "derma" in clean_brand else "",
        "dot-and-key" if "dot" in clean_brand else "",
        "dr-sheths" if "sheth" in clean_brand else "",
        "loreal-paris" if "loreal" in clean_brand or "l'oreal" in clean_brand else "",
    ]
    brand_slugs = [b for b in brand_slugs if b]
    
    for b_slug in brand_slugs:
        try:
            url = f"https://www.purplle.com/brand/{b_slug}"
            r = requests.get(url, impersonate="chrome120", timeout=8)
            if r.status_code == 200:
                p_links = re.findall(r'href=["\'](/product/[^"\']+)["\']', r.text)
                candidates = []
                for rel_url in set(p_links):
                    full_url = f"https://www.purplle.com{rel_url}"
                    cand_title = rel_url.replace('/product/', '').replace('-', ' ').title()
                    v_res = variant_verifier.verify_product_identity(target_query, cand_title, full_url, "")
                    if v_res['is_match']:
                        candidates.append((v_res['confidence'] + compute_word_overlap(target_query, cand_title) * 2, cand_title, full_url, v_res))
                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    top = candidates[0]
                    return {
                        'platform': 'Purplle',
                        'title': top[1],
                        'url': top[2],
                        'thumbnail_url': "",
                        'variant_found': top[3].get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': top[3]['confidence'],
                        'verified_badges': top[3]['verified_badges'],
                        'notes': top[3]['notes']
                    }
        except Exception:
            pass

    try:
        d_candidates = dork_search("purplle.com", target_query, max_results=4)
        for c in d_candidates:
            if '/product/' in c['url']:
                clean_url = c['url'].split('?')[0]
                v_res = variant_verifier.verify_product_identity(target_query, c['title'], clean_url, "")
                if v_res['is_match']:
                    return {
                        'platform': 'Purplle',
                        'title': c['title'],
                        'url': clean_url,
                        'thumbnail_url': "",
                        'variant_found': v_res.get('found_variant', ''),
                        'is_exact_match': True,
                        'confidence': v_res['confidence'],
                        'verified_badges': v_res['verified_badges'],
                        'notes': v_res['notes']
                    }
    except Exception:
        pass
        
    # Guaranteed 1-Click Search Fallback
    return {
        'platform': 'Purplle',
        'title': f"Purplle Search: {query}",
        'url': search_url,
        'thumbnail_url': '',
        'variant_found': '',
        'is_exact_match': False,
        'confidence': 50,
        'verified_badges': ['Search & Choose'],
        'notes': 'Exact PDP not auto-verified; 1-Click Search link provided to choose product directly'
    }

# ----------------- PARALLEL AGENT ORCHESTRATOR -----------------

def scout_single_product(
    raw_product_string: str,
    brand_hint: str = "",
    brand_domain_hint: str = "",
    target_size_hint: str = "",
    include_purplle: bool = True
) -> Dict[str, Any]:
    parsed = variant_verifier.parse_product_input(raw_product_string)
    
    brand = brand_hint or parsed.get('brand', '')
    product_name = parsed.get('clean_name', raw_product_string)
    target_size = target_size_hint or parsed.get('target_size', '')
    
    brand_domain = brand_domain_hint
    if not brand_domain and brand:
        brand_domain = brand_crawler.resolve_brand_domain(brand)
        
    results = {
        'input': raw_product_string,
        'brand': brand,
        'product_name': product_name,
        'target_size': target_size,
        'category': parsed.get('category', ''),
        'actives': parsed.get('actives', []),
        'platforms': {}
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        future_map = {
            executor.submit(resolve_amazon, product_name, brand, target_size): 'Amazon',
            executor.submit(resolve_flipkart, product_name, brand, target_size): 'Flipkart',
            executor.submit(resolve_nykaa, product_name, brand, target_size): 'Nykaa',
            executor.submit(resolve_blinkit, product_name, brand, target_size): 'Blinkit',
            executor.submit(resolve_zepto, product_name, brand, target_size): 'Zepto',
        }
        
        if brand_domain:
            future_map[executor.submit(brand_crawler.search_brand_d2c, brand_domain, f"{product_name} {target_size}", target_size)] = 'Brand D2C'
            
        if include_purplle:
            future_map[executor.submit(resolve_purplle, product_name, brand, target_size)] = 'Purplle'
            
        for future in concurrent.futures.as_completed(future_map):
            platform_key = future_map[future]
            try:
                res = future.result()
                if platform_key == 'Brand D2C' and res.get('is_exact_match'):
                    v_res = variant_verifier.verify_product_identity(
                        f"{brand} {product_name} {target_size}",
                        res.get('title', ''),
                        res.get('url', ''),
                        brand
                    )
                    res['verified_badges'] = v_res['verified_badges']
                    res['confidence'] = v_res['confidence']
                    if not v_res['is_match']:
                        res['is_exact_match'] = False
                        res['notes'] = v_res['notes']
                results['platforms'][platform_key] = res
            except Exception as e:
                # Guaranteed fallback URL even on error
                clean_q = urllib.parse.quote_plus(f"{brand} {product_name} {target_size}")
                err_url = f"https://www.google.com/search?q={clean_q}+{platform_key}"
                results['platforms'][platform_key] = {
                    'platform': platform_key,
                    'error': str(e),
                    'url': err_url,
                    'title': f"Search {platform_key}: {brand} {product_name}",
                    'is_exact_match': False,
                    'confidence': 30,
                    'verified_badges': ['Search & Choose'],
                    'notes': f"Resolution error: {str(e)}; 1-Click Search provided"
                }
                
    return results

def scout_bulk_products(
    product_list: List[Dict[str, Any]],
    progress_callback=None
) -> List[Dict[str, Any]]:
    total = len(product_list)
    results = []
    
    for idx, item in enumerate(product_list):
        p_name = item.get('name', '')
        b_name = item.get('brand', '')
        size = item.get('size', '')
        domain = item.get('brand_domain', '')
        
        res = scout_single_product(
            raw_product_string=p_name,
            brand_hint=b_name,
            brand_domain_hint=domain,
            target_size_hint=size
        )
        results.append(res)
        
        if progress_callback:
            progress_callback(idx + 1, total, res)
            
    return results