"""15: README.md dari CSV hasil (angka tidak diketik). Dijalankan paling akhir sebelum build_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import common as CM

R2, R1 = CM.RES2, CM.RES1
ba = pd.read_csv(R2 / "before_after.csv").iloc[0]; kp = pd.read_csv(R2 / "kpi.csv").set_index("version"); hs = pd.read_csv(R2 / "hours_saved.csv").iloc[0]
gto = pd.read_csv(R2 / "ground_truth_overall.csv").set_index("version"); fh = pd.read_csv(R2 / "formula_hardcode.csv"); fhb = fh[fh.version == "before"].iloc[0]
cx = pd.read_csv(R2 / "crosscheck.csv"); tt = pd.read_csv(R2 / "template_test.csv"); cos = pd.read_csv(R2 / "carryover_summary.csv").set_index("version")
rc = pd.read_csv(R2 / "audit_rule_counts.csv"); rb = rc[rc.version == "before"].sort_values(["pelanggaran", "rule_id"], ascending=[False, True])
inv = pd.read_csv(R2 / "column_inventory_summary.csv").set_index(["versi", "peran"]).jumlah_kolom
rec = pd.read_csv(R2 / "recap_reconcile.csv"); recb = rec[rec.version == "before"]


def I(n): return f"{int(round(float(n))):,}".replace(",", ".")
def D(x, d=1): return f"{float(x):.{d}f}".replace(".", ",")
def P(x, d=1): return D(float(x) * 100, d) + "%"


ob = gto.loc["before"]
rows = "\n".join(f"| {r.rule_id} | {CM.RULES[r.rule_id][0]} | {I(r.pelanggaran)} | {D(r.per_1000, 1)} |" for r in rb.itertuples())
txt = f"""[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 19: Data Quality Audit & Anti-Bypass Template

**Status: Selesai di branch `project-19-build` (belum di-merge ke `main`).** Halaman rancangan dan laporan: [`design-and-report/index.html`](design-and-report/index.html) (tab Design Project dan Report Project).

**Tujuan:** mengukur seberapa sering data yang diisi operator di log Excel salah, dikosongkan, atau menimpa rumus, lalu membangun template Excel tervalidasi dan terkunci yang mencegah kesalahan tersebut.

| | |
|---|---|
| Kategori | Manufaktur (perakitan PCBA) |
| Tingkat | Menengah |
| Data | **Simulasi**: log rework operator (struktur meniru log kerja) dengan error yang ditanam |
| Tools | Excel (Data Validation, proteksi sheet), Python (pandas, SciPy, openpyxl), DuckDB (cek silang), GitHub |

## 1. Problem

**Pertanyaan utama:** seberapa sering data input operator salah, dikosongkan, atau menimpa rumus, dan berapa banyak error yang bisa dicegah oleh template anti-bypass? Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan).

## 2. Data

- Data simulasi (100% karangan), dibuat `00_generate_log.py` (seed 19260701): {I(ba.entri_before)} entri log lama dan {I(ba.entri_after)} entri log template, Juli sampai September 2026. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`).
- Tabel: `log_entries`, `formula_audit`, `anomaly_log`, `dim_rule`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Audit aturan R01 sampai R07 (`project/docs/validation_rules.md`), audit rumus dengan openpyxl, rekonsiliasi rekap dan carry-over, uji template, before-after, dan uji pemulihan error tertanam. Definisi buatan sendiri berlabel asumsi di `project/docs/definitions.md`.

Log lama: {D(kp.loc['before', 'error_per_1000'], 1)} pelanggaran per 1.000 entri (salah isi {D(kp.loc['before', 'salah_isi_per_1000'], 1)}, dilewati {D(kp.loc['before', 'dilewati_per_1000'], 1)}, bypass {D(kp.loc['before', 'bypass_per_1000'], 1)}).

| Aturan | Isi | Pelanggaran | Per 1.000 entri |
|---|---|---|---|
{rows}

- {I(fhb.angka_ketikan)} dari {I(fhb.sel_rumus)} sel rumus Sisa ({P(fhb.persen_ketikan, 2)}) berisi angka ketikan.
- Carry-over antar bulan cocok {I(cos.loc['before', 'cocok'])} dari {I(cos.loc['before', 'pasangan'])} pasangan pada log lama.
- Recall error tertanam {P(ob.recall_entri, 1)} per entri (target 100% tidak tercapai); alarm palsu {P(1 - ob.precision_entri, 1)}.

## 4. Recommendation

Pakai template dengan proteksi struktur workbook manual dan baca kolom Cek tiap akhir shift; audit bulanan mulai dari kolom wajib kosong dan sel Sisa yang ditimpa; sepakati definisi R01 dengan pemilik proses.

## 5. Impact

Pada simulasi, template menurunkan error menjadi {D(ba.error_per_1000_after, 1)} per 1.000 entri (turun {P(ba.penurunan, 1)}). Estimasi (`estimated`): sekitar {D(hs.jam_hemat_per_bulan, 1)} jam koreksi per bulan (CI {D(hs.ci_low, 1)} sampai {D(hs.ci_high, 1)}).

```
jam hemat = (error per entri log lama - log template) x entri per bulan x {I(hs.menit_per_error)} menit per error (asumsi) / 60
```

## Batasan

- **Data adalah simulasi**; penurunan error di log template ditentukan asumsi generator dan belum diuji di lapangan.
- Definisi R01, minggu terakhir, tercile volume, rekap terkoreksi, dan {I(hs.menit_per_error)} menit per error adalah asumsi project.
- Fakta data pada rancangan hanya sebagian sesuai (error tersebar merata, R07 bulan pertama tidak terdeteksi, R01 recall rendah dengan definisi stok tersedia).
- Proteksi sheet bukan keamanan penuh; validasi tidak menghalangi salin-tempel; rumus template dihitung ulang LibreOffice, bukan Excel.
- Dashboard Excel belum diuji ke pembaca awam; slide presentasi tidak dibuat; data tidak di-commit; branch belum di-merge ke main.
- Cek silang: {I(cx.cocok.sum())} dari {I(len(cx))} cocok; uji template {I((tt.dibandingkan == tt.cocok).sum())} dari {I(len(tt))}.

## Menjalankan

Dari folder `project/`:

```
pip install -r requirements.txt
bash run19.sh
```

## Struktur repository

```
README.md
index.html                     pengalihan ke design-and-report/
design-and-report/             index.html (tab Design + Report), src/ (page_v1.html, report.css, report_lib.py, build_report.py)
project/
  code/                        common.py, audit_lib.py, template_lib.py; 1-data-preparation/python (00 sampai 03); 2-analysis/python (04 sampai 12); 3-presentation/python (13 sampai 15)
  results/                     1-data-preparation/ 2-analysis/ 3-presentation/ (CSV hasil, analysis.ipynb)
  outputs/                     Rework_Log_Template.xlsx, Audit_Dashboard.xlsx, audit_summary.png
  data/                        README.md (data tidak di-commit)
  docs/                        validation_rules.md, definitions.md, column_inventory.md, data_dictionary.md, cleaning_decisions.md, simulation_spec.md, datacenter_fingerprint.csv
  run19.sh, requirements.txt
```
"""
(CM.ROOT.parent / "README.md").write_text(txt, encoding="utf-8")
print("README ditulis")
