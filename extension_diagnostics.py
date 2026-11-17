"""Read-only diagnostics extension for the real-speech anchor.

Re-executes the EXACT protocol of run_real_check.py (same seeds, splits,
standardisation, holdout, training and calibration) and adds quantities the
released per-run table does not carry:

  * raw (uncalibrated) ECE and calibrated ECE side by side
  * FP / FN counts per 1,000 calls at both operating points
  * a threshold chosen on the calibration holdout by minimising cost
    (never on test data), and its test cost
  * test cost along a threshold grid, for the cost-vs-threshold curve

Nothing is overwritten: the released real_runs.csv / real_summary.json /
stat_metadata.json stay untouched.  Output goes to extension_runs.csv and
extension_summary.json.  The script first verifies that its 20 reproduced
rows agree with the released rows; if they do not, it aborts.
"""
import csv, json, sys
import numpy as np
import run_real_check as R

GRID = np.round(np.arange(0.02, 0.61, 0.02), 4)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def counts_per_1000(y, pred):
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    return fp, fn, fp / len(y) * 1000.0, fn / len(y) * 1000.0


def holdout_threshold(pcal, ycal):
    """Cost-minimising threshold on the calibration holdout only."""
    best_t, best_c = 0.5, np.inf
    for t in GRID:
        c = R.cost_per_1000(ycal, (pcal >= t).astype(int))
        if c < best_c:
            best_t, best_c = float(t), c
    return best_t, float(best_c)


def main():
    d = np.load("feats.npz", allow_pickle=True)
    X, y, spk = d["X"].astype(np.float64), d["y"].astype(int), d["spk"]
    released = {}
    with open("real_runs.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            released[(int(row["seed"]), int(row["fold"]), row["model"])] = row

    rows = []
    for seed in range(2):
        masks = R.speaker_grouped_fold_split(spk, seed, 5)
        for k in range(5):
            te = masks[k]
            tr = ~te
            Xtr, ytr = X[tr], y[tr]
            Xte, yte = X[te], y[te]
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
            hrng = np.random.default_rng(7000 + seed * 10 + k)
            hi = hrng.permutation(len(Xtr))
            ncal = max(64, int(0.15 * len(Xtr)))
            cal, fit = hi[:ncal], hi[ncal:]
            Xcal, ycal = Xtr[cal], ytr[cal]
            Xfit, yfit = Xtr[fit], ytr[fit]

            for kind in ("mlp", "lr"):
                m = R.train_model(kind, Xfit, yfit, seed * 100 + k)
                zcal, zte = R.logits_of(m, Xcal), R.logits_of(m, Xte)
                T, b = R.fit_temperature(zcal, ycal)
                pcal = sigmoid(zcal / T + b)
                p = sigmoid(zte / T + b)
                pred05 = (p >= 0.5).astype(int)
                predr = (p >= R.THR_RULE).astype(int)

                fp05, fn05, fp05_1k, fn05_1k = counts_per_1000(yte, pred05)
                fpr, fnr, fpr_1k, fnr_1k = counts_per_1000(yte, predr)
                thr_h, cost_h_fit = holdout_threshold(pcal, ycal)
                cost_h_test = R.cost_per_1000(yte, (p >= thr_h).astype(int))

                row = dict(
                    seed=seed, fold=k, model=kind, n_te=int(te.sum()),
                    pos_te=float(yte.mean()),
                    ece_raw=R.ece(yte, sigmoid(zte)),
                    ece_cal=R.ece(yte, p),
                    cost05=R.cost_per_1000(yte, pred05),
                    cost_rule=R.cost_per_1000(yte, predr),
                    auprc=R.auprc(yte, p), auroc=R.auroc(yte, p),
                    fp05=fp05, fn05=fn05, fp05_1k=fp05_1k, fn05_1k=fn05_1k,
                    fpr=fpr, fnr=fnr, fpr_1k=fpr_1k, fnr_1k=fnr_1k,
                    thr_holdout=thr_h, cost_holdout_fit=cost_h_fit,
                    cost_holdout_test=cost_h_test,
                    oracle_cost=min(R.cost_per_1000(yte, (p >= t).astype(int)) for t in GRID),
                )
                for t in GRID:
                    row[f"c@{t:.2f}"] = R.cost_per_1000(yte, (p >= t).astype(int))
                rows.append(row)
                # ---- reproduction gate ----
                rel = released[(seed, k, kind)]
                diffs = {"cost05": abs(row["cost05"] - float(rel["cost05"])),
                         "cost_rule": abs(row["cost_rule"] - float(rel["cost_rule"])),
                         "auprc": abs(row["auprc"] - float(rel["auprc"]))
                         , "auroc": abs(row["auroc"] - float(rel["auroc"]))
                         , "ece_cal": abs(row["ece_cal"] - float(rel["ece"]))}
                worst = max(diffs.values())
                print(f"seed{seed} fold{k} {kind}: worst |diff|={worst:.3e}")
                if worst > 1e-6:
                    sys.exit(f"REPRODUCTION FAILED: {diffs}")

    with open("extension_runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    agg = {}
    for kind in ("mlp", "lr"):
        rr = [r for r in rows if r["model"] == kind]
        keys = [k for k in rows[0] if k not in ("seed", "fold", "model", "n_te", "pos_te")
                and not k.startswith("c@")]
        agg[kind] = {k: {"mean": float(np.mean([r[k] for r in rr])),
                         "sd": float(np.std([r[k] for r in rr]))} for k in keys}
        agg[kind]["curve"] = {}
        for t in GRID:
            vals = [r["c@" + f"{t:.2f}"] for r in rr]
            agg[kind]["curve"][f"{t:.2f}"] = float(np.mean(vals))
    with open("extension_summary.json", "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)

    print("\nreproduction gate passed for all 20 rows")
    for kind in ("mlp", "lr"):
        a = agg[kind]
        print(f"{kind}: ece_raw={a['ece_raw']['mean']:.4f} ece_cal={a['ece_cal']['mean']:.4f} "
              f"FP@0.5={a['fp05_1k']['mean']:.1f}/1k FN@0.5={a['fn05_1k']['mean']:.1f}/1k "
              f"FP@rule={a['fpr_1k']['mean']:.1f}/1k FN@rule={a['fnr_1k']['mean']:.1f}/1k "
              f"thr_h={a['thr_holdout']['mean']:.3f} cost_h_test={a['cost_holdout_test']['mean']:.1f} "
              f"oracle={a['oracle_cost']['mean']:.1f}")


if __name__ == "__main__":
    main()
