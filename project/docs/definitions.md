# Definisi dan asumsi (label ASUMSI = tidak ada di rancangan)

- **ASUMSI** R01 memakai stok tersedia (Sisa Awal + Qty Diterima). Sensitivitas: definisi literal.
- **ASUMSI** minggu terakhir bulan = 7 hari kalender terakhir (`LAST_WEEK_DAYS`). Shift malam dipetakan ke Shift 2.
- **ASUMSI** kelompok volume harian = tercile total Qty Diterima per hari (rendah, sedang, tinggi).
- **ASUMSI** rekap terkoreksi: buang baris ganda R06 (baris pertama dipertahankan), teks "N pcs" dibaca N, desimal dibulatkan ke bawah (sensitivitas: pembulatan biasa, `recap_reconcile_sensitivity.csv`), negatif dianggap tidak terbaca (0), kosong 0, Sisa dihitung ulang. Hanya kesalahan format yang dikoreksi; angka salah yang lolos aturan tidak terdeteksi.
- **ASUMSI** 10 menit koreksi manual per error (`MENIT_KOREKSI_PER_ERROR`); jam hemat berlabel estimated. Volume entri per bulan = rata-rata dua versi.
- **ASUMSI** alarm palsu = entri bertanda yang tidak ada di ground truth aturan itu / entri bertanda aturan itu.
- Recall 100% dan alarm palsu < 5% (rancangan) dipakai apa adanya sebagai target; penurunan error minimal 70%.
- Uji: chi-square dengan koreksi Holm (pola), uji Fisher dan bootstrap (before-after), Wilson dan Poisson (CI). Alpha 0,05; seed 19.
- Template: validasi Excel hanya menghalangi ketikan langsung; salin-tempel dapat melewatinya, jadi kolom Cek tetap dipantau. Proteksi sheet bukan keamanan penuh.
