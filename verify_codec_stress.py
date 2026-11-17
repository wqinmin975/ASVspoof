"""Read-only validator for a local codec-stress re-run.

Checks output/cache integrity, feature-chain consistency, unchanged released
artifacts, and the hard guardrail that codec-stress metrics must NOT be merged
into the main Table-II result tables.

This script does NOT run codec_stress.py, does not decode audio, does not train
a model, and writes nothing. It is safe to run before the re-run (it will report
PENDING) and after it.
"""
import argparse
import csv
import hashlib
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
CONDS = ["clean", "g711_8k", "opus_12k", "opus_24k"]
REQUIRED_COLS = ["seed", "cond", "n", "temperature", "bias",
                 "auprc", "auroc", "cost_rule", "f1"]
RELEASED = ["feats.npz", "real_runs.csv", "real_summary.json"]


def p(name):
    return os.path.join(ROOT, name)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


results = []


def report(tag, ok, detail, pending=False):
    state = "PENDING" if pending else ("PASS" if ok else "FAIL")
    results.append((state, tag, detail))
    print(f"[{state:7}] {tag} — {detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600, help="must match the --n used in the re-run")
    a = ap.parse_args()
    half = a.n // 2
    out_csv = p("codec_stress.csv")
    caches = {c: p(os.path.join("codec_cache", f"{c}_n{a.n}.npz")) for c in CONDS}

    ran = os.path.exists(out_csv)

    # ---- O1 output integrity -------------------------------------------------
    if not ran:
        report("O1 output", False, "codec_stress.csv not found; re-run not executed yet", pending=True)
        rows = []
    else:
        with open(out_csv, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) if rows else []
        missing = [c for c in REQUIRED_COLS if c not in cols]
        pairs = [(r.get("seed"), r.get("cond")) for r in rows]
        seeds = sorted({r.get("seed") for r in rows})
        conds = sorted({r.get("cond") for r in rows})
        finite = True
        for r in rows:
            for c in REQUIRED_COLS[2:]:
                try:
                    if not np.isfinite(float(r.get(c, "nan"))):
                        finite = False
                except (TypeError, ValueError):
                    finite = False
        ok = (not missing and len(rows) == 8 and len(set(pairs)) == 8
              and seeds == ["0", "1"] and conds == sorted(CONDS) and finite
              and all(r.get("n") == str(a.n) for r in rows))
        report("O1 output", ok,
               f"rows={len(rows)} (expect 8), cols_missing={missing}, "
               f"seeds={seeds}, conds={conds}, finite={finite}")

    # ---- O2 shared calibration ----------------------------------------------
    if not rows:
        report("O2 shared T/b", False, "no rows", pending=not ran)
    else:
        ok = True
        for seed in ("0", "1"):
            sel = [r for r in rows if r["seed"] == seed]
            for key in ("temperature", "bias"):
                vals = [float(r[key]) for r in sel]
                if vals and max(vals) - min(vals) > 1e-9:
                    ok = False
        report("O2 shared T/b", ok,
               "one (temperature, bias) pair per seed, identical across all 4 conditions")

    # ---- O3 cache integrity --------------------------------------------------
    ok3, shapes = True, {}
    for c in CONDS:
        if not os.path.exists(caches[c]):
            ok3 = False
            shapes[c] = "missing"
            continue
        X = np.load(caches[c])["X"]
        shapes[c] = tuple(X.shape)
        if X.shape != (a.n, 50) or not np.all(np.isfinite(X)):
            ok3 = False
    report("O3 caches", ok3, f"shapes={shapes}", pending=not ran)

    # ---- O4 clean-chain consistency -----------------------------------------
    if not ran or not os.path.exists(caches["clean"]):
        report("O4 clean chain", False, "clean cache not available", pending=not ran)
    else:
        d = np.load(p("feats.npz"), allow_pickle=True)
        X, y = d["X"], d["y"]
        rng = np.random.default_rng(5)
        bona, spoof = np.where(y == 0)[0], np.where(y == 1)[0]
        pick = np.concatenate([rng.choice(bona, half, replace=False),
                               rng.choice(spoof, half, replace=False)])
        rest = np.setdiff1d(np.arange(len(y)), pick)
        mu, sd = X[rest].mean(0), X[rest].std(0) + 1e-9
        expected = (X[pick] - mu) / sd
        got = np.load(caches["clean"])["X"]
        delta = float(np.max(np.abs(got - expected)))
        report("O4 clean chain", delta < 1e-5,
               f"max|clean cache - feats.npz re-standardised| = {delta:.3e}")

    # ---- O5 released artifacts unchanged ------------------------------------
    ok5, detail = True, []
    for f in RELEASED:
        bak = p(os.path.join("backups", "2026-11-14", f))
        if not os.path.exists(bak):
            ok5, _ = False, detail.append(f"{f}: backup missing")
            continue
        same = sha(p(f)) == sha(bak)
        ok5 &= same
        detail.append(f"{f}={'same' if same else 'CHANGED'}")
    report("O5 released", ok5, ", ".join(detail))

    # ---- N1/N2 no-merge guardrails ------------------------------------------
    md = open(p("RESULTS.md"), encoding="utf-8").read()
    m3 = re.search(r"## S3 Results(.*?)(?=## S4)", md, re.S)
    m4 = re.search(r"## S4 Boundary(.*?)(?=## S5)", md, re.S)
    s3 = re.sub(r"\s+", " ", m3.group(1)) if m3 else ""
    s4 = re.sub(r"\s+", " ", m4.group(1)) if m4 else ""
    body_rows = [l for l in (m3.group(1).splitlines() if m3 else [])
                 if re.match(r"^\|\s*(MLP|logistic)\s*\|", l)]
    banned = [w for w in ("codec", "opus", "g711", "Table II") if w.lower() in s3.lower()]
    ok_n1 = len(body_rows) == 2 and not banned
    report("N1 S3 untouched", ok_n1,
           f"detector rows={len(body_rows)} (expect 2), banned tokens in S3={banned}")

    ok_n2 = ("must not be merged into the main result tables" in s4
             and "not quantitatively comparable" in s4)
    report("N2 S4 guardrail", ok_n2,
           "S4 retains non-comparability + no-merge statements")

    standalone = p("CODEC_STRESS_RESULTS.md")
    if not os.path.exists(standalone):
        report("N3 results file", False,
               "CODEC_STRESS_RESULTS.md not created yet (required if results are reported)",
               pending=True)
    else:
        head = open(standalone, encoding="utf-8").read()[:1600]
        ok_n3 = ("NOT comparable" in head and "Table II" in head
                 and "must NOT be merged" in head)
        report("N3 results file", ok_n3,
               "standalone results file carries the required non-comparability header")

    src = open(p("codec_stress.py"), encoding="utf-8").read()[:2000]
    report("N4 code warning", "NOT comparable" in src and "Do NOT merge" in src,
           "codec_stress.py top-of-file WARNING intact")

    fails = [t for s, t, _ in results if s == "FAIL"]
    pend = [t for s, t, _ in results if s == "PENDING"]
    print()
    print(f"summary: PASS={sum(1 for s, _, _ in results if s == 'PASS')} "
          f"FAIL={len(fails)} PENDING={len(pend)}")
    if pend:
        print("pending: " + ", ".join(pend))
    if fails:
        print("failed : " + ", ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
