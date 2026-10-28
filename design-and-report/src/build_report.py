"""Generator Report v2 (Project 19). Dijalankan paling akhir, setelah seluruh pipeline dijalankan ulang dari nol.

Input : design-and-report/src/page_v1.html (rancangan, pane Design TIDAK diubah), project/results/*.
Output: design-and-report/index.html
Angka di teks Report berasal dari CSV lewat helper report_lib (I, D, P, cs). audit() memeriksa token angka tak terdaftar.
"""
import re
import sys
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "project"
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(HERE))
import pandas as pd
import common as C
import report_lib as R
from report_lib import I, D, P, cs, pill, BLUE, GREY, table, qa, legend, bars, gbars, lines, pareto_svg, audit

SRC = (HERE / "page_v1.html").read_text(encoding="utf-8")
CSS_EXTRA = (HERE / "report.css").read_text(encoding="utf-8")
r1, r2, r3 = C.RES1, C.RES2, C.RES3


def rd(d, n, **k):
    return pd.read_csv(d / n, **k)


rc = rd(r2, "audit_rule_counts.csv"); cat = rd(r2, "audit_category.csv"); col = rd(r2, "audit_column.csv"); r01s = rd(r2, "audit_r01_sensitivity.csv")
pat = rd(r2, "patterns.csv"); ptt = rd(r2, "patterns_tests.csv"); pr3 = rd(r2, "patterns_r03.csv")
fh = rd(r2, "formula_hardcode.csv"); fds = rd(r2, "formula_diff_summary.csv"); fdc = rd(r2, "formula_diff_cells.csv")
rec = rd(r2, "recap_reconcile.csv"); recs = rd(r2, "recap_reconcile_sensitivity.csv"); cos = rd(r2, "carryover_summary.csv"); chn = rd(r2, "chain_check.csv")
ba = rd(r2, "before_after.csv").iloc[0]; bac = rd(r2, "before_after_category.csv"); rbr = rd(r2, "remaining_by_rule.csv"); rme = rd(r2, "remaining_errors.csv")
hs = rd(r2, "hours_saved.csv").iloc[0]; kpi = rd(r2, "kpi.csv").set_index("version"); inv = rd(r2, "column_inventory.csv"); invs = rd(r2, "column_inventory_summary.csv")
gtr = rd(r2, "ground_truth_recall.csv"); g01 = rd(r2, "ground_truth_r01_sensitivity.csv"); g07 = rd(r2, "ground_truth_r07.csv"); gto = rd(r2, "ground_truth_overall.csv").set_index("version")
fct = rd(r2, "design_facts.csv").set_index("fakta"); cx = rd(r2, "crosscheck.csv"); tt = rd(r2, "template_test.csv"); fl = rd(r2, "entry_flags.csv")
fp = rd(r1, "fingerprint_check.csv"); dimr = rd(r1, "dim_rule.csv"); cty = rd(r1, "cell_types.csv"); wk = rd(r3, "weekly_trend.csv")
hdr = pd.read_csv(r1 / "log_entries.csv", nrows=0).columns
rawc = {c: str for c in hdr if c.endswith("_raw")}
le = pd.read_csv(r1 / "log_entries.csv", dtype=rawc, keep_default_na=False, na_values=[""])

NB, NA = int(ba.entri_before), int(ba.entri_after)
rb = lambda r: rc[(rc.version == "before") & (rc.rule_id == r)].iloc[0]
cb = lambda c: cat[(cat.version == "before") & (cat.category == c)].iloc[0]
ca_ = lambda c: cat[(cat.version == "after") & (cat.category == c)].iloc[0]
rule_desc = dict(zip(dimr.rule_id, dimr.description))
n_cx = len(cx); n_cx_ok = int(cx.cocok.sum())
tc = lambda p: cx[cx.cek == p]
n_tt = len(tt); n_tt_ok = int((tt.dibandingkan == tt.cocok).sum())
n_fp, n_fp_ok = len(fp), int((fp.hasil == "cocok").sum())
rules = list(C.RULES)


def ci(lo, hi, d=1):
    return f"CI 95% {D(lo, d)} sampai {D(hi, d)}"


def cip(lo, hi, d=1):
    return f"CI 95% {D(lo * 100, d)}% sampai {D(hi * 100, d)}%"


def pv(p):
    return "< 0,001" if float(p) < 0.001 else D(float(p), 3)


def kp(v, l, d, color):
    return f'<div class="card kpi" style="--h:var(--{color})"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'


# ---------- nilai turunan ----------
tot_b, tot_a = cb("semua"), ca_("semua")
col_b = col[col.version == "before"].sort_values(["pelanggaran", "column"], ascending=[False, True])
rule_b = rc[rc.version == "before"].sort_values(["pelanggaran", "rule_id"], ascending=[False, True]).reset_index(drop=True)
rule_b["share"] = rule_b.pelanggaran / rule_b.pelanggaran.sum(); rule_b["cum"] = rule_b.share.cumsum()
vital = [bool(c - s < 0.8) for c, s in zip(rule_b.cum, rule_b.share)]
k80 = sum(vital)
ptb = ptt[ptt.version == "before"].set_index("faktor"); pta = ptt[ptt.version == "after"].set_index("faktor")
fh_b = fh[fh.version == "before"].iloc[0]; fh_a = fh[fh.version == "after"].iloc[0]
fd = fds.iloc[0]
cos_b = cos[cos.version == "before"].iloc[0]; cos_a = cos[cos.version == "after"].iloc[0]
rec_b = rec[rec.version == "before"]; rec_a = rec[rec.version == "after"]
tr = lambda d, f: d[f"selisih_{f}"].sum() / d[f"{f}_koreksi"].sum()
ov_b, ov_a = gto.loc["before"], gto.loc["after"]
r_ = lambda r: gtr[(gtr.version == "before") & (gtr.rule_id == r)].iloc[0]
lit_b = g01[(g01.version == "before") & (g01.definisi.str.startswith("qty"))].iloc[0]
base01 = g01[(g01.version == "before") & (g01.definisi.str.startswith("stok"))].iloc[0]
g07b = g07[g07.version == "before"].iloc[0]
tg = lambda f: ba[f]
sel_in = invs.set_index(["versi", "peran"]).jumlah_kolom
n_in_b = int(sel_in.loc[("log lama", "input operator")]); n_in_a = int(sel_in.loc[("template", "input operator")])
n_f_b = int(sel_in.loc[("log lama", "rumus (seharusnya)")]); n_f_a = int(sel_in.loc[("template", "rumus terkunci")])
top_rule = rule_b.iloc[0]; top_col = col_b.iloc[0]
pr_last = pat[(pat.version == "before") & (pat.faktor == "minggu")].set_index("level").proporsi
pr_sh = pat[(pat.version == "before") & (pat.faktor == "shift") & (pat.level != "(kosong)")]
pr_vol = pat[(pat.version == "before") & (pat.faktor == "volume harian")].set_index("level").proporsi
rem_rows = rbr[rbr.after > 0]
tot_pairs_b = int(cos_b.pasangan)
weeks_b = wk[wk.version == "before"]

# ---------- grafik ----------
chart_cat = gbars(["Salah isi", "Dilewati", "Bypass"], [("Log lama", BLUE, [kpi.loc["before", c] for c in ("salah_isi_per_1000", "dilewati_per_1000", "bypass_per_1000")]),
                  ("Template", "#188038", [kpi.loc["after", c] for c in ("salah_isi_per_1000", "dilewati_per_1000", "bypass_per_1000")])], lambda v: D(v, 0), "Grafik error per 1.000 entri menurut kategori", rot=0)
chart_par = pareto_svg(list(rule_b.rule_id), list(rule_b.share), list(rule_b.cum), vital,
                       [f"{r.rule_id}: {I(r.pelanggaran)} pelanggaran ({D(r.share * 100, 1)}%), kumulatif {D(r.cum * 100, 1)}%" for r in rule_b.itertuples()], "Grafik Pareto pelanggaran per aturan, log lama")
wkl = sorted(weeks_b.minggu)
chart_wk = lines([w[-3:] for w in wkl], [("Log lama", BLUE, 2, [float(weeks_b[weeks_b.minggu == w].error_per_1000.iloc[0]) for w in wkl])],
                 lambda v: D(v, 0), "Grafik error per 1.000 entri per minggu, log lama", h=250, zero=True)

# ---------- pertanyaan ----------
QS = [
    (1, "Berapa error per 1.000 entri di log lama, dipisah menjadi salah isi, dilewati, dan bypass rumus?", "Utama"),
    (2, "Kolom mana yang paling sering salah atau dibiarkan kosong?", "Utama"),
    (3, "Aturan validasi mana yang paling sering dilanggar?", "Utama"),
    (4, "Apakah error lebih sering terjadi di shift tertentu, model tertentu, atau di minggu terakhir bulan?", "Pendukung"),
    (5, "Apakah error naik pada hari dengan volume rework tinggi?", "Pendukung"),
    (6, "Berapa persen sel rumus yang sudah berisi angka ketikan, dan di sheet serta kolom mana?", "Utama"),
    (7, "Seberapa jauh angka ketikan itu berbeda dari hasil rumus yang seharusnya?", "Pendukung"),
    (8, "Berapa selisih rekap bulanan (OK, scrap, sisa) antara data mentah dan data yang sudah dikoreksi?", "Utama"),
    (9, "Apakah sisa akhir bulan selalu sama dengan sisa awal bulan berikutnya?", "Utama"),
    (10, "Setelah template dipakai, berapa error per 1.000 entri, dan berapa persen penurunannya?", "Utama"),
    (11, "Jenis error apa yang masih lolos dari validasi template?", "Utama"),
    (12, "Berapa kolom yang harus diisi operator sebelum dan sesudah template?", "Pendukung"),
    (13, "Apakah skrip audit menemukan semua error yang sengaja ditanam, tanpa banyak alarm palsu?", "Utama"),
    (14, "Berapa jam koreksi data per bulan yang bisa dihemat?", "Tambahan"),
]
WARN = {1, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14}
pair_txt = ", ".join(f"{r.rule_id} ({I(r.pelanggaran)})" for r in rule_b.head(3).itertuples())
bad_cell = fdc[fdc.sama_dengan_rumus == 0]
ANS = {
    1: (f"Log lama: {D(tot_b.per_1000, 1)} pelanggaran per 1.000 entri ({I(tot_b.pelanggaran)} pelanggaran pada {I(NB)} entri; {ci(tot_b.ci_low, tot_b.ci_high)}, Poisson). "
        f"Salah isi {D(cb('salah isi').per_1000, 1)}, dilewati {D(cb('dilewati').per_1000, 1)}, bypass rumus {D(cb('bypass').per_1000, 1)} per 1.000 entri; {I(tot_b.entri_terdampak)} entri ({P(ba.proporsi_before, 1)}) punya minimal satu pelanggaran. "
        f"Angka bergantung pada definisi R01 (asumsi: stok tersedia); dengan definisi literal rancangan R01 saja menghasilkan {I(r01s[(r01s.version == 'before') & (r01s.definisi.str.startswith('qty'))].pelanggaran.iloc[0])} pelanggaran (alarm palsu masif)."),
    2: (f"Kolom {top_col.column} paling sering bermasalah ({I(top_col.pelanggaran)} pelanggaran, {P(top_col.share, 1)} dari total, {D(top_col.per_1000, 1)} per 1.000 entri), diikuti " + ", ".join(f"{r.column} ({I(r.pelanggaran)})" for r in col_b.iloc[1:4].itertuples()) +
        ". Pelanggaran R03 dihitung per kolom kosong, sedangkan satu entri bisa melanggar lebih dari satu aturan."),
    3: (f"Tiga aturan teratas: {pair_txt}. R03 (kolom wajib kosong) terbanyak, yaitu {D(top_rule.per_1000, 1)} per 1.000 entri ({ci(top_rule.ci_low, top_rule.ci_high)}). Diperlukan {I(k80)} aturan untuk mencapai 80% pelanggaran. "
        f"R01 hanya {I(rb('R01').pelanggaran)} karena memakai asumsi stok tersedia (Sisa Awal + Qty Diterima); lihat sensitivitas di Tabel 2.1d."),
    4: (f"Tidak ada pola yang signifikan setelah koreksi Holm: shift (p Holm {pv(ptb.loc['shift', 'p_holm'])}), model ({pv(ptb.loc['model', 'p_holm'])}), minggu terakhir bulan ({pv(ptb.loc['minggu', 'p_holm'])}). "
        f"Proporsi entri bermasalah minggu terakhir {P(pr_last['minggu terakhir bulan'], 1)} dibanding {P(pr_last['hari lain'], 1)} di hari lain. Pada log template hanya {I(tot_a.pelanggaran)} pelanggaran sehingga pola tidak bisa diuji. Pola belum tentu penyebab; minggu terakhir adalah 7 hari kalender terakhir (asumsi)."),
    5: (f"Tidak. Proporsi entri bermasalah pada hari bervolume rendah {P(pr_vol['rendah'], 1)}, sedang {P(pr_vol['sedang'], 1)}, tinggi {P(pr_vol['tinggi'], 1)}; beda tidak signifikan (chi-square p {pv(ptb.loc['volume harian', 'p'])}). Kelompok volume adalah tercile total Qty Diterima per hari (asumsi)."),
    6: (f"Pada log lama, {I(fh_b.angka_ketikan)} dari {I(fh_b.sel_rumus)} sel rumus ({P(fh_b.persen_ketikan, 2)}; {cip(fh_b.ci_low, fh_b.ci_high, 2)}) berisi angka ketikan, semuanya di sheet {fh_b.sheet}, kolom {fh_b.column}. "
        f"Pada log template {I(fh_a.angka_ketikan)} dari {I(fh_a.sel_rumus)} (batas atas CI {P(fh_a.ci_high, 2)})."),
    7: (f"Dari {I(fd.sel_ketikan)} sel ketikan, {I(fd.sama_dengan_rumus)} sama dengan hasil rumus, {I(fd.berbeda)} berbeda, dan {I(fd.tak_terhitung)} tidak bisa dihitung ulang (masukan kosong). Selisih absolut rata-rata {D(fd.rata_selisih_abs, 1)}, median {D(fd.median_selisih_abs, 0)}, maksimum {D(fd.maks_selisih_abs, 0)}; jumlah selisih bersih {D(fd.total_selisih_bersih, 0)} (tanda negatif: ketikan lebih kecil dari rumus). Sampel hanya {I(fd.sel_ketikan)} sel."),
    8: (f"Rekap mentah (SUM Excel) berbeda dari rekap terkoreksi: OK {P(abs(tr(rec_b, 'ok')), 2)}, scrap {P(abs(tr(rec_b, 'scrap')), 2)}, sisa {P(abs(tr(rec_b, 'sisa')), 2)} (selisih total pada log lama, {I(rec_b.selisih_ok.sum())} unit OK, {I(rec_b.selisih_sisa.sum())} unit sisa; Tabel 2.4a). "
        f"Pada log template selisihnya {P(abs(tr(rec_a, 'ok')), 2)} untuk OK, karena {I(rec_a.entri_mentah.sum() - rec_a.entri_koreksi.sum())} baris ganda. Koreksi hanya menangani kesalahan format (asumsi di definitions.md); angka salah yang lolos aturan tidak terdeteksi."),
    9: (f"Tidak selalu. Log lama: {I(cos_b.cocok)} dari {I(cos_b.pasangan)} pasangan bulan cocok ({P(cos_b.persen_cocok, 1)}), {I(cos_b.tidak_cocok)} putus. Log template: {I(cos_a.cocok)} dari {I(cos_a.pasangan)} cocok, {I(cos_a.tidak_cocok)} putus. Jumlah pasangan kecil. Pasangan putus pada log template berasal dari tingkat error yang ditanam generator; template yang sebenarnya menghitung Sisa Awal dengan rumus."),
    10: (f"Log template {D(ba.error_per_1000_after, 1)} error per 1.000 entri dibanding {D(ba.error_per_1000_before, 1)} di log lama: turun {P(ba.penurunan, 1)} (bootstrap {cip(ba.penurunan_ci_low, ba.penurunan_ci_high, 1)}), melewati target {P(ba.target_penurunan, 0)}. "
         f"Entri bermasalah {P(ba.proporsi_before, 1)} menjadi {P(ba.proporsi_after, 2)} (Fisher p {pv(ba.p_fisher)}). Log template adalah simulasi dengan asumsi generator; penurunan belum dibuktikan di lapangan."),
    11: ("Yang masih lolos pada log template: " + ", ".join(f"{r.rule_id} ({I(r.after)})" for r in rem_rows.itertuples()) + ". Baris ganda (R06) hanya ditandai kolom Cek, tidak ditolak, dan carry-over (R07) tidak dicegah validasi sel. "
         f"Kategori salah isi tersisa {D(ca_('salah isi').per_1000, 1)} per 1.000 entri; dilewati dan bypass nol. Isian yang formatnya benar tetapi nilainya salah tidak terukur karena tidak ada nilai benar untuk dibandingkan."),
    12: (f"Kolom isian operator: {I(n_in_b)} di log lama menjadi {I(n_in_a)} di template; kolom rumus terkunci bertambah dari {I(n_f_b)} menjadi {I(n_f_a)} (Batch, Sisa Awal, Sisa, Cek). Batch dan Sisa Awal tidak diketik lagi."),
    13: (f"Sebagian. Pada log lama, {I(ov_b.tp)} dari {I(ov_b.entri_ditanam)} entri berisi error tertanam terdeteksi (recall entri {P(ov_b.recall_entri, 1)}); alarm palsu {P(1 - ov_b.precision_entri, 1)} dari entri bertanda. Target recall 100% tidak tercapai. "
         f"R02 sampai R06 recall 100%; R01 hanya {I(r_('R01').tp)} dari {I(r_('R01').ditanam)} ({P(r_('R01').recall, 1)}) dengan definisi stok tersedia, sedangkan definisi literal rancangan recall {P(lit_b.recall, 0)} tetapi presisi hanya {P(lit_b.precision, 1)}. "
         f"R07: {I(g07b.tak_dapat_dideteksi)} dari {I(g07b.ditanam)} ditanam pada bulan pertama sehingga tidak mungkin terdeteksi; recall pada yang dapat dideteksi {P(g07b.recall_dapat_dideteksi, 1)}."),
    14: (f"Estimasi (estimated): sekitar {D(hs.error_tercegah_per_bulan, 0)} error tercegah per bulan x {I(hs.menit_per_error)} menit = {D(hs.jam_hemat_per_bulan, 1)} jam per bulan ({ci(hs.ci_low, hs.ci_high)}, bootstrap) pada volume {D(hs.volume_entri_per_bulan, 0)} entri per bulan. Menit per error adalah asumsi, bukan pengukuran."),
}
n_ans = len(QS)


def qchip(n, t):
    return f'<a class="qc{" w" if n in WARN else ""}" href="#sec2{n}" title="{esc(t)}">Q{n}</a>'


def block(qs):
    return "".join(f'<span id="sec2{n}"></span>' + qa(f"Q{n}", t, p, ANS[n], status="Dengan catatan" if n in WARN else "Terjawab", warn=n in WARN) for n, t, p in QS if n in qs)


def rowfmt(df, cols):
    return [[cs(v) if isinstance(v, str) else I(v) for v in r] for r in df[cols].itertuples(index=False)]


sec2 = []
n_main = sum(1 for q in QS if q[2] == "Utama"); n_sup = sum(1 for q in QS if q[2] == "Pendukung"); n_add = sum(1 for q in QS if q[2] == "Tambahan")
sec2.append(f'<div class="card"><h3>Jawaban singkat</h3><p>Semua {I(n_ans)} pertanyaan terjawab dengan angka dari data ({I(n_main)} Utama, {I(n_sup)} Pendukung, {I(n_add)} Tambahan). {I(len(WARN))} pertanyaan diberi catatan kuning '
            f'(asumsi definisi, sampel kecil, hasil simulasi, atau estimasi). Pertanyaan utama project dijawab di bagian 7. Rancangan tidak memuat hipotesis formal.</p>'
            f'<p class="how">Klik nomor pertanyaan untuk melompat. Q hijau = terjawab. Q kuning = terjawab dengan catatan.</p><div class="qchips">' + "".join(qchip(n, t) for n, t, _ in QS) + '</div></div>')
sec2.append('<h3>2.1 Error rate, kolom, dan aturan</h3><div class="card"><p>Grafik 2.1a: error per 1.000 entri menurut kategori, log lama dan template.</p>' + chart_cat + legend([(BLUE, "Log lama"), ("#188038", "Template")])
            + '<p>Tabel 2.1b: error per kategori dengan CI Poisson.</p>'
            + table(["Versi", "Kategori", "Pelanggaran", "Entri terdampak", "Per 1.000 entri", "CI 95%"], [[("Log lama" if r.version == "before" else "Template"), r.category, I(r.pelanggaran), I(r.entri_terdampak), D(r.per_1000, 1), f"{D(r.ci_low, 1)} sampai {D(r.ci_high, 1)}"] for r in cat.itertuples()])
            + '<p>Grafik 2.1c: Pareto pelanggaran per aturan, log lama (batang biru = aturan hingga 80% kumulatif).</p>' + chart_par
            + table(["Aturan", "Isi", "Kategori", "Pelanggaran", "Per 1.000 entri", "CI 95%"], [[r.rule_id, esc(rule_desc[r.rule_id]), r.category, I(r.pelanggaran), D(r.per_1000, 1), f"{D(r.ci_low, 1)} sampai {D(r.ci_high, 1)}"] for r in rule_b.itertuples()])
            + '<p>Tabel 2.1d: sensitivitas definisi R01 (rancangan literal memakai Qty Diterima saja).</p>'
            + table(["Versi", "Definisi R01", "Pelanggaran"], [[("Log lama" if r.version == "before" else "Template"), cs(r.definisi), I(r.pelanggaran)] for r in r01s.itertuples()])
            + '<p>Tabel 2.1e: pelanggaran per kolom.</p>'
            + table(["Versi", "Kolom", "Pelanggaran", "Per 1.000 entri", "Porsi"], [[("Log lama" if r.version == "before" else "Template"), r.column, I(r.pelanggaran), D(r.per_1000, 1), P(r.share, 1)] for r in col.sort_values(["version", "pelanggaran"], ascending=[True, False]).itertuples()])
            + '</div>')
sec2.append(block([1, 2, 3]))
sec2.append('<h3>2.2 Pola per shift, model, minggu, dan volume</h3><div class="card"><p>Grafik 2.2a: error per 1.000 entri per minggu, log lama.</p>' + chart_wk
            + '<p>Tabel 2.2b: proporsi entri bermasalah per kelompok, log lama (CI Wilson).</p>'
            + table(["Faktor", "Kelompok", "Entri", "Bermasalah", "Proporsi", "CI 95%"], [[r.faktor, cs(r.level), I(r.entri), I(r.bermasalah), P(r.proporsi, 1), f"{D(r.ci_low * 100, 1)}% sampai {D(r.ci_high * 100, 1)}%"] for r in pat[(pat.version == "before") & (pat.level != "(kosong)")].itertuples()])
            + '<p>Tabel 2.2c: uji chi-square dengan koreksi Holm antar empat uji (kelompok kosong tidak diuji).</p>'
            + table(["Versi", "Faktor", "Chi-square", "Derajat bebas", "p", "p Holm", "Signifikan"], [[("Log lama" if r.version == "before" else "Template"), r.faktor, D(r.chi2, 2), I(r.dof), pv(r.p), pv(r.p_holm), "ya" if r.signifikan else "tidak"] for r in ptt.itertuples()])
            + '</div>')
sec2.append(block([4, 5]))
sec2.append('<h3>2.3 Rumus ditimpa angka ketikan</h3><div class="card"><p>Tabel 2.3a: sel rumus yang berisi angka ketikan (audit openpyxl dua kali baca).</p>'
            + table(["Workbook", "Sheet", "Kolom", "Sel rumus", "Angka ketikan", "Persen", "CI 95%"], [[cs(r.workbook), r.sheet, r.column, I(r.sel_rumus), I(r.angka_ketikan), P(r.persen_ketikan, 2), f"{D(r.ci_low * 100, 2)}% sampai {D(r.ci_high * 100, 2)}%"] for r in fh.itertuples()])
            + '<p>Tabel 2.3b: selisih angka ketikan terhadap hasil rumus (log lama).</p>'
            + table(["Sel ketikan", "Sama dengan rumus", "Berbeda", "Tak terhitung", "Rata-rata selisih abs", "Median", "Maksimum", "Selisih bersih"], [[I(fd.sel_ketikan), I(fd.sama_dengan_rumus), I(fd.berbeda), I(fd.tak_terhitung), D(fd.rata_selisih_abs, 1), D(fd.median_selisih_abs, 0), D(fd.maks_selisih_abs, 0), D(fd.total_selisih_bersih, 0)]])
            + '</div>')
sec2.append(block([6, 7]))
sec2.append('<h3>2.4 Rekonsiliasi rekap dan carry-over</h3><div class="card"><p>Tabel 2.4a: rekap bulanan mentah (SUM Excel) dan terkoreksi, unit.</p>'
            + table(["Versi", "Bulan", "OK mentah", "OK terkoreksi", "Scrap mentah", "Scrap terkoreksi", "Sisa mentah", "Sisa terkoreksi"], [[("Log lama" if r.version == "before" else "Template"), r.bulan, D(r.ok_mentah, 0), D(r.ok_koreksi, 0), D(r.scrap_mentah, 0), D(r.scrap_koreksi, 0), D(r.sisa_mentah, 1), D(r.sisa_koreksi, 0)] for r in rec.itertuples()])
            + f'<p>Tabel 2.4b: sensitivitas pembulatan (desimal dibulatkan biasa, bukan ke bawah): selisih sisa log lama {D(recs[recs.version == "before"].selisih_sisa.sum(), 1)} unit dibanding {D(rec_b.selisih_sisa.sum(), 1)} unit pada dasar.</p>'
            + '<p>Tabel 2.4c: rantai carry-over antar bulan.</p>'
            + table(["Versi", "Pasangan bulan", "Cocok", "Putus", "Persen cocok"], [[("Log lama" if r.version == "before" else "Template"), I(r.pasangan), I(r.cocok), I(r.tidak_cocok), P(r.persen_cocok, 1)] for r in cos.itertuples()])
            + '</div>')
sec2.append(block([8, 9]))
sec2.append('<h3>2.5 Before-after, error tersisa, dan kolom isian</h3><div class="card"><p>Tabel 2.5a: error per 1.000 entri, before dan after.</p>'
            + table(["Ukuran", "Log lama", "Template"], [["Entri", I(ba.entri_before), I(ba.entri_after)], ["Pelanggaran", I(ba.pelanggaran_before), I(ba.pelanggaran_after)], ["Error per 1.000 entri", D(ba.error_per_1000_before, 1), D(ba.error_per_1000_after, 1)],
               ["Entri bermasalah", f"{P(ba.proporsi_before, 1)} ({cip(ba.prop_before_ci_low, ba.prop_before_ci_high, 1)})", f"{P(ba.proporsi_after, 2)} ({cip(ba.prop_after_ci_low, ba.prop_after_ci_high, 2)})"],
               ["Penurunan error", "-", f"{P(ba.penurunan, 1)} ({cip(ba.penurunan_ci_low, ba.penurunan_ci_high, 1)})"]])
            + '<p>Tabel 2.5b: pelanggaran per aturan, before dan after.</p>'
            + table(["Aturan", "Isi", "Kategori", "Log lama", "Template"], [[r.rule_id, esc(r.deskripsi), r.kategori, I(r.before), I(r.after)] for r in rbr.itertuples()])
            + '<p>Tabel 2.5c: inventaris kolom per peran.</p>' + table(["Versi", "Peran", "Jumlah kolom"], [[r.versi, r.peran, I(r.jumlah_kolom)] for r in invs.itertuples()])
            + '<p>Tabel 2.5d: estimasi jam koreksi (estimated).</p>'
            + table(["Entri per bulan", "Error tercegah per bulan", "Menit per error (asumsi)", "Jam hemat per bulan", "CI 95%", "Label"], [[D(hs.volume_entri_per_bulan, 0), D(hs.error_tercegah_per_bulan, 0), I(hs.menit_per_error), D(hs.jam_hemat_per_bulan, 1), f"{D(hs.ci_low, 1)} sampai {D(hs.ci_high, 1)}", "estimated"]])
            + '</div>')
sec2.append(block([10, 11, 12, 14]))
sec2.append('<h3>2.6 Pemulihan error tertanam (ground truth)</h3><div class="card"><p>Tabel 2.6a: recall dan precision per aturan, log lama (entri bertanda vs ground truth).</p>'
            + table(["Aturan", "Ditanam", "Terdeteksi", "TP", "FP", "Recall", "CI 95% recall", "Precision"], [[r.rule_id, I(r.ditanam), I(r.terdeteksi), I(r.tp), I(r.fp), P(r.recall, 1), f"{D(r.recall_ci_low * 100, 1)}% sampai {D(r.recall_ci_high * 100, 1)}%", P(r.precision, 1)] for r in gtr[gtr.version == "before"].itertuples()])
            + '<p>Tabel 2.6b: sensitivitas definisi R01 terhadap ground truth.</p>'
            + table(["Versi", "Definisi", "Ditanam", "Terdeteksi", "Recall", "Precision"], [[("Log lama" if r.version == "before" else "Template"), cs(r.definisi), I(r.ditanam), I(r.terdeteksi), ("-" if pd.isna(r.recall) else P(r.recall, 1)), ("-" if pd.isna(r.precision) else P(r.precision, 1))] for r in g01.itertuples()])
            + '<p>Tabel 2.6c: R07 menurut kemungkinan terdeteksi (bulan pertama tidak punya bulan sebelumnya).</p>'
            + table(["Versi", "Ditanam", "Tak dapat dideteksi", "Dapat dideteksi", "Terdeteksi", "Recall yang dapat dideteksi"], [[("Log lama" if r.version == "before" else "Template"), I(r.ditanam), I(r.tak_dapat_dideteksi), I(r.dapat_dideteksi), I(r.terdeteksi), P(r.recall_dapat_dideteksi, 1)] for r in g07.itertuples()])
            + '<p>Tabel 2.6d: ringkasan per entri.</p>'
            + table(["Versi", "Entri", "Entri bergalat tertanam", "Entri bertanda", "TP", "Recall", "Precision", "Alarm palsu (1 - precision)"], [[("Log lama" if v == "before" else "Template"), I(r.entri), I(r.entri_ditanam), I(r.entri_bertanda), I(r.tp), P(r.recall_entri, 1), P(r.precision_entri, 1), P(1 - r.precision_entri, 1)] for v, r in gto.iterrows()])
            + '</div>')
sec2.append(block([13]))
sec2.append('<h3>2.7 Cek silang dan uji template</h3><div class="card"><p>Tabel 2.7a: cek silang audit R01 sampai R07 (pandas vs loop Python, vs SQL DuckDB) dan rekap mentah (pandas vs Excel dihitung ulang LibreOffice).</p>'
            + table(["Pembanding", "Dibandingkan", "Cocok"], [[g, I(len(d)), I(d.cocok.sum())] for g, d in cx.groupby("cek")])
            + f'<p>Tabel 2.7b: uji template (instance diisi data log template, dihitung ulang LibreOffice). {I(n_tt_ok)} dari {I(n_tt)} pemeriksaan cocok penuh.</p>'
            + table(["Pemeriksaan", "Dibandingkan", "Cocok"], [[esc(r.cek), I(r.dibandingkan), I(r.cocok)] for r in tt.itertuples()])
            + '<p>Baris ABNORMAL vs R01 berbeda satu entri karena baris ganda menggeser rantai Sisa Awal; bukan kegagalan template.</p></div>')

REP = []
REP.append('<div class="callout a"><h4>Data project ini adalah simulasi</h4>Log lama dan log template dibuat generator dengan error tertanam (lihat docs/simulation_spec.md). Angka menggambarkan simulasi, bukan lini produksi. Penurunan error di log template ditentukan asumsi generator dan belum dibuktikan di lapangan.</div>')
REP.append('<h2 id="rp1">1. Data yang berhasil didapatkan<small>Isi data mentah, tabel di database, dan data hasil analisis</small></h2>')
REP.append('<div class="kpis">' + kp(I(NB), "entri log lama", "Juli sampai September 2026.", "navyH") + kp(I(NA), "entri log template", "Tiga bulan pengisian lewat template.", "tealH")
           + kp(I(len(rules)), "aturan validasi", "R01 sampai R07.", "amberH") + kp(I(int(fh_b.sel_rumus)), "sel rumus Sisa", "Log lama, diaudit dengan openpyxl.", "plumH")
           + kp(I(n_cx), "cek silang", f"{I(n_cx_ok)} cocok.", "roseH") + kp(I(n_fp_ok), "sidik jari cocok", f"Dari {I(n_fp)} berkas, dicocokkan dengan repo DataCenter.", "skyH") + '</div>')
smp = le[le.version == "before"].head(6)
cols = ["date_raw", "shift_raw", "model_raw", "ng_origin_raw", "batch_raw", "sisa_awal_raw", "qty_received_raw", "qty_ok_raw", "qty_scrap_raw", "sisa_raw"]
REP.append('<h3>1.1 Data mentah</h3><div class="card"><p>Tabel 1.1a: enam baris pertama log lama apa adanya (data simulasi; Sisa berisi rumus).</p>'
           + table(["Tanggal", "Shift", "Model", "Stasiun Asal", "Batch", "Sisa Awal", "Diterima", "OK", "Scrap", "Sisa"], [[esc(cs(v)) for v in r] for r in smp[cols].fillna("").itertuples(index=False)])
           + '<p>Tabel 1.1b: jenis isi sel per kolom, log lama (teks, angka, rumus, kosong).</p>'
           + table(["Kolom", "Jenis", "Sel"], [[r.column, r.tipe, I(r.sel)] for r in cty[cty.version == "before"].itertuples()]) + '</div>')
FILES = {
    "anomaly_log.csv": "satu baris per pelanggaran aturan", "audit_category.csv": "error per kategori", "audit_column.csv": "pelanggaran per kolom", "audit_r01_sensitivity.csv": "sensitivitas definisi R01",
    "audit_rule_counts.csv": "pelanggaran per aturan", "before_after.csv": "perbandingan before-after", "before_after_category.csv": "before-after per kategori", "carryover_summary.csv": "ringkasan rantai carry-over",
    "chain_check.csv": "pasangan bulan carry-over", "column_inventory.csv": "inventaris kolom", "column_inventory_summary.csv": "ringkasan inventaris kolom", "crosscheck.csv": "cek silang pandas, loop, SQL, Excel",
    "design_facts.csv": "lima fakta data rancangan terhadap hasil", "entry_flags.csv": "bendera aturan per entri", "formula_diff_cells.csv": "selisih tiap sel ketikan terhadap rumus",
    "formula_diff_summary.csv": "ringkasan selisih ketikan", "formula_hardcode.csv": "sel rumus berisi angka ketikan", "ground_truth_overall.csv": "recall dan precision per entri", "ground_truth_r01_sensitivity.csv": "sensitivitas R01 vs ground truth",
    "ground_truth_r07.csv": "R07 menurut kemungkinan terdeteksi", "ground_truth_recall.csv": "recall dan precision per aturan", "hours_saved.csv": "estimasi jam koreksi (estimated)", "kpi.csv": "KPI kualitas data",
    "patterns.csv": "error per shift, model, minggu, volume", "patterns_r03.csv": "R03 per shift dan minggu", "patterns_tests.csv": "uji pola chi-square dan Holm", "recap_reconcile.csv": "rekap mentah vs terkoreksi",
    "recap_reconcile_sensitivity.csv": "rekap dengan pembulatan biasa", "remaining_by_rule.csv": "pelanggaran before-after per aturan", "remaining_errors.csv": "pelanggaran tersisa di template", "template_test.csv": "uji template"}
real = sorted(p.name for p in r2.glob("*.csv"))
assert set(real) == set(FILES), ("CSV belum terdokumentasi / tidak ada:", set(real) ^ set(FILES))
nrows = {"log_entries": len(le), "formula_audit": len(rd(r1, "formula_audit.csv")), "anomaly_log": len(rd(r2, "anomaly_log.csv")), "dim_rule": len(dimr)}
REP.append('<h3>1.2 Tabel hasil</h3><div class="card"><p>Tabel 1.2a: tabel data utama (CSV; project ini tidak memakai database SQL).</p>'
           + table(["Tabel", "Baris", "Isi"], [["log_entries", I(nrows["log_entries"]), "satu baris per entri log, dua versi"], ["formula_audit", I(nrows["formula_audit"]), "sel Sisa: rumus atau angka ketikan"],
                                              ["anomaly_log", I(nrows["anomaly_log"]), "satu baris per pelanggaran"], ["dim_rule", I(nrows["dim_rule"]), "daftar aturan validasi"]])
           + f'<p>Tabel 1.2b: pemeriksaan template. {I(n_tt_ok)} dari {I(n_tt)} cocok.</p>' + table(["Pemeriksaan", "Cocok"], [[esc(r.cek), pill("lulus" if r.dibandingkan == r.cocok else "sebagian", "" if r.dibandingkan == r.cocok else "p")] for r in tt.itertuples()])
           + f'<p>Tabel 1.2c: {I(len(FILES))} file hasil analisis di results/2-analysis.</p>' + table(["File", "Isi"], [[f, FILES[f]] for f in sorted(FILES)]) + '</div>')
REP.append('<h3>1.3 Angka kunci (KPI)</h3><div class="card"><p>Tabel 1.3: lima KPI kualitas data.</p>'
           + table(["KPI", "Rumus ringkas", "Log lama", "Template"], [
               ["Error per 1.000 entri", "pelanggaran / entri x 1.000", D(kpi.loc["before", "error_per_1000"], 1), D(kpi.loc["after", "error_per_1000"], 1)],
               ["Salah isi, dilewati, bypass per 1.000", "pelanggaran per kategori / entri x 1.000", f"{D(kpi.loc['before', 'salah_isi_per_1000'], 1)}; {D(kpi.loc['before', 'dilewati_per_1000'], 1)}; {D(kpi.loc['before', 'bypass_per_1000'], 1)}", f"{D(kpi.loc['after', 'salah_isi_per_1000'], 1)}; {D(kpi.loc['after', 'dilewati_per_1000'], 1)}; {D(kpi.loc['after', 'bypass_per_1000'], 1)}"],
               ["Selisih rekap OK", "|mentah - terkoreksi| / terkoreksi", P(kpi.loc["before", "selisih_rekap_ok_persen"], 2), P(kpi.loc["after", "selisih_rekap_ok_persen"], 2)],
               ["First-time-right", "entri tanpa pelanggaran / entri", P(kpi.loc["before", "first_time_right"], 1), P(kpi.loc["after", "first_time_right"], 1)],
               ["Penurunan error", "1 - after / before", "-", P(ba.penurunan, 1)]]) + '</div>')

REP.append('<h2 id="rp2">2. Apakah business question terjawab?<small>' + f'{I(n_ans)} pertanyaan pada Design Project, dijawab dengan data' + '</small></h2>')
REP.extend(sec2)

# ---------- rp3 ----------
f1, f2, f3, f4, f5 = (fct.loc[i] for i in (1, 2, 3, 4, 5))
REP.append('<h2 id="rp3">3. Apakah dataset sesuai dengan Design Project?<small>Perbandingan rancangan dengan realisasi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 3a. Rancangan dan realisasi dataset.</p>'
           + table(["Hal", "Rancangan", "Realisasi", "Verdict"], [
               ["Sumber data", "simulasi meniru log kerja operator", "dua workbook Excel dari generator (seed tetap), dibuat ulang dan dicocokkan dengan sidik jari DataCenter", pill("Sesuai", "")],
               ["Ukuran", f"log lama dan log template masing-masing ±{I(1800)} entri", f"{I(NB)} dan {I(NA)} entri", pill("Sesuai", "")],
               ["Model dan stasiun", "4 model papan sirkuit dan 3 stasiun asal NG dengan nama papan", "kode generik PCB-A1 sampai PCB-B2 dan Stasiun SMT, AOI, ICT", pill("Sesuai + penyesuaian", "p")],
               ["Tabel", "log_entries, formula_audit, anomaly_log, dim_rule", "sama, berupa CSV (tanpa database SQL)", pill("Sesuai", "")],
               ["Kolom contoh", "qty_pending, kolom shift dan ng_origin tidak ditampilkan", "kolom log nyata: Sisa Awal, Qty Diterima, OK, Scrap, Sisa dan kolom identitas entri", pill("Sesuai + penyesuaian", "p")],
               ["Aturan R01", "OK + scrap tidak melebihi qty diterima", f"stok tersedia (Sisa Awal + Diterima) karena log punya Sisa Awal; definisi literal diuji sebagai sensitivitas ({I(lit_b.terdeteksi)} alarm pada log lama)", pill("Sesuai + penyesuaian", "p")],
               [f"Fakta 1: OK + scrap melebihi diterima", "3% entri", f"{P(f1.nilai, 2)} dengan definisi dasar; {P(f1.nilai2, 1)} dengan definisi literal; tertanam {P(r_('R01').ditanam / NB, 1)} (stok tersedia membuat sebagian tidak terdeteksi)", pill("Sebagian", "p")],
               ["Fakta 2: sel wajib kosong", "2%, terpusat di shift malam dan minggu terakhir", f"{P(f2.nilai, 2)} entri; tidak terpusat (shift p {pv(f2.nilai2)}, minggu terakhir p {pv(f2.nilai3)})", pill("Sebagian", "p")],
               ["Fakta 3: Sisa ditimpa angka", "1,5%, terpusat di bulan ke-3", f"{P(f3.nilai, 2)} entri; {P(f3.nilai2, 1)} di bulan ke-3, tidak berbeda dari porsi entri (p {pv(f3.nilai3)})", pill("Sebagian", "p")],
               ["Fakta 4: carry-over putus", "satu carry-over putus", f"{I(f4.k)} dari {I(f4.n)} pasangan bulan putus pada log lama ({P(f4.nilai, 1)}); lebih banyak dari satu", pill("Lebih besar", "")],
               ["Fakta 5: data kotor lain", "2% sampai 3%", f"{P(f5.nilai, 2)} entri bermasalah format atau duplikat (R02, R04, R06)", pill("Sesuai", "")],
               ["Sidik jari data", "tidak ada di rancangan", f"{I(n_fp_ok)} dari {I(n_fp)} berkas cocok dengan repo DataCenter", pill("Tambahan", "")],
               ["Hipotesis", "tidak ada hipotesis formal pada rancangan", "lima fakta data di atas diperlakukan sebagai klaim yang diuji", pill("Tidak berlaku", "d")]]) + '</div>')

# ---------- rp4 ----------
REP.append('<h2 id="rp4">4. Apakah tools yang digunakan sesuai?<small>Perbandingan rancangan dengan eksekusi</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 4a. Tools rancangan dan realisasi.</p>' + table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
    ["Excel", "template (Data Validation, dropdown, conditional formatting, COUNTIFS, proteksi sheet) dan sheet dashboard", f"template dibangun dengan openpyxl dan rumusnya dihitung ulang LibreOffice (bukan Excel); {I(n_tt_ok)} dari {I(n_tt)} pemeriksaan cocok; dashboard workbook dengan grafik bawaan", pill("Sesuai + penyesuaian", "p")],
    ["Python (pandas, NumPy)", "data simulasi, audit R01 sampai R07, KPI before-after", "sama; ditambah SciPy untuk uji dan CI", pill("Sesuai + tambahan", "")],
    ["openpyxl", "membaca rumus dan nilai, membuat template", "sama; nilai rumus dihitung ulang lewat LibreOffice karena openpyxl tidak menyimpan hasil rumus", pill("Sesuai", "")],
    ["Plotly", "grafik Pareto dan before-after (opsional)", "grafik memakai matplotlib dan grafik bawaan Excel; Plotly tidak dipakai", pill("Diganti matplotlib", "d")],
    ["DuckDB + SQL", "tidak dipakai (analisis SQL N/A)", f"dipakai hanya sebagai cek silang audit R01 sampai R06 ({I(len(tc('pandas vs SQL DuckDB')))} pemeriksaan)", pill("Tambahan", "")],
    ["GitHub + Markdown", "skrip, template, README", "repo dan README; branch belum di-merge", pill("Sesuai", "")]]) + '</div>')
STEPS = [("1", "Memetakan kolom log", "09_build_template.py menulis inventaris kolom (docs/column_inventory.md)", "Sesuai", ""), ("2", "Menyusun aturan validasi dan KPI", "docs/validation_rules.md", "Sesuai", ""),
         ("3", "Membuat log lama simulasi", "00_generate_log.py dan sidik jari (01)", "Sesuai", ""), ("4", "Membaca workbook dua kali", "02_read_workbook.py", "Sesuai", ""), ("5", "Merapikan tipe data", "03_clean.py", "Sesuai", ""),
         ("6", "Menjalankan audit aturan", "04, 05, 12 (ground truth)", "Sesuai", ""), ("7", "Mengaudit rumus ditimpa", "06_formula_audit.py", "Sesuai", ""), ("8", "Rekonsiliasi rekap dan carry-over", "07_reconcile.py, 08_crosscheck.py", "Sesuai + tambahan", ""),
         ("9", "Membangun template anti-bypass", "09_build_template.py dan template_lib.py", "Sesuai", ""), ("10", "Menguji template dan before-after", "10_test_template.py, 11_before_after.py", "Sesuai", ""),
         ("11", "Membuat dashboard audit", "13_build_dashboard.py (workbook dan PNG)", "Sesuai", ""), ("12", "README dan finalisasi", "14 sampai 15, build_report.py; branch belum di-merge", "Sebagian", "p")]
RENAMES = [("docs/column_inventory.md", ["project/docs/column_inventory.md"], True), ("docs/validation_rules.md", ["project/docs/validation_rules.md", "project/docs/definitions.md"], True),
           ("scripts/generate_log.py", ["project/code/1-data-preparation/python/00_generate_log.py"], True), ("data/log_before.xlsx", ["project/data/sim/log_lama.xlsx"], False),
           ("data/ground_truth.json", ["project/data/sim/ground_truth.json"], False), ("scripts/read_workbook.py", ["project/code/1-data-preparation/python/02_read_workbook.py"], True),
           ("data/README.md", ["project/data/README.md"], True),
           ("scripts/audit.py", ["project/code/audit_lib.py", "project/code/2-analysis/python/04_audit_rules.py", "project/code/2-analysis/python/06_formula_audit.py"], True),
           ("outputs/anomaly_log.csv", ["project/results/2-analysis/anomaly_log.csv"], True), ("outputs/reconciliation.csv", ["project/results/2-analysis/recap_reconcile.csv", "project/results/2-analysis/carryover_summary.csv"], True),
           ("template/Rework_Log_Template.xlsx", ["project/outputs/Rework_Log_Template.xlsx"], True), ("data/log_after.xlsx", ["project/data/sim/log_template.xlsx"], False),
           ("notebooks/analysis.ipynb", ["project/results/3-presentation/analysis.ipynb"], True), ("outputs/Audit_Dashboard.xlsx", ["project/outputs/Audit_Dashboard.xlsx"], True),
           ("requirements.txt", ["project/requirements.txt"], True), ("README.md", ["README.md"], True), ("index.html", ["design-and-report/index.html"], True), ("slides/presentation.pdf", [], True)]
for _, dest, committed in RENAMES:
    for d in dest:
        assert (REPO / d).exists() or d.endswith("index.html") or not committed, d
rn_rows = [[a, "(tidak dibuat)" if not dest else ", ".join(dest) + ("" if committed else " (tidak di-commit)")] for a, dest, committed in RENAMES]
REP.append('<h2 id="rp5">5. Apakah alur pengerjaan sesuai dengan Design Project?<small>' + f'{I(12)} langkah rancangan vs yang dijalankan' + '</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 5a. Dua belas langkah rancangan dan yang dijalankan.</p>' + table(["No", "Langkah rancangan", "Realisasi", "Verdict"], [[n, t, r, pill(v, k)] for n, t, r, v, k in STEPS])
           + '<p>Tabel 5b: penyesuaian dan improvisasi yang tidak ada di rancangan.</p>' + table(["Penyesuaian", "Alasan"], [
               ["Data simulasi dari repo DataCenter", "data dibuat ulang dari generator dan diverifikasi dengan sidik jari SHA-256"],
               ["R01 memakai stok tersedia", "rancangan menyebut qty diterima saja; log punya Sisa Awal; definisi literal diuji sebagai sensitivitas"],
               ["Rekap terkoreksi", "rancangan tidak mendefinisikan koreksi; aturan di docs/definitions.md berlabel asumsi, sensitivitas pembulatan diuji"],
               ["Minggu terakhir bulan, kelompok volume, menit per error, alarm palsu", "tidak ada di rancangan; semuanya asumsi di docs/definitions.md"],
               ["Saldo awal di sheet Master template", "entri pertama tiap model dan stasiun butuh stok awal; tanpa itu 0 dan banyak ABNORMAL palsu"],
               ["Cek silang SQL DuckDB", "tambahan; rancangan tidak memakai SQL"],
               ["Uji pemulihan ground truth termasuk lima fakta rancangan", "validasi tambahan (12_ground_truth_check.py)"]])
           + '<p>Tabel 5c: perubahan nama dan lokasi file terhadap rancangan.</p>' + table(["Rancangan", "Realisasi"], rn_rows) + '</div>')
docs_list = [(a, d[0] if d else "", c) for a, d, c in RENAMES if a != "index.html"]


def doc_status(a, committed, path):
    if not path:
        return pill("Tidak dibuat", "d")
    if not committed:
        return pill("Tidak di-commit", "d")
    return pill("Ada", "") if (REPO / path).exists() else pill("Belum ada", "d")


REP.append('<h2 id="rp6">6. Apakah project output tercapai?<small>Output pada Design Project, bagian 7</small></h2>')
REP.append('<div class="card"><p class="how">Tabel 6a. Status output rancangan.</p>' + table(["Output", "Label", "Status", "Bukti"], [
    ["Template Excel anti-bypass", "Utama", pill("Tercapai", ""), f"project/outputs/Rework_Log_Template.xlsx; {I(n_tt_ok)} dari {I(n_tt)} pemeriksaan cocok; validasi tidak menghalangi salin-tempel"],
    ["Dashboard audit", "Utama", pill("Sebagian", "p"), "Audit_Dashboard.xlsx dan audit_summary.png; belum diuji ke pembaca awam; tren mingguan hanya log lama"],
    ["Skrip audit kualitas data", "Utama", pill("Tercapai", ""), "audit_lib.py dan 04_audit_rules.py; recall tidak 100%"],
    ["Aplikasi pembuat data simulasi", "Utama", pill("Tercapai", ""), "00_generate_log.py, seed tetap"],
    ["Notebook analisis", "Utama", pill("Tercapai", ""), "results/3-presentation/analysis.ipynb"],
    ["Laporan temuan dan rekomendasi", "Utama", pill("Tercapai", ""), "README dan Report"],
    ["Repositori GitHub", "Utama", pill("Sebagian", "p"), "branch belum di-merge ke main"],
    ["Slide presentasi", "Opsional", pill("Tidak dibuat", "d"), "-"]])
    + '<p>Tabel 6b: daftar dokumen rancangan dan status pada repositori.</p>' + table(["Dokumen", "Status"], [[a, doc_status(a, c, p)] for a, p, c in docs_list]) + '</div>')

crit = [("Kesembilan pertanyaan Utama terjawab dengan angka", "Terpenuhi", f"{I(n_main)} dari {I(n_main)} terjawab; beberapa dengan catatan asumsi"),
        ("Recall 100% dan alarm palsu di bawah 5%", "Tidak terpenuhi", f"recall entri {P(ov_b.recall_entri, 1)}; alarm palsu {P(1 - ov_b.precision_entri, 1)} (terpenuhi)"),
        ("Error per 1.000 entri turun minimal 70% dan semua bypass tercegah", "Terpenuhi", f"turun {P(ba.penurunan, 1)}; bypass di template {I(ca_('bypass').pelanggaran)}; hasil simulasi"),
        ("Rekap template sama persis dengan hitungan ulang Python, termasuk carry-over", "Terpenuhi", f"{I(n_tt_ok)} dari {I(n_tt)} pemeriksaan template cocok (Batch, Sisa Awal, Sisa, Cek, Rekap)"),
        ("Orang awam menyebut jenis error terbesar dari dashboard dalam 1 menit", "Belum diuji", "belum ada uji dengan pembaca awam"),
        ("Checklist standar terpenuhi", "Sebagian", "SQL N/A; branch belum di-merge ke main")]
n_ok_crit = sum(1 for c in crit if c[1] == "Terpenuhi")
REP.append('<h2 id="rp7">7. Kesimpulan<small>Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan</small></h2>')
REP.append('<h4>7.1 Hasil analisis</h4><div class="card"><p><b>Pertanyaan utama:</b> seberapa sering data input operator salah, dikosongkan, atau menimpa rumus, dan berapa banyak error yang bisa dicegah oleh template anti-bypass?</p>'
           f'<p>Log lama punya {D(tot_b.per_1000, 1)} pelanggaran per 1.000 entri: salah isi {D(cb("salah isi").per_1000, 1)}, dilewati {D(cb("dilewati").per_1000, 1)}, bypass rumus {D(cb("bypass").per_1000, 1)}. Aturan yang paling sering dilanggar adalah {top_rule.rule_id} (kolom wajib kosong) dan kolom {top_col.column} paling bermasalah. '
           f'Error tersebar merata: tidak ada pola signifikan menurut shift, model, minggu terakhir, atau volume harian. {I(fh_b.angka_ketikan)} dari {I(fh_b.sel_rumus)} sel Sisa ({P(fh_b.persen_ketikan, 2)}) ditimpa angka, dan rekap OK mentah menyimpang {P(abs(tr(rec_b, "ok")), 2)} dari rekap terkoreksi. '
           f'Template menurunkan error menjadi {D(ba.error_per_1000_after, 1)} per 1.000 entri (turun {P(ba.penurunan, 1)}) pada simulasi, dengan sisa {rem_rows.rule_id.str.cat(sep=" dan ")}. Skrip audit menemukan {P(ov_b.recall_entri, 1)} entri bergalat tertanam; kelemahan utama R01 dan R07 bulan pertama.</p></div>')
REP.append('<h4>7.2 Impact</h4><div class="card">' f'<p>Estimasi (estimated): sekitar {D(hs.error_tercegah_per_bulan, 0)} error tercegah per bulan, setara {D(hs.jam_hemat_per_bulan, 1)} jam koreksi per bulan ({ci(hs.ci_low, hs.ci_high)}) dengan asumsi {I(hs.menit_per_error)} menit per error. '
           'Angka bergantung pada asumsi menit dan pada generator, bukan pengukuran di lapangan.</p><p>Nilai praktis: template yang menutup bypass rumus dan menurunkan koreksi manual. Nilai analitis: audit aturan yang bisa dijalankan ulang dan diuji dengan ground truth. Nilai portofolio: dari audit sampai template terkunci. Belum terukur: dampak nyata di lini dan dalam rupiah.</p></div>')
REP.append('<h4>7.3 Success criteria</h4><div class="card">' + table(["Kriteria", "Status", "Bukti"], [[k, pill(s, "" if s == "Terpenuhi" else ("p" if s in ("Sebagian", "Belum diuji") else "d")), cs(b)] for k, s, b in crit]) + f'<p>Hasil: {I(n_ok_crit)} dari {I(len(crit))} kriteria tercapai.</p></div>')
REP.append('<h4>7.4 Rekomendasi</h4><div class="card"><ul class="tight">'
           f'<li>Pakai template dan aktifkan proteksi struktur workbook secara manual; wajibkan kolom Cek dibaca tiap akhir shift karena salin-tempel dapat melewati validasi.</li>'
           f'<li>Jalankan audit bulanan pada log yang masih dipakai, mulai dari kolom wajib kosong ({top_rule.rule_id}) dan sel Sisa yang ditimpa.</li>'
           '<li>Tinjau definisi R01 bersama pemilik proses (stok tersedia atau qty diterima) sebelum audit dipakai untuk menilai operator.</li>'
           '<li>Cek carry-over antar bulan dengan saldo awal yang disahkan supervisor.</li></ul></div>')
REP.append('<h4>7.5 Saran perbaikan</h4><div class="card"><ul class="tight">'
           '<li>Uji template satu bulan di lini nyata sebelum mengklaim penurunan error.</li><li>Tambahkan aturan rentang wajar (misal OK harian terhadap rata-rata) untuk menangkap angka benar-format tetapi salah.</li>'
           '<li>Bangun kunci duplikat yang menolak entri, bukan hanya menandai.</li><li>Uji dashboard dengan pembaca awam dan perluas tren mingguan ke log template.</li></ul></div>')
REP.append('<h4>7.6 Batasan</h4><div class="card"><ul class="tight">'
           f'<li><b>Data adalah simulasi;</b> angka menggambarkan simulasi, bukan lini produksi. Dari {I(ov_b.entri_ditanam)} entri bergalat tertanam di log lama, {I(ov_b.tp)} terdeteksi (recall {P(ov_b.recall_entri, 1)}), alarm palsu {P(1 - ov_b.precision_entri, 1)}.</li>'
           '<li>Penurunan error di log template ditentukan asumsi generator; hasil after juga simulasi dan belum diuji di lapangan.</li>'
           f'<li>Definisi dan batas buatan sendiri (asumsi): R01 stok tersedia, minggu terakhir 7 hari, tercile volume, rekap terkoreksi, {I(hs.menit_per_error)} menit per error, definisi alarm palsu.</li>'
           f'<li>Fakta data pada rancangan hanya sebagian sesuai: error tersebar merata, bukan terpusat; R07 bulan pertama tidak terdeteksi; R01 recall {P(r_("R01").recall, 1)} dengan definisi dasar.</li>'
           f'<li>Sampel kecil: {I(fd.sel_ketikan)} sel ketikan, {I(cos_b.pasangan)} pasangan carry-over, {I(tot_a.pelanggaran)} pelanggaran di template.</li>'
           '<li>Proteksi sheet bukan keamanan penuh; validasi tidak menghalangi salin-tempel; template dihitung ulang LibreOffice dan perlu dibuka di Excel untuk uji akhir; proteksi struktur workbook manual.</li>'
           '<li>Dashboard Excel belum diuji ke pembaca awam; slide presentasi tidak dibuat; branch belum di-merge ke main.</li>'
           '<li>Isian yang formatnya benar tetapi nilainya salah tidak terukur. Pola belum tentu penyebab.</li></ul></div>')

REPORT_PANE = ('<div class="pane" id="report" data-tab="report" hidden>\n<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Cek silang: {I(n_cx_ok)} dari {I(n_cx)} cocok (pandas, loop Python, SQL, Excel); uji template {I(n_tt_ok)} dari {I(n_tt)}. Angka diaudit dari CSV hasil. <b>Data pada project ini adalah simulasi.</b></div>\n'
               + '<div class="card"><p class="how">Ringkasan tujuh pertanyaan evaluasi. Klik untuk melompat ke bagian.</p>' + table(["No", "Pertanyaan evaluasi", "Verdict", "Ringkasan"], [
                   [f'<span class="en">{i}</span>', f'<a href="#rp{i}">{t}</a>', pill(v[0], v[1]), v[2]] for i, (t, v) in enumerate([
                       ("Data yang berhasil didapatkan", ("Berhasil", "", f"{I(NB)} dan {I(NA)} entri log")),
                       ("Apakah business question terjawab?", ("Sesuai", "", f"{I(n_ans)} dari {I(n_ans)} terjawab, {I(len(WARN))} dengan catatan")),
                       ("Apakah dataset sesuai dengan Design Project?", ("Sebagian", "p", "lima fakta data hanya sebagian sesuai")),
                       ("Apakah tools yang digunakan sesuai?", ("Sesuai + penyesuaian", "p", "LibreOffice menghitung rumus, Plotly diganti")),
                       ("Apakah alur pengerjaan sesuai dengan Design Project?", ("Sesuai + tambahan", "", "dua belas langkah dijalankan")),
                       ("Apakah project output tercapai?", ("Sebagian", "p", "slide tidak dibuat")),
                       ("Kesimpulan", ("Simulasi", "", f"error turun {P(ba.penurunan, 1)} pada simulasi"))], 1)]) + '</div>\n' + "\n".join(REP) + '\n</div>\n')

nav_src = SRC[SRC.index('<nav aria-label="Project navigation">'):SRC.index('</nav>') + 6]
btn_design = re.search(r'<button[^>]*data-t="design"[^>]*>.*?</button>', nav_src, re.S).group(0)
btn_report = re.search(r'<button[^>]*data-t="report"[^>]*>.*?</button>', nav_src, re.S).group(0)
links_design = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_src, re.S).group(0)
new_report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + '</div>')
nav_new = '<nav aria-label="Project navigation">' + btn_design + btn_report + links_design + new_report_links + '</nav>'
design_pane = SRC[SRC.index('<header class="banner">'):SRC.index('<div class="pane" id="report"')]
head_end = SRC.index('</style>'); body_start = SRC.index('<body>')
hub_link = SRC[body_start:SRC.index('<main>')]
html = SRC[:head_end] + CSS_EXTRA + "\n" + SRC[head_end:body_start] + hub_link + '<main>\n' + nav_new + '\n' + design_pane + REPORT_PANE + SRC[SRC.index('</main>'):]
assert design_pane in html, "pane Design berubah"

STATIC = {str(i) for i in range(0, 41)} | {"2026", "50", "60", "80", "100", "0,05", "1,5", "3,0", "2,5", "1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "7.1", "7.2", "7.3", "7.4", "7.5", "7.6",
                                           "01", "03", "04", "05", "06", "07", "08", "09", "00", "02", "10", "1.000", "1.800", "3a", "3b", "75", "85", "95", "1,0", "0,0"}
n_tok, bad = audit(REPORT_PANE, STATIC)
print(f"token angka diperiksa: {n_tok}; tidak terdaftar: {len(bad)}")
if bad:
    vt = R.visible_text(REPORT_PANE)
    print("TIDAK TERDAFTAR:", bad[:80])
    for t in bad[:40]:
        m = re.search(r"(?<![\d.,])" + re.escape(t) + r"(?![\d,])", vt)
        if m:
            print("  ", t, "|", vt[max(0, m.start() - 60):m.end() + 30].replace("\n", " "))
    raise SystemExit("audit gagal: ada angka yang tidak berasal dari data")
out = HERE.parent / "index.html"
out.write_text(html, encoding="utf-8")
print("written", out, len(html))
