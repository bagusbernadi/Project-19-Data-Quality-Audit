"""13: Hipotesis formal rancangan (ditambahkan 29 Okt 2026) diuji dari CSV hasil analisis dan uji pemulihan; hasil: hypotheses.csv.

Hipotesis dirumuskan dari kalimat rancangan yang sudah ada (kriteria keberhasilan dan fakta ground truth). Bunyi dan ambangnya tidak diubah setelah melihat hasil.
Dijalankan setelah 12_ground_truth_check.py (membaca design_facts.csv dan ground_truth_overall.csv).
Vonis: Terbukti (kriteria terpenuhi), Sebagian (sebagian kriteria terpenuhi), Tidak terbukti (kriteria tidak terpenuhi).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
import common as CM

R2 = CM.RES2
ALPHA = 0.05


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, ps[i] * (len(ps) - r)))
        adj[i] = run
    return adj


gtp = pd.read_csv(R2 / "ground_truth_overall.csv").set_index("version")
ba = pd.read_csv(R2 / "before_after.csv").iloc[0]
df = pd.read_csv(R2 / "design_facts.csv").set_index("fakta")
fh = pd.read_csv(R2 / "formula_hardcode.csv")
co = pd.read_csv(R2 / "carryover_summary.csv").set_index("version")
RECALL_TARGET, ALARM_MAX, DROP_MIN = 1.0, 0.05, 0.70      # dari rancangan: recall 100%, alarm palsu < 5%, penurunan minimal 70%

rows = []
b = gtp.loc["before"]
alarm = 1 - b.precision_entri
r_ok, a_ok = b.recall_entri >= RECALL_TARGET, alarm < ALARM_MAX
lo, hi = wilson(int(b.tp), int(b.entri_ditanam))
rows.append(dict(hid="H1", hipotesis_rancangan="Skrip audit menemukan semua error yang ditanam (recall 100%) dengan alarm palsu di bawah 5%.", pertanyaan="Q13", ukuran="recall entri; alarm palsu (1 - precision)",
                 nilai=b.recall_entri, ci_low=lo, ci_high=hi, nilai2=alarm, p=np.nan,
                 verdict="Terbukti" if r_ok and a_ok else ("Sebagian" if a_ok else "Tidak terbukti"),
                 bukti=f"recall entri {b.tp:.0f} dari {b.entri_ditanam:.0f}; alarm palsu {alarm * 100:.1f}%",
                 catatan_keputusan="Syarat recall 100% " + ("terpenuhi" if r_ok else "tidak terpenuhi") + "; syarat alarm palsu di bawah 5% " + ("terpenuhi" if a_ok else "tidak terpenuhi")))
ok2 = ba.penurunan_ci_low >= DROP_MIN
rows.append(dict(hid="H2", hipotesis_rancangan="Error per 1.000 entri di log template turun minimal 70% dibanding log lama.", pertanyaan="Q10", ukuran="penurunan error per 1.000 entri",
                 nilai=ba.penurunan, ci_low=ba.penurunan_ci_low, ci_high=ba.penurunan_ci_high, nilai2=np.nan, p=ba.p_fisher, verdict="Terbukti" if ok2 else ("Sebagian" if ba.penurunan >= DROP_MIN else "Tidak terbukti"),
                 bukti=f"{ba.error_per_1000_before:.1f} turun ke {ba.error_per_1000_after:.1f} per 1.000 entri",
                 catatan_keputusan="batas bawah CI " + ("di atas" if ok2 else "di bawah") + " 70%"))
p_shift, p_week = float(df.loc[2, "nilai2"]), float(df.loc[2, "nilai3"])
ph = holm([p_shift, p_week])
sig = any(p < ALPHA for p in ph)
rows.append(dict(hid="H3", hipotesis_rancangan="Sel wajib yang dibiarkan kosong terpusat di shift malam dan di minggu terakhir bulan.", pertanyaan="Q4", ukuran="p uji R03 shift malam vs siang; minggu terakhir vs lain (Holm)",
                 nilai=min(ph), ci_low=np.nan, ci_high=np.nan, nilai2=max(ph), p=min(p_shift, p_week), verdict="Terbukti" if all(p < ALPHA for p in ph) else ("Sebagian" if sig else "Tidak terbukti"),
                 bukti=f"p shift {p_shift:.3f}, p minggu terakhir {p_week:.3f}; {df.loc[2, 'k']:.0f} entri R03",
                 catatan_keputusan="definisi shift malam = Shift 2 (asumsi, docs/definitions.md); dua uji dikoreksi Holm"))
share, p_m3 = float(df.loc[3, "nilai2"]), float(df.loc[3, "nilai3"])
rows.append(dict(hid="H4", hipotesis_rancangan="Sel rumus Sisa yang ditimpa angka ketikan terpusat di bulan ketiga.", pertanyaan="Q6", ukuran="porsi entri R05 di bulan ketiga; p binomial",
                 nilai=share, ci_low=np.nan, ci_high=np.nan, nilai2=np.nan, p=p_m3, verdict="Terbukti" if (p_m3 < ALPHA and share > 1 / 3) else "Tidak terbukti",
                 bukti=f"{share * 100:.1f}% dari {df.loc[3, 'k']:.0f} sel ketikan di bulan ketiga; p binomial {p_m3:.3f}",
                 catatan_keputusan="pembanding: porsi entri di bulan ketiga; sampel kecil"))
c = co.loc["before"]
rows.append(dict(hid="H5", hipotesis_rancangan="Sisa akhir bulan tidak selalu tersambung ke sisa awal bulan berikutnya.", pertanyaan="Q9", ukuran="pasangan bulan tidak cocok per pasangan",
                 nilai=c.tidak_cocok / c.pasangan, ci_low=wilson(int(c.tidak_cocok), int(c.pasangan))[0], ci_high=wilson(int(c.tidak_cocok), int(c.pasangan))[1], nilai2=np.nan, p=np.nan,
                 verdict="Terbukti" if c.tidak_cocok >= 1 else "Tidak terbukti", bukti=f"{c.tidak_cocok:.0f} dari {c.pasangan:.0f} pasangan tidak cocok pada log lama",
                 catatan_keputusan="rancangan menanam satu kali; jumlah yang ditemukan dilaporkan apa adanya"))
a = fh[fh.version == "after"].iloc[0]
rows.append(dict(hid="H6", hipotesis_rancangan="Semua bypass rumus tercegah di log template.", pertanyaan="Q6", ukuran="sel Sisa berisi angka ketikan di log template",
                 nilai=a.persen_ketikan, ci_low=a.ci_low, ci_high=a.ci_high, nilai2=a.angka_ketikan, p=np.nan, verdict="Terbukti" if a.angka_ketikan == 0 else "Tidak terbukti",
                 bukti=f"{a.angka_ketikan:.0f} dari {a.sel_rumus:.0f} sel rumus berisi angka ketikan", catatan_keputusan="nol kejadian bukan bukti nol mutlak; batas atas CI Wilson dilaporkan"))
out = pd.DataFrame(rows)
out.to_csv(R2 / "hypotheses.csv", index=False, float_format="%.10g")
print(out[["hid", "verdict", "bukti"]].to_string(index=False))
