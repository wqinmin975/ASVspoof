"""make_figures_v2.py -- draw the five TNSM figures from extension_v2 outputs.

Reads:
  extension_v2_figdata.json  (curve / reliability / cost_sweep_fine)
  extension_v2_summary.json (bootstrap_ci, cost_ratio_sweep, tdcf, ...)

All values are transcribed from the computed extension_v2 artefacts; nothing is
re-run here.  Figures are IEEEtran double-column friendly (3.45in wide, serif).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 8.5,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.direction": "in", "ytick.direction": "in",
    "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "stix",
})

FG = json.load(open("extension_v2_figdata.json"))
SM = json.load(open("extension_v2_summary.json"))

# ---------------------------------------------------------------- Fig 1
labels = ["MLP", "Logistic\nregression"]
c05 = [SM["aggregate"]["mlp"]["cost05"]["mean"], SM["aggregate"]["lr"]["cost05"]["mean"]]
sd05 = [SM["aggregate"]["mlp"]["cost05"]["sd"], SM["aggregate"]["lr"]["cost05"]["sd"]]
cr = [SM["aggregate"]["mlp"]["cost_rule"]["mean"], SM["aggregate"]["lr"]["cost_rule"]["mean"]]
sdr = [SM["aggregate"]["mlp"]["cost_rule"]["sd"], SM["aggregate"]["lr"]["cost_rule"]["sd"]]
red = [round((c05[i] - cr[i]) / c05[i] * 100, 1) for i in range(2)]
x = np.arange(2); w = 0.34
fig, ax = plt.subplots(figsize=(3.45, 2.35))
ax.bar(x - w/2, c05, w, color="#8c8c8c", edgecolor="black", lw=0.6, yerr=sd05, capsize=2.5,
       error_kw={"elinewidth": 0.6, "capthick": 0.6}, label=r"fixed rule ($p\geq0.5$)")
ax.bar(x + w/2, cr, w, color="white", edgecolor="black", lw=0.6, hatch="////", yerr=sdr, capsize=2.5,
       error_kw={"elinewidth": 0.6, "capthick": 0.6}, label=r"cost rule ($p\geq0.2$)")
for i, r in enumerate(red):
    top = max(c05[i]+sd05[i], cr[i]+sdr[i])
    ax.annotate("", xy=(x[i]+w/2, cr[i]+sdr[i]+90), xytext=(x[i]-w/2, c05[i]+sd05[i]+90),
                arrowprops=dict(arrowstyle="-|>", lw=0.6))
    ax.text(x[i], top+260, f"$-{r}\\%$", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("Expected cost per 1,000 calls")
ax.set_ylim(0, 5200); ax.set_xlim(-0.6, 1.6)
ax.legend(loc="upper left", frameon=False, handlelength=1.4, borderaxespad=0.2)
ax.text(0.97, 0.03, "error bars: $\\pm1$ population SD", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=6.5)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.tight_layout(pad=0.4); fig.savefig("fig1_cost.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig 2 (cost-ratio sweep)
fig, ax = plt.subplots(figsize=(3.45, 2.45))
for kind, style, col in (("mlp", "-", "black"), ("lr", "--", "black")):
    tbl = SM["cost_ratio_sweep"][kind]
    ratios = [float(t["ratio"].split(":")[1]) for t in tbl]
    dv = [t["delta_mean"] for t in tbl]
    sv = [t["delta_sd"] for t in tbl]
    ax.plot(ratios, dv, style, color=col, lw=0.9, label=kind)
    ax.fill_between(ratios, np.array(dv)-np.array(sv), np.array(dv)+np.array(sv),
                    color=col, alpha=0.12)
ax.axhline(0, color="grey", lw=0.5, ls=":")
ax.set_xlabel(r"cost asymmetry $c_{\mathrm{FN}}:c_{\mathrm{FP}}$ (with $c_{\mathrm{FP}}=5$)")
ax.set_ylabel(r"$\Delta$ cost / 1,000 calls")
ax.set_xlim(1, 20)
ymax = max(max(t["delta_mean"] + t["delta_sd"] for t in SM["cost_ratio_sweep"][k]) for k in ("mlp", "lr"))
ax.set_ylim(-60, ymax * 1.10)
ax.legend(loc="upper left", frameon=False, handlelength=1.8, borderaxespad=0.2)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.tight_layout(pad=0.6); fig.savefig("fig2_costratio.pdf", bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- Fig 3 (C(tau))
fig, ax = plt.subplots(figsize=(3.45, 2.45))
for kind, style, label in (("mlp", "-", "MLP"), ("lr", "--", "Logistic regression")):
    curve = FG["curve"][kind]
    xs = np.array(curve["tau"]); ys = np.array(curve["cost"])
    ax.plot(xs, ys, style, color="black", lw=0.9, label=label)
ax.set_ylim(1750, 5800)
ax.axvline(0.2, color="black", ls=":", lw=0.8)
ax.axvline(0.5, color="black", ls="-.", lw=0.8)
_bbox = dict(boxstyle="square,pad=0.18", fc="white", ec="none")
ax.text(0.205, 5520, r"$p^{*}=0.2$", fontsize=7.5, ha="left", va="top", bbox=_bbox, zorder=5)
ax.text(0.49, 5520, "0.5", fontsize=7.5, ha="right", va="top", bbox=_bbox, zorder=5)
ax.set_xlabel(r"Decision threshold $\tau$ on the calibrated posterior $p$")
ax.set_ylabel("Expected cost per 1,000 calls")
ax.set_xlim(0.0, 0.62)
ax.legend(loc="center right", frameon=True, fancybox=False,
          edgecolor="black", framealpha=1.0, handlelength=1.8, borderaxespad=0.3)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.tight_layout(pad=0.4); fig.savefig("fig3_curve.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig 4 (FP/FN decomposition)
fig, ax = plt.subplots(figsize=(3.45, 2.45))
for kind, style, label in (("mlp", "-", "MLP"), ("lr", "--", "Logistic regression")):
    curve = FG["curve"][kind]
    xs = np.array(curve["tau"])
    ax.plot(xs, np.array(curve["fp1k"]), style, color="black", lw=0.9, label=f"{label} FP/1k")
    ax.plot(xs, np.array(curve["fn1k"]), style, color="grey", lw=0.9, label=f"{label} FN/1k")
ax.axvline(0.2, color="black", ls=":", lw=0.8); ax.axvline(0.5, color="black", ls="-.", lw=0.8)
ax.set_xlabel(r"Decision threshold $\tau$")
ax.set_ylabel("False alarms / misses per 1,000 calls")
ax.set_xlim(0.0, 0.62)
ax.legend(loc="upper right", frameon=False, handlelength=1.6, borderaxespad=0.2, fontsize=6.8)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.tight_layout(pad=0.4); fig.savefig("fig4_fpfn.pdf"); plt.close(fig)

# ---------------------------------------------------------------- Fig 5 (reliability before/after)
fig, ax = plt.subplots(figsize=(3.45, 2.45))
for kind, mk in (("mlp", "o"), ("lr", "s")):
    rel = FG["reliability"][kind]
    if "raw" in rel:
        ax.plot(rel["raw"]["bin_center"], rel["raw"]["empirical_spoof_frac"],
                mk, color="grey", ms=4, label=f"{kind} raw")
    ax.plot(rel["calibrated"]["bin_center"], rel["calibrated"]["empirical_spoof_frac"],
            mk, color="black", ms=4, label=f"{kind} calibrated")
ax.plot([0, 1], [0, 1], color="black", lw=0.6, ls="--")
ax.set_xlabel("Mean calibrated posterior $p$ in bin")
ax.set_ylabel("Empirical fraction spoof")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.legend(loc="upper left", frameon=False, handlelength=1.0, borderaxespad=0.2, fontsize=6.8)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.tight_layout(pad=0.4); fig.savefig("fig5_reliability.pdf"); plt.close(fig)

print("wrote fig1_cost.pdf fig2_costratio.pdf fig3_curve.pdf fig4_fpfn.pdf fig5_reliability.pdf")
