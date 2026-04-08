"""
Full dataset summary visualisations — all 97,449 patients.
Outputs saved to outputs/trends/
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
TRENDS = ROOT / "outputs" / "full_cohort"
TRENDS.mkdir(parents=True, exist_ok=True)

with open(PROCESSED / "df.pkl", "rb") as f:
    df = pickle.load(f)

print(f"Full dataset: {len(df):,} patients")

sns.set_theme(style="whitegrid", font_scale=1.15)
SEX_PAL  = {"Female": "#E07B54", "Male": "#5B8DB8"}
BLUE     = "#5B8DB8"
ORANGE   = "#E07B54"
GREEN    = "#7BBF6A"

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1 — Sex split (pie + bar)
# ─────────────────────────────────────────────────────────────────────────────
sex = df["sex"].value_counts().loc[["Female", "Male"]]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Sex distribution — full cohort (n=97,449)", fontweight="bold")

# Pie
axes[0].pie(sex.values, labels=sex.index, autopct="%1.1f%%",
            colors=[SEX_PAL[s] for s in sex.index],
            startangle=90, wedgeprops=dict(edgecolor="white", linewidth=2))
axes[0].set_title("Proportion")

# Bar
bars = axes[1].bar(sex.index, sex.values,
                   color=[SEX_PAL[s] for s in sex.index],
                   edgecolor="white", width=0.5)
for bar in bars:
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 300,
                 f"{bar.get_height():,}", ha="center", fontweight="bold")
axes[1].set_ylabel("Number of patients")
axes[1].set_title("Count")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
fig.savefig(TRENDS / "01_sex_distribution.png", dpi=150)
plt.close()
print("Saved: 01_sex_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2 — Age distribution overall + by sex
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Age distribution", fontweight="bold")

bins = range(50, 110)

# Overall
axes[0].hist(df["age"].dropna(), bins=bins, color=BLUE, edgecolor="none", alpha=0.8)
axes[0].axvline(df["age"].median(), color="black", linewidth=2, linestyle="--",
                label=f'Median: {df["age"].median():.0f}')
axes[0].set_xlabel("Age (years)")
axes[0].set_ylabel("Number of patients")
axes[0].set_title("Overall")
axes[0].legend()
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# By sex
for sex_grp in ["Female", "Male"]:
    sub = df[df["sex"] == sex_grp]["age"].dropna()
    axes[1].hist(sub, bins=bins, alpha=0.6, label=f"{sex_grp} (median {sub.median():.0f})",
                 color=SEX_PAL[sex_grp], edgecolor="none")
    axes[1].axvline(sub.median(), color=SEX_PAL[sex_grp], linewidth=2, linestyle="--")
axes[1].set_xlabel("Age (years)")
axes[1].set_ylabel("Number of patients")
axes[1].set_title("By sex")
axes[1].legend()
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
fig.savefig(TRENDS / "02_age_distribution.png", dpi=150)
plt.close()
print("Saved: 02_age_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3 — Admissions per year (trend)
# ─────────────────────────────────────────────────────────────────────────────
year_counts = (
    df[df["arrdate_year"].between(2016, 2024)]
    .groupby("arrdate_year")
    .size()
    .reset_index(name="n")
)

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(year_counts["arrdate_year"], year_counts["n"],
        marker="o", linewidth=2.5, color=BLUE, markersize=8)
for _, row in year_counts.iterrows():
    ax.text(row["arrdate_year"], row["n"] + 100, f"{int(row['n']):,}",
            ha="center", fontsize=9)
ax.set_xlabel("Year")
ax.set_ylabel("Number of admissions")
ax.set_title("Hip fracture admissions per year (2016–2024)", fontweight="bold")
ax.set_xticks(year_counts["arrdate_year"].astype(int))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(TRENDS / "03_admissions_per_year.png", dpi=150)
plt.close()
print("Saved: 03_admissions_per_year.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4 — Fracture type
# ─────────────────────────────────────────────────────────────────────────────
ftype_order = ["Intracapsular undisplaced", "Intracapsular displaced",
               "Per/intertrochanteric", "Subtrochanteric"]
ftype = df["ftype"].value_counts().reindex(ftype_order).dropna()

fig, ax = plt.subplots(figsize=(9, 5))
colors = [BLUE, ORANGE, GREEN, "#9B59B6"]
bars = ax.barh(ftype.index, ftype.values, color=colors, edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
            f"{int(bar.get_width()):,}  ({bar.get_width()/len(df)*100:.1f}%)",
            va="center", fontsize=10)
ax.set_xlabel("Number of patients")
ax.set_title("Fracture type", fontweight="bold")
ax.set_xlim(0, ftype.max() * 1.25)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(TRENDS / "04_fracture_type.png", dpi=150)
plt.close()
print("Saved: 04_fracture_type.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 5 — ASA grade
# ─────────────────────────────────────────────────────────────────────────────
asa_order = ["ASA 1", "ASA 2", "ASA 3", "ASA 4", "ASA 5"]
asa = df["asa"].value_counts().reindex(asa_order).dropna()

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(asa.index, asa.values, color=BLUE, edgecolor="white", width=0.6)
for bar in bars:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 150,
            f"{int(bar.get_height()):,}\n({bar.get_height()/asa.sum()*100:.1f}%)",
            ha="center", fontsize=9)
ax.set_ylabel("Number of patients")
ax.set_title("ASA grade (anaesthetic risk) — full cohort", fontweight="bold")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(TRENDS / "05_asa_grade.png", dpi=150)
plt.close()
print("Saved: 05_asa_grade.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 6 — Pre-admission walking ability
# ─────────────────────────────────────────────────────────────────────────────
walk_order = ["Walks without walking aids", "Walks with either a stick or crutch",
              "Walks with two aids or frame", "Uses a wheelchair / bed bound"]
walk = df["walk"].value_counts().reindex(walk_order).fillna(0)

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(walk.index, walk.values, color=ORANGE, edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
            f"{int(bar.get_width()):,}  ({bar.get_width()/walk.sum()*100:.1f}%)",
            va="center", fontsize=10)
ax.set_xlabel("Number of patients")
ax.set_title("Pre-admission walking ability — full cohort", fontweight="bold")
ax.set_xlim(0, walk.max() * 1.3)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(TRENDS / "06_walking_ability.png", dpi=150)
plt.close()
print("Saved: 06_walking_ability.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 7 — 30-day mortality by year
# ─────────────────────────────────────────────────────────────────────────────
mort_year = (
    df[df["arrdate_year"].between(2016, 2024) & df["mort30d"].notna()]
    .groupby("arrdate_year")
    .apply(lambda x: (x["mort30d"] == "Deceased").mean() * 100)
    .reset_index(name="mort_pct")
)

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(mort_year["arrdate_year"], mort_year["mort_pct"],
        marker="o", linewidth=2.5, color=ORANGE, markersize=8)
for _, row in mort_year.iterrows():
    ax.text(row["arrdate_year"], row["mort_pct"] + 0.1,
            f"{row['mort_pct']:.1f}%", ha="center", fontsize=9)
ax.set_xlabel("Year")
ax.set_ylabel("30-day mortality (%)")
ax.set_title("30-day mortality rate by year (2016–2024)", fontweight="bold")
ax.set_xticks(mort_year["arrdate_year"].astype(int))
ax.set_ylim(0, mort_year["mort_pct"].max() * 1.3)
fig.tight_layout()
fig.savefig(TRENDS / "07_mortality_by_year.png", dpi=150)
plt.close()
print("Saved: 07_mortality_by_year.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 8 — Usual place of residence
# ─────────────────────────────────────────────────────────────────────────────
res_order = ["Private residence", "Aged care facility", "Other"]
res = df["uresidence"].value_counts().reindex(res_order).dropna()

fig, ax = plt.subplots(figsize=(7, 5))
colors = [BLUE, ORANGE, GREEN]
wedges, texts, autotexts = ax.pie(
    res.values, labels=res.index, autopct="%1.1f%%",
    colors=colors, startangle=90,
    wedgeprops=dict(edgecolor="white", linewidth=2)
)
for at in autotexts:
    at.set_fontsize(11)
    at.set_fontweight("bold")
ax.set_title("Usual place of residence — full cohort", fontweight="bold")
fig.tight_layout()
fig.savefig(TRENDS / "08_usual_residence.png", dpi=150)
plt.close()
print("Saved: 08_usual_residence.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 9 — Surgical repair rate by year
# ─────────────────────────────────────────────────────────────────────────────
surg_year = (
    df[df["arrdate_year"].between(2016, 2024) & df["surg"].notna()]
    .groupby("arrdate_year")
    .apply(lambda x: (x["surg"] == "Yes").mean() * 100)
    .reset_index(name="surg_pct")
)

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(surg_year["arrdate_year"], surg_year["surg_pct"],
        marker="o", linewidth=2.5, color=GREEN, markersize=8)
for _, row in surg_year.iterrows():
    ax.text(row["arrdate_year"], row["surg_pct"] + 0.2,
            f"{row['surg_pct']:.1f}%", ha="center", fontsize=9)
ax.set_xlabel("Year")
ax.set_ylabel("Surgical repair rate (%)")
ax.set_title("Surgical repair rate by year (2016–2024)", fontweight="bold")
ax.set_xticks(surg_year["arrdate_year"].astype(int))
ax.set_ylim(80, 100)
fig.tight_layout()
fig.savefig(TRENDS / "09_surgical_rate_by_year.png", dpi=150)
plt.close()
print("Saved: 09_surgical_rate_by_year.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 10 — LOS distribution overall
# ─────────────────────────────────────────────────────────────────────────────
df["los_acute"] = df["wdisch_datediff"] - df["arrdate_datediff"]
los = df["los_acute"].clip(0, 60).dropna()

fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(los, bins=60, color=BLUE, edgecolor="none", alpha=0.85)
ax.axvline(los.median(), color="black", linewidth=2, linestyle="--",
           label=f"Median: {los.median():.0f} days")
ax.axvline(los.mean(), color=ORANGE, linewidth=2, linestyle="--",
           label=f"Mean: {los.mean():.1f} days")
ax.set_xlabel("Acute ward length of stay (days, capped at 60)")
ax.set_ylabel("Number of patients")
ax.set_title("Length of stay distribution — full cohort", fontweight="bold")
ax.legend()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(TRENDS / "10_los_distribution.png", dpi=150)
plt.close()
print("Saved: 10_los_distribution.png")

print(f"\nAll 10 figures saved to outputs/trends/")
