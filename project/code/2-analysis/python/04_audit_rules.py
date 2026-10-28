"""04: Audit aturan R01 sampai R07 pada kedua versi log (Q1, Q2, Q3, Q9, Q13 bagian data).

Hasil: anomaly_log.csv, entry_flags.csv, audit_rule_counts.csv, audit_category.csv, audit_column.csv, chain_check.csv, audit_r01_sensitivity.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy import stats
import audit_lib as AL
import common as CM

R2 = CM.RES2
df = pd.read_csv(CM.RES1 / "log_entries.csv", keep_default_na=False, na_values=[""], dtype=object)
# kolom *_raw harus string kosong (bukan NaN); kolom numerik kembali ke angka
for c in df.columns:
    if c.endswith("_raw") or c.endswith("_tipe") or c.endswith("_strip") or c in ("entry_id", "version", "shift", "model", "ng_origin", "batch", "date", "month"):
        df[c] = df[c].fillna("")
for c in ("excel_row", "sisa_awal", "qty_received", "qty_ok", "qty_scrap", "sisa", "sisa_is_formula"):
    df[c] = pd.to_numeric(df[c])
df["month"] = df.month.replace("", np.nan)
df["date"] = df.date.replace("", np.nan)
an = AL.audit(df)
an.insert(0, "anomaly_id", [f"A{i:05d}" for i in range(1, len(an) + 1)])
an.to_csv(R2 / "anomaly_log.csv", index=False)
n_ent = df.groupby("version").size()


def poisson_ci(k, n):
    lo = stats.chi2.ppf(CM.ALPHA / 2, 2 * k) / 2 if k > 0 else 0.0
    hi = stats.chi2.ppf(1 - CM.ALPHA / 2, 2 * (k + 1)) / 2
    return lo / n * 1000, hi / n * 1000


rows = []
for ver in ("before", "after"):
    for rid in CM.RULES:
        k = int(((an.version == ver) & (an.rule_id == rid)).sum())
        lo, hi = poisson_ci(k, n_ent[ver])
        rows.append(dict(version=ver, rule_id=rid, category=CM.RULE_CAT[rid], pelanggaran=k, entri=int(n_ent[ver]), per_1000=k / n_ent[ver] * 1000, ci_low=lo, ci_high=hi))
pd.DataFrame(rows).to_csv(R2 / "audit_rule_counts.csv", index=False, float_format="%.10g")
rows = []
for ver in ("before", "after"):
    sub = an[an.version == ver]
    for cat in CM.CATEGORIES + ["semua"]:
        s = sub if cat == "semua" else sub[sub.category == cat]
        k = len(s)
        lo, hi = poisson_ci(k, n_ent[ver])
        rows.append(dict(version=ver, category=cat, pelanggaran=k, entri_terdampak=int(s.entry_id.nunique()), entri=int(n_ent[ver]), per_1000=k / n_ent[ver] * 1000, ci_low=lo, ci_high=hi))
pd.DataFrame(rows).to_csv(R2 / "audit_category.csv", index=False, float_format="%.10g")
col = an.groupby(["version", "column"]).size().rename("pelanggaran").reset_index()
col["per_1000"] = col.pelanggaran / col.version.map(n_ent) * 1000
col["share"] = col.pelanggaran / col.groupby("version").pelanggaran.transform("sum")
col.sort_values(["version", "pelanggaran", "column"], ascending=[True, False, True]).to_csv(R2 / "audit_column.csv", index=False, float_format="%.10g")
flags = df[["entry_id", "version", "excel_row", "date", "month", "shift", "model", "ng_origin"]].copy()
for rid in CM.RULES:
    flags[rid] = flags.entry_id.isin(an[an.rule_id == rid].entry_id).astype(int)
flags["n_pelanggaran"] = flags.entry_id.map(an.groupby("entry_id").size()).fillna(0).astype(int)
flags.to_csv(R2 / "entry_flags.csv", index=False)
ch = AL.chain_check(AL.enrich(df)).drop(columns=["entry_key"])
ch.to_csv(R2 / "chain_check.csv", index=False, float_format="%.10g")
# sensitivitas R01: definisi rancangan literal (OK + scrap > qty diterima)
lit = AL.audit(df, r01_literal=True)
lit = lit[lit.rule_id == "R01"]
pd.DataFrame([dict(version=v, definisi=d, pelanggaran=int(((a.version == v) & (a.rule_id == "R01")).sum())) for v in ("before", "after")
              for d, a in (("stok tersedia (sisa awal + diterima), dasar", an), ("qty diterima saja (rancangan literal)", lit))]).to_csv(R2 / "audit_r01_sensitivity.csv", index=False)
print(pd.read_csv(R2 / "audit_rule_counts.csv").round(2).to_string(index=False))
print(pd.read_csv(R2 / "audit_category.csv").round(2).to_string(index=False))
print(ch.groupby("version").cocok.agg(["sum", "count"]))
print(pd.read_csv(R2 / "audit_r01_sensitivity.csv"))
