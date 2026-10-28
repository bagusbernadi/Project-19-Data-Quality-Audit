# Keputusan cleaning

`03_clean.py` menjaga nilai asli (kolom `*_raw`) dan menambah kolom bertipe supaya error tetap bisa dihitung. Tidak ada baris yang dibuang pada tahap audit.

- Tipe sel dicatat (`*_tipe`): int, float, teks, tanggal, rumus, kosong.
- Kolom `*_strip` hanya untuk pengelompokan (spasi dirapikan); aturan R04 memeriksa nilai asli.
- `entry_id` = L (log lama) atau T (template) + nomor baris Excel lima digit.
- Sisa yang berisi rumus dibaca nilai terhitung lewat LibreOffice (openpyxl tidak menyimpan hasil rumus).
- Rekap terkoreksi (Q8): lihat `definitions.md`.
