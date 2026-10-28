"""11: Perbandingan before-after (Q10), error yang masih lolos (Q11), jam koreksi (Q14, estimated), dan KPI ringkas.

Error per 1.000 entri = jumlah pelanggaran aturan R01-R07 / entri x 1.000 (satu entri bisa melanggar >1 aturan).
Penurunan = 1 - after/before. CI penurunan: bootstrap entri (B dan seed dari common.py).
Q14 (estimated): selisih error per 1.000 x volume entri per bulan x menit koreksi per error (asumsi 10 menit, lihat docs/definitions.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy import stats
import common as CM

R2 = CM.RES2
an = pd.read_csv(R2 / "anomaly_log.csv")
fl = pd.read_csv(R2 / "entry_flags.csv")
rec = pd.read_csv(R2 / "recap_reconcile.csv")
rng = np.random.default_rng(CM.SEED)
rules = list(CM.RULES)


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


per = {}
for v in ("before", "after"):
    f = fl[fl.version == v]
    per[v] = f.n_pelanggaran.values
nb, na = len(per["before"]), len(per["after"])
rb, ra = per["before"].mean() * 1000, per["after"].mean() * 1000
red = 1 - ra / rb
B = CM.BOOT_B
bs = np.empty(B)
for i in range(B):
    bs[i] = 1 - rng.choice(per["after"], na).mean() / rng.choice(per["before"], nb).mean()
lo, hi = np.percentile(bs, [2.5, 97.5])
eb, ea = int((per["before"] > 0).sum()), int((per["after"] > 0).sum())
tab = np.array([[eb, nb - eb], [ea, na - ea]])
_, p_fisher = stats.fisher_exact(tab)
wb, wa = wilson(eb, nb), wilson(ea, na)
q10 = pd.DataFrame([dict(
    entri_before=nb, entri_after=na, pelanggaran_before=int(per["before"].sum()), pelanggaran_after=int(per["after"].sum()),
    error_per_1000_before=rb, error_per_1000_after=ra, penurunan=red, penurunan_ci_low=lo, penurunan_ci_high=hi,
    target_penurunan=CM.TARGET_REDUCTION, tercapai=int(red >= CM.TARGET_REDUCTION), tercapai_ci_low=int(lo >= CM.TARGET_REDUCTION),
    entri_bermasalah_before=eb, entri_bermasalah_after=ea, proporsi_before=eb / nb, proporsi_after=ea / na,
    prop_before_ci_low=wb[0], prop_before_ci_high=wb[1], prop_after_ci_low=wa[0], prop_after_ci_high=wa[1], p_fisher=p_fisher)])
q10.to_csv(R2 / "before_after.csv", index=False, float_format="%.10g")

# per kategori
rows = []
for cat in CM.CATEGORIES:
    kb = int(((an.version == "before") & (an.category == cat)).sum()); ka = int(((an.version == "after") & (an.category == cat)).sum())
    rows.append(dict(category=cat, before=kb, after=ka, per_1000_before=kb / nb * 1000, per_1000_after=ka / na * 1000, penurunan=1 - (ka / na) / (kb / nb) if kb else np.nan))
pd.DataFrame(rows).to_csv(R2 / "before_after_category.csv", index=False, float_format="%.10g")

# Q11: error yang masih lolos
rem = an[an.version == "after"].copy()
rem["deskripsi"] = rem.rule_id.map(lambda r: CM.RULES[r][0])
rem.to_csv(R2 / "remaining_errors.csv", index=False)
rr = []
for r in rules:
    rr.append(dict(rule_id=r, deskripsi=CM.RULES[r][0], kategori=CM.RULE_CAT[r], before=int(((an.version == "before") & (an.rule_id == r)).sum()),
                   after=int(((an.version == "after") & (an.rule_id == r)).sum())))
pd.DataFrame(rr).to_csv(R2 / "remaining_by_rule.csv", index=False)

# Q14 estimated
vol = (nb + na) / 6.0
bs14 = []
rng2 = np.random.default_rng(CM.SEED + 1)
for i in range(B):
    d = rng2.choice(per["before"], nb).mean() - rng2.choice(per["after"], na).mean()
    bs14.append(d * vol * CM.MENIT_KOREKSI_PER_ERROR / 60)
est = (per["before"].mean() - per["after"].mean()) * vol
q14 = pd.DataFrame([dict(volume_entri_per_bulan=vol, menit_per_error=CM.MENIT_KOREKSI_PER_ERROR, error_tercegah_per_bulan=est,
                         jam_hemat_per_bulan=est * CM.MENIT_KOREKSI_PER_ERROR / 60, ci_low=np.percentile(bs14, 2.5), ci_high=np.percentile(bs14, 97.5), label="estimated")])
q14.to_csv(R2 / "hours_saved.csv", index=False, float_format="%.10g")

# KPI
kp = []
for v, n in (("before", nb), ("after", na)):
    s = an[an.version == v]; f = fl[fl.version == v]
    cat = lambda c: int((s.category == c).sum()) / n * 1000
    rv = rec[rec.version == v]
    kp.append(dict(version=v, error_per_1000=len(s) / n * 1000, salah_isi_per_1000=cat("salah isi"), dilewati_per_1000=cat("dilewati"), bypass_per_1000=cat("bypass"),
                   first_time_right=float((f.n_pelanggaran == 0).mean()), selisih_rekap_ok_persen=float(abs(rv.selisih_ok.sum()) / rv.ok_koreksi.sum()),
                   selisih_rekap_sisa_persen=float(abs(rv.selisih_sisa.sum()) / rv.sisa_koreksi.sum())))
pd.DataFrame(kp).to_csv(R2 / "kpi.csv", index=False, float_format="%.10g")
print(q10.T.to_string()); print(q14.T.to_string()); print(pd.DataFrame(kp).T.to_string())
