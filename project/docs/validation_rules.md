# Aturan validasi dan KPI

Aturan R01 sampai R07 ada di `code/common.py` (`RULES`) dan diterapkan oleh `code/audit_lib.py`. Tabel referensi: `results/1-data-preparation/dim_rule.csv`.

| Aturan | Isi | Kategori |
|---|---|---|
| R01 | Qty OK + Qty Scrap tidak boleh melebihi stok tersedia (Sisa Awal + Qty Diterima) | salah isi |
| R02 | Sisa Awal, Qty Diterima, OK, Scrap bilangan bulat >= 0 | salah isi |
| R03 | Sembilan kolom isian tidak boleh kosong | dilewati |
| R04 | Shift, model, stasiun asal dari daftar baku | salah isi |
| R05 | Sel Sisa berisi rumus | bypass |
| R06 | Tidak ada dua baris dengan tanggal, shift, model, stasiun, batch sama | salah isi |
| R07 | Sisa Awal entri pertama (model, stasiun) tiap bulan = Sisa terhitung entri terakhir bulan sebelumnya | salah isi |

**ASUMSI R01:** rancangan menulis "qty diterima", sedangkan log punya kolom Sisa Awal sehingga stok tersedia mencakup Sisa Awal. Definisi literal (qty diterima saja) diuji sebagai sensitivitas (`audit_r01_sensitivity.csv`, `ground_truth_r01_sensitivity.csv`).

## KPI
1. Error per 1.000 entri = pelanggaran R01 sampai R07 / entri x 1.000 (satu entri bisa melanggar lebih dari satu aturan).
2. Salah isi, dilewati, bypass per 1.000 entri = KPI 1 per kategori aturan.
3. Selisih rekap = |rekap mentah - rekap terkoreksi| / rekap terkoreksi (OK dan Sisa).
4. First-time-right = entri tanpa pelanggaran / entri.
5. Penurunan error = 1 - error per 1.000 template / error per 1.000 log lama.
