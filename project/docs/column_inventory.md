# Inventaris kolom

Dibuat dari `results/2-analysis/column_inventory.csv` oleh `09_build_template.py`.

| Kolom | Log lama | Template |
|---|---|---|
| Tanggal, Shift, Model, Stasiun Asal | input operator | input operator (dropdown, validasi tanggal) |
| Batch | input operator | rumus terkunci (urutan) |
| Sisa Awal | input operator | rumus terkunci (Sisa terakhir model dan stasiun yang sama; saldo awal di sheet Master) |
| Qty Diterima, Qty OK, Qty Scrap | input operator | input operator (bilangan bulat >= 0; OK + Scrap <= stok) |
| Sisa | rumus (bisa ditimpa) | rumus terkunci |
| Cek | tidak ada | rumus terkunci (OK, LENGKAPI, ABNORMAL, DUPLIKAT) |
