import os
import openpyxl
import re

p_raw = r"c:\Users\elaya.n\Documents\HONASA TDC\IM\Sept'26 FW & SS.xlsx"
p_ana = r"c:\Users\elaya.n\Documents\HONASA TDC\IM\Sept'26 FW & SS IM analysis.xlsx"

wb_raw = openpyxl.load_workbook(p_raw, data_only=True)
ws_raw = wb_raw['Sheet1']

wb_ana = openpyxl.load_workbook(p_ana, data_only=True)
ws_ana = wb_ana['Consolidated All SKUs']

print(f"RAW rows: {ws_raw.max_row}, ANA rows: {ws_ana.max_row}")

def get_sc(url):
    m = re.search(r"(?:reel|p|reels)/([A-Za-z0-9_-]+)", str(url or ""))
    return m.group(1) if m else ""

raw_links = []
for r in range(2, 48):
    link = ws_raw.cell(r, 29).value # Col 29 Live Link
    sc = get_sc(link)
    raw_links.append((r, ws_raw.cell(r, 3).value, sc, str(link)[:40]))

ana_links = []
for r in range(2, 48):
    link = ws_ana.cell(r, 29).value # Col 29 Live Link
    sc = get_sc(link)
    ana_links.append((r, ws_ana.cell(r, 3).value, sc, str(link)[:40]))

print("\nComparing Row 2 to 10:")
for i in range(10):
    r_item = raw_links[i]
    a_item = ana_links[i]
    print(f"Row {r_item[0]}: RAW creator='{r_item[1]}', sc='{r_item[2]}' | ANA creator='{a_item[1]}', sc='{a_item[2]}'")

raw_sc_set = set(x[2] for x in raw_links if x[2])
ana_sc_set = set(x[2] for x in ana_links if x[2])

print(f"\nUnique RAW shortcodes count: {len(raw_sc_set)}")
print(f"Unique ANA shortcodes count: {len(ana_sc_set)}")
print(f"Overlap count: {len(raw_sc_set.intersection(ana_sc_set))}")
missing = raw_sc_set - ana_sc_set
if missing:
    print(f"RAW sc not in ANA: {list(missing)[:5]}")

# Check creators
creators_raw = [str(x[1]).strip() for x in raw_links if x[1]]
creators_clean = set(c.lower() for c in creators_raw)
print(f"\nTotal raw creators: {len(creators_raw)}, unique lowercase: {len(creators_clean)}")
print(f"Distinct creators list ({len(creators_clean)}):", sorted(list(creators_clean)))
