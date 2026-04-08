"""
Adjusted analysis — impact of malnutrition on hip fracture outcomes.

Models:
  1. Logistic regression — 30-day mortality
  2. Logistic regression — discharge to aged care (vs home/rehab)
  3. Linear regression  — LOS acute ward (log-transformed due to skew)

Confounders adjusted for: age, sex, ASA grade, pre-admission walking ability,
cognitive status, usual residence, fracture type, surgical repair, ward type.

Outputs:
  outputs/tables/adjusted_results.csv
  outputs/tables/adjusted_results.html
  outputs/adjusted/  — forest plots
"""

import pickle
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES    = ROOT / "outputs" / "tables"
ADJ_DIR   = ROOT / "outputs" / "adjusted"
TABLES.mkdir(parents=True, exist_ok=True)
ADJ_DIR.mkdir(parents=True, exist_ok=True)

with open(PROCESSED / "df_clean.pkl", "rb") as f:
    df = pickle.load(f)

# ── Prep modelling dataframe ──────────────────────────────────────────────────
# Reference categories chosen as the most common / least severe group
mdf = df.copy()

# Binary exposure: malnourished = 1, not malnourished = 0
mdf["malnourished"] = (mdf["malnutrition"] == "Malnourished").astype(int)

# Recode to simpler binary/ordinal where needed
mdf["female"]        = (mdf["sex"] == "Female").astype(float)
mdf["aged_care"]     = (mdf["uresidence"] == "Aged care facility").astype(float)
mdf["impaired_cog"]  = (mdf["cogstat"] == "Impaired/dementia").astype(float)
mdf["asa_num"]       = mdf["asa"].map({"ASA 1":1,"ASA 2":2,"ASA 3":3,"ASA 4":4,"ASA 5":5})
mdf["walk_num"]      = mdf["walk"].map({"No aids":1,"Stick/crutch":2,"Two aids/frame":3,"Wheelchair/bed bound":4})
mdf["had_surgery"]   = (mdf["surg"] == "Yes").astype(float)
mdf["outlying_ward"] = (mdf["ward"] == "Outlying").astype(float)
mdf["intertroch"]    = (mdf["ftype"] == "Per/intertrochanteric").astype(float)

# Outcomes
mdf["died_30d_num"]  = (mdf["mort30d"] == "Deceased").astype(float)
mdf["to_aged_care"]  = (mdf["wdest"] == "Aged care facility").astype(float)
mdf["los_log"]       = np.log1p(mdf["los_acute"])  # log(LOS+1) for normality

COVARS = "age + female + asa_num + walk_num + impaired_cog + aged_care + intertroch + had_surgery"

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 1 — Logistic: 30-day mortality
# ─────────────────────────────────────────────────────────────────────────────
m1_data = mdf[["died_30d_num","malnourished"] + COVARS.split(" + ")].dropna()
m1 = smf.logit("died_30d_num ~ malnourished + " + COVARS, data=m1_data).fit(disp=0)

or1   = np.exp(m1.params["malnourished"])
ci1   = np.exp(m1.conf_int().loc["malnourished"])
p1    = m1.pvalues["malnourished"]
print(f"\n── MODEL 1: 30-day mortality ──")
print(f"  n = {len(m1_data):,}  |  OR = {or1:.2f} (95% CI {ci1[0]:.2f}–{ci1[1]:.2f})  |  p = {p1:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 2 — Logistic: discharge to aged care
# ─────────────────────────────────────────────────────────────────────────────
m2_data = mdf[["to_aged_care","malnourished"] + COVARS.split(" + ")].dropna()
m2 = smf.logit("to_aged_care ~ malnourished + " + COVARS, data=m2_data).fit(disp=0)

or2   = np.exp(m2.params["malnourished"])
ci2   = np.exp(m2.conf_int().loc["malnourished"])
p2    = m2.pvalues["malnourished"]
print(f"\n── MODEL 2: Discharge to aged care ──")
print(f"  n = {len(m2_data):,}  |  OR = {or2:.2f} (95% CI {ci2[0]:.2f}–{ci2[1]:.2f})  |  p = {p2:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 3 — Linear: log(LOS)
# ─────────────────────────────────────────────────────────────────────────────
m3_data = mdf[["los_log","malnourished"] + COVARS.split(" + ")].dropna()
m3 = smf.ols("los_log ~ malnourished + " + COVARS, data=m3_data).fit()

b3    = m3.params["malnourished"]
ci3   = m3.conf_int().loc["malnourished"]
p3    = m3.pvalues["malnourished"]
# Back-transform: % difference in LOS
pct3  = (np.exp(b3) - 1) * 100
print(f"\n── MODEL 3: LOS acute ward (log-transformed) ──")
print(f"  n = {len(m3_data):,}  |  Beta = {b3:.3f}  |  % diff = {pct3:+.1f}%  |  p = {p3:.3f}")
print(f"  95% CI: {ci3[0]:.3f} to {ci3[1]:.3f}  ({(np.exp(ci3[0])-1)*100:+.1f}% to {(np.exp(ci3[1])-1)*100:+.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# Summary table
# ─────────────────────────────────────────────────────────────────────────────
results = pd.DataFrame([
    {
        "Outcome":       "30-day mortality",
        "Model":         "Logistic regression",
        "n":             len(m1_data),
        "Estimate":      f"OR {or1:.2f}",
        "95% CI":        f"{ci1[0]:.2f} – {ci1[1]:.2f}",
        "P-value":       f"{p1:.3f}",
        "Interpretation": "Odds of dying within 30 days"
    },
    {
        "Outcome":       "Discharge to aged care",
        "Model":         "Logistic regression",
        "n":             len(m2_data),
        "Estimate":      f"OR {or2:.2f}",
        "95% CI":        f"{ci2[0]:.2f} – {ci2[1]:.2f}",
        "P-value":       f"{p2:.3f}",
        "Interpretation": "Odds of being discharged to aged care (vs home/rehab)"
    },
    {
        "Outcome":       "Length of stay (acute)",
        "Model":         "Linear regression (log LOS)",
        "n":             len(m3_data),
        "Estimate":      f"{pct3:+.1f}%",
        "95% CI":        f"{(np.exp(ci3[0])-1)*100:+.1f}% – {(np.exp(ci3[1])-1)*100:+.1f}%",
        "P-value":       f"{p3:.3f}",
        "Interpretation": "% difference in LOS vs not malnourished"
    },
])

print("\n\n" + "="*70)
print("ADJUSTED RESULTS SUMMARY")
print("Adjusted for: age, sex, ASA grade, walking ability, cognition,")
print("              residence, fracture type, surgical repair")
print("="*70)
print(results.to_string(index=False))

results.to_csv(TABLES / "adjusted_results.csv", index=False)
print(f"\nSaved: outputs/tables/adjusted_results.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Forest plot — all three outcomes
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle(
    "Adjusted effect of malnutrition on hip fracture outcomes\n"
    "(adjusted for age, sex, ASA, walking ability, cognition, residence, fracture type, surgery)",
    fontweight="bold", fontsize=10
)

ORANGE = "#E07B54"
BLUE   = "#5B8DB8"

# ── Panel 1: OR mortality ──
ax = axes[0]
ax.errorbar(or1, 0, xerr=[[or1 - ci1[0]], [ci1[1] - or1]],
            fmt="o", color=ORANGE, markersize=10, capsize=6, linewidth=2)
ax.axvline(1, color="black", linestyle="--", linewidth=1.2)
ax.set_yticks([])
ax.set_xlabel("Odds Ratio")
ax.set_title(f"30-day mortality\nOR {or1:.2f} ({ci1[0]:.2f}–{ci1[1]:.2f})\np = {p1:.3f}")
ax.set_xlim(0.5, 2.0)

# ── Panel 2: OR discharge to aged care ──
ax = axes[1]
ax.errorbar(or2, 0, xerr=[[or2 - ci2[0]], [ci2[1] - or2]],
            fmt="o", color=ORANGE, markersize=10, capsize=6, linewidth=2)
ax.axvline(1, color="black", linestyle="--", linewidth=1.2)
ax.set_yticks([])
ax.set_xlabel("Odds Ratio")
ax.set_title(f"Discharge to aged care\nOR {or2:.2f} ({ci2[0]:.2f}–{ci2[1]:.2f})\np = {p2:.3f}")
ax.set_xlim(0.5, 2.5)

# ── Panel 3: % LOS difference ──
ax = axes[2]
lo_err = pct3 - (np.exp(ci3[0])-1)*100
hi_err = (np.exp(ci3[1])-1)*100 - pct3
ax.errorbar(pct3, 0, xerr=[[lo_err], [hi_err]],
            fmt="o", color=BLUE, markersize=10, capsize=6, linewidth=2)
ax.axvline(0, color="black", linestyle="--", linewidth=1.2)
ax.set_yticks([])
ax.set_xlabel("% difference in LOS")
ax.set_title(f"Acute LOS\n{pct3:+.1f}% ({(np.exp(ci3[0])-1)*100:+.1f}% to {(np.exp(ci3[1])-1)*100:+.1f}%)\np = {p3:.3f}")

fig.tight_layout()
fig.savefig(ADJ_DIR / "forest_plot.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: outputs/adjusted/forest_plot.png")
