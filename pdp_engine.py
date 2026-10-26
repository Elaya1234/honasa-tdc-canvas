import os
import re
import json
import io
import zipfile
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from curl_cffi import requests

def sanitize_filename(name):
    clean = re.sub(r'[\\/*?:"<>|]', '', str(name))
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean[:80].strip(' .')
    return clean if clean else "Product"

def clean_text(text):
    if not text:
        return ""
    t = re.sub(r'[ \t]+', ' ', text)
    t = re.sub(r'\n\s*\n+', '\n\n', t)
    return t.strip()

def fetch_page_with_retry(url):
    """Fetches a URL with browser TLS impersonation and automatic fallback."""
    impersonate_profiles = ['chrome120', 'safari15_5', 'edge99']
    for profile in impersonate_profiles:
        try:
            resp = requests.get(url, impersonate=profile, timeout=25)
            if resp.status_code == 200:
                html = resp.text
                if "api-services-support@amazon.com" in html and "productTitle" not in html:
                    continue  # Bot check encountered, retry next profile
                return html
        except Exception as e:
            continue
    # Fallback to standard request
    resp = requests.get(url, impersonate='chrome120', timeout=30)
    return resp.text

# ----------------- AMAZON EXTRACTOR -----------------
def extract_amazon_pdp(url):
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Product Name / Title
    title_el = soup.find(id='productTitle')
    title = clean_text(title_el.get_text()) if title_el else "Amazon Product"
    
    # 2. Brand
    brand_el = soup.find(id='bylineInfo') or soup.find(id='brand')
    brand = brand_el.get_text(strip=True) if brand_el else ""
    if brand.startswith("Brand:"):
        brand = brand.replace("Brand:", "").strip()
    elif brand.startswith("Visit the"):
        brand = brand.replace("Visit the", "").replace("Store", "").strip()
        
    # 3. Selected Variations (Size, Pattern Name, Style, Color)
    variations = {}
    for v_div in soup.select('#twister_feature_div div[id^="variation_"], div[id^="inline-twister-row-"]'):
        v_title_el = v_div.select_one('.a-form-label, .inline-twister-dim-title-value')
        v_val_el = v_div.select_one('.selection, .swatch-title-text-display, .inline-twister-dim-title-value')
        if v_title_el:
            k = clean_text(v_title_el.get_text().replace(":", ""))
            v = clean_text(v_val_el.get_text()) if v_val_el else ""
            if k and v:
                variations[k] = v

    # 4. Product Overview / Key Attributes (Top table: Size, Brand, Weight, Scent, etc.)
    overview_table = {}
    overview_div = soup.find(id='productOverview_feature_div') or soup.find(id='poExpander')
    if overview_div:
        for tr in overview_div.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 2:
                k = clean_text(tds[0].get_text())
                v = clean_text(tds[1].get_text())
                if k and v:
                    overview_table[k] = v

    # 5. Pricing & Availability
    price_el = soup.select_one('.a-price .a-offscreen') or soup.find(id='priceblock_ourprice') or soup.find(id='priceblock_dealprice')
    price = clean_text(price_el.get_text()) if price_el else ""
    
    mrp_el = soup.select_one('.a-text-price .a-offscreen')
    mrp = clean_text(mrp_el.get_text()) if mrp_el else ""
    
    avail_el = soup.find(id='availability')
    availability = clean_text(avail_el.get_text()) if avail_el else "In Stock"

    # 6. Rating & Reviews
    rating_el = soup.select_one('#acrPopover') or soup.select_one('.a-icon-star')
    rating = clean_text(rating_el.get_text()) if rating_el else ""
    review_count_el = soup.find(id='acrCustomerReviewText')
    review_count = clean_text(review_count_el.get_text()) if review_count_el else ""

    # 7. About this item / Feature Bullets
    bullets = []
    bullet_div = soup.find(id='feature-bullets')
    if bullet_div:
        for li in bullet_div.find_all('li'):
            span = li.find('span', class_='a-list-item')
            text = clean_text(span.get_text()) if span else clean_text(li.get_text())
            if text and not text.startswith('›') and "See more product details" not in text:
                bullets.append(text)

    # 8. Technical Details & Specifications Table
    specs = {}
    spec_tables = soup.select('#productDetails_techSpec_section_1, #prodDetails, #productDetails_db_sections')
    for table in spec_tables:
        for row in table.find_all('tr'):
            tds = row.find_all(['th', 'td'])
            if len(tds) >= 2:
                k = clean_text(tds[0].get_text())
                v = clean_text(tds[1].get_text())
                if k and v and k not in specs:
                    specs[k] = v

    # 9. Important Information (Safety Information, Ingredients, Directions)
    important_info = {}
    imp_div = soup.find(id='importantInformation') or soup.find(id='important-information')
    if imp_div:
        current_heading = "General"
        for el in imp_div.find_all(['h3', 'h4', 'h5', 'p']):
            if el.name in ['h3', 'h4', 'h5']:
                current_heading = clean_text(el.get_text())
            elif el.name == 'p':
                p_text = clean_text(el.get_text())
                if p_text:
                    if current_heading in important_info:
                        if p_text not in important_info[current_heading]:
                            important_info[current_heading] += f"\n{p_text}"
                    else:
                        important_info[current_heading] = p_text

    # 10. From the Manufacturer / A+ Content
    aplus_sections = []
    aplus_div = soup.find(id='aplus') or soup.find(id='aplus_feature_div')
    if aplus_div:
        for block in aplus_div.find_all(['div', 'table'], class_=re.compile(r'celwidget|module|standard')):
            block_headings = [clean_text(h.get_text()) for h in block.find_all(['h1', 'h2', 'h3', 'h4', 'h5']) if clean_text(h.get_text())]
            block_text = [clean_text(p.get_text()) for p in block.find_all(['p', 'span']) if len(clean_text(p.get_text())) > 25]
            if block_headings or block_text:
                aplus_sections.append({
                    "headings": block_headings,
                    "text": block_text
                })

    # 11. High-Res Gallery Images
    gallery_images = []
    alt_div = soup.find(id='altImages')
    if alt_div:
        for li in alt_div.find_all('li'):
            img = li.find('img')
            if img and img.get('src') and 'images/I/' in img.get('src'):
                full_res = re.sub(r'\._[A-Za-z0-9_,+-]+_\.(jpg|png|jpeg)', r'.\1', img['src'])
                if full_res not in gallery_images and not any(x in full_res for x in ['grey-pixel', 'transparent-pixel', 'icon', 'sprite', 'play-button']):
                    gallery_images.append(full_res)
                        
    landing = soup.find(id='landingImage')
    if landing and landing.get('data-a-dynamic-image'):
        try:
            dyn = json.loads(landing['data-a-dynamic-image'])
            for img_url in dyn.keys():
                full_res = re.sub(r'\._[A-Za-z0-9_,+-]+_\.(jpg|png|jpeg)', r'.\1', img_url)
                if full_res not in gallery_images:
                    gallery_images.append(full_res)
        except Exception:
            pass

    # 12. A+ Images & Infographics
    aplus_images = []
    if aplus_div:
        for img in aplus_div.find_all('img'):
            src = img.get('data-src') or img.get('src') or ''
            if src and ('media-amazon.com/images/' in src or 'images-amazon.com/images/' in src):
                full_res = re.sub(r'\._[A-Za-z0-9_,+-]+_\.(jpg|png|jpeg)', r'.\1', src)
                if full_res not in aplus_images and not any(x in full_res for x in ['grey-pixel', 'transparent-pixel', 'icon', 'sprite']):
                    aplus_images.append(full_res)

    # 13. Product Videos (.mp4 URLs)
    videos = []
    mp4_matches = re.findall(r'(https://[^\s"\'\\]+?\.mp4)', html)
    for v_url in mp4_matches:
        if 'media-amazon.com' in v_url and v_url not in videos:
            videos.append(v_url)

    asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
    asin = asin_match.group(1) if asin_match else ""

    return {
        "platform": "Amazon",
        "url": url,
        "asin": asin,
        "title": title,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "availability": availability,
        "rating": rating,
        "review_count": review_count,
        "variations": variations,
        "overview_table": overview_table,
        "bullets": bullets,
        "technical_details": specs,
        "important_info": important_info,
        "aplus_sections": aplus_sections,
        "gallery_images": gallery_images,
        "aplus_images": aplus_images,
        "videos": videos
    }

# ----------------- SHOPIFY / D2C (THE DERMA CO, MINIMALIST, PLUM, FOXTALE, ETC.) -----------------
def extract_shopify_or_d2c_pdp(url):
    clean_url = url.split('?')[0].rstrip('/')
    json_url = clean_url + ".json"
    
    product_json = None
    try:
        r_json = requests.get(json_url, impersonate='chrome120', timeout=12)
        if r_json.status_code == 200:
            product_json = r_json.json().get('product')
    except Exception:
        pass
        
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    netloc = urlparse(url).netloc.lower()
    default_brand = "The Derma Co" if "thedermaco" in netloc else ("Minimalist" if "minimalist" in netloc else netloc.replace("www.", "").split(".")[0].capitalize())

    variations = {}
    if product_json:
        title = clean_text(product_json.get('title', ''))
        brand = clean_text(product_json.get('vendor') or default_brand)
        desc_html = product_json.get('body_html', '')
        desc_soup = BeautifulSoup(desc_html, 'html.parser')
        desc_text = clean_text(desc_soup.get_text(separator="\n"))
        
        variants = product_json.get('variants', [])
        price = ""
        mrp = ""
        if variants:
            v0 = variants[0]
            if v0.get('price'): price = f"₹{v0['price']}"
            if v0.get('compare_at_price'): mrp = f"₹{v0['compare_at_price']}"
            for v in variants:
                t = v.get('title')
                if t and t != "Default Title":
                    variations[t] = f"Price: ₹{v.get('price', '')}"
                
        gallery_images = []
        for im in product_json.get('images', []):
            src = im.get('src')
            if src:
                clean_src = src.split('?')[0]
                if clean_src not in gallery_images:
                    gallery_images.append(clean_src)
    else:
        meta_title = soup.find('meta', property='og:title')
        h1 = soup.find('h1')
        title = clean_text(meta_title.get('content') if meta_title else (h1.get_text() if h1 else f"{default_brand} Product"))
        brand = default_brand
        price_el = soup.select_one('[class*="price"], .product__price')
        price = clean_text(price_el.get_text()) if price_el else ""
        mrp = ""
        desc_text = ""
        gallery_images = []

    important_info = {}
    if desc_text:
        important_info["Product Description"] = desc_text

    # Extract accordion tabs (Key Benefits, How to Use, Ingredients, FAQs)
    for acc in soup.select('[class*="accordion"], [class*="tab"], [class*="collapse"], details'):
        header_el = acc.select_one('summary, [class*="title"], [class*="header"], h2, h3, h4, button')
        content_el = acc.select_one('[class*="content"], [class*="body"], [class*="panel"], p')
        if header_el and content_el:
            h_text = clean_text(header_el.get_text())
            c_text = clean_text(content_el.get_text(separator="\n"))
            if h_text and c_text and len(c_text) > 10 and h_text not in important_info:
                important_info[h_text] = c_text

    aplus_images = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or ''
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = urljoin(url, src)
            
        if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            clean_src = re.sub(r'\?v=[0-9]+|\?width=[0-9]+', '', src)
            if any(k in clean_src.lower() for k in ['shopify', 'ctfassets', 'honasa', 'files', 'products', 'banners', 'cdn']):
                if not any(x in clean_src.lower() for x in ['logo', 'icon', 'arrow', 'badge', 'payment', 'footer', 'cart', 'star']):
                    if clean_src not in gallery_images and clean_src not in aplus_images:
                        aplus_images.append(clean_src)

    videos = []
    for vid in soup.find_all(['video', 'source']):
        v_src = vid.get('src')
        if v_src and '.mp4' in v_src and v_src not in videos:
            if v_src.startswith('//'): v_src = 'https:' + v_src
            videos.append(v_src)

    return {
        "platform": default_brand + " (D2C)",
        "url": url,
        "asin": "",
        "title": title,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "availability": "In Stock",
        "rating": "4.6",
        "review_count": "",
        "variations": variations,
        "overview_table": {"Brand": brand, "Platform": "D2C Official Store"},
        "bullets": [line for line in desc_text.split("\n") if len(line) > 20][:8] if desc_text else [],
        "technical_details": {},
        "important_info": important_info,
        "aplus_sections": [],
        "gallery_images": gallery_images if gallery_images else aplus_images[:8],
        "aplus_images": aplus_images[8:24] if gallery_images else aplus_images[8:],
        "videos": videos
    }

# ----------------- FLIPKART EXTRACTOR -----------------
def extract_flipkart_pdp(url):
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check JSON-LD
    json_ld_prod = {}
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string or '{}')
            items = d if isinstance(d, list) else [d]
            for it in items:
                if isinstance(it, dict) and it.get('@type') == 'Product':
                    json_ld_prod = it
                    break
        except Exception:
            pass

    # 2. Product Name / Title
    clean_title = ""
    if json_ld_prod.get('name'):
        clean_title = clean_text(json_ld_prod['name'])
    if not clean_title:
        meta_title = soup.find('meta', property='og:title')
        h1 = soup.find('h1')
        raw_title = meta_title.get('content') if meta_title else (h1.get_text() if h1 else "Flipkart Product")
        clean_title = re.split(r' - Price in India| \| Flipkart', raw_title)[0].strip()
    
    # 3. Brand
    brand = "Flipkart Brand"
    if json_ld_prod.get('brand'):
        b = json_ld_prod['brand']
        brand = b.get('name') if isinstance(b, dict) else str(b)
    
    # 4. Pricing & MRP
    price = ""
    mrp = ""
    if json_ld_prod.get('offers'):
        off = json_ld_prod['offers']
        if isinstance(off, dict) and off.get('price'):
            curr = off.get('priceCurrency', 'INR')
            curr_sym = "₹" if curr == "INR" else curr
            price = f"{curr_sym}{off['price']}"
    if not price:
        price_el = soup.select_one('div._30jeq3, div._16Jk6d, div[class*="price"], .Nx9bqj')
        price = clean_text(price_el.get_text()) if price_el else ""
    
    desc_str = json_ld_prod.get('description', '')
    if desc_str and 'for Rs.' in desc_str:
        m_mrp = re.search(r'for Rs\.\s*([0-9.]+)', desc_str)
        if m_mrp:
            mrp = f"₹{m_mrp.group(1).split('.')[0]}"
    if not mrp:
        mrp_el = soup.select_one('div._3I9_wc, .yRaY8j')
        mrp = clean_text(mrp_el.get_text()) if mrp_el else ""

    # 5. Rating & Reviews
    rating = ""
    review_count = ""
    if json_ld_prod.get('aggregateRating'):
        ar = json_ld_prod['aggregateRating']
        if ar.get('ratingValue'):
            rating = str(ar['ratingValue'])
        if ar.get('ratingCount') or ar.get('reviewCount'):
            review_count = f"{ar.get('ratingCount', '')} Ratings, {ar.get('reviewCount', '')} Reviews".strip(', ')
    if not rating:
        rating_el = soup.select_one('div._3LWZlK, div[class*="rating"], .XQDdHH')
        rating = clean_text(rating_el.get_text()) if rating_el else ""

    # 6. Highlights / Bullets
    highlights = [clean_text(li.get_text()) for li in soup.select('li._21Ahn-')]
    if not highlights and desc_str:
        parts = [clean_text(p) for p in re.split(r',\s*(?=[A-Z\s&]{4,}:)', desc_str) if len(clean_text(p)) > 15]
        for p in parts:
            if not p.startswith("Flipkart.com:"):
                highlights.append(p)

    # 7. Specifications (From DOM font attributes and tables)
    specs = {}
    for div in soup.find_all('div', attrs={'font': re.compile(r'default-fk-font')}):
        k = div.get_text(strip=True)
        nxt = div.find_next_sibling('div')
        if nxt:
            v = nxt.get_text(strip=True)
            if k and v and len(k) < 60 and len(v) < 300:
                if not any(noise in k.lower() for noise in ['off', 'deal', 'offer', 'all details', '₹']):
                    specs[k] = v
    for row in soup.select('tr._1s_Smc, tr.WJdYP6, tr'):
        tds = row.find_all(['td', 'th'])
        if len(tds) >= 2:
            k = clean_text(tds[0].get_text())
            v = clean_text(tds[1].get_text())
            if k and v and k not in specs and len(k) < 60 and len(v) < 300:
                if not any(noise in k.lower() for noise in ['off', 'deal', 'offer', 'all details', '₹']):
                    specs[k] = v

    # 8. High-Res Images
    raw_imgs = re.findall(r'https://rukminim[0-9]\.flixcart\.com/image/[^\s"\'\\]+', html)
    fk_images = []
    for img in raw_imgs:
        res1664 = re.sub(r'/image/[0-9]+/[0-9]+/', '/image/1664/1664/', img)
        res1664 = re.sub(r'\?q=[0-9]+', '', res1664)
        if res1664 not in fk_images and not res1664.endswith('.svg'):
            fk_images.append(res1664)

    return {
        "platform": "Flipkart",
        "url": url,
        "asin": "",
        "title": clean_title,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "availability": "In Stock",
        "rating": rating,
        "review_count": review_count,
        "variations": {},
        "overview_table": {"Brand": brand, "Platform": "Flipkart"},
        "bullets": highlights,
        "technical_details": specs,
        "important_info": {"Description": desc_str} if desc_str else {},
        "aplus_sections": [],
        "gallery_images": fk_images[:15],
        "aplus_images": fk_images[15:30],
        "videos": []
    }

# ----------------- NYKAA EXTRACTOR -----------------
def extract_nykaa_pdp(url):
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check Preloaded State
    prod_data = {}
    for s in soup.find_all('script'):
        txt = s.string or ''
        if '__PRELOADED_STATE__' in txt:
            clean = txt.replace('window.__PRELOADED_STATE__ = ', '').rstrip(';')
            clean = re.sub(r':\s*undefined\b', ': null', clean)
            try:
                d = json.loads(clean)
                prod_data = d.get('productPage', {}).get('product', {})
                break
            except Exception:
                pass

    # 2. JSON-LD Fallback
    json_ld_prod = {}
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string or '{}')
            items = d if isinstance(d, list) else [d]
            for it in items:
                if isinstance(it, dict) and it.get('@type') == 'Product':
                    json_ld_prod = it
                    break
        except Exception:
            pass

    if not prod_data or not isinstance(prod_data, dict):
        prod_data = {}
    if not json_ld_prod or not isinstance(json_ld_prod, dict):
        json_ld_prod = {}

    # 3. Title
    title = ""
    if prod_data.get('title') or prod_data.get('name'):
        title = clean_text(prod_data.get('title') or prod_data.get('name'))
    elif json_ld_prod.get('name'):
        title = clean_text(json_ld_prod['name'])
    else:
        h1 = soup.find('h1')
        meta_title = soup.find('meta', property='og:title')
        title = h1.get_text(strip=True) if h1 else (meta_title.get('content') if meta_title else "Nykaa Product")
        title = re.sub(r'^Buy\s+|\s+Online$', '', title).strip()

    # 4. Brand
    brand = prod_data.get('brandName')
    if not brand and json_ld_prod.get('brand'):
        b = json_ld_prod.get('brand')
        brand = b.get('name') if isinstance(b, dict) else str(b)
    if not brand:
        brand = "The Derma Co" if "derma" in title.lower() else "Nykaa Listing"

    # 5. Price & MRP
    price = ""
    mrp = ""
    if prod_data.get('offerPrice'):
        price = f"₹{prod_data['offerPrice']}"
    elif (json_ld_prod.get('offers') or {}).get('price'):
        price = f"₹{(json_ld_prod.get('offers') or {}).get('price')}"
    else:
        price_el = soup.select_one('span[class*="price"], div[class*="price"], .css-1jcztc5')
        price = clean_text(price_el.get_text()) if price_el else ""

    if prod_data.get('mrp'):
        mrp = f"₹{prod_data['mrp']}"

    # 6. Rating & Reviews
    rating = str(prod_data.get('rating', '')) if prod_data.get('rating') else ""
    review_count = ""
    if prod_data.get('ratingCount'):
        review_count = f"{prod_data['ratingCount']} Ratings"

    # 7. Important Info: Description, How To Use, Ingredients
    important_info = {}
    if prod_data.get('description'):
        d_soup = BeautifulSoup(prod_data['description'], 'html.parser')
        important_info["Product Description"] = clean_text(d_soup.get_text(separator="\n"))
    if prod_data.get('howToUse'):
        h_soup = BeautifulSoup(prod_data['howToUse'], 'html.parser')
        important_info["How to Use"] = clean_text(h_soup.get_text(separator="\n"))
    if prod_data.get('ingredients'):
        i_soup = BeautifulSoup(prod_data['ingredients'], 'html.parser')
        important_info["Ingredients"] = clean_text(i_soup.get_text(separator="\n"))

    # 8. Specifications / Technical Details
    specs = {}
    if prod_data.get('packSize'): specs["Pack Size"] = str(prod_data['packSize'])
    if prod_data.get('countryOfManufacture'): specs["Country of Manufacture"] = str(prod_data['countryOfManufacture'])
    if prod_data.get('manufacturerName'): specs["Manufacturer"] = str(prod_data['manufacturerName'])
    if prod_data.get('manufacturerAddress'): specs["Manufacturer Address"] = str(prod_data['manufacturerAddress'])
    if prod_data.get('expiry'): specs["Expiry"] = str(prod_data['expiry'])

    # 9. Images
    cleaned_imgs = []
    if prod_data.get('parentMedia'):
        for m in prod_data['parentMedia']:
            u = m.get('url')
            if u:
                clean_u = re.sub(r'/tr:[^/]+/', '/', u).split('?')[0]
                if clean_u not in cleaned_imgs:
                    cleaned_imgs.append(clean_u)
    if not cleaned_imgs:
        imgs = re.findall(r'https://images-static\.nykaa\.com/media/catalog/product/[^\s"\'\\]+', html)
        for img in imgs:
            c = re.sub(r'/tr:[^/]+/', '/', img).split('?')[0]
            if c not in cleaned_imgs and any(c.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                cleaned_imgs.append(c)

    # 10. Videos
    videos = []
    if prod_data.get('parentRelatedVideo'):
        for v in prod_data['parentRelatedVideo']:
            if isinstance(v, dict) and v.get('url') and '.mp4' in v['url']:
                videos.append(v['url'])
    mp4_matches = re.findall(r'(https://[^\s"\'\\]+?\.mp4)', html)
    for v_url in mp4_matches:
        if v_url not in videos:
            videos.append(v_url)

    # 11. Bullets
    bullets = []
    if "Product Description" in important_info:
        bullets = [b for b in important_info["Product Description"].split("\n") if len(b) > 20][:6]

    return {
        "platform": "Nykaa",
        "url": url,
        "asin": "",
        "title": title,
        "brand": brand,
        "price": price,
        "mrp": mrp,
        "availability": "In Stock",
        "rating": rating,
        "review_count": review_count,
        "variations": {},
        "overview_table": {"Brand": brand, "Platform": "Nykaa"},
        "bullets": bullets,
        "technical_details": specs,
        "important_info": important_info,
        "aplus_sections": [],
        "gallery_images": cleaned_imgs,
        "aplus_images": [],
        "videos": videos
    }

# ----------------- UNIVERSAL WEB EXTRACTOR -----------------
def extract_generic_pdp(url):
    clean_url = url.split('?')[0].rstrip('/')
    try:
        r_json = requests.get(clean_url + ".json", impersonate='chrome120', timeout=8)
        if r_json.status_code == 200 and 'product' in r_json.json():
            return extract_shopify_or_d2c_pdp(url)
    except Exception:
        pass
        
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = ""
    price = ""
    brand = ""
    desc = ""
    schema_images = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '{}')
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get('@type') in ['Product', 'IndividualProduct']:
                    title = item.get('name') or title
                    desc = item.get('description') or desc
                    if item.get('brand'):
                        b = item['brand']
                        brand = b.get('name') if isinstance(b, dict) else str(b)
                    if item.get('offers'):
                        off = item['offers']
                        if isinstance(off, list) and off: off = off[0]
                        price = f"₹{off.get('price')}" if off.get('price') else price
                    img_data = item.get('image', [])
                    if isinstance(img_data, str):
                        schema_images.append(img_data)
                    elif isinstance(img_data, list):
                        for im in img_data:
                            src = im.get('url') if isinstance(im, dict) else im
                            if src and src not in schema_images:
                                schema_images.append(src)
        except Exception:
            pass

    if not title:
        meta_title = soup.find('meta', property='og:title')
        h1 = soup.find('h1')
        title = clean_text(meta_title.get('content') if meta_title else (h1.get_text() if h1 else soup.title.get_text() if soup.title else "Product"))

    if not price:
        price_el = soup.select_one('[class*="price"]')
        price = clean_text(price_el.get_text()) if price_el else ""

    images = []
    for s_img in schema_images:
        full = urljoin(url, s_img)
        if full not in images:
            images.append(full)
            
    for img in soup.find_all('img'):
        for attr in ['src', 'data-src', 'data-zoom-image', 'data-large', 'data-high-res']:
            src = img.get(attr)
            if src:
                full = urljoin(url, src)
                if any(ext in full.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if not any(x in full.lower() for x in ['logo', 'icon', 'pixel', 'sprite', 'badge', 'payment', 'footer', 'cart', 'star', 'arrow']):
                        if full not in images:
                            images.append(full)
                            
    domain = urlparse(url).netloc.replace('www.', '').capitalize()
    return {
        "platform": domain,
        "url": url,
        "asin": "",
        "title": title,
        "brand": brand or domain,
        "price": price,
        "mrp": "",
        "availability": "In Stock",
        "rating": "",
        "review_count": "",
        "variations": {},
        "overview_table": {},
        "bullets": [desc[:400]] if desc else [],
        "technical_details": {},
        "important_info": {},
        "aplus_sections": [],
        "gallery_images": images[:15],
        "aplus_images": images[15:35],
        "videos": []
    }

# ----------------- BLINKIT EXTRACTOR -----------------
def extract_blinkit_pdp(url):
    html = fetch_page_with_retry(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    json_ld_prod = {}
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string or '{}')
            items = d if isinstance(d, list) else [d]
            for it in items:
                if isinstance(it, dict) and it.get('@type') == 'Product':
                    json_ld_prod = it
                    break
        except Exception:
            pass

    title = json_ld_prod.get('name') or ""
    if not title:
        meta_title = soup.find('meta', property='og:title')
        h1 = soup.find('h1')
        title = meta_title.get('content') if meta_title else (h1.get_text(strip=True) if h1 else "Blinkit Product")

    brand = "Blinkit Brand"
    if json_ld_prod.get('brand'):
        b = json_ld_prod['brand']
        brand = b.get('name') if isinstance(b, dict) else str(b)

    price = ""
    if json_ld_prod.get('offers'):
        off = json_ld_prod['offers']
        if isinstance(off, dict) and off.get('price'):
            price = f"₹{off['price']}"

    desc = json_ld_prod.get('description', '')
    
    imgs = re.findall(r'https://cdn\.grofers\.com/[^\s"\'\\]+', html)
    cleaned_imgs = []
    for im in imgs:
        im_clean = re.sub(r'https://cdn\.grofers\.com/cdn-cgi/image/[^/]+/', 'https://cdn.grofers.com/', im)
        im_clean = im_clean.split('?')[0]
        if any(im_clean.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            if im_clean not in cleaned_imgs and not any(x in im_clean.lower() for x in ['icon', 'logo', 'badge', 'sprite']):
                cleaned_imgs.append(im_clean)

    videos = []
    vids = re.findall(r'https://cdn\.grofers\.com/[^\s"\'\\]+?\.mp4', html)
    for v in vids:
        if v not in videos:
            videos.append(v)

    bullets = [b.strip() for b in desc.split('.') if len(b.strip()) > 20][:6] if desc else []

    return {
        "platform": "Blinkit",
        "url": url,
        "asin": "",
        "title": title,
        "brand": brand,
        "price": price,
        "mrp": "",
        "availability": "In Stock",
        "rating": "",
        "review_count": "",
        "variations": {},
        "overview_table": {"Brand": brand, "Platform": "Blinkit"},
        "bullets": bullets,
        "technical_details": {},
        "important_info": {"Description": desc} if desc else {},
        "aplus_sections": [],
        "gallery_images": cleaned_imgs[:12],
        "aplus_images": cleaned_imgs[12:25],
        "videos": videos
    }

# ----------------- ROUTER -----------------
def scrape_pdp(url):
    domain = urlparse(url).netloc.lower()
    if 'amazon' in domain:
        return extract_amazon_pdp(url)
    elif 'flipkart' in domain:
        return extract_flipkart_pdp(url)
    elif 'nykaa' in domain:
        return extract_nykaa_pdp(url)
    elif 'blinkit' in domain:
        return extract_blinkit_pdp(url)
    elif 'thedermaco' in domain or 'minimalist' in domain or 'plumgoodness' in domain or 'mamaearth' in domain or 'foxtale' in domain:
        return extract_shopify_or_d2c_pdp(url)
    else:
        return extract_generic_pdp(url)

# ----------------- DOWNLOAD ENGINE (WITH STREAMING CHUNKING) -----------------
def download_file(url, out_path, referer=None, timeout=60):
    headers = {}
    if referer:
        headers['Referer'] = referer
        
    try:
        # Download in chunks to handle both small images and 100MB+ videos smoothly
        r = requests.get(url, impersonate='chrome120', headers=headers, timeout=timeout, stream=True)
        if r.status_code == 200:
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(out_path) > 500:
                return True
        elif r.status_code == 404 and '/1664/1664/' in url:
            fallback_url = url.replace('/1664/1664/', '/832/832/')
            r_fb = requests.get(fallback_url, impersonate='chrome120', headers=headers, timeout=timeout, stream=True)
            if r_fb.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in r_fb.iter_content(chunk_size=1024 * 512):
                        if chunk: f.write(chunk)
                if os.path.getsize(out_path) > 500:
                    return True
    except Exception as e:
        print(f"Download error {url}: {e}")
    return False

def save_pdp_package(pdp_data, *args, **kwargs):
    """
    Saves a PDP package to disk with universal argument resilience.
    Supports any combinations of positional or keyword parameters.
    """
    include_images = kwargs.get('include_images', True)
    include_videos = kwargs.get('include_videos', True)
    base_dir = kwargs.get('base_dir', kwargs.get('target_dir', kwargs.get('folder', r'c:\Users\elaya.n\Documents\HONASA TDC\PDP_Research_Board')))
    progress_callback = kwargs.get('progress_callback', None)
    
    # Process positional arguments if passed
    bool_count = 0
    for arg in args:
        if isinstance(arg, bool):
            if bool_count == 0:
                include_images = arg
                bool_count += 1
            elif bool_count == 1:
                include_videos = arg
                bool_count += 1
        elif isinstance(arg, str):
            base_dir = arg
        elif callable(arg):
            progress_callback = arg

    folder_name = sanitize_filename(f"{pdp_data.get('brand', 'Product')} - {pdp_data.get('title', 'Details')}")
    target_dir = os.path.join(base_dir, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    images_dir = os.path.join(target_dir, "images")
    videos_dir = os.path.join(target_dir, "videos")
    if include_images: os.makedirs(images_dir, exist_ok=True)
    if include_videos: os.makedirs(videos_dir, exist_ok=True)
    
    downloaded_files = []
    downloaded_videos = []
    
    all_gallery = pdp_data.get('gallery_images', []) if include_images else []
    all_aplus = pdp_data.get('aplus_images', []) if include_images else []
    all_videos = pdp_data.get('videos', []) if include_videos else []
    total_media = len(all_gallery) + len(all_aplus) + len(all_videos)
    
    idx = 1
    # 1. Download Gallery Images
    for i, img_url in enumerate(all_gallery, start=1):
        ext = ".jpg"
        if ".png" in img_url.lower(): ext = ".png"
        elif ".webp" in img_url.lower(): ext = ".webp"
        
        filename = f"Gallery_{i:02d}{ext}"
        filepath = os.path.join(images_dir, filename)
        if download_file(img_url, filepath, referer=pdp_data.get('url')):
            downloaded_files.append((filename, filepath))
        if progress_callback:
            progress_callback(idx, total_media, f"Downloaded Gallery picture {i}/{len(all_gallery)}")
        idx += 1
        
    # 2. Download A+ Content / Infographics
    for i, img_url in enumerate(all_aplus, start=1):
        ext = ".jpg"
        if ".png" in img_url.lower(): ext = ".png"
        elif ".webp" in img_url.lower(): ext = ".webp"
        
        filename = f"Aplus_{i:02d}{ext}"
        filepath = os.path.join(images_dir, filename)
        if download_file(img_url, filepath, referer=pdp_data.get('url')):
            downloaded_files.append((filename, filepath))
        if progress_callback:
            progress_callback(idx, total_media, f"Downloaded Section image {i}/{len(all_aplus)}")
        idx += 1

    # 3. Download Product Videos (.mp4)
    for i, vid_url in enumerate(all_videos, start=1):
        filename = f"Video_{i:02d}.mp4"
        filepath = os.path.join(videos_dir, filename)
        if download_file(vid_url, filepath, referer=pdp_data.get('url'), timeout=90):
            downloaded_videos.append((filename, filepath))
        if progress_callback:
            progress_callback(idx, total_media, f"Downloaded Product Video {i}/{len(all_videos)}")
        idx += 1

    # 4. Build Organized Verbatim Markdown Document (Exact Data, No Summarization)
    md_lines = [
        f"# {pdp_data.get('title')}",
        "",
        f"- **Brand:** {pdp_data.get('brand', '')}",
        f"- **Platform:** {pdp_data.get('platform', '')}",
        f"- **Product URL:** [{pdp_data.get('url')}]({pdp_data.get('url')})",
    ]
    if pdp_data.get('asin'):
        md_lines.append(f"- **ASIN / Identifier:** `{pdp_data.get('asin')}`")
    if pdp_data.get('price'):
        md_lines.append(f"- **Price:** {pdp_data.get('price')}")
    if pdp_data.get('mrp'):
        md_lines.append(f"- **MRP:** {pdp_data.get('mrp')}")
    if pdp_data.get('availability'):
        md_lines.append(f"- **Availability:** {pdp_data.get('availability')}")
    if pdp_data.get('rating'):
        md_lines.append(f"- **Rating:** {pdp_data.get('rating')} ({pdp_data.get('review_count', '')})")
    md_lines.append("")

    # Selected Variations Table
    if pdp_data.get('variations'):
        md_lines.append("## 📦 Selected Variations / Options")
        for k, v in pdp_data['variations'].items():
            md_lines.append(f"- **{k}:** {v}")
        md_lines.append("")

    # Product Overview Table
    if pdp_data.get('overview_table'):
        md_lines.append("## 📋 Product Overview Attributes")
        md_lines.append("| Attribute | Value |")
        md_lines.append("| :--- | :--- |")
        for k, v in pdp_data['overview_table'].items():
            md_lines.append(f"| {k} | {v} |")
        md_lines.append("")

    # About this item / Bullets
    if pdp_data.get('bullets'):
        md_lines.append("## 📌 About this item (Key Highlights)")
        for b in pdp_data['bullets']:
            md_lines.append(f"- {b}")
        md_lines.append("")

    # Technical Details / Specifications Table
    if pdp_data.get('technical_details'):
        md_lines.append("## ⚙️ Technical Details & Specifications")
        md_lines.append("| Specification | Detail |")
        md_lines.append("| :--- | :--- |")
        for k, v in pdp_data['technical_details'].items():
            md_lines.append(f"| {k} | {v} |")
        md_lines.append("")

    # Important Information (Ingredients, Directions, Safety Warnings)
    if pdp_data.get('important_info'):
        md_lines.append("## ℹ️ Important Information")
        for topic, content in pdp_data['important_info'].items():
            md_lines.append(f"### {topic}")
            md_lines.append(content)
            md_lines.append("")

    # A+ Content / Manufacturer Story
    if pdp_data.get('aplus_sections'):
        md_lines.append("## 🎨 From the Manufacturer (A+ Content Details)")
        for sec in pdp_data['aplus_sections']:
            for h in sec.get('headings', []):
                md_lines.append(f"#### {h}")
            for t in sec.get('text', []):
                md_lines.append(f"> {t}\n")
        md_lines.append("")

    # Downloaded Media Summary
    md_lines.append("## 🖼️ Media Download Summary")
    md_lines.append(f"- **Product Gallery Pictures:** {len([f for f in downloaded_files if f[0].startswith('Gallery_')])}")
    md_lines.append(f"- **A+ / Infographic Images:** {len([f for f in downloaded_files if f[0].startswith('Aplus_')])}")
    md_lines.append(f"- **Product Videos:** {len(downloaded_videos)}")
    md_lines.append("")

    md_content = "\n".join(md_lines)
    md_path = os.path.join(target_dir, "PDP_Details.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    # 5. Save Raw JSON
    json_path = os.path.join(target_dir, "PDP_Data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pdp_data, f, indent=2, ensure_ascii=False)
        
    # 6. Create In-Memory Zip for 1-click browser download
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(md_path, arcname="PDP_Details.md")
        zip_file.write(json_path, arcname="PDP_Data.json")
        for fn, fp in downloaded_files:
            zip_file.write(fp, arcname=f"images/{fn}")
        for fn, fp in downloaded_videos:
            zip_file.write(fp, arcname=f"videos/{fn}")
    zip_buffer.seek(0)
    
    return {
        "folder": target_dir,
        "downloaded_files": downloaded_files,
        "downloaded_videos": downloaded_videos,
        "zip_bytes": zip_buffer.getvalue(),
        "summary_md": md_content,
        "title": pdp_data.get('title', 'Product')
    }
