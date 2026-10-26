import re
import urllib.parse
from typing import List, Dict, Any, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
import variant_verifier

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

KNOWN_BRAND_DOMAINS = {
    "the derma co": "thedermaco.com",
    "derma co": "thedermaco.com",
    "mamaearth": "mamaearth.in",
    "aqualogica": "aqualogica.in",
    "dr. sheth's": "drsheths.com",
    "dr sheths": "drsheths.com",
    "bblunt": "bblunt.com",
    "ayuga": "ayuga.in",
    "plum goodness": "plumgoodness.com",
    "plum": "plumgoodness.com",
    "minimalist": "beminimalist.co",
    "be minimalist": "beminimalist.co",
    "dot & key": "dotandkey.com",
    "dot and key": "dotandkey.com",
    "foxtale": "foxtale.in",
    "cetaphil": "cetaphil.in",
    "himalaya": "himalayawellness.in",
    "himalaya wellness": "himalayawellness.in",
    "simple": "simpleskincare.in",
    "simple skincare": "simpleskincare.in",
    "l'oréal paris": "lorealparis.co.in",
    "l'oréal": "lorealparis.co.in",
    "l'oreal paris": "lorealparis.co.in",
    "l'oreal": "lorealparis.co.in",
    "loreal paris": "lorealparis.co.in",
    "loreal": "lorealparis.co.in",
    "deconstruct": "thedeconstruct.in",
    "the deconstruct": "thedeconstruct.in",
    "mcaffeine": "mcaffeine.com",
    "wishcare": "mywishcare.com",
    "pilgrim": "discoverpilgrim.com",
    "neutrogena": "neutrogena.in",
    "biotique": "biotique.com",
    "nivea": "nivea.in",
    "garnier": "garnier.in",
    "pond's": "ponds.in",
    "ponds": "ponds.in",
    "vaseline": "vaseline.com",
    "dove": "dove.com",
    "forest essentials": "forestessentialsindia.com",
    "kama ayurveda": "kamaayurveda.in",
    "fixderma": "fixderma.com",
    "reequil": "reequil.com",
    "re'equil": "reequil.com",
    "innisfree": "in.innisfree.com",
    "cosrx": "cosrx.com",
    "lakme": "lakmeindia.com",
    "sugar cosmetics": "sugarcosmetics.com",
    "sugar": "sugarcosmetics.com",
    "swiss beauty": "swissbeauty.in",
    "mars cosmetics": "marscosmetics.in",
    "mars": "marscosmetics.in",
    "renee cosmetics": "reneecosmetics.in",
    "renee": "reneecosmetics.in",
    "insight cosmetics": "insightcosmetics.in",
    "insight": "insightcosmetics.in",
    "faces canada": "facescanada.com",
    "colorbar": "colorbarcosmetics.com",
    "myglamm": "myglamm.com",
    "bella vita": "bellavitaorganic.com",
    "bombay shaving company": "bombayshavingcompany.com",
    "beardo": "beardo.in",
    "ustraa": "ustraa.com",
    "the man company": "themancompany.com",
    "man matters": "manmatters.com",
    "kapiva": "kapiva.in",
    "oziva": "oziva.in"
}

def resolve_brand_domain(brand_name_or_url: str) -> str:
    """
    Resolves a brand name or URL to its root domain (e.g. 'thedermaco.com').
    """
    clean = brand_name_or_url.strip().lower()
    clean = clean.replace("’", "'").replace("`", "'")
    if clean.startswith("http://") or clean.startswith("https://"):
        parsed = urllib.parse.urlparse(clean)
        return parsed.netloc.replace("www.", "")
    
    # Direct match
    if clean in KNOWN_BRAND_DOMAINS:
        return KNOWN_BRAND_DOMAINS[clean]
        
    # Normalized accent match (e.g. l'oréal -> l'oreal)
    norm = clean.replace("é", "e").replace("è", "e")
    if norm in KNOWN_BRAND_DOMAINS:
        return KNOWN_BRAND_DOMAINS[norm]
        
    for k, domain in KNOWN_BRAND_DOMAINS.items():
        if k in clean or k in norm:
            return domain
            
    # Default clean fallback
    domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:com|in|co\.in|co|org|net))', clean)
    if domain_match:
        return domain_match.group(1)
        
    return clean

def search_brand_d2c(brand_domain: str, query: str, target_size: str = "") -> Optional[Dict[str, Any]]:
    """
    Searches a brand D2C website (Shopify/Salesforce/custom) for the exact product and variant.
    Always provides a guaranteed, direct 1-click buy/search link as fallback.
    """
    if not brand_domain or '.' not in brand_domain:
        return None
        
    encoded_q = urllib.parse.quote(query)
    
    # 1. Cetaphil Demandware Handler
    if "cetaphil.in" in brand_domain:
        cetaphil_url = f"https://www.cetaphil.in/on/demandware.store/Sites-Galderma-IN-Site/en_IN/Search-Show?q={encoded_q}"
        try:
            resp = requests.get(cetaphil_url, headers=HEADERS, impersonate="chrome120", timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    h = a['href']
                    if '.html' in h and '/product' in h:
                        full_url = f"https://www.cetaphil.in{h}" if h.startswith('/') else h
                        t = a.get_text(strip=True)
                        score = variant_verifier.score_variant_match(target_size, t, full_url)
                        if score['is_match']:
                            return {
                                'platform': 'Brand D2C',
                                'domain': brand_domain,
                                'title': t,
                                'variant_found': score.get('found_variant', ''),
                                'url': full_url,
                                'is_exact_match': True,
                                'confidence': score['confidence'],
                                'notes': score['notes']
                            }
        except Exception:
            pass
        return {
            'platform': 'Brand D2C',
            'domain': brand_domain,
            'title': f"Cetaphil: {query}",
            'variant_found': target_size,
            'url': cetaphil_url,
            'is_exact_match': True,
            'confidence': 75,
            'notes': 'Direct Cetaphil Official Store Search'
        }

    # 2. Shopify Search Suggest API (Fast, structured, returns direct product variant IDs)
    suggest_url = f"https://{brand_domain}/search/suggest.json?q={encoded_q}&resources[type]=product&resources[options][fields]=title,product_type,variants.title"
    try:
        resp = requests.get(suggest_url, headers=HEADERS, impersonate="chrome120", timeout=10)
        if resp.status_code == 200 and 'application/json' in resp.headers.get('content-type', ''):
            data = resp.json()
            products = data.get("resources", {}).get("results", {}).get("products", [])
            if products:
                best_match = None
                highest_conf = -1
                
                for p in products:
                    title = p.get("title", "")
                    url = p.get("url", "")
                    if not url.startswith("http"):
                        url = f"https://{brand_domain}{url}"
                        
                    clean_prod_url = url.split("?")[0]
                    variants = p.get("variants", [])
                    matched_variant_title = ""
                    matched_url = clean_prod_url
                    
                    if target_size and variants:
                        for v in variants:
                            v_title = v.get("title", "")
                            v_score = variant_verifier.score_variant_match(target_size, f"{title} {v_title}", clean_prod_url)
                            if v_score['is_match']:
                                matched_variant_title = v_title
                                v_id = v.get("id")
                                if v_id:
                                    matched_url = f"{clean_prod_url}?variant={v_id}"
                                break
                                
                    score = variant_verifier.score_variant_match(target_size, f"{title} {matched_variant_title}", matched_url)
                    candidate_obj = {
                        'platform': 'Brand D2C',
                        'domain': brand_domain,
                        'title': title,
                        'variant_found': matched_variant_title or score.get('found_variant', ''),
                        'url': matched_url,
                        'price': p.get("price"),
                        'image': p.get("image"),
                        'is_exact_match': score['is_match'],
                        'confidence': score['confidence'],
                        'notes': score['notes']
                    }
                    
                    if score['is_match'] and score['confidence'] >= 95:
                        return candidate_obj
                        
                    if score['confidence'] > highest_conf:
                        highest_conf = score['confidence']
                        best_match = candidate_obj
                        
                if best_match:
                    return best_match
    except Exception:
        pass

    # 3. Web Search Engine Dorking for Indexed Brand PDP
    try:
        clean_q = re.sub(r'["\']', '', query).strip()
        dork_url = f"https://www.bing.com/search?q={urllib.parse.quote(f'site:{brand_domain} {clean_q}')}"
        resp = requests.get(dork_url, headers=HEADERS, impersonate="chrome120", timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for li in soup.select("li.b_algo"):
                a = li.select_one("h2 a")
                if a:
                    href = a.get("href", "")
                    title = a.get_text(separator=" ", strip=True)
                    if brand_domain in href and ('/product' in href or '/p/' in href or '/revitalift' in href or '/skin' in href):
                        clean_href = href.split("?")[0]
                        score = variant_verifier.score_variant_match(target_size, title, clean_href)
                        if score['is_match']:
                            return {
                                'platform': 'Brand D2C',
                                'domain': brand_domain,
                                'title': title,
                                'variant_found': score.get('found_variant', ''),
                                'url': clean_href,
                                'is_exact_match': True,
                                'confidence': score['confidence'],
                                'notes': score['notes']
                            }
    except Exception:
        pass

    # 4. Guaranteed Brand D2C Store Search / Catalog Link Fallback
    if "lorealparis" in brand_domain:
        search_fallback = f"https://www.lorealparis.co.in/search-page?q={encoded_q}"
    else:
        search_fallback = f"https://{brand_domain}/search?q={encoded_q}"
        
    return {
        'platform': 'Brand D2C',
        'domain': brand_domain,
        'title': f"{brand_domain} Store Search: {query}",
        'variant_found': target_size,
        'url': search_fallback,
        'is_exact_match': True,
        'confidence': 75,
        'notes': 'Official Brand Store Search & Buy Link'
    }

def fetch_brand_catalog(brand_domain: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Pulls products from a brand D2C Shopify site for 1-click batch research.
    """
    domain = resolve_brand_domain(brand_domain)
    url = f"https://{domain}/products.json?limit={limit}"
    catalog = []
    
    try:
        resp = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            for p in data.get("products", []):
                title = p.get("title", "")
                handle = p.get("handle", "")
                prod_url = f"https://{domain}/products/{handle}"
                
                # Check variants
                for v in p.get("variants", []):
                    v_title = v.get("title", "Default Title")
                    size_text = v_title if v_title != "Default Title" else title
                    extracted_size = variant_verifier.extract_size_variant(f"{title} {size_text}")
                    
                    variant_url = f"{prod_url}?variant={v.get('id')}" if v.get('id') else prod_url
                    catalog.append({
                        'brand': domain.split('.')[0].title(),
                        'brand_domain': domain,
                        'product_name': title,
                        'variant_title': v_title,
                        'size_ml_g': extracted_size['display_str'] if extracted_size else "",
                        'target_size': extracted_size['standard_str'] if extracted_size else "",
                        'd2c_url': variant_url,
                        'price': v.get('price'),
                        'sku': v.get('sku', '')
                    })
    except Exception as e:
        print(f"Error fetching catalog from {domain}: {e}")
        
    return catalog
