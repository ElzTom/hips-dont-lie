"""
Load and label the ANZHFR SAHMRI Datathon 2026 dataset.
Outputs:
  data/processed/df.pkl       — labelled DataFrame (fast reload)
  data/processed/df_raw.pkl   — raw numeric DataFrame (fast reload)
"""

import pickle
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

# ── 1. Load raw data ──────────────────────────────────────────────────────────
df_raw = pd.read_csv(RAW / "sahmri_datathon_2026.csv", low_memory=False)
print(f"Loaded: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

# ── 2. Parse value labels from data dictionary ────────────────────────────────
dict_df = pd.read_csv(RAW / "sahmri_datathon_2026_data_dict.csv")

def parse_value_labels(label_str):
    """Parse '[1] Foo; [2] Bar' → {1: 'Foo', 2: 'Bar'}"""
    if pd.isna(label_str) or str(label_str).strip() == "":
        return {}
    pattern = r"\[(-?\d+)\]\s*([^;]+)"
    return {int(k): v.strip() for k, v in re.findall(pattern, label_str)}

label_map = {}   # variable → {int: str}
col_labels = {}  # variable → human-readable label
for _, row in dict_df.iterrows():
    col_labels[row["variable"]] = row["label"]
    parsed = parse_value_labels(row.get("value_labels", ""))
    if parsed:
        label_map[row["variable"]] = parsed

# ── 3. Apply value labels ─────────────────────────────────────────────────────
df = df_raw.copy()
for col, mapping in label_map.items():
    if col in df.columns:
        df[col] = df[col].map(mapping).astype("category")

# ── 4. Summary ────────────────────────────────────────────────────────────────
labelled_cols = [c for c in df.columns if c in label_map]
numeric_cols  = [c for c in df.columns if c not in label_map]

print(f"Labelled categorical columns : {len(labelled_cols)}")
print(f"Numeric / other columns      : {len(numeric_cols)}")
print(f"\nMortality (30d) value counts:")
print(df["mort30d"].value_counts(dropna=False))

# ── 5. Save ───────────────────────────────────────────────────────────────────
with open(PROCESSED / "df.pkl", "wb") as f:
    pickle.dump(df, f)
with open(PROCESSED / "df_raw.pkl", "wb") as f:
    pickle.dump(df_raw, f)

print(f"\nSaved to {PROCESSED}/")
print("  df.pkl     — labelled categories")
print("  df_raw.pkl — raw numeric")
