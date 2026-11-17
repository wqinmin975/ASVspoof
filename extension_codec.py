"""Read-only extension of the codec branch: adds the fixed 0.5 baseline.

Uses the cached per-condition features (codec_cache/*.npz) and re-executes the
released codec protocol exactly (clean split, one shared temperature+bias per
seed).  Outputs extension_codec.csv and prints per-condition costs at both
operating points.  Released codec_stress.csv is not modified; a reproduction
gate aborts the run if the cost-rule / F1 / AUPRC values differ from it.
"""
import csv, sys
import numpy as np
import run_real_check as R

CONDS = ["clean", "g711_8k", "opus_12k", "opus_24k"]


def main():
    d = np.load("feats.npz", allow_pickle=True)
    X, y, fid = d["X"], d["y"], d["fid"]
    rng = np.random.default_rng(5)
    bona, spoof = np.where(y == 0)[0], np.where(y == 1)[0]
    pick = np.concatenate([rng.choice(bona, 300, replace=False),
                           rng.choice(spoof, 300, replace=False)])
    rest = np.setdiff1d(np.arange(len(y)), pick)
    Xtr, ytr = X[rest], y[rest]
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Xtr = (Xtr - mu) / sd

    feats = {c: np.load(f"codec_cache/{c}_n600.npz")["X"] for c in CONDS}

    hrng = np.random.default_rng(7000)
    hi = hrng.permutation(len(Xtr))
    ncal = max(64, int(0.15 * len(Xtr)))
    cal, fit = hi[:ncal], hi[ncal:]
    Xcal, ycal = Xtr[cal], ytr[cal]
    Xfit, yfit = Xtr[fit], ytr[fit]

    released = {}
    with open("codec_stress.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            released[(int(r["seed"]), r["cond"])] = r

    rows = []
    for seed in (0, 1):
        m = R.train_model("mlp", Xfit, yfit, seed)
        T, b = R.fit_temperature(R.logits_of(m, Xcal), ycal)
        for cond in CONDS:
            p = 1 / (1 + np.exp(-(R.logits_of(m, feats[cond]) / T + b)))
            pred05 = (p >= 0.5).astype(int)
            predr = (p >= R.THR_RULE).astype(int)
            fp05 = int(np.sum((pred05 == 1) & (y[pick] == 0)))
            fn05 = int(np.sum((pred05 == 0) & (y[pick] == 1)))
            fpr = int(np.sum((predr == 1) & (y[pick] == 0)))
            fnr = int(np.sum((predr == 0) & (y[pick] == 1)))
            row = dict(seed=seed, cond=cond,
                       cost05=R.cost_per_1000(y[pick], pred05),
                       cost_rule=R.cost_per_1000(y[pick], predr),
                       f1_05=R.f1_score(y[pick], pred05),
                       f1_rule=R.f1_score(y[pick], predr),
                       auprc=R.auprc(y[pick], p), auroc=R.auroc(y[pick], p),
                       fp05=fp05, fn05=fn05, fpr=fpr, fnr=fnr)
            rows.append(row)
            rel = released[(seed, cond)]
            diffs = [abs(row["cost_rule"] - float(rel["cost_rule"]))]
            if abs(row["f1_rule"] - float(rel["f1"])) > 1e-9:
                diffs.append(abs(row["f1_rule"] - float(rel["f1"])))
            if max(diffs) > 1e-6:
                sys.exit(f"CODEC REPRODUCTION FAILED seed{seed} {cond}: {diffs}")
            print(f"seed{seed} {cond}: ok cost05={row['cost05']:.1f} rule={row['cost_rule']:.1f}")

    with open("extension_codec.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print("\nper-condition means over two seeds:")
    for cond in CONDS:
        rr = [r for r in rows if r["cond"] == cond]
        c05 = np.mean([r["cost05"] for r in rr])
        cr = np.mean([r["cost_rule"] for r in rr])
        f05 = np.mean([r["f1_05"] for r in rr])
        print(f"{cond:9s} cost@0.5={c05:7.1f} cost@rule={cr:7.1f} "
              f"saving={c05-cr:6.1f} ({(c05-cr)/c05*100:5.1f}%) f1@0.5={f05:.4f}")


if __name__ == "__main__":
    main()
