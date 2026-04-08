"""
Longer-term mortality analysis: 30d, 90d, 120d, 365d
- Unadjusted rates by malnutrition group
- Adjusted logistic regression for each time point
- Visualisations saved to outputs/malnourished_vs_not/
"""

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT      = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MV        = ROOT / "outputs" / "malnourished_vs_not"
TABLES    = ROOT / "outputs" / "tables"

with open(PROCESSED / "df_clean.pkl", "rb") as f:
    df = pickle.load(f)

PALETTE = {"Malnourished": "#E07B54", "Not malnourished": "#5B8DB8"}
COVARS  = "age + female + asa_num + walk_num + impaired_cog + aged_care + intertroch + had_surgery"

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

TIMEPOINTS = [
    ("mort30d",  "died_30d",  "30-day"),
    ("mort90d",  "died_90d",  "90-day"),
    ("mort120d", "died_120d", "120-day"),
    ("mort365d", "died_365d", "365-day"),
]

for raw_col, num_col, label in TIMEPOINTS:
    mdf[num_col] = (mdf[raw_col] == "Deceased").astype(float)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Unadjusted mortality rates across all time points
# ─────────────────────────────────────────────────────────────────────────────
print("=== UNADJUSTED MORTALITY RATES ===")
unadj_rows = []
for raw_col, num_col, label in TIMEPOINTS:
    for grp in ["Malnourished", "Not malnourished"]:
        sub = mdf[(mdf["malnutrition"] == grp) & mdf[raw_col].notna()]
        rate = (sub[raw_col] == "Deceased").mean() * 100
        n    = len(sub)
        unadj_rows.append({"Time": label, "Group": grp, "n": n, "Rate (%)": round(rate, 1)})

unadj = pd.DataFrame(unadj_rows)
print(unadj.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 2. Adjusted logistic regression — all time points
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== ADJUSTED LOGISTIC REGRESSION ===")
adj_rows = []
for raw_col, num_col, label in TIMEPOINTS:
    data = mdf[[num_col, "malnourished"] + COVARS.split(" + ")].dropna()
    m = smf.logit(f"{num_col} ~ malnourished + {COVARS}", data=data).fit(disp=0)
    OR  = np.exp(m.params["malnourished"])
    ci  = np.exp(m.conf_int().loc["malnourished"])
    p   = m.pvalues["malnourished"]
    print(f"  {label}: OR {OR:.2f} (95% CI {ci[0]:.2f}-{ci[1]:.2f}), p={p:.3f}, n={len(data):,}")
    adj_rows.append({
        "Time":      label,
        "n":         len(data),
        "OR":        round(OR, 2),
        "CI_lo":     round(ci[0], 2),
        "CI_hi":     round(ci[1], 2),
        "P-value":   round(p, 3),
    })

adj = pd.DataFrame(adj_rows)

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1 — Unadjusted rates over time (grouped bar)
# ─────────────────────────────────────────────────────────────────────────────
import seaborn as sns
sns.set_theme(style="whitegrid", font_scale=1.1)

pivot = unadj.pivot(index="Time", columns="Group", values="Rate (%)")
pivot = pivot.reindex(["30-day", "90-day", "120-day", "365-day"])

x      = np.arange(len(pivot))
width  = 0.35
fig, ax = plt.subplots(figsize=(10, 5))

for i, grp in enumerate(["Malnourished", "Not malnourished"]):
    bars = ax.bar(x + (i - 0.5) * width, pivot[grp], width,
                  label=grp, color=PALETTE[grp], edgecolor="white")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}%", ha="center", fontsize=10, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(pivot.index)
ax.set_ylabel("Mortality rate (%)")
ax.set_title("Unadjusted mortality rates by time point and malnutrition status\n(Malnourished vs Not Malnourished — Assessed Cohort)",
             fontweight="bold")
ax.legend(title="Malnutrition status")
ax.set_ylim(0, pivot.values.max() * 1.25)
fig.tight_layout()
fig.savefig(MV / "08_mortality_all_timepoints_unadj.png", dpi=150)
plt.close()
print("\nSaved: 08_mortality_all_timepoints_unadj.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2 — Adjusted OR forest plot across all time points
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

colors = ["#5B8DB8", "#7BBF6A", "#E8B84B", "#E07B54"]
y_pos  = list(range(len(adj)))

for i, row in adj.iterrows():
    ax.errorbar(row["OR"], i,
                xerr=[[row["OR"] - row["CI_lo"]], [row["CI_hi"] - row["OR"]]],
                fmt="o", color=colors[i], markersize=11,
                capsize=6, linewidth=2.5,
                label=f'{row["Time"]}  OR {row["OR"]:.2f} ({row["CI_lo"]:.2f}-{row["CI_hi"]:.2f})  p={row["P-value"]:.3f}')

ax.axvline(1, color="black", linestyle="--", linewidth=1.5, label="No effect (OR=1)")
ax.set_yticks(y_pos)
ax.set_yticklabels(adj["Time"].tolist(), fontsize=13)
ax.set_xlabel("Odds Ratio (malnourished vs not malnourished)", fontsize=12)
ax.set_title("Adjusted odds ratios for mortality — all time points\n"
             "Adjusted for: age, sex, ASA, walking ability, cognition, residence, fracture type, surgery",
             fontweight="bold")
ax.legend(loc="lower right", fontsize=10)
ax.set_xlim(0.6, 1.6)
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(MV / "09_mortality_forest_all_timepoints.png", dpi=150)
plt.close()
print("Saved: 09_mortality_forest_all_timepoints.png")

# ─────────────────────────────────────────────────────────────────────────────
# Save results table
# ─────────────────────────────────────────────────────────────────────────────
adj["95% CI"] = adj.apply(lambda r: f"{r['CI_lo']} - {r['CI_hi']}", axis=1)
adj[["Time","n","OR","95% CI","P-value"]].to_csv(
    TABLES / "longterm_mortality_adjusted.csv", index=False)
print("Saved: outputs/tables/longterm_mortality_adjusted.csv")
