"""
Table 1 — Baseline characteristics by malnutrition status.
Outputs:
  outputs/tables/table1.csv
  outputs/tables/table1.html
"""

import pickle
from pathlib import Path
from tableone import TableOne

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

with open(PROCESSED / "df_clean.pkl", "rb") as f:
    df = pickle.load(f)

# ── Columns to include ────────────────────────────────────────────────────────
continuous = ["age", "los_acute", "los_hospital"]

categorical = [
    "sex",
    "uresidence",
    "ptype",
    "e_dadmit",
    "ward",
    "walk",
    "cogstat",
    "bonemed",
    "ftype",
    "afracture",
    "asa",
    "delay",
    "anaesth",
    "surg",
    "wbear",
    "mobil",
    "pulcers",
    "gerimed",
    "passess",
    "wdest",
    "dresidence",
    "mort30d",
    "mort90d",
    "mort120d",
    "mort365d",
]

columns = continuous + categorical

# ── Rename for display ────────────────────────────────────────────────────────
rename = {
    "age":          "Age (years)",
    "los_acute":    "LOS — acute ward (days)",
    "los_hospital": "LOS — hospital (days)",
    "sex":          "Sex",
    "uresidence":   "Usual residence",
    "ptype":        "Patient type",
    "e_dadmit":     "ED admission type",
    "ward":         "Ward type",
    "walk":         "Pre-admission walking ability",
    "cogstat":      "Cognitive status",
    "bonemed":      "Bone protection medication (admission)",
    "ftype":        "Fracture type",
    "afracture":    "Atypical fracture",
    "asa":          "ASA grade",
    "delay":        "Surgery delay",
    "anaesth":      "Anaesthesia type",
    "surg":         "Surgical repair",
    "wbear":        "Post-op weight bearing",
    "mobil":        "Day 1 mobilisation",
    "pulcers":      "New pressure injuries",
    "gerimed":      "Geriatric medicine assessment",
    "passess":      "Pre-op medical assessment",
    "wdest":        "Discharge destination (acute ward)",
    "dresidence":   "Discharge place of residence",
    "mort30d":      "30-day mortality",
    "mort90d":      "90-day mortality",
    "mort120d":     "120-day mortality",
    "mort365d":     "365-day mortality",
}

# ── Non-normal continuous variables (use median [IQR]) ────────────────────────
nonnormal = ["age", "los_acute", "los_hospital"]

# ── Build table ───────────────────────────────────────────────────────────────
t1 = TableOne(
    df,
    columns=columns,
    categorical=categorical,
    groupby="malnutrition",
    nonnormal=nonnormal,
    rename=rename,
    pval=True,
    missing=True,
    label_suffix=False,
    order={"malnutrition": ["Malnourished", "Not malnourished"]},
)

print(t1.tabulate(tablefmt="simple"))

# ── Save ──────────────────────────────────────────────────────────────────────
t1.to_csv(TABLES / "table1.csv")
t1.to_html(TABLES / "table1.html")

print(f"\nSaved to outputs/tables/")
print("  table1.csv")
print("  table1.html")
