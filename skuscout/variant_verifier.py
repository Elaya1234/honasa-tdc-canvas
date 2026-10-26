import re
from typing import Dict, Any, Optional, Tuple, List, Set

UNIT_MAP = {
    'g': 'g',
    'gm': 'g',
    'gms': 'g',
    'gram': 'g',
    'grams': 'g',
    'ml': 'ml',
    'm.l.': 'ml',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'millilitre': 'ml',
    'millilitres': 'ml',
    'kg': 'kg',
    'kgs': 'kg',
    'kilogram': 'kg',
    'kilograms': 'kg',
    'l': 'l',
    'ltr': 'l',
    'liter': 'l',
    'liters': 'l',
    'litre': 'l',
    'litres': 'l',
    'oz': 'oz',
    'fl oz': 'oz',
    'ounce': 'oz',
    'ounces': 'oz',
    'fluid ounce': 'oz',
    'fluid ounces': 'oz',
    'pc': 'pcs',
    'pcs': 'pcs',
    'piece': 'pcs',
    'pieces': 'pcs',
    'patch': 'patches',
    'patches': 'patches',
    'sheet': 'sheets',
    'sheets': 'sheets',
    'capsule': 'capsules',
    'capsules': 'capsules',
    'tablet': 'tablets',
    'tablets': 'tablets',
    'sachet': 'sachets',
    'sachets': 'sachets',
}

SIZE_REGEX = re.compile(
    r'(?<!\w)(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|ml|m\.l\.|milliliters?|millilitres?|kg|kgs|kilograms?|ltr?|liters?|litres?|fl\s*oz|oz|ounces?|fluid\s*ounces?|pcs?|pieces?|patches?|sheets?|capsules?|tablets?|sachets?)(?!\w)',
    re.IGNORECASE
)

MULTIPACK_REGEX = re.compile(
    r'(?:pack\s+of\s+([2-9]\d*)|(?:set|combo)\s+of\s+([2-9]\d*)|([2-9]\d*)\s*(?:x|\*)\s*(\d+(?:\.\d+)?\s*(?:g|gm|ml|kg|l))|(\d+(?:\.\d+)?\s*(?:g|gm|ml|kg|l))\s*(?:x|\*)\s*([2-9]\d*)|buy\s+(\d+)\s+get\s+(\d+)|\bcombo\b|\bcombos\b|\bduo\b|\btrio\b|\bbundle\b|\bkit\b|\bitems in the set\b|\d+\s*(?:ml|g|gm)\s*\+\s*\d+\s*(?:ml|g|gm)|\b[2-9]\d*\s*\+\s*[2-9]\d*\b)',
    re.IGNORECASE
)

PERCENTAGE_REGEX = re.compile(r'(?<!\w)(\d+(?:\.\d+)?)\s*%(?!\w)', re.IGNORECASE)

KNOWN_BRANDS = sorted([
    "The Derma Co", "Derma Co", "Mamaearth", "Aqualogica", "Dr. Sheth's", "Dr Sheths",
    "BBlunt", "Ayuga", "Plum Goodness", "Plum", "Minimalist", "Be Minimalist",
    "Dot & Key", "Dot and Key", "Cetaphil", "Neutrogena",
    "L'Oréal Paris", "L'Oreal Paris", "L'Oréal", "L'Oreal", "Loreal Paris", "Loreal",
    "Garnier", "Biotique", "Himalaya Wellness", "Himalaya", "Forest Essentials",
    "Kama Ayurveda", "Simple Skincare", "Simple", "Innisfree", "COSRX", "Foxtale", "Deconstruct",
    "The Deconstruct", "Re'equil", "Reequil", "mCaffeine", "Fixderma", "WishCare", "Pilgrim",
    "Urban Company", "Dove", "Nivea", "Vaseline", "Pond's", "Ponds",
    "Lakme", "Sugar Cosmetics", "Sugar", "Swiss Beauty", "Mars Cosmetics", "Mars",
    "Renee Cosmetics", "Renee", "Insight Cosmetics", "Insight", "Faces Canada",
    "Colorbar", "MyGlamm", "Bella Vita Organic", "Bella Vita", "Bombay Shaving Company",
    "Beardo", "Ustraa", "The Man Company", "Man Matters", "Kapiva", "Oziva"
], key=len, reverse=True)

CATEGORIES = {
    "face_serum": {
        "positive": ["face serum", "facial serum", "skin serum", "peeling solution"],
        "negative": ["hair serum", "scalp", "hair growth", "lip serum", "eye serum"]
    },
    "hair_serum": {
        "positive": ["hair serum", "scalp serum", "hair growth", "hair actives"],
        "negative": ["face serum", "facial serum"]
    },
    "eye_serum": {
        "positive": ["eye serum", "under eye", "eye cream", "eye gel", "dark circles"],
        "negative": ["face serum", "hair serum"]
    },
    "cleanser": {
        "positive": ["cleanser", "face wash", "facial wash", "cleansing lotion", "cleansing gel", "cleansing foam"],
        "negative": ["body wash", "body lotion", "shampoo", "hair wash"]
    },
    "sunscreen": {
        "positive": ["sunscreen", "sun screen", "sun gel", "sun fluid", "aqua gel", "spf"],
        "negative": ["body wash", "shampoo"]
    },
    "moisturizer": {
        "positive": ["moisturizer", "moisturiser", "face cream", "hydrating cream", "barrier repair", "water gel", "day cream", "night cream"],
        "negative": ["body wash", "shampoo", "body lotion"]
    },
    "body_lotion": {
        "positive": ["body lotion", "body milk", "body cream", "body yogurt"],
        "negative": ["face cream", "face serum", "facial"]
    },
    "toner": {
        "positive": ["toner", "toning water", "skin mist", "essence"],
        "negative": ["face wash", "cleanser"]
    }
}

ACTIVES = [
    ("hyaluronic", [r"\bhyaluronic\b", r"\bhyaluron\b", r"\bha\b"]),
    ("niacinamide", [r"\bniacinamide\b", r"\bvitamin b3\b", r"\bb3\b"]),
    ("salicylic", [r"\bsalicylic\b", r"\bbha\b"]),
    ("vitamin_c", [r"\bvitamin c\b", r"\bvit c\b", r"\bascorbic\b", r"\bc-cinamide\b"]),
    ("ceramide", [r"\bceramide\b", r"\bceramides\b"]),
    ("kojic", [r"\bkojic\b", r"\bkojic acid\b"]),
    ("retinol", [r"\bretinol\b", r"\bretinoid\b", r"\bretinal\b"]),
    ("alpha_arbutin", [r"\balpha arbutin\b", r"\barbutin\b"]),
    ("cica", [r"\bcica\b", r"\bcentella\b", r"\bmadecassoside\b"]),
    ("gentle_skin", [r"\bgentle skin\b", r"\bgentle cleansing\b"]),
    ("oily_skin", [r"\boily skin\b"]),
    ("daily_exfoliating", [r"\bdaily exfoliating\b"]),
    ("revitalift", [r"\brevitalift\b"]),
    ("refreshing", [r"\brefreshing\b", r"\bkind to skin\b"]),
    ("barrier_repair", [r"\bbarrier repair\b", r"\bbarrier\b"]),
    ("peptides", [r"\bpeptides?\b", r"\bmatrixyl\b", r"\bcopper peptide\b"]),
    ("hair_growth", [r"\bhair growth\b", r"\bhair actives\b", r"\bredensyl\b", r"\bprocapil\b", r"\banagain\b"]),
]

def normalize_unit(unit_str: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z]', '', unit_str.lower().strip())
    return UNIT_MAP.get(cleaned, cleaned)

def is_combo_or_multipack(title: str, url: str = "") -> Tuple[bool, str]:
    """Strictly detects combo products, multipacks, bundles, kits, and dual-item listings.
    Guarantees that only single product listings pass verification."""
    t = title.lower()
    u = url.lower()
    
    # 1. Explicit combo/multipack keywords in Title
    kw = re.search(
        r'\b(?:combo|combos|bundle|bundles|duo|duos|trio|trios|kit|kits|pack\s+of\s+[2-9]\d*|set\s+of\s+[2-9]\d*|gift\s+set|travel\s+pack|travel\s+kit|routine\s+kit|routine\s+set|items?\s+in\s+the\s+set|[2-9]\d*\s*pack|[2-9]\d*\s*pcs?|[2-9]\d*\s*pieces?|[2-9]\d*\s*items?|buy\s+\d+\s+get\s+\d+|bogo|\d+\s*\+\s*\d+\s*free|with\s+free|free\s+(?:mini|pouch|bag|sample|tote|gift))\b',
        t
    )
    if kw:
        return True, f"Explicit combo/multipack keyword: '{kw.group(0)}'"

    # 1b. Explicit combo keywords in URL path (ignoring query parameters)
    u_path = u.split('?')[0]
    kw_url = re.search(r'\b(?:combo|combos|bundle|bundles|duo|trio|kit|kits|pack-of-[2-9]\d*)\b', u_path)
    if kw_url:
        return True, f"Combo keyword in URL: '{kw_url.group(0)}'"
        
    # 2. Multipliers (e.g. 2x50ml, 30mlx2, 2*50ml) in Title
    if re.search(r'\b[2-9]\s*(?:x|\*)\s*\d+|\b\d+\s*(?:ml|g|gm)\s*(?:x|\*)\s*[2-9]\b', t):
        return True, "Multipack multiplier detected (e.g. 2x or x2)"
        
    # 3. Multiple distinct sizes in Title (e.g. 125ml and 100g, 100ml / 118ml)
    sizes = re.findall(r'(\d+(?:\.\d+)?)\s*(ml|g|gm|kg|l|ltr)\b', t)
    if len(sizes) >= 2:
        distinct = set(f"{float(q) if '.' in q else int(q)}{unit}" for q, unit in sizes)
        if len(distinct) >= 2:
            return True, f"Multiple distinct sizes in listing: {distinct}"
        elif any(c in t for c in ['+', '&', ' and ', ' with ']):
            return True, f"Multiple size declarations connected in listing: {sizes}"
            
    # 4. Product addition with + in Title (excluding skincare active ingredients)
    allowed_actives = r'^(?:zinc|b5|niacinamide|hyaluronic|salicylic|vitamin|vit|ceramide|peptides?|retinol|arbutin|kojic|ferulic|cica|centella|matmarine|rice|green|aloe|tea|glycolic|lactic|squalane|oats?|caffeine|mandelic|pa\+{1,4})'
    for m in re.finditer(r'\+\s*([a-zA-Z0-9]+)', t):
        nxt = m.group(1).lower()
        if not re.match(allowed_actives, nxt):
            return True, f"Product addition with +: '+ {nxt}'"
            
    # 5. Dual Category Conflict in Title (e.g. Cleanser AND Lotion/Cream/Moisturizer/Sunscreen)
    has_cleanser = bool(re.search(r'\b(?:cleanser|face\s*wash|facial\s*wash)\b', t))
    has_moisturizer = bool(re.search(r'\b(?:moisturi[zs]er|moisturi[zs]ing\s*cream|face\s*cream|lotion|dam)\b', t)) and not re.search(r'\bcleansing\s*lotion\b', t)
    has_sunscreen = bool(re.search(r'\b(?:sunscreen|sun\s*screen|sun\s*gel|spf\s*\d+)\b', t))
    has_serum = bool(re.search(r'\b(?:face\s*serum|facial\s*serum)\b', t))
    
    cats = [c for c, present in [('cleanser', has_cleanser), ('moisturizer', has_moisturizer), ('sunscreen', has_sunscreen), ('serum', has_serum)] if present]
    if len(cats) >= 2 and any(c in t for c in ['&', '+', ' and ', ' with ']):
        return True, f"Conflicting categories combined in listing: {cats}"
        
    return False, "Single product"

def extract_size_variant(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    clean_text = str(text)
    is_multipack, combo_reason = is_combo_or_multipack(clean_text)
    pack_count = 1
    multipack_match = MULTIPACK_REGEX.search(clean_text)
    if multipack_match:
        groups = multipack_match.groups()
        for g in groups:
            if g and g.isdigit():
                pack_count = int(g)
                break

    matches = SIZE_REGEX.findall(clean_text)
    if not matches:
        return None
    
    qty_str, unit_raw = matches[-1]
    qty = float(qty_str) if '.' in qty_str else int(qty_str)
    normalized_unit = normalize_unit(unit_raw)
    
    standard_size_str = f"{qty}{normalized_unit}"
    if is_multipack and pack_count > 1:
        standard_size_str = f"Pack of {pack_count} ({standard_size_str})"
    elif is_multipack:
        standard_size_str = f"Combo ({standard_size_str})"
        
    return {
        'quantity': qty,
        'unit': normalized_unit,
        'standard_str': f"{qty}{normalized_unit}",
        'display_str': standard_size_str,
        'is_multipack': is_multipack,
        'combo_reason': combo_reason if is_multipack else "",
        'pack_count': pack_count,
        'raw_match': f"{qty_str} {unit_raw}"
    }

def extract_category(text: str) -> Optional[str]:
    t = text.lower()
    for cat, rules in CATEGORIES.items():
        if any(p in t for p in rules["positive"]):
            if not any(n in t for n in rules["negative"]):
                return cat
    return None

def extract_actives(text: str) -> Set[str]:
    t = text.lower()
    found = set()
    for name, patterns in ACTIVES:
        if any(re.search(pat, t) for pat in patterns):
            found.add(name)
    return found

def extract_percentages(text: str) -> Set[str]:
    return set(PERCENTAGE_REGEX.findall(text))

def detect_brand(text: str) -> Optional[str]:
    clean = text.lower()
    for brand in KNOWN_BRANDS:
        pattern = rf'\b{re.escape(brand.lower())}\b'
        if re.search(pattern, clean):
            return brand
    return None

def parse_product_input(raw_input: str) -> Dict[str, Any]:
    text = raw_input.strip()
    brand = detect_brand(text) or ""
    variant = extract_size_variant(text)
    category = extract_category(text) or ""
    actives = extract_actives(text)
    percentages = extract_percentages(text)
    
    clean_name = text
    if brand:
        clean_name = re.sub(rf'\b{re.escape(brand)}\b', '', clean_name, flags=re.IGNORECASE).strip()
    if variant:
        clean_name = clean_name.replace(variant['raw_match'], '').strip()
        
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    return {
        'original_input': raw_input,
        'brand': brand,
        'clean_name': clean_name or raw_input,
        'category': category,
        'actives': list(actives),
        'percentages': list(percentages),
        'variant': variant,
        'target_size': variant['standard_str'] if variant else ""
    }

def verify_product_identity(
    target_query: str,
    candidate_title: str,
    candidate_url: str = "",
    candidate_brand: str = ""
) -> Dict[str, Any]:
    """
    Performs comprehensive verification between requested target SKU and found marketplace candidate.
    Strictly eliminates combos, multipacks, sister products, formula divergence, and brand dupes.
    """
    target_parsed = parse_product_input(target_query)
    target_brand = (target_parsed.get('brand') or "").lower()
    target_cat = target_parsed.get('category') or ""
    target_actives = set(target_parsed.get('actives', []))
    target_pcts = set(target_parsed.get('percentages', []))
    target_variant = target_parsed.get('variant')
    
    cand_brand = (candidate_brand or detect_brand(candidate_title) or "").lower()
    cand_cat = extract_category(candidate_title)
    cand_actives = extract_actives(candidate_title)
    cand_pcts = extract_percentages(candidate_title)
    
    mismatch_reasons = []
    confidence = 100
    
    # 0. Strict Single Product vs Combo / Multipack Check (Zero combos allowed)
    is_combo, combo_reason = is_combo_or_multipack(candidate_title, candidate_url)
    if is_combo and not (target_variant and target_variant.get('is_multipack', False)):
        mismatch_reasons.append(f"Rejected combo/multipack ({combo_reason}); only single product permitted")
        confidence = 0
        return {
            'is_match': False,
            'confidence': 0,
            'mismatch_reasons': mismatch_reasons,
            'verified_badges': ['Rejected Combo'],
            'found_variant': 'Combo / Multipack',
            'notes': mismatch_reasons[0]
        }
    
    # 1. Brand Verification (Strict)
    clean_tb = target_brand.replace("'", "").replace("’", "").replace(".", "").replace(" ", "")
    clean_cb = cand_brand.replace("'", "").replace("’", "").replace(".", "").replace(" ", "")
    cand_text_clean = candidate_title.lower().replace("'", "").replace("’", "").replace(".", "").replace(" ", "")
    if target_brand:
        if clean_tb not in clean_cb and clean_tb not in cand_text_clean:
            mismatch_reasons.append(f"Brand mismatch: expected {target_brand}, found {cand_brand or 'unknown'}")
            confidence -= 60
            
    # 2. Product Form / Category Verification
    if target_cat and cand_cat and target_cat != cand_cat:
        mismatch_reasons.append(f"Product Category mismatch: target is {target_cat}, candidate is {cand_cat}")
        confidence -= 50
        
    # 3. Active Concentrations Verification (%)
    if target_pcts and cand_pcts:
        if not (target_pcts & cand_pcts):
            mismatch_reasons.append(f"Concentration mismatch: target requires {target_pcts}%, candidate has {cand_pcts}%")
            confidence -= 45
            
    # 4. Active Ingredient Verification (Strict)
    if target_actives:
        missing_actives = target_actives - cand_actives
        if missing_actives:
            mismatch_reasons.append(f"Formula mismatch: target requires {list(missing_actives)} but candidate lacks it")
            confidence -= 50
            
    # 5. Size / Volume Verification
    variant_res = score_variant_match(target_parsed['target_size'], candidate_title, candidate_url)
    if not variant_res['is_match']:
        mismatch_reasons.append(variant_res['notes'])
        confidence = min(confidence, variant_res['confidence'])
    else:
        confidence = min(confidence, variant_res['confidence'])
        
    is_match = (len(mismatch_reasons) == 0) and (confidence >= 70)
    
    badges = []
    if target_brand and (clean_tb in cand_text_clean or clean_tb in clean_cb):
        badges.append(f"Brand: {target_parsed['brand']}")
    if target_cat:
        badges.append(f"Form: {target_cat.replace('_', ' ').title()}")
    if target_actives:
        badges.append(f"Actives: {', '.join(sorted(target_actives)).title()}")
    if target_variant:
        badges.append(f"Size: {target_variant['display_str']}")
        
    return {
        'is_match': is_match,
        'confidence': max(confidence, 10),
        'mismatch_reasons': mismatch_reasons,
        'verified_badges': badges,
        'found_variant': variant_res.get('found_variant', ''),
        'notes': "; ".join(mismatch_reasons) if mismatch_reasons else variant_res.get('notes', 'Verified Exact Product')
    }

def score_variant_match(target_variant_str: str, candidate_title: str, candidate_url: str = "") -> Dict[str, Any]:
    if not target_variant_str:
        return {
            'is_match': True,
            'confidence': 85,
            'match_type': 'No Variant Specified',
            'found_variant': "",
            'notes': 'Matched title without specific size constraint'
        }
        
    target_info = extract_size_variant(target_variant_str)
    if not target_info:
        return {
            'is_match': True,
            'confidence': 80,
            'match_type': 'Variant Check Passed',
            'found_variant': "",
            'notes': 'Could not parse target variant constraint'
        }
        
    target_qty = target_info['quantity']
    target_unit = target_info['unit']
    
    # Multipack / Combo check (Zero combo tolerance for single unit requests)
    is_combo, combo_reason = is_combo_or_multipack(candidate_title, candidate_url)
    if is_combo and not target_info.get('is_multipack', False):
        return {
            'is_match': False,
            'confidence': 0,
            'match_type': 'Multipack / Combo Mismatch',
            'found_variant': 'Combo / Multipack',
            'notes': f"Rejected combo/multipack ({combo_reason}). Only single product permitted."
        }
        
    candidate_sizes = SIZE_REGEX.findall(candidate_title)
    parsed_candidate_sizes = []
    for q_str, u_str in candidate_sizes:
        q = float(q_str) if '.' in q_str else int(q_str)
        u = normalize_unit(u_str)
        parsed_candidate_sizes.append((q, u))
        
    if parsed_candidate_sizes:
        distinct_sizes = set(parsed_candidate_sizes)
        if len(distinct_sizes) > 1 and not target_info.get('is_multipack', False):
            return {
                'is_match': False,
                'confidence': 0,
                'match_type': 'Multipack / Combo Mismatch',
                'found_variant': f"Multiple sizes: {distinct_sizes}",
                'notes': f"Candidate lists multiple distinct sizes {distinct_sizes}, indicating a combo bundle. Only single product permitted."
            }
        
    if not parsed_candidate_sizes:
        if target_qty in (125, 118) and target_unit == 'ml':
            if '118' in candidate_title or '125' in candidate_title or '118' in candidate_url or '125' in candidate_url:
                return {
                    'is_match': True,
                    'confidence': 100,
                    'match_type': 'Exact Match (Tolerance)',
                    'found_variant': f"{target_qty}{target_unit}",
                    'notes': f"Size {target_qty}{target_unit} verified with international packaging tolerance."
                }
        slug_pattern = rf'(?:-|_|\/){target_qty}(?:-|_)?{target_unit}(?:-|_|\.|\/)'
        if re.search(slug_pattern, candidate_url, re.IGNORECASE):
            return {
                'is_match': True,
                'confidence': 95,
                'match_type': 'Exact Match (URL Slug)',
                'found_variant': f"{target_qty}{target_unit}",
                'notes': f"Exact size {target_qty}{target_unit} verified via URL structure."
            }
        return {
            'is_match': True,
            'confidence': 70,
            'match_type': 'Probable Match',
            'found_variant': 'Unspecified on page',
            'notes': 'Size not explicitly written in page title; needs visual confirmation.'
        }
        
    def to_base(q_val, u_val):
        if u_val in ('ml', 'milliliter', 'millilitre'): return q_val, 'ml'
        if u_val in ('l', 'ltr', 'liter', 'litre'): return q_val * 1000.0, 'ml'
        if u_val in ('oz', 'fl oz'): return q_val * 29.5735, 'ml'
        if u_val in ('g', 'gm', 'gram'): return q_val, 'g'
        if u_val in ('kg', 'kilogram'): return q_val * 1000.0, 'g'
        return q_val, u_val

    t_base_qty, t_base_unit = to_base(target_qty, target_unit)

    for q, u in parsed_candidate_sizes:
        c_base_qty, c_base_unit = to_base(q, u)
        if c_base_unit == t_base_unit:
            if abs(c_base_qty - t_base_qty) <= max(2.0, t_base_qty * 0.06) or (target_qty in (125, 118) and q in (125, 118)):
                return {
                    'is_match': True,
                    'confidence': 100,
                    'match_type': 'Exact Match (100%)',
                    'found_variant': f"{q}{u}",
                    'notes': f"Exact {target_qty}{target_unit} variant matched and verified in product title."
                }
                
    diff_str = ", ".join(f"{q}{u}" for q, u in parsed_candidate_sizes)
    return {
        'is_match': False,
        'confidence': 20,
        'match_type': 'Variant Mismatch',
        'found_variant': diff_str,
        'notes': f"Size mismatch: Page is for {diff_str} (Target: {target_qty}{target_unit})."
    }