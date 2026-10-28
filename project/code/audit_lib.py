"""Aturan audit R01 sampai R07 untuk log rework (Project 19). Dipakai audit utama (04), uji template, dan analisis sensitivitas.

Implementasi pandas (vektor). Cek silang independen: 08_crosscheck.py (loop Python murni dan SQL DuckDB).
Input: tabel log_entries (results/1-data-preparation/log_entries.csv). Keluaran: DataFrame pelanggaran (satu baris per pelanggaran).
"""
import re

import numpy as np
import pandas as pd

import common as CM

COL_OF = {"sisa_awal": "Sisa Awal", "qty_received": "Qty Diterima", "qty_ok": "Qty OK", "qty_scrap": "Qty Scrap",
          "shift": "Shift", "model": "Model", "ng_origin": "Stasiun Asal", "date": "Tanggal", "batch": "Batch"}
NUMF = ["sisa_awal", "qty_received", "qty_ok", "qty_scrap"]
REQ = ["date", "shift", "model", "ng_origin", "batch", "sisa_awal", "qty_received", "qty_ok", "qty_scrap"]


def _norm_model(v):
    return re.sub(r"[^A-Z0-9]", "", str(v).upper())


MODEL_MAP = {_norm_model(m): m for m in CM.MODELS}


def norm_pair(df):
    """Identitas (model, stasiun) yang dirapikan hanya untuk pengelompokan (R07); data asli tidak diubah."""
    m = df.model_raw.map(lambda v: MODEL_MAP.get(_norm_model(v)) if v != "" else None)
    s = df.ng_origin_raw.str.strip().str.replace("Stn", "Stasiun", regex=False)
    s = s.where(s.isin(CM.STATIONS))
    return m, s


def _numeric_ok(s):
    return s.notna() & (s >= 0) & (s == np.floor(s))


def enrich(df):
    df = df.copy().reset_index(drop=True)
    df["m_norm"], df["s_norm"] = norm_pair(df)
    return df


def audit(df, r01_literal=False):
    """Kembalikan DataFrame pelanggaran: entry_id, version, rule_id, column, value_found."""
    df = enrich(df)
    rows = []

    def add(mask, rule, col, val):
        sub = df[mask]
        v = val(sub) if callable(val) else val
        rows.append(pd.DataFrame({"entry_id": sub.entry_id.values, "version": sub.version.values, "rule_id": rule, "column": col, "value_found": v}))

    # R01
    ok_v = df.qty_ok.where(_numeric_ok(df.qty_ok), 0.0).fillna(0)
    sc_v = df.qty_scrap.where(_numeric_ok(df.qty_scrap), 0.0).fillna(0)
    recv = df.qty_received.where(_numeric_ok(df.qty_received))
    awal = df.sisa_awal.where(_numeric_ok(df.sisa_awal), 0.0).fillna(0)
    avail = recv if r01_literal else recv + awal
    add(avail.notna() & ((ok_v + sc_v) > avail), "R01", "Qty OK", lambda s: (s.qty_ok_raw + " + " + s.qty_scrap_raw + " > " + (s.qty_received_raw if r01_literal else "stok")).values)
    # R02
    for f in NUMF:
        bad = df[f"{f}_tipe"].isin(["int", "float", "teks"]) & ~_numeric_ok(df[f])
        add(bad, "R02", COL_OF[f], lambda s, f=f: s[f"{f}_raw"].values)
    # R03
    for f in REQ:
        add(df[f"{f}_raw"] == "", "R03", COL_OF[f], "(kosong)")
    # R04
    for f, items in (("shift", CM.SHIFTS), ("model", CM.MODELS), ("ng_origin", CM.STATIONS)):
        add((df[f"{f}_raw"] != "") & ~df[f"{f}_raw"].isin(items), "R04", COL_OF[f], lambda s, f=f: s[f"{f}_raw"].values)
    # R05
    add(df.sisa_is_formula == 0, "R05", "Sisa", lambda s: s.sisa_raw.values)
    # R06
    key = ["version", "date_raw", "shift_raw", "model_raw", "ng_origin_raw", "batch_raw"]
    add(df.duplicated(key, keep="first"), "R06", "Batch", lambda s: s.batch_raw.values)
    # R07
    chain = chain_check(df)
    bad_keys = chain[chain.cocok == 0][["version", "entry_key"]]
    keyf = df[["date_raw", "shift_raw", "model_raw", "ng_origin_raw", "batch_raw"]].astype(str).agg("|".join, axis=1)
    bk = set(map(tuple, bad_keys.values))
    add(pd.Series([(v, k) in bk for v, k in zip(df.version, keyf)], index=df.index), "R07", "Sisa Awal", lambda s: s.sisa_awal_raw.values)
    out = pd.concat(rows, ignore_index=True)
    out["category"] = out.rule_id.map(CM.RULE_CAT)
    return out.sort_values(["version", "entry_id", "rule_id", "column"]).reset_index(drop=True)


def chain_check(df):
    """Rantai carry-over: Sisa Awal entri pertama tiap (model, stasiun) tiap bulan vs Sisa terhitung entri terakhir bulan sebelumnya."""
    df = df.copy()
    if "m_norm" not in df:
        df["m_norm"], df["s_norm"] = norm_pair(df)
    df["entry_key"] = df[["date_raw", "shift_raw", "model_raw", "ng_origin_raw", "batch_raw"]].astype(str).agg("|".join, axis=1)
    comp = df.sisa_awal.where(_numeric_ok(df.sisa_awal)) + df.qty_received.where(_numeric_ok(df.qty_received)) \
        - df.qty_ok.where(_numeric_ok(df.qty_ok)) - df.qty_scrap.where(_numeric_ok(df.qty_scrap))
    df["sisa_terhitung"] = comp
    out = []
    g = df[df.m_norm.notna() & df.s_norm.notna() & (df.month.notna())]
    for (ver, m, s), d in g.groupby(["version", "m_norm", "s_norm"], sort=True):
        months = sorted(d.month.unique())
        for prev, cur in zip(months[:-1], months[1:]):
            last = d[d.month == prev].sort_values("excel_row").iloc[-1]
            first = d[d.month == cur].sort_values("excel_row").iloc[0]
            akhir = last.sisa_terhitung
            awal = first.sisa_awal
            if pd.isna(akhir) or pd.isna(awal):
                continue
            out.append(dict(version=ver, model=m, stasiun=s, bulan_sebelumnya=prev, sisa_akhir_terhitung=akhir, bulan=cur, sisa_awal_dicatat=awal,
                            selisih=awal - akhir, cocok=int(awal == akhir), entry_key=first.entry_key, entry_id=first.entry_id))
    return pd.DataFrame(out)
