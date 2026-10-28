# Kamus data

| Tabel / file | Isi | Kolom utama |
|---|---|---|
| `results/1-data-preparation/log_entries.csv` | satu baris per entri log (dua versi) | entry_id, version, excel_row, date, shift, model, ng_origin, batch, sisa_awal, qty_received, qty_ok, qty_scrap, sisa, sisa_is_formula, kolom `*_raw` dan `*_tipe` |
| `formula_audit.csv` | sel Sisa: rumus atau angka ketikan | version, cell, is_formula, value, recomputed_value |
| `dim_rule.csv` | tabel referensi aturan | rule_id, description, category, check_logic |
| `results/2-analysis/anomaly_log.csv` | satu baris per pelanggaran | anomaly_id, entry_id, version, rule_id, column, value_found, category |
| `entry_flags.csv` | satu baris per entri, bendera R01 sampai R07 | entry_id, R01..R07, n_pelanggaran |

Hasil lain didaftarkan di Report (Tabel 1.2c).
