"""
Clean the ANZHFR dataset for the malnutrition-outcomes analysis.

Decisions made:
  - malnutrition == 1 ("Not done") treated as missing — not the same as assessed & not malnourished
  - Year outliers 2009 and 2025 dropped (likely data entry errors; n=6)
  - LOS capped at 365 days (2 extreme values >5000 days are implausible)
  - Retain only columns relevant to the analysis + key confounders
  - Rows missing mort30d are retained but flagged

Outputs:
  data/processed/df_clean.pkl   — analysis-ready DataFrame
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

# ── value label maps (from data dictionary) ──────────────────────────────────
LABELS = {
    "sex":          {1: "Male", 2: "Female", 3: "Intersex/indeterminate"},
    "ptype":        {1: "Public", 2: "Private", 3: "Overseas"},
    "uresidence":   {1: "Private residence", 2: "Aged care facility", 3: "Other"},
    "ward":         {1: "Orthopaedic/preferred", 2: "Outlying", 3: "HDU/ICU/CCU"},
    "walk":         {1: "No aids", 2: "Stick/crutch", 3: "Two aids/frame", 4: "Wheelchair/bed bound"},
    "cogstat":      {1: "Normal cognition", 2: "Impaired/dementia"},
    "bonemed":      {1: "None", 2: "Calcium/vitamin D", 3: "Anti-resorptive"},
    "ftype":        {1: "Intracapsular undisplaced", 2: "Intracapsular displaced",
                     3: "Per/intertrochanteric", 4: "Subtrochanteric"},
    "asa":          {1: "ASA 1", 2: "ASA 2", 3: "ASA 3", 4: "ASA 4", 5: "ASA 5"},
    "delay":        {1: "No delay (<48h)", 2: "Medically unfit", 3: "Anticoagulation",
                     4: "Theatre availability", 5: "Surgeon availability",
                     6: "Delayed diagnosis", 7: "Other"},
    "anaesth":      {1: "General", 2: "Spinal", 3: "General+spinal",
                     4: "Spinal/regional", 5: "General+spinal/regional", 6: "Other"},
    "malnutrition": {1: "Not assessed", 2: "Malnourished", 3: "Not malnourished"},
    "wdest":        {1: "Private residence", 2: "Aged care facility",
                     3: "Rehab (public)", 4: "Rehab (private)",
                     5: "Other hospital/ward", 6: "Deceased",
                     7: "Short-term care (NZ)", 8: "Other"},
    "dresidence":   {1: "Private residence", 2: "Aged care facility", 3: "Deceased", 4: "Other"},
    "mort30d":      {1: "Alive", 2: "Deceased"},
    "mort90d":      {1: "Alive", 2: "Deceased"},
    "mort120d":     {1: "Alive", 2: "Deceased"},
    "mort365d":     {1: "Alive", 2: "Deceased"},
    "surg":         {1: "No", 2: "Yes", 3: "Not indicated", 4: "Palliation", 5: "Other reason"},
    "gerimed":      {0: "No", 1: "Yes", 8: "No service available", 9: "Not known"},
    "wbear":        {1: "Unrestricted", 2: "Restricted/non weight bearing"},
    "mobil":        {1: "Mobilised day 1", 2: "Not mobilised day 1"},
    "passess":      {1: "None", 2: "Geriatrician", 3: "Physician", 4: "GP", 5: "Specialist nurse"},
    "e_dadmit":     {1: "ED", 2: "Transfer via ED", 3: "In-patient fall", 4: "Transfer direct to ward"},
}

KEEP_COLS = [
    # identifiers / dates
    "ahos_code", "arrdate_year",
    # demographics
    "age", "sex", "ptype", "uresidence",
    # admission
    "e_dadmit", "ward",
    # pre-admission status
    "walk", "cogstat", "bonemed", "passess",
    # fracture
    "side", "afracture", "ftype",
    # surgery
    "asa", "frailty", "delay", "anaesth", "analges", "consult", "surg",
    # peri-operative
    "wbear", "mobil", "pulcers", "gerimed",
    # KEY EXPOSURE
    "malnutrition",
    # KEY OUTCOMES
    "mort30d", "mort90d", "mort120d", "mort365d",
    "wdest", "dresidence",
    # date diffs for LOS
    "arrdate_datediff", "wdisch_datediff", "hdisch_datediff",
]

# ── 1. Load raw ───────────────────────────────────────────────────────────────
with open(PROCESSED / "df_raw.pkl", "rb") as f:
    df = pickle.load(f)

print(f"Raw: {df.shape[0]:,} rows")

# ── 2. Drop year outliers (2009, 2025 — n=6) ─────────────────────────────────
df = df[df["arrdate_year"].between(2016, 2024)]
print(f"After dropping year outliers: {df.shape[0]:,} rows")

# ── 3. Compute LOS ────────────────────────────────────────────────────────────
df["los_acute"]   = df["wdisch_datediff"] - df["arrdate_datediff"]
df["los_hospital"] = df["hdisch_datediff"] - df["arrdate_datediff"]

# Cap implausible values (>365 days)
df.loc[df["los_acute"]    > 365, "los_acute"]    = np.nan
df.loc[df["los_hospital"] > 365, "los_hospital"] = np.nan

# ── 4. Select columns ─────────────────────────────────────────────────────────
df = df[KEEP_COLS + ["los_acute", "los_hospital"]].copy()

# ── 5. Apply labels ───────────────────────────────────────────────────────────
for col, mapping in LABELS.items():
    if col in df.columns:
        df[col] = df[col].map(mapping).astype("category")

# ── 6. Drop unassessed malnutrition rows ─────────────────────────────────────
# "Not assessed" and NaN are both uninformative for the exposure of interest
df = df[df["malnutrition"] != "Not assessed"]
df["malnutrition"] = df["malnutrition"].cat.remove_categories(["Not assessed"])
df = df[df["malnutrition"].notna()].copy()

# ── 7. Binary outcome columns ─────────────────────────────────────────────────
df["died_30d"]  = (df["mort30d"]  == "Deceased").astype("boolean")
df["died_90d"]  = (df["mort90d"]  == "Deceased").astype("boolean")
df["died_365d"] = (df["mort365d"] == "Deceased").astype("boolean")

# ── 8. Summary ────────────────────────────────────────────────────────────────
print(f"\nFinal shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

print("\n--- Malnutrition status ---")
print(df["malnutrition"].value_counts(dropna=False))

print("\n--- 30-day mortality ---")
print(df["mort30d"].value_counts(dropna=False))

print("\n--- LOS acute (days) ---")
print(df["los_acute"].describe().round(1))

print("\n--- Discharge destination ---")
print(df["wdest"].value_counts(dropna=False))

# ── 9. Save ───────────────────────────────────────────────────────────────────
with open(PROCESSED / "df_clean.pkl", "wb") as f:
    pickle.dump(df, f)

print(f"\nSaved: data/processed/df_clean.pkl")
