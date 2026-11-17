"""Real-data anchor: cost-aware decision layer vs a fixed 0.5 threshold on ASVspoof5 dev audio.

Feature-channel note (P0-3 / 2026-11-14): features here are waveform-derived
50-dim vectors, DIFFERENT from the 4-channel 50-feature set of the main
synthetic simulation manuscript. A speech corpus has no signalling, media-flow
or dialogue-semantic channel. No external manuscript / Table II reference is
hardcoded here; absolute cost levels are not comparable with that testbed.

Protocol: 5 speaker-grouped folds x 2 seeds; 15% calibration holdout inside each
training fold (floor 64); temperature+bias calibration (torch LBFGS on log-T and
bias); two decoders (0.5 threshold vs the cost rule p >= c_FP/(c_FP+c_FN));
cost per 1,000 calls with c_FP=5, c_FN=20. Aggregation settings (population SD,
bootstrap seed/resamples/scope) are registered in stat_metadata.json; this
script writes ONLY real_runs.csv and never rewrites real_summary.json.
"""
import argparse, json, os
import numpy as np
import torch
import torch.nn as nn

C_FP, C_FN = 5.0, 20.0
THR_RULE = C_FP / (C_FP + C_FN)   # 0.2
EPS = 1e-6


def auroc(y, s):
    order = np.argsort(s)
    s_sorted = np.asarray(s)[order]
    ranks = np.empty(len(s), dtype=float)
    i = 0
    n = len(s)
    while i < n:
        j = i
        while j + 1 < n and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        ranks[order[i:j + 1]] = avg
        i = j + 1
    pos = np.asarray(y) == 1
    npos, nneg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def auprc(y, s):
    order = np.argsort(-s)
    yy = y[order]
    tp = np.cumsum(yy == 1)
    fp = np.cumsum(yy == 0)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / max(yy.sum(), 1)
    return float(np.sum(prec * (yy == 1)) / max(yy.sum(), 1))


def ece(y, p, bins=15):
    out = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if m.sum() == 0:
            continue
        out += m.mean() * abs(p[m].mean() - (y[m] == 1).mean())
    return float(out)


def f1_score(y, pred):
    tp = np.sum((pred == 1) & (y == 1))
    fp = np.sum((pred == 1) & (y == 0))
    fn = np.sum((pred == 0) & (y == 1))
    return float(2 * tp / max(2 * tp + fp + fn, 1))


def cost_per_1000(y, pred):
    fp = np.sum((pred == 1) & (y == 0))
    fn = np.sum((pred == 0) & (y == 1))
    return float((fp * C_FP + fn * C_FN) / len(y) * 1000)


def expected_cost(p, prior, thr):
    """Expected cost per 1,000 calls when the posterior is reweighted to `prior`."""
    odds = (prior / (1 - prior))
    pp = (p * odds) / (p * odds + (1 - p))
    pred = (pp >= thr).astype(int)
    c = np.where(pred == 1, (1 - pp) * C_FP, pp * C_FN)
    return float(c.mean() * 1000)


def pava(y, p):
    """Pool-adjacent-violators isotonic fit; returns (breakpoints, values)."""
    order = np.argsort(p)
    p_s, y_s = p[order], y[order].astype(float)
    blocks = []  # [start, end, sum_w, sum_wy]
    for i in range(len(p_s)):
        blocks.append([i, i, 1.0, y_s[i]])
        while len(blocks) > 1:
            a, b = blocks[-2], blocks[-1]
            if a[3] / a[2] <= b[3] / b[2]:
                break
            blocks.pop()
            blocks.pop()
            blocks.append([a[0], b[1], a[2] + b[2], a[3] + b[3]])
    xs, vs = [], []
    for st_, en_, sw, swy in blocks:
        xs.append(float(p_s[st_:en_ + 1].mean()))
        vs.append(float(swy / sw))
    return np.array(xs), np.array(vs)


def apply_isotonic(p, fit_p, fit_v):
    return np.interp(p, fit_p, fit_v, left=fit_v[0], right=fit_v[-1])


class MLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, 128), nn.ReLU(), nn.Dropout(0.1),
                                 nn.Linear(128, 128), nn.ReLU(), nn.Dropout(0.1),
                                 nn.Linear(128, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)


class LR(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.lin = nn.Linear(d, 1)

    def forward(self, x):
        return self.lin(x).squeeze(-1)


def train_model(kind, Xtr, ytr, seed, epochs=40):
    torch.manual_seed(seed)
    m = MLP(Xtr.shape[1]) if kind == "mlp" else LR(Xtr.shape[1])
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    lossf = nn.BCEWithLogitsLoss()
    X, y = torch.tensor(Xtr, dtype=torch.float32), torch.tensor(ytr, dtype=torch.float32)
    n = len(X)
    for ep in range(epochs):
        perm = torch.randperm(n, generator=torch.Generator().manual_seed(seed + ep))
        for i in range(0, n, 128):
            idx = perm[i:i + 128]
            opt.zero_grad()
            loss = lossf(m(X[idx]), y[idx])
            loss.backward()
            opt.step()
    m.eval()
    return m


def logits_of(m, X):
    with torch.no_grad():
        return m(torch.tensor(X, dtype=torch.float32)).numpy()


def fit_temperature(z, y):
    zt, yt = torch.tensor(z, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)
    a = torch.zeros(1, requires_grad=True)   # log temperature
    b = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([a, b], lr=0.5, max_iter=80)

    def closure():
        opt.zero_grad()
        loss = nn.functional.binary_cross_entropy_with_logits(zt / torch.exp(a) + b, yt)
        loss.backward()
        return loss
    opt.step(closure)
    return float(torch.exp(a)), float(b)


def speaker_grouped_fold_split(spk, seed, k=5):
    """Return k boolean test masks; each speaker appears in exactly one fold.

    P1-8 (2026-11-14): replaces the former pass-only ``fold_split`` stub. The
    RNG state, shuffle order and array_split are identical to the inline split
    previously used in main(), so the per-run numbers do NOT change. Equivalence
    is verified in RESULTS.check.md section 12.
    """
    uniq = np.unique(spk)
    rng = np.random.default_rng(1000 + seed)
    rng.shuffle(uniq)
    return [np.isin(spk, g) for g in np.array_split(uniq, k)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="feats.npz")
    ap.add_argument("--out", default="real_runs.csv")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--folds", type=int, default=5)
    a = ap.parse_args()

    d = np.load(a.feats, allow_pickle=True)
    X, y, spk = d["X"].astype(np.float64), d["y"].astype(int), d["spk"]
    print("data", X.shape, "pos", y.mean())

    rows = []
    for seed in range(a.seeds):
        masks = speaker_grouped_fold_split(spk, seed, a.folds)
        for k in range(a.folds):
            te = masks[k]
            tr = ~te
            Xtr, ytr = X[tr], y[tr]
            Xte, yte = X[te], y[te]
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd

            # 15% calibration holdout inside the training fold
            hrng = np.random.default_rng(7000 + seed * 10 + k)
            hi = hrng.permutation(len(Xtr))
            ncal = max(64, int(0.15 * len(Xtr)))
            cal, fit = hi[:ncal], hi[ncal:]
            Xcal, ycal = Xtr[cal], ytr[cal]
            Xfit, yfit = Xtr[fit], ytr[fit]

            for kind in ("mlp", "lr"):
                m = train_model(kind, Xfit, yfit, seed * 100 + k)
                zcal, zte = logits_of(m, Xcal), logits_of(m, Xte)
                T, b = fit_temperature(zcal, ycal)
                pcal = 1 / (1 + np.exp(-(zcal / T + b)))
                p = 1 / (1 + np.exp(-(zte / T + b)))
                # isotonic control on the same holdout
                fp_, fv_ = pava(ycal, pcal)
                p_iso = apply_isotonic(p, fp_, fv_)

                pred05 = (p >= 0.5).astype(int)
                predr = (p >= THR_RULE).astype(int)
                prediso = (p_iso >= THR_RULE).astype(int)
                rows.append(dict(seed=seed, fold=k, model=kind,
                                 n_te=int(te.sum()), pos_te=float(yte.mean()),
                                 auprc=auprc(yte, p), auroc=auroc(yte, p),
                                 ece=ece(yte, p), f1_05=f1_score(yte, pred05),
                                 f1_rule=f1_score(yte, predr),
                                 cost05=cost_per_1000(yte, pred05),
                                 cost_rule=cost_per_1000(yte, predr),
                                 delta=cost_per_1000(yte, pred05) - cost_per_1000(yte, predr),
                                 ece_iso=ece(yte, p_iso),
                                 cost_iso=cost_per_1000(yte, prediso),
                                 exp60_05=expected_cost(p, 0.60, 0.5),
                                 exp60_rule=expected_cost(p, 0.60, THR_RULE),
                                 # P1-7: exp22_* is a HISTORICAL NAME. These two
                                 # fields reweight using each fold's measured
                                 # test positive rate yte.mean(), NOT a fixed
                                 # prior of 0.22. Not reported in RESULTS.md.
                                 exp22_05=expected_cost(p, float(yte.mean()), 0.5),
                                 exp22_rule=expected_cost(p, float(yte.mean()), THR_RULE),
                                 thr_block=float(np.quantile(p, 0.5))))
                print(f"seed{seed} fold{k} {kind}: cost05={rows[-1]['cost05']:.0f} "
                      f"rule={rows[-1]['cost_rule']:.0f} auprc={rows[-1]['auprc']:.3f}", flush=True)

    import csv
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
