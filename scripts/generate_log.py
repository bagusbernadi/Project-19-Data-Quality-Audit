"""Project 19: workbook log rework simulasi (log lama tanpa validasi vs log hasil uji template). Seed tetap.

Dua workbook, masing-masing +-1.800 entri (Jul - Sep 2026): 65 hari kerja x 2 shift x 14 entri.
Error ditanam sebagai ground truth (aturan R01-R07), dicatat di data/sim/ground_truth_errors.csv.
Hasil (data/sim/): log_lama.xlsx, log_template.xlsx, ground_truth_errors.csv, ground_truth.json.
Jalankan: python scripts/generate_log.py   (versi data: v1; butuh openpyxl)
Catatan: log_template di sini disimulasikan lewat tingkat error yang lebih rendah (asumsi generator);
template Excel sebenarnya dibangun di folder template/ dan perlu uji coba nyata sebelum klaim angka.
"""
import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sim"
SEED = 19260701
DATA_VERSION = "v1"
MODELS = ["PCB-A1", "PCB-A2", "PCB-B1", "PCB-B2"]
STATIONS = ["Stasiun SMT", "Stasiun AOI", "Stasiun ICT"]
SHIFTS = ["Shift 1", "Shift 2"]
HEADER = ["Tanggal", "Shift", "Model", "Stasiun Asal", "Batch", "Sisa Awal", "Qty Diterima", "Qty OK", "Qty Scrap", "Sisa"]
COLS = {h: i + 1 for i, h in enumerate(HEADER)}
# tingkat error per aturan (per entri). Log lama diisi bebas; log template divalidasi (asumsi generator)
RATES = {
    "log_lama":     {"R01": 0.020, "R02": 0.008, "R03": 0.018, "R04": 0.012, "R05": 0.015, "R06": 0.010, "R07": 0.35},
    "log_template": {"R01": 0.000, "R02": 0.000, "R03": 0.000, "R04": 0.000, "R05": 0.000, "R06": 0.001, "R07": 0.03},
}
# R07: peluang sisa awal pada entri pertama tiap (model, stasiun) tiap bulan TIDAK sama dengan sisa akhir bulan lalu
# R06 di log template: baris ganda masih mungkin (validasi sel tidak mencegahnya)


def normalize_zip(path):
    """Tulis ulang zip dengan cap waktu tetap supaya byte hasil identik tiap dijalankan."""
    buf = io.BytesIO()
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in sorted(zin.namelist()):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            data = zin.read(name)
            if name == "docProps/core.xml":               # openpyxl menimpa waktu modifikasi dengan waktu sekarang
                data = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", data)
            zout.writestr(zi, data)
    Path(path).write_bytes(buf.getvalue())


def build(kind, rng):
    rates = RATES[kind]
    days = pd.bdate_range("2026-07-01", periods=65)
    carry = {(m, s): int(rng.integers(0, 15)) for m in MODELS for s in STATIONS}
    last_month = {}
    rows, truth = [], []
    batch_no = 0
    for day in days:
        for sh in SHIFTS:
            combos = [(m, s) for m in MODELS for s in STATIONS]
            combos += [combos[int(k)] for k in rng.integers(0, len(combos), 2)]
            for m, s in combos:
                batch_no += 1
                first_of_month = last_month.get((m, s)) != day.month
                sisa_awal = carry[(m, s)]
                if first_of_month and rng.random() < rates["R07"]:
                    sisa_awal_input = max(0, sisa_awal + int(rng.integers(-6, 7)) or sisa_awal + 3)
                else:
                    sisa_awal_input = sisa_awal
                last_month[(m, s)] = day.month
                recv = int(rng.integers(20, 121))
                avail = sisa_awal + recv
                done = int(avail * rng.uniform(0.55, 0.95))
                scrap = int(done * rng.uniform(0.0, 0.12))
                ok = done - scrap
                sisa = avail - ok - scrap
                carry[(m, s)] = sisa
                row = dict(zip(HEADER, [day.date(), sh, m, s, f"B{batch_no:05d}", sisa_awal_input, recv, ok, scrap, sisa]))
                errs = []
                if sisa_awal_input != sisa_awal:
                    errs.append("R07")
                if rng.random() < rates["R01"]:
                    row["Qty OK"] = recv + int(rng.integers(1, 15)); errs.append("R01")
                if rng.random() < rates["R02"]:
                    row["Qty Scrap"] = [-int(rng.integers(1, 5)), f"{scrap}.5", f"{scrap} pcs"][int(rng.integers(0, 3))]; errs.append("R02")
                if rng.random() < rates["R03"]:
                    row[["Shift", "Model", "Stasiun Asal", "Qty Diterima", "Qty OK"][int(rng.integers(0, 5))]] = None; errs.append("R03")
                if rng.random() < rates["R04"]:
                    which = "Model" if rng.random() < 0.6 else "Stasiun Asal"
                    row[which] = str(row[which]).lower().replace("-", "") if which == "Model" else str(row[which]).replace("Stasiun", "Stn")
                    errs.append("R04")
                bypass = rng.random() < rates["R05"]
                if bypass:
                    row["Sisa"] = int(sisa + rng.integers(-5, 6)) if rng.random() < 0.7 else sisa
                    errs.append("R05")
                rows.append((row, bypass))
                truth.append(errs)
                if rng.random() < rates["R06"]:
                    rows.append((dict(row), bypass))
                    truth.append(errs + ["R06"])
    return rows, truth


def write(kind, rows, truth):
    wb = Workbook()
    wb.properties.creator = "simulasi"
    wb.properties.created = wb.properties.modified = datetime(2026, 1, 1)
    ws = wb.active
    ws.title = "Log"
    ws.append(HEADER)
    for r, (row, bypass) in enumerate(rows, start=2):
        vals = [row[h] for h in HEADER]
        if not bypass:                                # sel Sisa berisi rumus (R05 terpenuhi)
            vals[COLS["Sisa"] - 1] = f"=F{r}+G{r}-H{r}-I{r}"
        ws.append(vals)
    if kind == "log_template":
        for col, items in (("B", SHIFTS), ("C", MODELS), ("D", STATIONS)):
            dv = DataValidation(type="list", formula1='"' + ",".join(items) + '"', allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(f"{col}2:{col}{len(rows) + 1}")
    path = OUT / f"{kind}.xlsx"
    wb.save(path)
    normalize_zip(path)
    return [(kind, r, rule) for r, errs in enumerate(truth, start=2) for rule in errs]


OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)
all_truth, counts = [], {}
for kind in ("log_lama", "log_template"):
    rows, truth = build(kind, rng)
    all_truth += write(kind, rows, truth)
    counts[kind] = {"entries": len(rows), "entries_with_error": sum(1 for t in truth if t)}
pd.DataFrame(all_truth, columns=["workbook", "excel_row", "rule"]).to_csv(OUT / "ground_truth_errors.csv", index=False)
(OUT / "ground_truth.json").write_text(json.dumps({"seed": SEED, "version": DATA_VERSION, "rates": RATES, "counts": counts},
                                                   indent=2, ensure_ascii=False), encoding="utf-8")
print(counts)
