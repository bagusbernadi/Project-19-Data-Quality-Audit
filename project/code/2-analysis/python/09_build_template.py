"""09: Bangun template anti-bypass Rework_Log_Template.xlsx (kosong) dan inventaris kolom input vs rumus (Q12)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM
import template_lib as T

T.build(CM.OUTPUTS / "Rework_Log_Template.xlsx")
rows = []
for h in CM.HEADER:
    rows.append(dict(versi="log lama", kolom=h, peran="rumus (seharusnya)" if h == "Sisa" else "input operator", wajib=0 if h == "Sisa" else 1))
for h, t in T.LAYOUT:
    rows.append(dict(versi="template", kolom=h, peran="input operator" if t == "input" else "rumus terkunci", wajib=int(t == "input")))
inv = pd.DataFrame(rows)
inv.to_csv(CM.RES2 / "column_inventory.csv", index=False)
s = inv.groupby(["versi", "peran"]).size().reset_index(name="jumlah_kolom")
s.to_csv(CM.RES2 / "column_inventory_summary.csv", index=False)
print(s.to_string(index=False))
