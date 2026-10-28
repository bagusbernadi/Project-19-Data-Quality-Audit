"""05: Pola error (Q4 dan Q5): per shift, model, minggu terakhir bulan, dan kelompok volume harian. Hasil: patterns.csv, patterns_tests.csv.

Dasar: entri dengan >= 1 pelanggaran (entri bermasalah) per versi. Uji chi-square antar kelompok, koreksi Holm antar uji dalam satu versi.
Entri tanpa identitas valid (sel kosong) tetap dihitung pada kelompok "(kosong)". Volume harian = total Qty Diterima numerik per tanggal, tersil tiga kelompok (tercile) per versi.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
import audit_lib as AL
import common as CM

R2 = CM.RES2
fl = pd.read_csv(R2 / "entry_flags.csv", keep_default_na=False, na_values=[""])
le = pd.read_csv(CM.RES1 / "log_entries.csv", keep_default_na=False, na_values=[""], dtype=object)
le["qty_received"] = pd.to_numeric(le.qty_received)
fl = fl.merge(le[["entry_id", "qty_received", "model_raw", "shift_raw"]], on="entry_id")
fl["bermasalah"] = (fl.n_pelanggaran > 0).astype(int)
d = pd.to_datetime(fl.date)
fl["minggu_akhir"] = np.where(d.isna(), "(kosong)", np.where(d.dt.day > d.dt.days_in_month - CM.LAST_WEEK_DAYS, "minggu terakhir bulan", "hari lain"))
fl["shift_g"] = fl.shift_raw.where(fl.shift_raw.isin(CM.SHIFTS), "(kosong)")
fl["model_g"] = fl.model_raw.map(lambda v: AL.MODEL_MAP.get(AL._norm_model(v)) if v else None).fillna("(kosong)")
# volume harian per versi
vol = fl.groupby(["version", "date"]).qty_received.sum().rename("volume_harian").reset_index()
vol["kelompok_volume"] = vol.groupby("version").volume_harian.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=["rendah", "sedang", "tinggi"]).astype(str))
fl = fl.merge(vol, on=["version", "date"], how="left")
fl["kelompok_volume"] = fl.kelompok_volume.fillna("(kosong)")
rows, tests = [], []
for ver in ("before", "after"):
    sub = fl[fl.version == ver]
    for fak, col, extra in (("shift", "shift_g", None), ("model", "model_g", None), ("minggu", "minggu_akhir", None), ("volume harian", "kelompok_volume", None)):
        t = sub.groupby(col).bermasalah.agg(["sum", "count"])
        for lv, r in t.iterrows():
            lo, hi = proportion_confint(int(r["sum"]), int(r["count"]), alpha=CM.ALPHA, method="wilson")
            rows.append(dict(version=ver, faktor=fak, level=lv, entri=int(r["count"]), bermasalah=int(r["sum"]), proporsi=r["sum"] / r["count"], ci_low=lo, ci_high=hi))
        tt = t[t.index != "(kosong)"]
        if tt["sum"].sum() > 0 and len(tt) > 1:
            tab = np.vstack([tt["sum"], tt["count"] - tt["sum"]])
            c2, p, dof, _ = stats.chi2_contingency(tab)
        else:
            c2, p, dof = np.nan, np.nan, np.nan
        tests.append(dict(version=ver, faktor=fak, chi2=c2, dof=dof, p=p, kelompok=len(tt), bermasalah_total=int(tt["sum"].sum())))
tt = pd.DataFrame(tests)
tt["p_holm"] = np.nan
for ver in ("before", "after"):
    m = (tt.version == ver) & tt.p.notna()
    if m.sum():
        tt.loc[m, "p_holm"] = multipletests(tt.loc[m, "p"], method="holm")[1]
tt["signifikan"] = (tt.p_holm < CM.ALPHA).astype(int)
# R03 per shift (rancangan: "dilewati terpusat di shift malam dan minggu terakhir")
r3 = []
for ver in ("before",):
    sub = fl[fl.version == ver]
    for fak, col in (("shift", "shift_g"), ("minggu", "minggu_akhir")):
        t = sub.groupby(col)["R03"].agg(["sum", "count"])
        for lv, r in t.iterrows():
            r3.append(dict(version=ver, faktor=fak, level=lv, entri=int(r["count"]), entri_R03=int(r["sum"]), proporsi=r["sum"] / r["count"]))
r3 = pd.DataFrame(r3)
pd.DataFrame(rows).to_csv(R2 / "patterns.csv", index=False, float_format="%.10g")
tt.to_csv(R2 / "patterns_tests.csv", index=False, float_format="%.10g")
r3.to_csv(R2 / "patterns_r03.csv", index=False, float_format="%.10g")
print(pd.DataFrame(rows)[lambda x: x.version == "before"].round(4).to_string(index=False)); print(tt.round(4).to_string(index=False)); print(r3.round(4))
