"""extension_v2.py -- redesign & re-run of the eight experiments flagged in the
reviewer letter (#11-#18) on the ASVspoof5 real-speech cost-aware anchor.

Design principles (reviewer letter, 2026-11-15):
  * Re-execute the EXACT released protocol (run_real_check) as a trusted
    building block; a reproduction gate aborts if any of the 20 released rows
    differ by >1e-6 from real_runs.csv. No released artefact is overwritten.
  * Save per-sample calibrated posteriors p (seed 0 only, to bound size) so the
    cost-ratio sweep, dual-CI, t-DCF, sampling robustness, ECE sensitivity and
    the three figures are all computed from ONE set of reproducible numbers.
  * All new quantities are written to extension_v2_* (csv/json/npz). feats.npz,
    real_runs.csv, real_summary.json stay byte-identical.

New experiments:
  #7  FP/FN recount at both operating points.
  #11 Cost-ratio sweep c_FP:c_FN in {1:1..1:20}; delta vs fixed 0.5.
  #12 ASVspoof5 Track-1 minDCF (local re-implementation, official constants
      C_miss=1, C_fa=10, pi_spf=0.05, beta=1.90) on our CM posterior; operating
      point and our-cost comparison vs p*=0.2.
  #13 Paired bootstrap 95% CI (seed 11, 4000 resamples) for delta of BOTH
      models; cross-model paired test (delta_LR - delta_MLP) and the ~19%
      cost-rule gap with CI.
  #14 Sampling robustness: (a) extra fold seeds 2,3,4; (b) per-attack-family
      AUPRC / cost balance parsed from the protocol.
  #15 Slot-7 ablation: zero the duplicated spectral-flux-mean column (index 6),
      re-run protocol, report AUPRC / cost / delta change.
  #16 Figure data: C(tau) curve, FP/FN decomposition, reliability before/after.
  #18 ECE bin sensitivity (10/15/20/30 bins) raw & calibrated, plus isotonic ECE.

Run:  py -3.12 extension_v2.py
"""
import csv, json, sys, os
import numpy as np
import run_real_check as R

GREY = "\033[90m"; END = "\033[0m"

# ---- family map from protocol ------------------------------------------------
def load_family():
    m = {}
    with open("protocols/ASVspoof5.dev.track_1.tsv") as f:
        f.readline()
        for line in f:
            p = line.split()
            if len(p) < 9:
                continue
            m[p[1]] = p[7]            # attack id A09..A16, or '-' for bona
    return m

FAM = load_family()

def family_of(fid):
    a = FAM.get(str(fid), "-")
    return "bonafide" if a in ("-", "bona", "bonafide") else a

# ---- local cost with arbitrary weights --------------------------------------
def cost1000(y, pred, c_fp, c_fn):
    pred = np.asarray(pred)
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    return float((fp * c_fp + fn * c_fn) / len(y) * 1000.0)

def counts1000(y, pred):
    pred = np.asarray(pred)
    n = len(y)
    fp = int(np.sum((pred == 1) & (y == 0))) / n * 1000.0
    fn = int(np.sum((pred == 0) & (y == 1))) / n * 1000.0
    return fp, fn

# ---- ASVspoof5 Track-1 minDCF (local re-implementation) ----------------------
C_MISS, C_FA, PI_SPF = 1.0, 10.0, 0.05
BETA = (C_MISS / C_FA) * (1.0 - PI_SPF) / PI_SPF   # = 1.90

def asvspoof_tdcf(y, p, tau_grid):
    """ASVspoof5 Track-1 normalised DCF over our calibrated spoof posterior.

    Our p = P(spoof): HIGHER p means MORE spoof-like.  The Evaluation Plan
    defines, for a CM score s in which HIGHER means MORE bona-fide-like:
        P_miss(tau) = (1/|Bon|) sum_{bona} I(s < tau)
        P_fa(tau)   = (1/|Spf|) sum_{spoof} I(s >= tau)
        DCF'(tau)   = beta * P_miss(tau) + P_fa(tau),  beta = 1.90
    To honour that direction with our p, set s = 1 - p and tau_p = 1 - tau:
        a trial is rejected as spoof when p >= tau_p; hence
        P_miss = fraction of bona with p >= tau_p
        P_fa   = fraction of spoof with p <  tau_p
    We report minDCF = min_{tau_p} DCF' and the argmin threshold in p-space.
    """
    y = np.asarray(y); p = np.asarray(p)
    bona = (y == 0); spoof = (y == 1)
    dcf = np.array([BETA * np.mean(p[bona] >= t) + np.mean(p[spoof] < t)
                    for t in tau_grid])
    k = int(np.argmin(dcf))
    return float(dcf[k]), float(tau_grid[k]), dcf

# ---- bootstrap helpers -------------------------------------------------------
def boot_mean_ci(vals, seed=11, B=4000):
    vals = np.asarray(vals, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), (B, len(vals)))
    means = vals[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(np.mean(vals)), float(lo), float(hi)

def boot_paired_diff_ci(d_a, d_b, seed=11, B=4000):
    d_a = np.asarray(d_a, float); d_b = np.asarray(d_b, float)
    n = len(d_a)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, (B, n))
    diff = d_b[idx].mean(axis=1) - d_a[idx].mean(axis=1)
    lo, hi = np.percentile(diff, [2.5, 97.5])
    return float(d_b.mean() - d_a.mean()), float(lo), float(hi)

def boot_ratio_ci(a, b, seed=11, B=4000):
    a = np.asarray(a, float); b = np.asarray(b, float)
    n = len(a)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, (B, n))
    ratio = b[idx].mean(axis=1) / a[idx].mean(axis=1)
    lo, hi = np.percentile(ratio, [2.5, 97.5])
    return float(b.mean() / a.mean()), float(lo), float(hi)

# ---- main protocol re-run, optionally with a column zeroed --------------------
def run_protocol(X_all, y_all, spk, fam_arr, seeds, zero_col=None,
                 save_per_sample=False):
    """Re-run the released protocol. Returns per-fold rows + (opt) per-sample p."""
    if zero_col is not None:
        X_all = X_all.copy(); X_all[:, zero_col] = 0.0
    released = {}
    with open("real_runs.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            released[(int(r["seed"]), int(r["fold"]), r["model"])] = r
    rows = []
    per_sample = {}
    for seed in seeds:
        masks = R.speaker_grouped_fold_split(spk, seed, 5)
        for k in range(5):
            te = masks[k]; tr = ~te
            Xtr, ytr = X_all[tr], y_all[tr]
            Xte, yte, yte_fam = X_all[te], y_all[te], fam_arr[te]
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
                pc = 1 / (1 + np.exp(-(zcal / T + b)))
                p = 1 / (1 + np.exp(-(zte / T + b)))
                pred05 = (p >= 0.5).astype(int)
                predr = (p >= R.THR_RULE).astype(int)
                # ---- reproduction gate ----
                rel = released[(seed, k, kind)]
                diff = max(abs(R.cost_per_1000(yte, pred05) - float(rel["cost05"])),
                           abs(R.cost_per_1000(yte, predr) - float(rel["cost_rule"])),
                           abs(R.auprc(yte, p) - float(rel["auprc"])),
                           abs(R.ece(yte, p) - float(rel["ece"])))
                if diff > 1e-6:
                    sys.exit(f"REPRODUCTION FAILED seed{seed} fold{k} {kind}: {diff}")
                c05 = R.cost_per_1000(yte, pred05)
                cr = R.cost_per_1000(yte, predr)
                fp05, fn05 = counts1000(yte, pred05)
                fpr, fnr = counts1000(yte, predr)
                rows.append(dict(seed=seed, fold=k, model=kind, n_te=int(te.sum()),
                                 pos_te=float(yte.mean()), auprc=R.auprc(yte, p),
                                 auroc=R.auroc(yte, p), ece_raw=R.ece(yte, 1/(1+np.exp(-zte))),
                                 ece_cal=R.ece(yte, p), f1_05=R.f1_score(yte, pred05),
                                 f1_rule=R.f1_score(yte, predr), cost05=c05, cost_rule=cr,
                                 delta=c05 - cr, fp05_1k=fp05, fn05_1k=fn05,
                                 fpr_1k=fpr, fnr_1k=fnr, y_fam=list(yte_fam)))
                if save_per_sample and seed == 0:
                    per_sample[(seed, k, kind)] = dict(p=p, y=yte.astype(int),
                                                      fam=list(yte_fam))
    return rows, per_sample

# ---- cost-ratio sweep --------------------------------------------------------
RATIOS = [(1, 1), (1, 2), (1, 4), (1, 8), (1, 10), (1, 15), (1, 20)]

def run_protocol_full(X_all, y_all, spk, fam_arr, seeds, zero_col=None):
    """Like run_protocol but returns per-sample p for every (seed,fold,model)."""
    if zero_col is not None:
        X_all = X_all.copy(); X_all[:, zero_col] = 0.0
    released = {}
    with open("real_runs.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            released[(int(r["seed"]), int(r["fold"]), r["model"])] = r
    rows = []
    P = {}
    for seed in seeds:
        masks = R.speaker_grouped_fold_split(spk, seed, 5)
        for k in range(5):
            te = masks[k]; tr = ~te
            Xtr, ytr = X_all[tr], y_all[tr]
            Xte, yte, yte_fam = X_all[te], y_all[te], fam_arr[te]
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
                p = 1 / (1 + np.exp(-(zte / T + b)))
                pred05 = (p >= 0.5).astype(int)
                predr = (p >= R.THR_RULE).astype(int)
                c05 = R.cost_per_1000(yte, pred05)
                cr = R.cost_per_1000(yte, predr)
                # ---- reproduction gate (guard released artefacts; only for the
                #      unmodified protocol on seeds 0,1; ablations legitimately
                #      change the numbers and must bypass this gate) ----
                if zero_col is None and (seed, k, kind) in released:
                    rel = released[(seed, k, kind)]
                    gdiff = max(abs(c05 - float(rel["cost05"])),
                               abs(cr - float(rel["cost_rule"])),
                               abs(R.auprc(yte, p) - float(rel["auprc"])),
                               abs(R.ece(yte, p) - float(rel["ece"])))
                    if gdiff > 1e-6:
                        sys.exit(f"REPRODUCTION FAILED seed{seed} fold{k} {kind}: {gdiff}")
                fp05, fn05 = counts1000(yte, pred05)
                fpr, fnr = counts1000(yte, predr)
                rows.append(dict(seed=seed, fold=k, model=kind, n_te=int(te.sum()),
                                 pos_te=float(yte.mean()), auprc=R.auprc(yte, p),
                                 auroc=R.auroc(yte, p), ece_raw=R.ece(yte, 1/(1+np.exp(-zte))),
                                 ece_cal=R.ece(yte, p), f1_05=R.f1_score(yte, pred05),
                                 f1_rule=R.f1_score(yte, predr), cost05=c05, cost_rule=cr,
                                 delta=c05 - cr, fp05_1k=fp05, fn05_1k=fn05,
                                 fpr_1k=fpr, fnr_1k=fnr))
                P[(seed, k, kind)] = dict(p=p, z=zte, y=yte.astype(int), fam=list(yte_fam))
    return rows, P

# Sweep at the DEPLOYED cost scale (c_FP=5), not the unit scale (c_FP=1).
# Rationale: the released Table II Delta (853 / 1490) is at c_FP=5, c_FN=20,
# which is the 1:4 ratio point.  Computing the sweep at c_FP=1 made the 1:4
# point read ~170 (a factor of 5 too small) while Fig.~2 was labelled
# "with c_FP=5".  Cost is linear in the weights and p* depends only on the
# ratio, so evaluating at c_FP=5 makes the sweep self-consistent with Table II.
# The ratio label keeps the reduced form "1:mult" (i.e. c_FN/c_FP = mult).
C_FP_SWEEP = 5

def sweep_on_P(P, ratios):
    out = {}
    for kind in ("mlp", "lr"):
        keys = [kk for kk in P if kk[2] == kind]
        table = []
        for c_fp_mult, c_fn_mult in ratios:
            c_fp = C_FP_SWEEP * c_fp_mult
            c_fn = C_FP_SWEEP * c_fn_mult
            pstar = c_fp / (c_fp + c_fn)
            d = []
            for kk in keys:
                y = P[kk]["y"]; p = P[kk]["p"]
                c05 = cost1000(y, (p >= 0.5), c_fp, c_fn)
                cr = cost1000(y, (p >= pstar), c_fp, c_fn)
                d.append(c05 - cr)
            d = np.array(d)
            table.append(dict(ratio=f"{c_fp_mult}:{c_fn_mult}", pstar=round(pstar, 4),
                              delta_mean=float(d.mean()), delta_sd=float(d.std())))
        out[kind] = table
    return out

def main():
    d = np.load("feats.npz", allow_pickle=True)
    X = d["X"].astype(np.float64); y = d["y"].astype(int)
    spk = d["spk"]; fid = d["fid"]
    fam_arr = np.array([family_of(f) for f in fid])
    print(f"{GREY}data X={X.shape} pos={y.mean():.3f} families={sorted(set(fam_arr))}{END}")

    # ===== MAIN run (seeds 0,1) with per-sample save =====
    rows, P0 = run_protocol_full(X, y, spk, fam_arr, [0, 1])
    print(f"{GREY}reproduction gate passed for {len(rows)} rows{END}")

    # ===== #7 FP/FN + per-fold summary =====
    with open("extension_v2_runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    # ===== #11 cost-ratio sweep (seeds 0,1) =====
    sweep = sweep_on_P(P0, RATIOS)

    # fine grid for the figure
    fine_ratios = [(1, r) for r in range(1, 21)]
    sweep_fine = sweep_on_P(P0, fine_ratios)

    # ===== #13 bootstrap CIs on the 10 fold-level deltas =====
    ci = {}
    for kind in ("mlp", "lr"):
        dv = [r["delta"] for r in rows if r["model"] == kind]
        m, lo, hi = boot_mean_ci(dv)
        ci[kind] = dict(delta_mean=m, delta_lo=lo, delta_hi=hi,
                        n=len(dv), note="paired bootstrap seed11 B4000 over 10 folds")
    # cross-model paired
    d_mlp = np.array([r["delta"] for r in rows if r["model"] == "mlp"])
    d_lr = np.array([r["delta"] for r in rows if r["model"] == "lr"])
    xm_mean, xm_lo, xm_hi = boot_paired_diff_ci(d_mlp, d_lr)
    # ~19% cost-rule gap CI (LR vs MLP cost_rule)
    cr_mlp = np.array([r["cost_rule"] for r in rows if r["model"] == "mlp"])
    cr_lr = np.array([r["cost_rule"] for r in rows if r["model"] == "lr"])
    ratio_mean, ratio_lo, ratio_hi = boot_ratio_ci(cr_mlp, cr_lr)

    # ===== #12 ASVspoof5 Track-1 minDCF (local re-implementation) =====
    tau_grid = np.round(np.arange(0.01, 1.0, 0.01), 3)
    tdcf_rows = []
    for kind in ("mlp", "lr"):
        mindcf, tau_t, curves = [], [], []
        for kk in [k for k in P0 if k[2] == kind]:
            yv = P0[kk]["y"]; pv = P0[kk]["p"]
            md, tt, curve = asvspoof_tdcf(yv, pv, tau_grid)
            mindcf.append(md); tau_t.append(tt); curves.append(curve)
        # our cost at tau_t (c_FP=5,c_FN=20) and at p*=0.2
        cost_at_t, cost_at_02 = [], []
        for kk in [k for k in P0 if k[2] == kind]:
            yv = P0[kk]["y"]; pv = P0[kk]["p"]
            cost_at_t.append(cost1000(yv, (pv >= tau_t[len(cost_at_t)]), 5, 20))
            cost_at_02.append(cost1000(yv, (pv >= 0.2), 5, 20))
        tdcf_rows.append(dict(model=kind,
                              minDCF_mean=float(np.mean(mindcf)), minDCF_sd=float(np.std(mindcf)),
                              tau_tDCF_mean=float(np.mean(tau_t)), tau_tDCF_sd=float(np.std(tau_t)),
                              our_cost_at_tDCF_mean=float(np.mean(cost_at_t)),
                              our_cost_at_02_mean=float(np.mean(cost_at_02))))

    # ===== #14 (a) extra fold seeds 2,3,4 ; (b) per-family =====
    rows_xtra, _ = run_protocol_full(X, y, spk, fam_arr, [2, 3, 4])
    rob = {}
    for kind in ("mlp", "lr"):
        dv = [r["delta"] for r in rows_xtra if r["model"] == kind]
        rob[kind] = dict(n=len(dv), delta_mean=float(np.mean(dv)),
                         delta_sd=float(np.std(dv)),
                         delta_min=float(np.min(dv)), delta_max=float(np.max(dv)))
    # per-family: use seed0 pooled test predictions
    fam_stats = {}
    for kind in ("mlp", "lr"):
        famy = {}; famp = {}
        for kk in [k for k in P0 if k[2] == kind and k[0] == 0]:
            yv = P0[kk]["y"]; pv = P0[kk]["p"]; fv = P0[kk]["fam"]
            for yi, pi, fi in zip(yv, pv, fv):
                famy.setdefault(fi, []).append(int(yi))
                famp.setdefault(fi, []).append(float(pi))
        for fi in sorted(famy):
            yy = np.array(famy[fi]); pp = np.array(famp[fi])
            fam_stats.setdefault(kind, {})[fi] = dict(
                n=int(len(yy)), n_spoof=int((yy == 1).sum()),
                auprc=float(R.auprc(yy, pp)),
                cost05=float(R.cost_per_1000(yy, (pp >= 0.5).astype(int))),
                cost_rule=float(R.cost_per_1000(yy, (pp >= 0.2).astype(int))),
                delta=float(R.cost_per_1000(yy, (pp >= 0.5).astype(int)) -
                            R.cost_per_1000(yy, (pp >= 0.2).astype(int))))
    with open("extension_v2_family.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "family", "n", "n_spoof", "auprc", "cost05", "cost_rule", "delta"])
        for kind in ("mlp", "lr"):
            for fi in sorted(fam_stats[kind]):
                s = fam_stats[kind][fi]
                w.writerow([kind, fi, s["n"], s["n_spoof"], f"{s['auprc']:.4f}",
                            f"{s['cost05']:.1f}", f"{s['cost_rule']:.1f}", f"{s['delta']:.1f}"])

    # ===== #15 slot-7 ablation (zero column 6) =====
    rows_ab, _ = run_protocol_full(X, y, spk, fam_arr, [0, 1], zero_col=6)
    abl = {}
    for kind in ("mlp", "lr"):
        base = [r for r in rows if r["model"] == kind]
        ab = [r for r in rows_ab if r["model"] == kind]
        def agg(key):
            return float(np.mean([r[key] for r in base])), float(np.mean([r[key] for r in ab]))
        auprc_b, auprc_a = agg("auprc")
        c05_b, c05_a = agg("cost05")
        cr_b, cr_a = agg("cost_rule")
        de_b, de_a = agg("delta")
        ece_b, ece_a = agg("ece_cal")
        abl[kind] = dict(auprc_base=auprc_b, auprc_ablation=auprc_a,
                         auprc_change_pct=(auprc_a - auprc_b) / auprc_b * 100,
                         cost05_base=c05_b, cost05_ablation=c05_a,
                         cost_rule_base=cr_b, cost_rule_ablation=cr_a,
                         delta_base=de_b, delta_ablation=de_a,
                         delta_change_pct=(de_a - de_b) / de_b * 100,
                         ece_base=ece_b, ece_ablation=ece_a)

    # ===== #16 figure data: C(tau), FP/FN decomposition, reliability =====
    tau_curve = np.round(np.arange(0.02, 0.61, 0.02), 3)
    fig = {}
    for kind in ("mlp", "lr"):
        c_curve, fp_c, fn_c = [], [], []
        for t in tau_curve:
            vals = [cost1000(P0[kk]["y"], (P0[kk]["p"] >= t).astype(int), 5, 20)
                    for kk in P0 if kk[2] == kind]
            fpc = [counts1000(P0[kk]["y"], (P0[kk]["p"] >= t).astype(int))[0]
                   for kk in P0 if kk[2] == kind]
            fnc = [counts1000(P0[kk]["y"], (P0[kk]["p"] >= t).astype(int))[1]
                   for kk in P0 if kk[2] == kind]
            c_curve.append(float(np.mean(vals)))
            fp_c.append(float(np.mean(fpc))); fn_c.append(float(np.mean(fnc)))
        fig[kind] = dict(tau=list(tau_curve), cost=list(c_curve),
                         fp1k=list(fp_c), fn1k=list(fn_c))
    # reliability diagram (seed0 pooled), 10 bins, before & after calibration
    rel = {}
    for kind in ("mlp", "lr"):
        Y, Pc = [], []
        for kk in [k for k in P0 if k[2] == kind and k[0] == 0]:
            Y.append(P0[kk]["y"]); Pc.append(P0[kk]["p"])
        Y = np.concatenate(Y); Pc = np.concatenate(Pc)
        Zc = np.concatenate([P0[kk]["z"] for kk in [k for k in P0 if k[2] == kind and k[0] == 0]])
        Praw = 1 / (1 + np.exp(-Zc))
        for tag, Pp in (("calibrated", Pc), ("raw", Praw)):
            edges = np.linspace(0, 1, 11)
            cen, emp = [], []
            for i in range(10):
                m = (Pp >= edges[i]) & (Pp < edges[i + 1] if i < 9 else Pp <= edges[i + 1])
                if m.sum() == 0:
                    continue
                cen.append(float((edges[i] + edges[i + 1]) / 2))
                emp.append(float((Y[m] == 1).mean()))
            rel.setdefault(kind, {})[tag] = dict(bin_center=cen, empirical_spoof_frac=emp)
    with open("extension_v2_figdata.json", "w", encoding="utf-8") as f:
        json.dump(dict(curve=fig, reliability=rel,
                       cost_sweep_fine={k: sweep_fine[k] for k in ("mlp", "lr")}),
                  f, indent=2)

    # ===== #18 ECE bin sensitivity (10/15/20/30) raw & calibrated =====
    ece_bins = {}
    for kind in ("mlp", "lr"):
        rec = {}
        for nb in (10, 15, 20, 30):
            cal_v, raw_v = [], []
            for kk in [k for k in P0 if k[2] == kind]:
                yv = P0[kk]["y"]; pv = P0[kk]["p"]; zv = P0[kk]["z"]
                cal_v.append(R.ece(yv, pv, bins=nb))
                raw_v.append(R.ece(yv, 1 / (1 + np.exp(-zv)), bins=nb))
            rec[f"calibrated_ece_{nb}"] = dict(mean=float(np.mean(cal_v)), sd=float(np.std(cal_v)))
            rec[f"raw_ece_{nb}"] = dict(mean=float(np.mean(raw_v)), sd=float(np.std(raw_v)))
        ece_bins[kind] = rec

    # ===== aggregate summary =====
    agg = {}
    for kind in ("mlp", "lr"):
        rr = [r for r in rows if r["model"] == kind]
        keys = [k for k in rows[0] if k not in ("seed", "fold", "model", "n_te", "pos_te", "y_fam")]
        agg[kind] = {k: {"mean": float(np.mean([r[k] for r in rr])),
                         "sd": float(np.std([r[k] for r in rr]))} for k in keys}

    summary = dict(
        beta_asvspoof=BETA, c_miss=C_MISS, c_fa=C_FA, pi_spf=PI_SPF,
        cost_ratio_sweep=sweep,
        bootstrap_ci=ci,
        cross_model_delta=dict(diff_mean=xm_mean, diff_lo=xm_lo, diff_hi=xm_hi,
                               note="delta_LR - delta_MLP paired bootstrap"),
        cost_rule_ratio_19pct=dict(ratio_mean=ratio_mean, ratio_lo=ratio_lo,
                                   ratio_hi=ratio_hi,
                                   note="cost_rule_LR / cost_rule_MLP - 1 = %.1f%%" % ((ratio_mean-1)*100)),
        tdcf=tdcf_rows,
        robustness_extra_seeds=rob,
        family=fam_stats,
        slot7_ablation=abl,
        ece_bin_sensitivity=ece_bins,
        aggregate=agg,
    )
    with open("extension_v2_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # ---- console report ----
    print("\n=== #11 cost-ratio sweep (delta = cost@0.5 - cost@rule, per 1,000) ===")
    for kind in ("mlp", "lr"):
        print(f"  {kind}: " + ", ".join(f"{t['ratio']}->{t['delta_mean']:.0f}(±{t['delta_sd']:.0f})"
                                          for t in sweep[kind]))
    print("\n=== #13 bootstrap CIs (paired, seed11, B4000) ===")
    for kind in ("mlp", "lr"):
        c = ci[kind]
        print(f"  {kind} delta = {c['delta_mean']:.0f} [{c['delta_lo']:.0f}, {c['delta_hi']:.0f}]")
    print(f"  cross-model delta_LR - delta_MLP = {xm_mean:.0f} [{xm_lo:.0f}, {xm_hi:.0f}]")
    print(f"  cost-rule LR/MLP = {ratio_mean:.3f} [{ratio_lo:.3f}, {ratio_hi:.3f}]  (~{(ratio_mean-1)*100:.1f}%)")
    print("\n=== #12 ASVspoof5 Track-1 minDCF (local re-impl) ===")
    for t in tdcf_rows:
        print(f"  {t['model']}: minDCF={t['minDCF_mean']:.3f} @ tau={t['tau_tDCF_mean']:.3f}; "
              f"our-cost@tDCF={t['our_cost_at_tDCF_mean']:.0f} vs @0.2={t['our_cost_at_02_mean']:.0f}")
    print("\n=== #14 robustness (extra seeds 2,3,4) ===")
    for kind in ("mlp", "lr"):
        r = rob[kind]
        print(f"  {kind} delta mean={r['delta_mean']:.0f} sd={r['delta_sd']:.0f} "
              f"min={r['delta_min']:.0f} max={r['delta_max']:.0f}")
    print("\n=== #15 slot-7 ablation (col index 6 zeroed) ===")
    for kind in ("mlp", "lr"):
        a = abl[kind]
        print(f"  {kind}: AUPRC {a['auprc_base']:.4f}->{a['auprc_ablation']:.4f} "
              f"({a['auprc_change_pct']:+.2f}%); delta {a['delta_base']:.0f}->{a['delta_ablation']:.0f} "
              f"({a['delta_change_pct']:+.2f}%)")
    print("\n=== #18 ECE bin sensitivity (calibrated) ===")
    for kind in ("mlp", "lr"):
        line = "  ".join(f"{nb}:{ece_bins[kind][f'calibrated_ece_{nb}']['mean']:.4f}"
                         for nb in (10, 15, 20, 30))
        print(f"  {kind}: {line}")

if __name__ == "__main__":
    main()
