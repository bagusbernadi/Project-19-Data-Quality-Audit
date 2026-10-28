"""06: Audit rumus ditimpa (Q6) dan selisih terhadap hasil rumus (Q7).

Input: results/1-data-preparation/formula_audit.csv (dari 02). Sel Sisa seharusnya rumus =F+G-H-I.
Q6: persen sel rumus yang berisi angka ketikan per sheet/kolom. Q7: selisih absolut nilai ketikan vs hasil hitung ulang.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import common as CM

fa = pd.read_csv(CM.RES1 / "formula_audit.csv")
fa["workbook"] = fa.version.map({"before": "log_lama", "after": "log_template"})
g = fa.groupby(["version", "workbook", "sheet", "column"]).agg(sel_rumus=("cell", "size"), angka_ketikan=("is_formula", lambda s: int((s == 0).sum()))).reset_index()
g["persen_ketikan"] = (g.angka_ketikan / g.sel_rumus).round(6)
from scipy.stats import beta
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)
g["ci_low"], g["ci_high"] = zip(*[wilson(k, n) for k, n in zip(g.angka_ketikan, g.sel_rumus)])
g[["ci_low", "ci_high"]] = g[["ci_low", "ci_high"]].round(6)
g.to_csv(CM.RES2 / "formula_hardcode.csv", index=False)

h = fa[fa.is_formula == 0].copy()
h["selisih"] = (h.value - h.recomputed_value)
h["selisih_abs"] = h.selisih.abs()
h["sama_dengan_rumus"] = (h.selisih_abs == 0).astype(int)
h[["version", "sheet", "cell", "column", "value", "recomputed_value", "selisih", "selisih_abs", "sama_dengan_rumus"]].to_csv(CM.RES2 / "formula_diff_cells.csv", index=False)
rows = []
for v, d in h.groupby("version"):
    a = d.selisih_abs
    rows.append(dict(version=v, sel_ketikan=len(d), sama_dengan_rumus=int((a == 0).sum()), berbeda=int((a > 0).sum()), tak_terhitung=int(a.isna().sum()),
                     rata_selisih_abs=round(a.mean(), 4), median_selisih_abs=float(a.median()), maks_selisih_abs=float(a.max()),
                     total_selisih_bersih=float(d.selisih.sum()), total_selisih_abs=float(a.sum())))
pd.DataFrame(rows).to_csv(CM.RES2 / "formula_diff_summary.csv", index=False)
print(g.to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False))
