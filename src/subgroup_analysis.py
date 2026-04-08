"""
Subgroup analyses — does the effect of malnutrition vary by:
  1. Age group (<80 vs 80+)
  2. Usual residence (community vs aged care)
  3. Cognitive status (intact vs impaired)

For each subgroup: adjusted logistic regression for 30-day mortality
Visualisations saved to outputs/malnourished_vs_not/
"""

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import seaborn as sns

warnings.filterwarnings("ignore")

ROOT      = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MV        = ROOT / "outputs" / "malnourished_vs_not"
TABLES    = ROOT / "outputs" / "tables"

with open(PROCESSED / "df_clean.pkl", "rb") as f:
    df = pickle.load(f)

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = {"Malnourished": "#E07B54", "Not malnourished": "#5B8DB8"}

# ── Prep ──────────────────────────────────────────────────────────────────────
mdf = df.copy()
mdf["malnourished"] = (mdf["malnutrition"] == "Malnourished").astype(int)
mdf["female"]       = (mdf["sex"] == "Female").astype(float)
mdf["aged_care"]    = (mdf["uresidence"] == "Aged care facility").astype(float)
mdf["impaired_cog"] = (mdf["cogstat"] == "Impaired/dementia").astype(float)
mdf["asa_num"]      = mdf["asa"].map({"ASA 1":1,"ASA 2":2,"ASA 3":3,"ASA 4":4,"ASA 5":5})
mdf["walk_num"]     = mdf["walk"].map({"No aids":1,"Stick/crutch":2,"Two aids/frame":3,"Wheelchair/bed bound":4})
mdf["had_surgery"]  = (mdf["surg"] == "Yes").astype(float)
mdf["intertroch"]   = (mdf["ftype"] == "Per/intertrochanteric").astype(float)
mdf["died_30d"]     = (mdf["mort30d"] == "Deceased").astype(float)
mdf["to_aged_care"] = (mdf["wdest"] == "Aged care facility").astype(float)
mdf["age_group"]    = pd.cut(mdf["age"], bins=[49, 79, 200],
                              labels=["<80 years", "80+ years"])

# Subgroup definitions
SUBGROUPS = {
    "Age < 80":          mdf["age"] < 80,
    "Age 80+":           mdf["age"] >= 80,
    "Community-dwelling": mdf["uresidence"] == "Private residence",
    "Aged care resident": mdf["uresidence"] == "Aged care facility",
    "Cognitively intact": mdf["cogstat"] == "Normal cognition",
    "Cognitively impaired": mdf["cogstat"] == "Impaired/dementia",
}

OUTCOMES = [
    ("died_30d",    "30-day mortality"),
    ("to_aged_care","Discharge to aged care"),
]

# ── Adjusted OR per subgroup per outcome ──────────────────────────────────────
def run_subgroup(data, outcome, covars):
    try:
        m = smf.logit(f"{outcome} ~ malnourished + {covars}", data=data).fit(disp=0)
        OR  = np.exp(m.params["malnourished"])
        ci  = np.exp(m.conf_int().loc["malnourished"])
        p   = m.pvalues["malnourished"]
        return OR, ci[0], ci[1], p, len(data)
    except Exception:
        return np.nan, np.nan, np.nan, np.nan, 0

results = []
print("=== SUBGROUP ANALYSIS ===\n")

for subgrp_label, mask in SUBGROUPS.items():
    sub = mdf[mask].copy()
    n_mal  = (sub["malnutrition"] == "Malnourished").sum()
    n_not  = (sub["malnutrition"] == "Not malnourished").sum()

    # Drop covariates that don't vary within subgroup
    covars = "age + female + asa_num + walk_num + had_surgery + intertroch"
    if subgrp_label not in ("Aged care resident", "Community-dwelling"):
        covars += " + aged_care"
    if subgrp_label not in ("Cognitively intact", "Cognitively impaired"):
        covars += " + impaired_cog"

    print(f"--- {subgrp_label} (n={len(sub):,} | mal={n_mal:,} | not={n_not:,}) ---")
    for outcome_col, outcome_label in OUTCOMES:
        data = sub[[outcome_col, "malnourished"] + covars.split(" + ")].dropna()
        OR, lo, hi, p, n = run_subgroup(data, outcome_col, covars)
        sig = "*" if p < 0.05 else ""
        print(f"  {outcome_label:30s}: OR {OR:.2f} ({lo:.2f}-{hi:.2f})  p={p:.3f} {sig}")
        results.append({
            "Subgroup":       subgrp_label,
            "Outcome":        outcome_label,
            "n":              n,
            "OR":             OR,
            "CI_lo":          lo,
            "CI_hi":          hi,
            "P-value":        p,
            "Significant":    p < 0.05,
        })
    print()

res = pd.DataFrame(results)

# ── Unadjusted mortality rates by subgroup ────────────────────────────────────
print("=== UNADJUSTED 30-DAY MORTALITY BY SUBGROUP ===\n")
unadj = []
for subgrp_label, mask in SUBGROUPS.items():
    sub = mdf[mask & mdf["mort30d"].notna()]
    for grp in ["Malnourished", "Not malnourished"]:
        s2   = sub[sub["malnutrition"] == grp]
        rate = (s2["mort30d"] == "Deceased").mean() * 100
        unadj.append({"Subgroup": subgrp_label, "Group": grp,
                       "n": len(s2), "Mortality (%)": round(rate, 1)})
        print(f"  {subgrp_label:25s} | {grp:20s} | n={len(s2):,} | {rate:.1f}%")

unadj_df = pd.DataFrame(unadj)

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1 — Forest plot: 30-day mortality across subgroups
# ─────────────────────────────────────────────────────────────────────────────
mort_res = res[res["Outcome"] == "30-day mortality"].reset_index(drop=True)

fig, ax = plt.subplots(figsize=(11, 6))

colors = {
    "Age < 80":              "#5B8DB8",
    "Age 80+":               "#2471A3",
    "Community-dwelling":    "#7BBF6A",
    "Aged care resident":    "#27AE60",
    "Cognitively intact":    "#E07B54",
    "Cognitively impaired":  "#C0392B",
}

y_labels = []
for i, row in mort_res.iterrows():
    color = colors.get(row["Subgroup"], "#888888")
    ax.errorbar(row["OR"], i,
                xerr=[[row["OR"] - row["CI_lo"]], [row["CI_hi"] - row["OR"]]],
                fmt="o", color=color, markersize=10, capsize=5, linewidth=2,
                markeredgecolor="white", markeredgewidth=0.5)
    sig_marker = "  *" if row["Significant"] else ""
    y_labels.append(f'{row["Subgroup"]}  (n={row["n"]:,.0f}){sig_marker}')

ax.axvline(1, color="black", linestyle="--", linewidth=1.5)
ax.set_yticks(range(len(mort_res)))
ax.set_yticklabels(y_labels, fontsize=12)
ax.set_xlabel("Adjusted Odds Ratio — 30-day mortality\n(malnourished vs not malnourished)", fontsize=12)
ax.set_title("Subgroup analysis: adjusted effect of malnutrition on 30-day mortality\n"
             "* p < 0.05", fontweight="bold")
ax.set_xlim(0.4, 2.2)
ax.invert_yaxis()

# Group annotations
for label, y_start, y_end, color in [
    ("Age group",        -0.6, 1.6, "#5B8DB8"),
    ("Residence",         1.4, 3.6, "#7BBF6A"),
    ("Cognition",         3.4, 5.6, "#E07B54"),
]:
    ax.annotate("", xy=(0.42, y_end), xytext=(0.42, y_start),
                arrowprops=dict(arrowstyle="-", color=color, lw=2))
    ax.text(0.41, (y_start + y_end)/2, label, ha="right", va="center",
            fontsize=10, color=color, fontweight="bold", rotation=90)

fig.tight_layout()
fig.savefig(MV / "10_subgroup_mortality_forest.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nSaved: 10_subgroup_mortality_forest.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2 — Unadjusted mortality rates by subgroup (grouped bar)
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
fig.suptitle("Unadjusted 30-day mortality by malnutrition status — subgroups",
             fontweight="bold")

subgroup_pairs = [
    ("Age group",   ["Age < 80",           "Age 80+"]),
    ("Residence",   ["Community-dwelling",  "Aged care resident"]),
    ("Cognition",   ["Cognitively intact",  "Cognitively impaired"]),
]

for ax, (group_label, subgrps) in zip(axes, subgroup_pairs):
    x = np.arange(len(subgrps))
    width = 0.35
    for i, grp in enumerate(["Malnourished", "Not malnourished"]):
        vals = [unadj_df[(unadj_df["Subgroup"] == s) &
                          (unadj_df["Group"] == grp)]["Mortality (%)"].values[0]
                for s in subgrps]
        bars = ax.bar(x + (i - 0.5)*width, vals, width,
                      label=grp, color=PALETTE[grp], edgecolor="white")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4,
                    f"{bar.get_height():.1f}%", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace(" ", "\n") for s in subgrps], fontsize=10)
    ax.set_title(group_label, fontweight="bold")
    ax.set_ylabel("30-day mortality (%)" if ax == axes[0] else "")
    ax.legend(fontsize=8.5)

fig.tight_layout()
fig.savefig(MV / "11_subgroup_mortality_unadj.png", dpi=150)
plt.close()
print("Saved: 11_subgroup_mortality_unadj.png")

# ── Save results ──────────────────────────────────────────────────────────────
res[["Subgroup","Outcome","n","OR","CI_lo","CI_hi","P-value","Significant"]].to_csv(
    TABLES / "subgroup_analysis.csv", index=False)
print("Saved: outputs/tables/subgroup_analysis.csv")
