[← Back to portfolio](https://bagusbernadi.github.io/)

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

- Data simulasi (100% karangan), dibuat `00_generate_log.py` (seed 19260701): 1.839 entri log lama dan 1.822 entri log template, Juli sampai September 2026. Data tidak di-commit; dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256 di repo [DataCenter](https://github.com/bagusbernadi/DataCenter/tree/main/simulasi) (`01_verify_fingerprint.py`).
- Tabel: `log_entries`, `formula_audit`, `anomaly_log`, `dim_rule`. Kamus data: `project/docs/data_dictionary.md`.

## 3. Analysis

Audit aturan R01 sampai R07 (`project/docs/validation_rules.md`), audit rumus dengan openpyxl, rekonsiliasi rekap dan carry-over, uji template, before-after, dan uji pemulihan error tertanam. Definisi buatan sendiri berlabel asumsi di `project/docs/definitions.md`.

Log lama: 66,9 pelanggaran per 1.000 entri (salah isi 34,8, dilewati 19,6, bypass 12,5).

| Aturan | Isi | Pelanggaran | Per 1.000 entri |
|---|---|---|---|
| R03 | Kolom wajib tidak boleh kosong | 36 | 19,6 |
| R05 | Sel Sisa harus berisi rumus | 23 | 12,5 |
| R06 | Tidak boleh ada dua baris dengan tanggal, shift, model, stasiun, dan batch yang sama | 19 | 10,3 |
| R04 | Shift, model, dan stasiun asal harus dari daftar baku | 18 | 9,8 |
| R02 | Semua qty bilangan bulat >= 0 | 15 | 8,2 |
| R01 | Qty OK + Qty Scrap tidak boleh melebihi stok tersedia (Sisa Awal + Qty Diterima) | 6 | 3,3 |
| R07 | Sisa awal bulan sama dengan sisa akhir bulan sebelumnya | 6 | 3,3 |

- 23 dari 1.839 sel rumus Sisa (1,25%) berisi angka ketikan.
- Carry-over antar bulan cocok 17 dari 23 pasangan pada log lama.
- Recall error tertanam 77,4% per entri (target 100% tidak tercapai); alarm palsu 0,8%.

Hipotesis rancangan (`hypotheses.csv`, bunyi dan ambang tidak diubah): H1 Sebagian; H2 Terbukti; H3 Tidak terbukti; H4 Tidak terbukti; H5 Terbukti; H6 Terbukti.

## 4. Recommendation

Pakai template dengan proteksi struktur workbook manual dan baca kolom Cek tiap akhir shift; audit bulanan mulai dari kolom wajib kosong dan sel Sisa yang ditimpa; sepakati definisi R01 dengan pemilik proses.

## 5. Impact

Pada simulasi, template menurunkan error menjadi 1,6 per 1.000 entri (turun 97,5%). Estimasi (`estimated`): sekitar 6,6 jam koreksi per bulan (CI 5,4 sampai 7,9).

```
jam hemat = (error per entri log lama - log template) x entri per bulan x 10 menit per error (asumsi) / 60
```

## Batasan

- **Data adalah simulasi**; penurunan error di log template ditentukan asumsi generator dan belum diuji di lapangan.
- Definisi R01, minggu terakhir, tercile volume, rekap terkoreksi, dan 10 menit per error adalah asumsi project.
- Fakta data pada rancangan hanya sebagian sesuai (error tersebar merata, R07 bulan pertama tidak terdeteksi, R01 recall rendah dengan definisi stok tersedia).
- Proteksi sheet bukan keamanan penuh; validasi tidak menghalangi salin-tempel; rumus template dihitung ulang LibreOffice, bukan Excel.
- Dashboard Excel belum diuji ke pembaca awam; slide presentasi tidak dibuat; data tidak di-commit; branch belum di-merge ke main.
- Cek silang: 48 dari 48 cocok; uji template 16 dari 17.

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
