"""07: Rekonsiliasi rekap bulanan data mentah vs terkoreksi (Q8) dan rantai carry-over antar bulan (Q9).

Rekap mentah meniru SUM Excel: hanya sel angka dijumlah (teks dan kosong diabaikan), duplikat dan angka negatif ikut.
Rekap terkoreksi (ASUMSI, lihat docs/definitions.md): buang duplikat R06 (baris pertama dipertahankan), teks "N pcs" dibaca N,
desimal dibulatkan ke bawah (sensitivitas: pembulatan biasa), negatif dianggap tidak terbaca (0), kosong 0, Sisa dihitung ulang
= Sisa Awal + Diterima - OK - Scrap. Yang dikoreksi hanya kesalahan format; salah angka yang lolos aturan tidak terdeteksi.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import audit_lib as AL
import common as CM

df = pd.read_csv(CM.RES1 / "log_entries.csv", dtype=str, keep_default_na=False)
raw = pd.read_csv(CM.RES1 / "log_entries.csv")
for c in ["month", "version", "entry_id"]:
    df[c] = raw[c]
df = AL.enrich(raw.assign(**{c: raw[c].fillna("") for c in raw.columns if c.endswith("_raw")}))
al = pd.read_csv(CM.RES2 / "anomaly_log.csv")
dup_ids = set(zip(al[al.rule_id == "R06"].version, al[al.rule_id == "R06"].entry_id))
df["is_dup"] = [(v, e) in dup_ids for v, e in zip(df.version, df.entry_id)]

FIELDS = {"qty_received": "diterima", "qty_ok": "ok", "qty_scrap": "scrap"}


def parse(raw_s, mode):
    s = str(raw_s).strip()
    if s == "":
        return 0.0
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?:\s*pcs)?", s, flags=re.I)
    if not m:
        return 0.0
    v = float(m.group(1))
    if v < 0:
        return 0.0
    return float(np.floor(v) if mode == "floor" else np.floor(v + 0.5))


def excel_sum(sub, f):
    t = sub[f"{f}_tipe"]
    return float(pd.to_numeric(sub.loc[t.isin(["int", "float"]), f], errors="coerce").sum())


rows = []
for mode in ("floor", "round"):
    for (ver, mon), d in df.groupby(["version", "month"]):
        r = {"mode": mode, "version": ver, "bulan": mon}
        keep = d[~d.is_dup]
        for f, n in FIELDS.items():
            r[f"{n}_mentah"] = excel_sum(d, f)
            r[f"{n}_koreksi"] = float(keep[f"{f}_raw"].map(lambda x: parse(x, mode)).sum())
        r["sisa_mentah"] = float(pd.to_numeric(d.sisa, errors="coerce").sum())
        awal = keep.sisa_awal_raw.map(lambda x: parse(x, mode))
        rc = keep.qty_received_raw.map(lambda x: parse(x, mode)); ok = keep.qty_ok_raw.map(lambda x: parse(x, mode)); sc = keep.qty_scrap_raw.map(lambda x: parse(x, mode))
        r["sisa_koreksi"] = float((awal + rc - ok - sc).sum())
        r["entri_mentah"] = len(d); r["entri_koreksi"] = len(keep)
        for n in ("diterima", "ok", "scrap", "sisa"):
            r[f"selisih_{n}"] = r[f"{n}_mentah"] - r[f"{n}_koreksi"]
            r[f"persen_selisih_{n}"] = round(r[f"selisih_{n}"] / r[f"{n}_koreksi"], 6) if r[f"{n}_koreksi"] else np.nan
        rows.append(r)
rec = pd.DataFrame(rows)
rec[rec["mode"] == "floor"].drop(columns="mode").to_csv(CM.RES2 / "recap_reconcile.csv", index=False)
rec[rec["mode"] == "round"].drop(columns="mode").to_csv(CM.RES2 / "recap_reconcile_sensitivity.csv", index=False)

chain = AL.chain_check(df)
s = chain.groupby("version").agg(pasangan=("cocok", "size"), cocok=("cocok", "sum")).reset_index()
s["tidak_cocok"] = s.pasangan - s.cocok; s["persen_cocok"] = (s.cocok / s.pasangan).round(6)
s.to_csv(CM.RES2 / "carryover_summary.csv", index=False)
print(rec[rec["mode"] == "floor"][["version", "bulan", "ok_mentah", "ok_koreksi", "scrap_mentah", "scrap_koreksi", "sisa_mentah", "sisa_koreksi", "entri_mentah", "entri_koreksi"]].to_string(index=False))
print(s.to_string(index=False))
