"""Pembangun template Rework_Log_Template.xlsx (anti-bypass). Dipakai 09 (template kosong) dan 10 (instance uji diisi data)."""
import datetime as dt

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

import common as CM

N_ROWS = 2000
FIRST, LAST = 2, N_ROWS + 1
# kolom: A Tanggal, B Shift, C Model, D Stasiun (input) | E Batch (rumus) | F Sisa Awal (rumus) | G Diterima, H OK, I Scrap (input) | J Sisa (rumus) | K Cek (rumus)
LAYOUT = [("Tanggal", "input"), ("Shift", "input"), ("Model", "input"), ("Stasiun Asal", "input"), ("Batch", "rumus"), ("Sisa Awal", "rumus"),
          ("Qty Diterima", "input"), ("Qty OK", "input"), ("Qty Scrap", "input"), ("Sisa", "rumus"), ("Cek", "rumus")]
INPUT_HDR = [h for h, t in LAYOUT if t == "input"]
FORMULA_HDR = [h for h, t in LAYOUT if t == "rumus"]
MONTHS = [(dt.date(2026, 7, 1), dt.date(2026, 8, 1)), (dt.date(2026, 8, 1), dt.date(2026, 9, 1)), (dt.date(2026, 9, 1), dt.date(2026, 10, 1))]


def build(path, rows=None, opening=None):
    """rows: DataFrame/iterable berkolom date, shift, model, ng_origin, qty_received, qty_ok, qty_scrap (instance uji)."""
    wb = Workbook()
    info = wb.active; info.title = "Petunjuk"
    for i, t in enumerate([
        "Rework Log Template (Project 19, data simulasi)",
        "Isi hanya sel putih bergaris biru (Tanggal, Shift, Model, Stasiun Asal, Qty Diterima, Qty OK, Qty Scrap). Sel abu-abu adalah rumus dan terkunci.",
        "Batch, Sisa Awal, Sisa dihitung otomatis. Sisa Awal = Sisa terakhir model dan stasiun yang sama (saldo awal di sheet Master bila belum ada).",
        "Kolom Cek: ABNORMAL bila OK + Scrap melebihi Sisa Awal + Diterima; DUPLIKAT bila kunci tanggal, shift, model, stasiun sama; LENGKAPI bila ada isian wajib kosong.",
        "Dropdown dan validasi angka (bilangan bulat >= 0) memblokir ketikan langsung. Salin-tempel dapat melewati validasi, jadi kolom Cek tetap dipantau.",
        f"Proteksi sheet berkata sandi '{CM.TEMPLATE_PASSWORD}' mencegah timpa tidak sengaja, bukan keamanan penuh. Admin: Review > Unprotect Sheet.",
        "Menambah kategori atau mengisi saldo awal bulan pertama: ubah sheet Master (admin). Proteksi struktur workbook diaktifkan manual lewat Review > Protect Workbook."], 1):
        info.cell(i, 1, t).font = Font(bold=(i == 1), size=14 if i == 1 else 11)
    info.column_dimensions["A"].width = 130
    m = wb.create_sheet("Master")
    for c, (h, vals) in enumerate([("Shift", CM.SHIFTS), ("Model", CM.MODELS), ("Stasiun Asal", CM.STATIONS)], 1):
        m.cell(1, c, h).font = Font(bold=True)
        for r, v in enumerate(vals, 2):
            m.cell(r, c, v)
    for nm, col, n in (("ListShift", "A", len(CM.SHIFTS)), ("ListModel", "B", len(CM.MODELS)), ("ListStasiun", "C", len(CM.STATIONS))):
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"Master!${col}$2:${col}${n + 1}")
    for c, h in enumerate(["Model", "Stasiun Asal", "Saldo awal"], 5):
        m.cell(1, c, h).font = Font(bold=True)
    for i, (mdl, stn) in enumerate([(a, b) for a in CM.MODELS for b in CM.STATIONS], 2):
        m.cell(i, 5, mdl); m.cell(i, 6, stn); m.cell(i, 7, (opening or {}).get((mdl, stn), 0))
    m.protection.sheet = True; m.protection.password = CM.TEMPLATE_PASSWORD

    ws = wb.create_sheet("Log", 1)
    side = Side(style="thin", color="9AA0A6")
    hdr_fill = PatternFill("solid", fgColor="1A73E8"); in_fill = PatternFill("solid", fgColor="FFFFFF"); f_fill = PatternFill("solid", fgColor="E8EAED")
    for c, (h, t) in enumerate(LAYOUT, 1):
        x = ws.cell(1, c, h); x.font = Font(bold=True, color="FFFFFF"); x.fill = hdr_fill; x.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.freeze_panes = "A2"
    for r in range(FIRST, LAST + 1):
        ws[f"E{r}"] = f'=IF(A{r}="","","B"&TEXT(COUNT($A${FIRST}:A{r}),"00000"))'
        ws[f"F{r}"] = f'=IF(OR(C{r}="",D{r}=""),"",IFERROR(LOOKUP(2,1/(($C$1:C{r - 1}=C{r})*($D$1:D{r - 1}=D{r})*ISNUMBER($J$1:J{r - 1})),$J$1:J{r - 1}),SUMIFS(Master!$G$2:$G$13,Master!$E$2:$E$13,C{r},Master!$F$2:$F$13,D{r})))'
        ws[f"J{r}"] = f'=IF(OR(F{r}="",COUNT(G{r}:I{r})<3),"",F{r}+G{r}-H{r}-I{r})'
        ws[f"K{r}"] = (f'=IF(COUNTA(A{r}:D{r},G{r}:I{r})=0,"",IF(COUNTA(A{r}:D{r},G{r}:I{r})<7,"LENGKAPI",'
                       f'IF(H{r}+I{r}>N(F{r})+G{r},"ABNORMAL",IF(COUNTIFS($A${FIRST}:$A${LAST},A{r},$B${FIRST}:$B${LAST},B{r},$C${FIRST}:$C${LAST},C{r},$D${FIRST}:$D${LAST},D{r})>1,"DUPLIKAT","OK"))))')
        for c, (h, t) in enumerate(LAYOUT, 1):
            x = ws.cell(r, c)
            x.border = Border(left=side, right=side, top=side, bottom=side)
            x.fill = in_fill if t == "input" else f_fill
            x.protection = Protection(locked=(t != "input"))
        ws[f"A{r}"].number_format = "yyyy-mm-dd"
    rng = lambda col: f"{col}{FIRST}:{col}{LAST}"
    dv_date = DataValidation(type="date", operator="between", formula1="DATE(2026,7,1)", formula2="DATE(2026,9,30)", allow_blank=True, showErrorMessage=True,
                             errorTitle="Tanggal", error="Tanggal harus 2026-07-01 sampai 2026-09-30.")
    dvs = [dv_date]; dv_date.add(rng("A"))
    for nm, col in (("ListShift", "B"), ("ListModel", "C"), ("ListStasiun", "D")):
        d = DataValidation(type="list", formula1=f"={nm}", allow_blank=True, showErrorMessage=True, errorTitle="Pilihan", error="Pilih dari daftar."); d.add(rng(col)); dvs.append(d)
    d = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True, showErrorMessage=True, errorTitle="Angka", error="Isi bilangan bulat >= 0."); d.add(rng("G")); dvs.append(d)
    d = DataValidation(type="custom", formula1=f"=AND(ISNUMBER(H{FIRST}),H{FIRST}>=0,H{FIRST}=INT(H{FIRST}),H{FIRST}+N(I{FIRST})<=N(F{FIRST})+N(G{FIRST}))", allow_blank=True, showErrorMessage=True,
                       errorTitle="Qty OK", error="Bilangan bulat >= 0 dan OK + Scrap tidak boleh melebihi Sisa Awal + Diterima."); d.add(rng("H")); dvs.append(d)
    d = DataValidation(type="custom", formula1=f"=AND(ISNUMBER(I{FIRST}),I{FIRST}>=0,I{FIRST}=INT(I{FIRST}),N(H{FIRST})+I{FIRST}<=N(F{FIRST})+N(G{FIRST}))", allow_blank=True, showErrorMessage=True,
                       errorTitle="Qty Scrap", error="Bilangan bulat >= 0 dan OK + Scrap tidak boleh melebihi Sisa Awal + Diterima."); d.add(rng("I")); dvs.append(d)
    for d in dvs:
        ws.add_data_validation(d)
    ws.conditional_formatting.add(rng("K"), FormulaRule(formula=[f'K{FIRST}<>"OK"*(K{FIRST}<>"")'][:0] or [f'AND(K{FIRST}<>"",K{FIRST}<>"OK")'], fill=PatternFill("solid", bgColor="F4B6B0", fgColor="F4B6B0"), font=Font(bold=True, color="B3261E")))
    ws.protection.sheet = True; ws.protection.password = CM.TEMPLATE_PASSWORD
    ws.protection.formatColumns = False; ws.protection.formatRows = False; ws.protection.sort = True; ws.protection.autoFilter = False

    rk = wb.create_sheet("Rekap")
    for c, h in enumerate(["Bulan", "Model", "Jumlah entri", "Qty Diterima", "Qty OK", "Qty Scrap", "Entri bertanda (bukan OK)"], 1):
        x = rk.cell(1, c, h); x.font = Font(bold=True, color="FFFFFF"); x.fill = hdr_fill; rk.column_dimensions[get_column_letter(c)].width = 22
    r = 2
    for a, b in MONTHS:
        for mdl in CM.MODELS:
            rk.cell(r, 1, a.strftime("%Y-%m")); rk.cell(r, 2, mdl)
            cond = f'Log!$A${FIRST}:$A${LAST},">="&DATE({a.year},{a.month},1),Log!$A${FIRST}:$A${LAST},"<"&DATE({b.year},{b.month},1),Log!$C${FIRST}:$C${LAST},$B{r}'
            rk.cell(r, 3, f"=COUNTIFS({cond})")
            for c, col in ((4, "G"), (5, "H"), (6, "I")):
                rk.cell(r, c, f"=SUMIFS(Log!${col}${FIRST}:${col}${LAST},{cond})")
            rk.cell(r, 7, f'=COUNTIFS({cond},Log!$K${FIRST}:$K${LAST},"<>OK",Log!$K${FIRST}:$K${LAST},"<>")')
            r += 1
    rk.protection.sheet = True; rk.protection.password = CM.TEMPLATE_PASSWORD
    if rows is not None:
        for i, t in enumerate(rows.itertuples(index=False), FIRST):
            ws[f"A{i}"] = t.date; ws[f"B{i}"] = t.shift; ws[f"C{i}"] = t.model; ws[f"D{i}"] = t.ng_origin
            ws[f"G{i}"] = t.qty_received; ws[f"H{i}"] = t.qty_ok; ws[f"I{i}"] = t.qty_scrap
    wb.save(path)
    return path
