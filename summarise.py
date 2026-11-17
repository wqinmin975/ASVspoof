"""Aggregate the real-data runs into the numbers quoted in the manuscript."""
import csv, json, statistics as st

# P1-4 (2026-11-14): disclose every statistical setting in a machine-readable
# sidecar instead of burying it in code. G04 arbitration: the released
# real_summary.json is a SIMULATION OUTPUT and must stay byte-identical
# (P0-1 / revision plan section 3). Therefore the metadata is written to a
# separate file, NOT injected into real_summary.json. delta_ci95 stays at the
# top level of real_summary.json -- it is NOT part of this metadata dict.
STAT_METADATA = {
    "revision_date": "2026-11-14",
    "deviation_type": "population standard deviation (statistics.pstdev, ddof=0)",
    "bootstrap_seed": 11,
    "bootstrap_resample_times": 4000,
    "bootstrap_scope": "paired bootstrap 95% CI over the 10 MLP delta runs only",
    "bootstrap_ci_field": "real_summary.json -> delta_ci95 (top-level key)",
    "bootstrap_not_applied_to": "logistic-regression delta",
    "calibration_method": "temperature+bias (torch LBFGS over log-temperature and bias)",
    "calibration_holdout_fraction": 0.15,
    "calibration_holdout_min_samples": 64,
    "cost_fp": 5.0,
    "cost_fn": 20.0,
    "threshold_thr_rule": 0.2,
    "threshold_formula": "c_FP/(c_FP + c_FN)",
    "delta_definition": "cost@0.5 - cost@rule (per 1,000 calls)",
    "n_runs_per_detector": 10,
    "folds": 5,
    "seeds": 2,
    "cost_unit": "per 1,000 calls",
    "aggregation_input": "real_runs.csv (20 rows = 2 seeds x 5 folds x 2 detectors)",
    "exp22_naming_note": (
        "exp22_* fields use each fold's measured test positive rate yte.mean(), "
        "NOT a fixed prior 0.22; the name is a historical artifact."
    ),
}

rows = list(csv.DictReader(open("real_runs.csv", encoding="utf-8")))
keys = ["auprc", "auroc", "ece", "ece_iso", "f1_05", "f1_rule", "cost05", "cost_rule",
        "delta", "cost_iso", "exp60_05", "exp60_rule", "exp22_05", "exp22_rule"]
out = {}
for m in ("mlp", "lr"):
    r = [x for x in rows if x["model"] == m]
    out[m] = {k: dict(mean=st.mean(float(x[k]) for x in r),
                      sd=st.pstdev(float(x[k]) for x in r),
                      n=len(r)) for k in keys}

# paired bootstrap over the 10 runs
import random
random.seed(11)
mlp = [x for x in rows if x["model"] == "mlp"]
d = [float(x["cost05"]) - float(x["cost_rule"]) for x in mlp]
boot = []
for _ in range(4000):
    s = [d[random.randrange(len(d))] for _ in range(len(d))]
    boot.append(st.mean(s))
boot.sort()
out["delta_ci95"] = [round(boot[int(0.025 * len(boot))], 1), round(boot[int(0.975 * len(boot)) - 1], 1)]
print(json.dumps(out, indent=1))

with open("real_summary.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)

# Sidecar only: real_summary.json is left with its original schema/values.
with open("stat_metadata.json", "w", encoding="utf-8") as f:
    json.dump(STAT_METADATA, f, indent=1, ensure_ascii=False)
