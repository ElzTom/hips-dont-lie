"""
Who gets assessed for malnutrition vs not?
Compares assessed (n=50,354) vs unassessed (n=42,767) patients
on key baseline characteristics and outcomes.

Outputs:
  outputs/malnourished_vs_not/12_assessment_bias_characteristics.png
  outputs/malnourished_vs_not/13_assessment_bias_outcomes.png
  outputs/malnourished_vs_not/14_assessment_by_year.png
  outputs/tables/assessment_bias.csv
"""

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT      = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MV        = ROOT / "outputs" / "malnourished_vs_not"
TABLES    = ROOT / "outputs" / "tables"

# Load FULL labelled dataset (before malnutrition filtering)
with open(PROCESSED / "df.pkl", "rb") as f:
    df_full = pickle.load(f)

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = {"Assessed": "#5B8DB8", "Not assessed": "#AAAAAA"}
BLUE    = "#5B8DB8"
ORANGE  = "#E07B54"
GREY    = "#AAAAAA"

# Drop year outliers
df_full = df_full[df_full["arrdate_year"].between(2016, 2024)].copy()

# Flag assessed vs not
# In df.pkl: "Not done" = not assessed, NaN = missing, "Malnourished"/"Not malnourished" = assessed
df_full["assessed"] = df_full["malnutrition"].isin(["Malnourished", "Not malnourished"])
df_full["assessed_label"] = df_full["assessed"].map({True: "Assessed", False: "Not assessed"})

# Fix label references for full dataset (uses original long labels)
AGED_CARE_LABEL   = "Residential aged care facility"
IMPAIRED_COG_LABEL = "Impaired cognition or known dementia"
ASA_HIGH_LABELS   = [
    "Severe systemic disease that limits activity but is not incapacitating",
    "Incapacitating systemic disease which is constantly life threatening",
    "Moribund not expected to survive 24 hours with or without surgery",
]
WALK_NO_AIDS_LABEL = "Walks without walking aids"

assessed     = df_full[df_full["assessed"]]
not_assessed = df_full[~df_full["assessed"]]

print(f"Assessed    : {len(assessed):,} ({len(assessed)/len(df_full)*100:.1f}%)")
print(f"Not assessed: {len(not_assessed):,} ({len(not_assessed)/len(df_full)*100:.1f}%)")

# ── Key stats comparison ───────────────────────────────────────────────────────
print("\n=== BASELINE COMPARISON ===")
rows = []
for label, grp in [("Assessed", assessed), ("Not assessed", not_assessed)]:
    age_med = grp["age"].median()
    pct_female = (grp["sex"] == "Female").mean() * 100
    pct_aged_care = (grp["uresidence"] == AGED_CARE_LABEL).mean() * 100
    pct_impaired = (grp["cogstat"] == IMPAIRED_COG_LABEL).mean() * 100
    pct_asa34 = grp["asa"].isin(ASA_HIGH_LABELS).mean() * 100
    pct_no_aids = (grp["walk"] == WALK_NO_AIDS_LABEL).mean() * 100
    mort30 = (grp["mort30d"] == "Deceased").mean() * 100
    los = (grp["wdisch_datediff"] - grp["arrdate_datediff"]).median()
    rows.append({
        "Group": label,
        "n": len(grp),
        "Median age": age_med,
        "% Female": round(pct_female, 1),
        "% From aged care": round(pct_aged_care, 1),
        "% Cognitively impaired": round(pct_impaired, 1),
        "% ASA 3-5": round(pct_asa34, 1),
        "% Walk without aids": round(pct_no_aids, 1),
        "30-day mortality (%)": round(mort30, 1),
        "Median LOS (days)": los,
    })

comp = pd.DataFrame(rows).set_index("Group")
print(comp.T.to_string())
comp.T.to_csv(TABLES / "assessment_bias.csv")
print("\nSaved: outputs/tables/assessment_bias.csv")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1 — Baseline characteristics comparison
# ─────────────────────────────────────────────────────────────────────────────
metrics = [
    ("Median age (years)",        assessed["age"].median(),
                                  not_assessed["age"].median()),
    ("% Female",                  (assessed["sex"]=="Female").mean()*100,
                                  (not_assessed["sex"]=="Female").mean()*100),
    ("% From aged care",          (assessed["uresidence"]==AGED_CARE_LABEL).mean()*100,
                                  (not_assessed["uresidence"]==AGED_CARE_LABEL).mean()*100),
    ("% Cognitively impaired",    (assessed["cogstat"]==IMPAIRED_COG_LABEL).mean()*100,
                                  (not_assessed["cogstat"]==IMPAIRED_COG_LABEL).mean()*100),
    ("% ASA 3–5",                 assessed["asa"].isin(ASA_HIGH_LABELS).mean()*100,
                                  not_assessed["asa"].isin(ASA_HIGH_LABELS).mean()*100),
    ("% Walk without aids",       (assessed["walk"]==WALK_NO_AIDS_LABEL).mean()*100,
                                  (not_assessed["walk"]==WALK_NO_AIDS_LABEL).mean()*100),
]

labels   = [m[0] for m in metrics]
assessed_vals     = [m[1] for m in metrics]
not_assessed_vals = [m[2] for m in metrics]

x     = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 5.5))
bars1 = ax.bar(x - width/2, assessed_vals,     width, label="Assessed",     color=BLUE,   edgecolor="white")
bars2 = ax.bar(x + width/2, not_assessed_vals, width, label="Not assessed", color=GREY, edgecolor="white")

for bars in [bars1, bars2]:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{bar.get_height():.1f}", ha="center", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=10)
ax.set_ylabel("Value")
ax.set_title("Baseline characteristics: assessed vs not assessed for malnutrition\n(Full cohort, n=93,121)",
             fontweight="bold")
ax.legend(title="Assessment status")
fig.tight_layout()
fig.savefig(MV / "12_assessment_bias_characteristics.png", dpi=150)
plt.close()
print("Saved: 12_assessment_bias_characteristics.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2 — Outcomes comparison
# ─────────────────────────────────────────────────────────────────────────────
los_assessed     = (assessed["wdisch_datediff"] - assessed["arrdate_datediff"]).clip(0, 60)
los_not_assessed = (not_assessed["wdisch_datediff"] - not_assessed["arrdate_datediff"]).clip(0, 60)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle("Outcomes: assessed vs not assessed for malnutrition", fontweight="bold")

# 30-day mortality
mort_vals = [
    (assessed["mort30d"] == "Deceased").mean() * 100,
    (not_assessed["mort30d"] == "Deceased").mean() * 100,
]
bars = axes[0].bar(["Assessed", "Not assessed"], mort_vals,
                   color=[BLUE, GREY], edgecolor="white", width=0.5)
for bar in bars:
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                 f"{bar.get_height():.1f}%", ha="center", fontweight="bold")
axes[0].set_ylabel("30-day mortality (%)")
axes[0].set_title("30-day mortality")
axes[0].set_ylim(0, max(mort_vals) * 1.35)

# LOS distribution
axes[1].hist(los_assessed.dropna(),     bins=40, alpha=0.6, color=BLUE, label="Assessed",     edgecolor="none")
axes[1].hist(los_not_assessed.dropna(), bins=40, alpha=0.6, color=GREY, label="Not assessed", edgecolor="none")
axes[1].axvline(los_assessed.median(),     color=BLUE,   linestyle="--", linewidth=2)
axes[1].axvline(los_not_assessed.median(), color="#888888", linestyle="--", linewidth=2)
axes[1].set_xlabel("LOS acute ward (days, capped 60)")
axes[1].set_ylabel("Number of patients")
axes[1].set_title(f"LOS distribution\n(medians: {los_assessed.median():.0f}d vs {los_not_assessed.median():.0f}d)")
axes[1].legend()

# Assessment rate by year
yr = (
    df_full[df_full["arrdate_year"].between(2016, 2024)]
    .groupby("arrdate_year")
    .apply(lambda x: x["assessed"].mean() * 100)
    .reset_index(name="pct_assessed")
)
axes[2].plot(yr["arrdate_year"], yr["pct_assessed"],
             marker="o", linewidth=2.5, color=BLUE, markersize=8)
for _, row in yr.iterrows():
    axes[2].text(row["arrdate_year"], row["pct_assessed"] + 0.8,
                 f"{row['pct_assessed']:.0f}%", ha="center", fontsize=9)
axes[2].set_xlabel("Year")
axes[2].set_ylabel("% assessed for malnutrition")
axes[2].set_title("Assessment rate by year")
axes[2].set_xticks(yr["arrdate_year"].astype(int))
axes[2].tick_params(axis="x", rotation=45)
axes[2].set_ylim(0, 100)

fig.tight_layout()
fig.savefig(MV / "13_assessment_bias_outcomes.png", dpi=150)
plt.close()
print("Saved: 13_assessment_bias_outcomes.png")
