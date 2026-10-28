# Spesifikasi simulasi

Generator `00_generate_log.py` (seed 19260701, versi data v1) membuat dua workbook Excel dengan struktur log rework: log lama (1.839 entri) dan log hasil template (1.822 entri), tiga bulan (Juli sampai September 2026), 4 model, 3 stasiun asal NG, 2 shift. Semua nilai karangan.

Tingkat error ditanam (ground truth, `data/sim/ground_truth.json`): log lama R01 2%, R02 0,8%, R03 1,8%, R04 1,2%, R05 1,5%, R06 1%, R07 35% pada entri pertama tiap bulan; log template R06 0,1% dan R07 3%. Ground truth hanya dibaca `12_ground_truth_check.py`.

Penyimpangan dari fakta rancangan: error tersebar merata (tidak terpusat pada shift malam, minggu terakhir, atau bulan ke-3); R07 juga ditanam pada bulan pertama sehingga tidak bisa dideteksi; Penurunan error di log template ditentukan asumsi generator (hasil after juga simulasi).
