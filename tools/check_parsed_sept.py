import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tdc_im_agent.input_intelligence import ExcelInputIntelligence

sept_path = os.path.join(r"c:\Users\elaya.n\Documents\HONASA TDC\IM", "Sept'26 FW & SS.xlsx")
parser = ExcelInputIntelligence(sept_path)
rows, meta = parser.parse_sheet()

print("Detected Header Row:", meta["header_row"])
print("Total rows parsed:", meta["total_rows_parsed"])
print("\nColumn Mappings:")
for k, v in meta["column_mapping"].items():
    print(f"  {k} -> '{v}'")

print("\nFirst 3 rows parsed:")
for r in rows[:3]:
    print(f"  Row {r.source_row}: creator='{r.creator}', shortcode='{r.shortcode}', link='{r.live_link}'")
