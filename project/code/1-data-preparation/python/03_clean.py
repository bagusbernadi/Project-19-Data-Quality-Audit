"""03: Susun tabel log_entries (satu baris per entri log) dan dim_rule dari cell_raw.csv.

Data asli tidak diperbaiki agar error tetap bisa dihitung: nilai mentah disimpan apa adanya (kolom *_raw, teks) dan
nilai angka hanya diisi bila sel bertipe angka (kolom tanpa akhiran). Spasi ekstra dibuang hanya pada kolom pembantu *_strip.
Hasil: results/1-data-preparation/log_entries.csv, dim_rule.csv, cell_types.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import common as CM

cr = pd.read_csv(CM.CLEAN / "cell_raw.csv", keep_default_na=False, dtype=str)
cr["excel_row"] = cr.excel_row.astype(int)
FIELD = {"Tanggal": "date", "Shift": "shift", "Model": "model", "Stasiun Asal": "ng_origin", "Batch": "batch", "Sisa Awal": "sisa_awal",
         "Qty Diterima": "qty_received", "Qty OK": "qty_ok", "Qty Scrap": "qty_scrap", "Sisa": "sisa"}
cr["field"] = cr.column.map(FIELD)
raw = cr.pivot(index=["version", "excel_row"], columns="field", values="value").reset_index()
typ = cr.pivot(index=["version", "excel_row"], columns="field", values="tipe").reset_index()
calc = cr.pivot(index=["version", "excel_row"], columns="field", values="nilai_terhitung").reset_index()
out = raw[["version", "excel_row"]].copy()
for f in FIELD.values():
    out[f"{f}_raw"] = raw[f]
    out[f"{f}_tipe"] = typ[f]
for f in ("sisa_awal", "qty_received", "qty_ok", "qty_scrap"):
    out[f] = np.where(out[f"{f}_tipe"].isin(["int", "float"]), pd.to_numeric(out[f"{f}_raw"], errors="coerce"), np.nan)
out["sisa"] = pd.to_numeric(calc["sisa"], errors="coerce")                  # nilai yang tampil di sel (rumus dihitung ulang LibreOffice)
out["sisa_is_formula"] = (out.sisa_tipe == "rumus").astype(int)
out["date"] = pd.to_datetime(out.date_raw, errors="coerce")
out["month"] = out.date.dt.strftime("%Y-%m")
for f in ("shift", "model", "ng_origin", "batch"):
    out[f] = out[f"{f}_raw"]
    out[f"{f}_strip"] = out[f"{f}_raw"].str.strip()
out["entry_id"] = np.where(out.version == "before", "L", "T") + out.excel_row.map(lambda r: f"{r:05d}")
out["date"] = out.date.dt.strftime("%Y-%m-%d")
cols = ["entry_id", "version", "excel_row", "date", "month", "shift", "model", "ng_origin", "batch", "sisa_awal", "qty_received", "qty_ok", "qty_scrap", "sisa", "sisa_is_formula"] + \
       [f"{f}_{s}" for f in FIELD.values() for s in ("raw", "tipe")] + [f"{f}_strip" for f in ("shift", "model", "ng_origin", "batch")]
out = out[cols].sort_values(["version", "excel_row"]).reset_index(drop=True)
out.to_csv(CM.RES1 / "log_entries.csv", index=False, float_format="%.10g")
dr = pd.DataFrame([(k, v[0], v[1], v[2]) for k, v in CM.RULES.items()], columns=["rule_id", "description", "category", "check_logic"])
dr.to_csv(CM.RES1 / "dim_rule.csv", index=False)
ct = cr.groupby(["version", "column", "tipe"]).size().rename("sel").reset_index()
ct.to_csv(CM.RES1 / "cell_types.csv", index=False)
print(out.groupby("version").size().to_dict(), "entri;", len(dr), "aturan")
