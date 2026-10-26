import json, re, urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

with open(r"c:\Users\elaya.n\Documents\HONASA TDC\skuscout\blinkit_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

def search_catalog(brand, variant):
    b = brand.lower().replace(" ", "").replace("&", "").replace("'", "")
    clean_v = re.sub(r"[—–\-+]+", " ", variant)
    v_words = [w.lower() for w in clean_v.split() if len(w) > 2]
    matches = []
    for item in catalog:
        title = item.get("title", "").lower()
        slug = item.get("slug", "").lower()
        comb = f"{title} {slug}".replace("-", " ")
        if b in comb.replace(" ", ""):
            score = sum(1 for w in v_words if w in comb)
            if score >= 2:
                matches.append((score, item))
    matches.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matches[:5]]

def search_ddg_blinkit(query):
    encoded = urllib.parse.quote_plus(f"Blinkit {query}")
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    results = []
    try:
        r = requests.get(url, impersonate="chrome120", headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.find_all("div", class_="result"):
            a_link = div.find("a", class_="result__snippet")
            if not a_link:
                continue
            href = a_link.get("href", "")
            if "uddg=" in href:
                actual = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if "blinkit.com" in actual and ("/prn/" in actual or "/prid/" in actual):
                    title = div.find("h2").get_text(strip=True) if div.find("h2") else ""
                    results.append({"url": actual.split("?")[0], "title": title})
    except Exception as e:
        pass
    return results[:5]

test_items = [
    ("The Derma Co", "1% Salicylic Acid Gel Face Wash — 100ml"),
    ("Minimalist", "Salicylic + LHA 2% Cleanser — 100ml"),
    ("Dot & Key", "Cica + Salicylic Acid Face Wash — 100ml"),
    ("The Derma Co", "10% Niacinamide + 2% Zinc PCA — 30ml"),
    ("Minimalist", "Niacinamide 10% Face Serum — 30ml")
]

for b, v in test_items:
    cat_res = search_catalog(b, v)
    ddg_res = search_ddg_blinkit(f"{b} {v}")
    print(f"\n=== {b} | {v} ===")
    print("  Catalog matches:", [c["url"] for c in cat_res[:2]])
    print("  DDG matches:    ", [d["url"] for d in ddg_res[:2]])
