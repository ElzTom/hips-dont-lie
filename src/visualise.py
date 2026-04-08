"""
Visualisations: malnutrition vs key outcomes
Outputs saved to outputs/figures/
"""

import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "malnourished_vs_not"
FIGURES.mkdir(parents=True, exist_ok=True)

with open(PROCESSED / "df_clean.pkl", "rb") as f:
    df = pickle.load(f)

# ── Palette ───────────────────────────────────────────────────────────────────
PALETTE = {"Malnourished": "#E07B54", "Not malnourished": "#5B8DB8"}
ORDER = ["Malnourished", "Not malnourished"]

sns.set_theme(style="whitegrid", font_scale=1.1)

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1 — Age distribution
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
for grp in ORDER:
    sub = df[df["malnutrition"] == grp]["age"].dropna()
    ax.hist(sub, bins=30, alpha=0.6, label=grp, color=PALETTE[grp], edgecolor="white")
    ax.axvline(sub.median(), color=PALETTE[grp], linewidth=2, linestyle="--")

ax.set_xlabel("Age (years)")
ax.set_ylabel("Number of patients")
ax.set_title("Age distribution by malnutrition status\n(dashed lines = medians)")
ax.legend(title="Malnutrition status")
fig.tight_layout()
fig.savefig(FIGURES / "01_age_distribution.png", dpi=150)
plt.close()
print("Saved: 01_age_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2 — LOS distribution (log scale for skew)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
for grp in ORDER:
    sub = df[df["malnutrition"] == grp]["los_acute"].dropna()
    ax.hist(sub, bins=40, alpha=0.6, label=grp, color=PALETTE[grp], edgecolor="white")
    ax.axvline(sub.median(), color=PALETTE[grp], linewidth=2, linestyle="--")

ax.set_xlabel("Acute ward length of stay (days)")
ax.set_ylabel("Number of patients")
ax.set_title("LOS distribution by malnutrition status\n(dashed lines = medians)")
ax.legend(title="Malnutrition status")
fig.tight_layout()
fig.savefig(FIGURES / "02_los_distribution.png", dpi=150)
plt.close()
print("Saved: 02_los_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3 — 30-day mortality rate (bar)
# ─────────────────────────────────────────────────────────────────────────────
mort = (
    df[df["mort30d"].notna()]
    .groupby("malnutrition", observed=True)
    .apply(lambda x: (x["mort30d"] == "Deceased").mean() * 100)
    .reset_index(name="mort_pct")
)

fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(
    mort["malnutrition"], mort["mort_pct"],
    color=[PALETTE[g] for g in mort["malnutrition"]],
    edgecolor="white", width=0.5
)
for bar, pct in zip(bars, mort["mort_pct"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
            f"{pct:.1f}%", ha="center", va="bottom", fontweight="bold")

ax.set_ylabel("30-day mortality (%)")
ax.set_title("30-day mortality by malnutrition status\n(unadjusted)")
ax.set_ylim(0, mort["mort_pct"].max() * 1.3)
ax.set_xlabel("")
fig.tight_layout()
fig.savefig(FIGURES / "03_mortality_30d.png", dpi=150)
plt.close()
print("Saved: 03_mortality_30d.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4 — Discharge destination (stacked %)
# ─────────────────────────────────────────────────────────────────────────────
dest_order = [
    "Private residence", "Rehab (public)", "Rehab (private)",
    "Aged care facility", "Other hospital/ward", "Deceased", "Other"
]
dest_palette = {
    "Private residence":    "#5B8DB8",
    "Rehab (public)":       "#7BBF6A",
    "Rehab (private)":      "#A8D88A",
    "Aged care facility":   "#E8B84B",
    "Other hospital/ward":  "#AAAAAA",
    "Deceased":             "#C0392B",
    "Other":                "#DDDDDD",
}

wdest = (
    df[df["wdest"].notna()]
    .groupby(["malnutrition", "wdest"], observed=True)
    .size()
    .reset_index(name="n")
)
wdest_pct = wdest.copy()
totals = wdest.groupby("malnutrition", observed=True)["n"].transform("sum")
wdest_pct["pct"] = wdest["n"] / totals * 100
wdest_pivot = (
    wdest_pct.pivot(index="malnutrition", columns="wdest", values="pct")
    .reindex(columns=[c for c in dest_order if c in wdest_pct["wdest"].unique()])
    .fillna(0)
)

fig, ax = plt.subplots(figsize=(8, 5))
bottom = np.zeros(len(wdest_pivot))
for col in wdest_pivot.columns:
    vals = wdest_pivot[col].values
    color = dest_palette.get(col, "#CCCCCC")
    bars = ax.bar(wdest_pivot.index, vals, bottom=bottom, label=col, color=color, edgecolor="white")
    for bar, val, bot in zip(bars, vals, bottom):
        if val > 3:
            ax.text(bar.get_x() + bar.get_width() / 2, bot + val / 2,
                    f"{val:.0f}%", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    bottom += vals

ax.set_ylabel("Percentage of patients (%)")
ax.set_title("Discharge destination by malnutrition status")
ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
ax.set_ylim(0, 105)
ax.set_xlabel("")
fig.tight_layout()
fig.savefig(FIGURES / "04_discharge_destination.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 04_discharge_destination.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 5 — ASA grade (grouped bar)
# ─────────────────────────────────────────────────────────────────────────────
asa_order = ["ASA 1", "ASA 2", "ASA 3", "ASA 4", "ASA 5"]
asa = (
    df[df["asa"].notna()]
    .groupby(["malnutrition", "asa"], observed=True)
    .size()
    .reset_index(name="n")
)
totals = asa.groupby("malnutrition", observed=True)["n"].transform("sum")
asa["pct"] = asa["n"] / totals * 100
asa_pivot = (
    asa.pivot(index="asa", columns="malnutrition", values="pct")
    .reindex(asa_order)
    .fillna(0)
)

x = np.arange(len(asa_pivot))
width = 0.35
fig, ax = plt.subplots(figsize=(8, 4.5))
for i, grp in enumerate(ORDER):
    if grp in asa_pivot.columns:
        bars = ax.bar(x + (i - 0.5) * width, asa_pivot[grp], width,
                      label=grp, color=PALETTE[grp], edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(asa_pivot.index)
ax.set_ylabel("Percentage of patients (%)")
ax.set_title("ASA grade by malnutrition status")
ax.legend(title="Malnutrition status")
fig.tight_layout()
fig.savefig(FIGURES / "05_asa_grade.png", dpi=150)
plt.close()
print("Saved: 05_asa_grade.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 6 — Pre-admission walking ability
# ─────────────────────────────────────────────────────────────────────────────
walk_order = ["No aids", "Stick/crutch", "Two aids/frame", "Wheelchair/bed bound"]
walk = (
    df[df["walk"].notna()]
    .groupby(["malnutrition", "walk"], observed=True)
    .size()
    .reset_index(name="n")
)
totals = walk.groupby("malnutrition", observed=True)["n"].transform("sum")
walk["pct"] = walk["n"] / totals * 100
walk_pivot = (
    walk.pivot(index="walk", columns="malnutrition", values="pct")
    .reindex(walk_order)
    .fillna(0)
)

x = np.arange(len(walk_pivot))
fig, ax = plt.subplots(figsize=(9, 4.5))
for i, grp in enumerate(ORDER):
    if grp in walk_pivot.columns:
        ax.bar(x + (i - 0.5) * width, walk_pivot[grp], width,
               label=grp, color=PALETTE[grp], edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(walk_pivot.index, rotation=10)
ax.set_ylabel("Percentage of patients (%)")
ax.set_title("Pre-admission walking ability by malnutrition status")
ax.legend(title="Malnutrition status")
fig.tight_layout()
fig.savefig(FIGURES / "06_walking_ability.png", dpi=150)
plt.close()
print("Saved: 06_walking_ability.png")

print("\nAll figures saved to outputs/figures/")
