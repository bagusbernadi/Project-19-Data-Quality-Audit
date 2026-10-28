[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 19: Data Quality Audit & Anti-Bypass Template

**Status: Design (rancangan).**

**Tujuan:** Mengukur seberapa sering data yang diisi operator di log Excel salah, dikosongkan, atau menimpa rumus, lalu membangun template Excel tervalidasi dan terkunci yang mencegah kesalahan tersebut, sehingga rekap bulanan bisa dipercaya tanpa koreksi manual dan penurunan error dapat dibuktikan dengan angka.

| | |
|---|---|
| Kategori | Manufaktur (perakitan PCBA) |
| Tingkat | Menengah |
| Data | Simulasi: log rework operator (struktur meniru log kerja) dengan error yang ditanam |
| Tools | Excel (Data Validation, proteksi sheet), Python (pandas, NumPy, openpyxl), Plotly (opsional), GitHub |

## 1. Problem
Seberapa sering data input operator salah, dikosongkan, atau menimpa rumus, dan berapa banyak error yang bisa dicegah oleh template anti-bypass?

## 2. Data
Data simulasi buatan sendiri, dibuat oleh `scripts/generate_log.py` (seed tetap): workbook log lama dan log hasil uji template, masing-masing ±3 bulan dan ±1.800 entri (4 model papan sirkuit, 3 stasiun asal NG, 2 shift). Error ditanam sebagai ground truth: OK + scrap melebihi qty diterima, sel wajib kosong, sel rumus ditimpa angka, carry-over tidak tersambung, kode salah ketik, baris ganda. Tidak memakai data perusahaan.

Versi data: v1. Tanggal dibuat: 28 Okt 2026. Seed: 19260701. Generator: `scripts/generate_log.py`. Hasil v1: 2 workbook (1.839 entri log lama, 1.822 entri log template).

## 3. Analysis
Rencana: audit aturan R01–R07, error rate per 1.000 entri, Pareto error per kolom dan aturan, audit rumus vs hardcode dengan openpyxl, rekonsiliasi rekap dan carry-over, perbandingan before–after template. Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- Penurunan error di log template ditentukan asumsi generator; perlu uji coba nyata sebelum klaim angka.
- Proteksi sheet Excel mencegah salah tidak sengaja, bukan manipulasi yang disengaja.
- Isian yang formatnya benar tetap bisa salah dan diukur terpisah.
- Tidak ada database SQL; poin "analisis SQL" di checklist standar ditandai N/A.

## Struktur repository (rencana)
```
docs/            # inventaris kolom, aturan validasi, definisi KPI
scripts/         # generator workbook, pembaca workbook, audit
data/            # workbook simulasi log lama dan log template
template/        # template Excel anti-bypass
outputs/         # anomaly_log, rekonsiliasi, dashboard audit
notebooks/       # analisis
index.html       # halaman rancangan (GitHub Pages)
README.md
```
