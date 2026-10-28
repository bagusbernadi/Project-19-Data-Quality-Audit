"""Konstanta dan path bersama Project 19 (Data Quality Audit & Anti-Bypass Template).

ROOT = folder project/. Semua skrip memakai path dari sini. Folder hasil dibuat otomatis.
Definisi yang tidak ada di rancangan ditulis di project/docs/definitions.md dengan label asumsi.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SIM = DATA / "sim"                       # hasil generator: dua workbook dan ground truth (tidak di-commit)
CLEAN = DATA / "clean"                   # tabel hasil baca workbook (tidak di-commit, dibuat ulang)
RES1 = ROOT / "results" / "1-data-preparation"
RES2 = ROOT / "results" / "2-analysis"
RES3 = ROOT / "results" / "3-presentation"
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"
for _d in (DATA, SIM, CLEAN, RES1, RES2, RES3, OUTPUTS):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 19
ALPHA = 0.05
BOOT_B = 2000
WORKBOOKS = {"log_lama": "before", "log_template": "after"}
HEADER = ["Tanggal", "Shift", "Model", "Stasiun Asal", "Batch", "Sisa Awal", "Qty Diterima", "Qty OK", "Qty Scrap", "Sisa"]
INPUT_COLS = HEADER[:-1]                  # sel yang diisi operator di log lama; "Sisa" seharusnya rumus
REQUIRED_COLS = INPUT_COLS                # asumsi: semua kolom isian wajib diisi
NUM_COLS = ["Sisa Awal", "Qty Diterima", "Qty OK", "Qty Scrap"]   # harus bilangan bulat >= 0 (R02)
MODELS = ["PCB-A1", "PCB-A2", "PCB-B1", "PCB-B2"]
STATIONS = ["Stasiun SMT", "Stasiun AOI", "Stasiun ICT"]
SHIFTS = ["Shift 1", "Shift 2"]

# Aturan validasi (rancangan R01 sampai R07). Kategori mengikuti dim_rule di rancangan: salah isi, dilewati, bypass.
RULES = {
    "R01": ("Qty OK + Qty Scrap tidak boleh melebihi stok tersedia (Sisa Awal + Qty Diterima)", "salah isi",
            "OK + scrap > sisa awal + diterima (asumsi: rancangan menulis 'qty diterima', log punya kolom Sisa Awal)"),
    "R02": ("Semua qty bilangan bulat >= 0", "salah isi", "sel Sisa Awal, Diterima, OK, Scrap bukan angka bulat >= 0 (teks, desimal, negatif)"),
    "R03": ("Kolom wajib tidak boleh kosong", "dilewati", "salah satu dari sembilan kolom isian kosong"),
    "R04": ("Shift, model, dan stasiun asal harus dari daftar baku", "salah isi", "nilai tidak persis sama dengan daftar baku (spasi, huruf, ejaan)"),
    "R05": ("Sel Sisa harus berisi rumus", "bypass", "sel Sisa tidak berisi rumus (ditimpa angka ketikan)"),
    "R06": ("Tidak boleh ada dua baris dengan tanggal, shift, model, stasiun, dan batch yang sama", "salah isi", "baris kedua dan seterusnya dengan kunci sama"),
    "R07": ("Sisa awal bulan sama dengan sisa akhir bulan sebelumnya", "salah isi", "Sisa Awal entri pertama (model, stasiun) tiap bulan berbeda dari Sisa terhitung entri terakhir bulan sebelumnya"),
}
CATEGORIES = ["salah isi", "dilewati", "bypass"]
RULE_CAT = {k: v[1] for k, v in RULES.items()}

# Asumsi dampak dan batas (lihat docs/definitions.md)
LAST_WEEK_DAYS = 7              # asumsi: "minggu terakhir bulan" = 7 hari kalender terakhir bulan
MENIT_KOREKSI_PER_ERROR = 10    # asumsi: menit koreksi manual per error (Q14, estimated)
VOLUME_BULAN = 613              # entri per bulan pada simulasi (dihitung ulang di skrip; konstanta hanya contoh slider rancangan 600)
TARGET_REDUCTION = 0.70         # rancangan: penurunan error per 1.000 entri >= 70%
TARGET_RECALL = 1.0             # rancangan: recall 100%
TARGET_FALSE_ALARM = 0.05       # rancangan: alarm palsu di bawah 5%
TEMPLATE_PASSWORD = "rework"    # kata sandi proteksi sheet template (bukan keamanan penuh; lihat Batasan)
