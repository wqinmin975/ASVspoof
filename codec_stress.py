"""Waveform-level codec stress: re-encode real audio, recompute features, re-score.

Conditions: clean FLAC, G.711 mu-law at 8 kHz, Opus at 12 and 24 kb/s.
The detector is trained once on the clean training split and evaluated on every
condition, so the numbers are a genuine waveform-chain degradation test rather
than the feature-domain proxy used in the main synthetic simulation.

# WARNING (P0-4 / 2026-11-14): Even after this repair, codec-stress results are
# NOT comparable against the main Table-II synthetic testbed. This anchor only
# uses waveform-audio-derived features, with NO signalling / media-flow semantic
# channels, and its protocol (single clean split) differs from the main
# 5-fold x 2-seed protocol. Do NOT merge codec-stress metrics into the main
# result tables.
#
# Repairs applied in this revision (code logic only; NOT executed here):
#   1. Scoring chain now reuses run_real_check.fit_temperature(): a 15% clean
#      calibration holdout (floor 64) fits ONE shared (temperature, bias) pair,
#      applied identically to every condition. Previously raw logits -> sigmoid
#      were thresholded directly, which is NOT the main protocol's calibrated
#      posterior (run_real_check.py:210-212).
#   2. ffmpeg concurrency is capped and each condition is processed with its own
#      bounded pool; per-condition .npz caches allow resuming after an OOM abort.
#      The 2026-11-13 attempt exhausted the host page-file with 6 workers.
"""
import argparse, os, subprocess, tempfile, wave, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import featlib

AUDIO = r"D:\ace\语义攻击\asvspoof5_check\audio\flac_D"
MAX_WORKERS = 4          # hard cap; the earlier run used 6 and exhausted page-file space
ALL_CONDS = ["clean", "g711_8k", "opus_12k", "opus_24k"]
CONDS = {
    "opus_12k": (["-ar", "16000", "-ac", "1", "-c:a", "libopus", "-b:a", "12k", "-f", "ogg"], ".ogg"),
    "opus_24k": (["-ar", "16000", "-ac", "1", "-c:a", "libopus", "-b:a", "24k", "-f", "ogg"], ".ogg"),
}
MU = 255.0


def g711(x16k):
    """G.711 mu-law round trip at 8 kHz, applied sample-wise in numpy."""
    x8 = x16k[::2]
    y = np.sign(x8) * np.log1p(MU * np.abs(x8)) / np.log1p(MU)
    q = np.round(y * 127.0) / 127.0
    xq = np.sign(q) * (np.expm1(np.abs(q) * np.log1p(MU))) / MU
    # back to 16 kHz by simple sample-and-hold
    up = np.repeat(xq, 2)
    return up


def stressed(path, args, suffix):
    fd, mid = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path] + args + [mid],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return featlib.features(featlib.decode(mid))
    finally:
        try:
            os.remove(mid)
        except OSError:
            pass


def _job(fid, cond):
    p = os.path.join(AUDIO, fid + ".flac")
    if cond == "clean":
        return featlib.features(featlib.decode(p)).tolist()
    if cond == "g711_8k":
        return featlib.features(g711(featlib.decode(p))).tolist()
    return stressed(p, *CONDS[cond]).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="feats.npz")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--workers", type=int, default=2,
                    help="ffmpeg workers, hard-capped at MAX_WORKERS (page-file protection)")
    ap.add_argument("--conds", default=",".join(ALL_CONDS),
                    help="comma-separated condition subset; run one at a time to bound peak memory")
    ap.add_argument("--cache-dir", default="codec_cache",
                    help="per-condition feature cache for resume after an OOM abort")
    ap.add_argument("--out", default="codec_stress.csv")
    a = ap.parse_args()
    workers = max(1, min(a.workers, MAX_WORKERS))
    conds = [c.strip() for c in a.conds.split(",") if c.strip()]
    bad = [c for c in conds if c not in ALL_CONDS]
    if bad:
        raise SystemExit(f"unknown conditions {bad}; choose from {ALL_CONDS}")
    os.makedirs(a.cache_dir, exist_ok=True)

    d = np.load(a.feats, allow_pickle=True)
    X, y, fid = d["X"], d["y"], d["fid"]
    rng = np.random.default_rng(5)
    bona = np.where(y == 0)[0]
    spoof = np.where(y == 1)[0]
    pick = np.concatenate([rng.choice(bona, a.n // 2, replace=False),
                           rng.choice(spoof, a.n // 2, replace=False)])
    rest = np.setdiff1d(np.arange(len(y)), pick)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import run_real_check as R

    rows = []
    Xtr, ytr = X[rest], y[rest]
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    Xtr = (Xtr - mu) / sd

    # P0-4: one bounded pool per condition + a per-condition .npz cache.
    # A crashed run can resume by re-invoking with --conds for the missing part;
    # completed conditions skip ffmpeg entirely.
    feats = {}
    for cond in conds:
        cache = os.path.join(a.cache_dir, f"{cond}_n{a.n}.npz")
        if os.path.exists(cache):
            feats[cond] = np.load(cache)["X"]
            print("cache hit", cond, feats[cond].shape, flush=True)
            continue
        with ProcessPoolExecutor(max_workers=workers) as ex:
            got = list(ex.map(_job, [fid[i] for i in pick], [cond] * len(pick), chunksize=4))
        F = (np.asarray(got) - mu) / sd
        np.savez_compressed(cache, X=F)
        feats[cond] = F
        print("feats", cond, F.shape, flush=True)

    # P0-4: ONE shared (temperature, bias) fitted on a 15% clean holdout
    # (floor 64), mirroring run_real_check.py:199-212. The same pair is applied
    # to EVERY condition, so the only variable between conditions is the codec.
    hrng = np.random.default_rng(7000)
    hi = hrng.permutation(len(Xtr))
    ncal = max(64, int(0.15 * len(Xtr)))
    cal, fit = hi[:ncal], hi[ncal:]
    Xcal, ycal = Xtr[cal], ytr[cal]
    Xfit, yfit = Xtr[fit], ytr[fit]

    for seed in (0, 1):
        m = R.train_model("mlp", Xfit, yfit, seed)
        T, b = R.fit_temperature(R.logits_of(m, Xcal), ycal)
        for cond in conds:
            p = 1 / (1 + np.exp(-(R.logits_of(m, feats[cond]) / T + b)))
            pred = (p >= R.THR_RULE).astype(int)
            rows.append(dict(seed=seed, cond=cond, n=int(len(pick)),
                             temperature=float(T), bias=float(b),
                             auprc=R.auprc(y[pick], p), auroc=R.auroc(y[pick], p),
                             cost_rule=R.cost_per_1000(y[pick], pred),
                             f1=R.f1_score(y[pick], pred)))
            print(rows[-1], flush=True)
    import csv
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
