"""12: Uji pemulihan ground truth (Q13): recall, precision, alarm palsu per aturan, dan lima fakta data rancangan.

Ground truth (data/sim/ground_truth_errors.csv) hanya dibaca di skrip ini, bukan di analisis. Entri digabung lewat nomor baris Excel.
R07 ditanam pada entri pertama tiap bulan termasuk Juli, padahal Juli tidak punya bulan sebelumnya sehingga tidak bisa dideteksi (dilaporkan terpisah).
Definisi alarm palsu = entri bertanda aturan tetapi tidak ada di ground truth aturan itu, dibagi entri bertanda aturan (1 - precision).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import audit_lib as AL
import common as CM

R2 = CM.RES2
gt = pd.read_csv(CM.SIM / "ground_truth_errors.csv")
gt["version"] = gt.workbook.map({"log_lama": "before", "log_template": "after"})
gt["entry_id"] = [("L" if v == "before" else "T") + f"{r:05d}" for v, r in zip(gt.version, gt.excel_row)]
fl = pd.read_csv(R2 / "entry_flags.csv")
raw = pd.read_csv(CM.RES1 / "log_entries.csv", dtype={c: str for c in pd.read_csv(CM.RES1 / "log_entries.csv", nrows=0).columns if c.endswith("_raw")})
raw[[c for c in raw.columns if c.endswith("_raw")]] = raw[[c for c in raw.columns if c.endswith("_raw")]].fillna("")
an_lit = AL.audit(raw, r01_literal=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


month = fl.set_index(["version", "entry_id"]).month
rows = []
for v in ("before", "after"):
    for r in CM.RULES:
        t = set(gt[(gt.version == v) & (gt.rule == r)].entry_id)
        d = set(fl[(fl.version == v) & (fl[r] == 1)].entry_id)
        tp, fn, fp = len(t & d), len(t - d), len(d - t)
        rec_lo, rec_hi = wilson(tp, len(t)); pr_lo, pr_hi = wilson(tp, len(d))
        rows.append(dict(version=v, rule_id=r, ditanam=len(t), terdeteksi=len(d), tp=tp, fn=fn, fp=fp, recall=tp / len(t) if t else np.nan,
                         recall_ci_low=rec_lo, recall_ci_high=rec_hi, precision=tp / len(d) if d else np.nan, pr_ci_low=pr_lo, pr_ci_high=pr_hi,
                         alarm_palsu=fp / len(d) if d else np.nan))
res = pd.DataFrame(rows)
res.to_csv(R2 / "ground_truth_recall.csv", index=False, float_format="%.10g")

# R07 yang tidak mungkin terdeteksi (bulan pertama)
r07 = gt[(gt.rule == "R07")].copy()
r07["bulan"] = [month.get((v, e), np.nan) for v, e in zip(r07.version, r07.entry_id)]
r07["dapat_dideteksi"] = (r07.bulan != "2026-07").astype(int)
d7 = fl.set_index(["version", "entry_id"]).R07
r07["terdeteksi"] = [int(d7.get((v, e), 0)) for v, e in zip(r07.version, r07.entry_id)]
s7 = r07.groupby("version").agg(ditanam=("entry_id", "size"), tak_dapat_dideteksi=("dapat_dideteksi", lambda s: int((s == 0).sum())), dapat_dideteksi=("dapat_dideteksi", "sum"),
                                terdeteksi=("terdeteksi", "sum")).reset_index()
s7["recall_dapat_dideteksi"] = s7.terdeteksi / s7.dapat_dideteksi
s7.to_csv(R2 / "ground_truth_r07.csv", index=False, float_format="%.10g")

# sensitivitas R01: definisi literal rancangan (qty diterima saja)
lit = {}
for v in ("before", "after"):
    t = set(gt[(gt.version == v) & (gt.rule == "R01")].entry_id)
    d = set(an_lit[(an_lit.version == v) & (an_lit.rule_id == "R01")].entry_id)
    lit[v] = dict(version=v, definisi="qty diterima saja (rancangan literal)", ditanam=len(t), terdeteksi=len(d), tp=len(t & d), recall=len(t & d) / len(t) if t else np.nan,
                  precision=len(t & d) / len(d) if d else np.nan)
    b = res[(res.version == v) & (res.rule_id == "R01")].iloc[0]
lit_df = pd.DataFrame(list(lit.values()))
base = res[res.rule_id == "R01"][["version", "ditanam", "terdeteksi", "tp", "recall", "precision"]].assign(definisi="stok tersedia (dasar)")
pd.concat([base, lit_df]).to_csv(R2 / "ground_truth_r01_sensitivity.csv", index=False, float_format="%.10g")

# ringkasan keseluruhan (log lama): entri bermasalah (ground truth entri) vs entri bertanda
ent = []
for v in ("before", "after"):
    t = set(gt[gt.version == v].entry_id)
    d = set(fl[(fl.version == v) & (fl.n_pelanggaran > 0)].entry_id)
    nn = int((fl.version == v).sum())
    ent.append(dict(version=v, entri=nn, entri_ditanam=len(t), entri_bertanda=len(d), tp=len(t & d), recall_entri=len(t & d) / len(t), precision_entri=len(t & d) / len(d),
                    alarm_palsu_persen_entri_bersih=len(d - t) / (nn - len(t)), tercapai_recall=int(len(t & d) == len(t)), tercapai_alarm=int(len(d - t) / len(d) < CM.TARGET_FALSE_ALARM)))
pd.DataFrame(ent).to_csv(R2 / "ground_truth_overall.csv", index=False, float_format="%.10g")
print(res[res.version == "before"][["rule_id", "ditanam", "terdeteksi", "tp", "fp", "recall", "precision"]].to_string(index=False))
print(s7.to_string(index=False)); print(pd.concat([base, lit_df]).to_string(index=False)); print(pd.DataFrame(ent).T)

# Lima fakta data pada rancangan (diukur pada log lama; verdict dibuat di build_report dari angka ini)
from scipy import stats
b = fl[fl.version == "before"].copy()
n = len(b)
b["tgl"] = pd.to_datetime(b.date, errors="coerce")
b["akhir_bulan"] = (b.tgl.dt.day > b.tgl.dt.days_in_month - CM.LAST_WEEK_DAYS).astype(int)
lit_b = int(an_lit[(an_lit.version == "before") & (an_lit.rule_id == "R01")].entry_id.nunique())
base_b = int(b.R01.sum())
r03 = b[b.R03 == 1]
def chi(col, mask):
    t = pd.crosstab(mask, b.R03)
    return stats.chi2_contingency(t, correction=False)[1] if t.shape == (2, 2) else np.nan
p_shift = chi("shift", b["shift"] == "Shift 2")
p_week = chi("akhir_bulan", b.akhir_bulan == 1)
r05 = b[b.R05 == 1]
m3 = int((r05.month == "2026-09").sum())
p_m3 = stats.binomtest(m3, len(r05), (b.month == "2026-09").mean()).pvalue
facts = [
    dict(fakta=1, rancangan="3% entri OK + scrap melebihi qty diterima", ukuran="entri R01 proporsi entri (definisi dasar, stok tersedia)", nilai=base_b / n, n=n, k=base_b, ukuran2="definisi literal (qty diterima saja)", nilai2=lit_b / n),
    dict(fakta=2, rancangan="2% sel wajib kosong, terpusat shift malam dan minggu terakhir bulan", ukuran="entri R03 proporsi entri", nilai=len(r03) / n, n=n, k=len(r03),
         ukuran2="p-value R03 Shift 2 vs Shift 1 | minggu terakhir vs lain", nilai2=p_shift, nilai3=p_week),
    dict(fakta=3, rancangan="1,5% sel Sisa ditimpa angka, terpusat bulan ke-3", ukuran="entri R05 proporsi entri", nilai=len(r05) / n, n=n, k=len(r05),
         ukuran2="porsi R05 di bulan ke-3 | p-value binomial vs porsi entri", nilai2=m3 / len(r05), nilai3=p_m3),
    dict(fakta=4, rancangan="carry-over bulanan putus", ukuran="pasangan bulan dengan Sisa Awal tidak sama / pasangan", nilai=np.nan, n=0, k=0),
    dict(fakta=5, rancangan="2% sampai 3% data kotor lain (format dan duplikat)", ukuran="entri R02, R04, atau R06 proporsi entri", nilai=int(((b.R02 == 1) | (b.R04 == 1) | (b.R06 == 1)).sum()) / n, n=n,
         k=int(((b.R02 == 1) | (b.R04 == 1) | (b.R06 == 1)).sum())),
]
ch = pd.read_csv(R2 / "carryover_summary.csv") if (R2 / "carryover_summary.csv").exists() else None
if ch is not None:
    c = ch[ch.version == "before"].iloc[0]; facts[3].update(nilai=c.tidak_cocok / c.pasangan, n=int(c.pasangan), k=int(c.tidak_cocok))
pd.DataFrame(facts).to_csv(R2 / "design_facts.csv", index=False, float_format="%.10g")
print(pd.DataFrame(facts).to_string())
