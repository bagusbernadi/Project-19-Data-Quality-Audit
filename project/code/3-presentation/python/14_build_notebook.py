"""14: Notebook analisis Q1-Q14 (analysis.ipynb), dieksekusi tanpa error. Membaca CSV hasil, tidak menghitung ulang."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import nbformat as nbf
from nbclient import NotebookClient
import common as CM

nb = nbf.v4.new_notebook()
md = lambda t: nbf.v4.new_markdown_cell(t)
code = lambda t: nbf.v4.new_code_cell(t)
R = "from pathlib import Path\nimport pandas as pd\nR2 = Path('..') / '2-analysis'\nR1 = Path('..') / '1-data-preparation'\nrd = lambda n, d=R2: pd.read_csv(d / n)\n"
cells = [md("# Project 19: Data Quality Audit & Anti-Bypass Template\nData simulasi. Notebook membaca CSV hasil pipeline (`results/`); angka tidak dihitung ulang di sini."), code(R)]
SEC = [
    ("Q1 sampai Q3: error per kategori, kolom, aturan", ["audit_category.csv", "audit_column.csv", "audit_rule_counts.csv"]),
    ("Q4 dan Q5: pola per shift, model, minggu, volume", ["patterns.csv", "patterns_tests.csv", "patterns_r03.csv"]),
    ("Q6 dan Q7: rumus ditimpa angka ketikan", ["formula_hardcode.csv", "formula_diff_summary.csv"]),
    ("Q8 dan Q9: rekonsiliasi rekap dan carry-over", ["recap_reconcile.csv", "recap_reconcile_sensitivity.csv", "carryover_summary.csv"]),
    ("Q10, Q11, Q14: before-after, error tersisa, jam koreksi (estimated)", ["before_after.csv", "before_after_category.csv", "remaining_by_rule.csv", "hours_saved.csv", "kpi.csv"]),
    ("Q12: inventaris kolom", ["column_inventory_summary.csv"]),
    ("Q13: recall dan precision terhadap ground truth", ["ground_truth_recall.csv", "ground_truth_r01_sensitivity.csv", "ground_truth_r07.csv", "ground_truth_overall.csv", "design_facts.csv"]),
    ("Cek silang dan uji template", ["crosscheck.csv", "template_test.csv"]),
]
for t, files in SEC:
    cells.append(md(f"## {t}"))
    for f in files:
        cells.append(code(f"print('{f}'); display(rd('{f}'))"))
cells.append(md("Pareto pelanggaran per aturan (log lama)"))
cells.append(code("import matplotlib.pyplot as plt\nd = rd('audit_rule_counts.csv'); d = d[d.version == 'before'].sort_values('pelanggaran', ascending=False)\nplt.bar(d.rule_id, d.pelanggaran); plt.ylabel('pelanggaran'); plt.show()"))
nb.cells = cells
out = CM.RES3 / "analysis.ipynb"
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(CM.RES3)}}).execute()
nbf.write(nb, out)
print("notebook ditulis", out)
