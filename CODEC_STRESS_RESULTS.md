# Codec-stress anchor — standalone results (NOT part of the main result tables)

> **Non-comparability notice (P0-4, 2026-11-14):** these numbers are a waveform-codec
> robustness check on a separate ASVspoof5 anchor. They are **NOT comparable** with
> **Table II** of the main synthetic testbed and **must NOT be merged** into the main
> result tables. Reasons: waveform-only 50-dim features (no signalling / media-flow /
> semantic channel), a balanced 600-utterance subset, and a single clean-split protocol
> with one shared (temperature, bias) pair, versus the 5-fold × 2-seed speaker-grouped
> main protocol with per-fold calibration. Absolute `cost_rule` values here describe
> only **within-anchor relative degradation across codec conditions**.

*Executed 2026-11-14 on this host under explicit author instruction (exception to B01).
Raw output: `codec_stress.csv` (8 rows). Procedure and acceptance criteria:
`CODEC_STRESS_RUNBOOK.md`; validator: `verify_codec_stress.py`.*

## 1. Conditions and protocol

| Item | Value |
|---|---|
| Detector | MLP, trained on the clean split only (`n = 600` held out, 1,400 training) |
| Evaluation subset | 600 utterances, balanced 300 bona fide + 300 spoof (`default_rng(5)`) |
| Conditions | `clean` (FLAC), `g711_8k` (mu-law at 8 kHz, numpy round trip), `opus_12k`, `opus_24k` (libopus via ffmpeg) |
| Calibration | 15% clean holdout (floor 64, `default_rng(7000)`), **one shared** `(T, b)` from `run_real_check.fit_temperature`, applied identically to all four conditions |
| Seeds | 0, 1 → 2 runs per condition |
| Decoding | `@rule`, `p ≥ 0.2 = c_FP/(c_FP+c_FN)`, `c_FP = 5`, `c_FN = 20` |
| Cost unit | per 1,000 calls |
| ffmpeg | 9.0-full build, `libopus`; `--workers 2`, hard cap 4, one bounded pool per condition |

Because `T` and `b` are shared, the **only variable between conditions is the codec**.
`seed 0`: `T = 2.0316`, `b = -0.2623`; `seed 1`: `T = 1.8809`, `b = -0.0085`.
Within each seed the four conditions use identical values (verified by O2).

## 2. Results (mean over 2 seeds)

| condition | AUPRC | AUROC | cost @rule [per 1,000 calls] | F1 @rule |
|---|---|---|---|---|
| clean | 0.8923 | 0.8814 | 1,862.5 | 0.7930 |
| g711_8k | 0.7094 | 0.7225 | 2,670.8 | 0.7079 |
| opus_12k | 0.8618 | 0.8562 | 2,095.8 | 0.7441 |
| opus_24k | 0.8640 | 0.8586 | 2,033.3 | 0.7624 |

### Within-anchor change relative to `clean` (the only comparison drawn here)

| condition | Δ cost [per 1,000 calls] | relative Δ cost | Δ AUPRC | Δ F1 |
|---|---|---|---|---|
| g711_8k | +808.3 | +43.4% | −0.1829 | −0.0851 |
| opus_12k | +233.3 | +12.5% | −0.0305 | −0.0489 |
| opus_24k | +170.8 | +9.2% | −0.0283 | −0.0306 |

The ordering is monotone in codec severity within this anchor: G.711 8 kHz degrades
the detector most, Opus 24 kb/s least; every degraded condition raises `cost @rule`
and lowers AUPRC and F1 relative to `clean`.

## 3. What these numbers do **not** support

1. No comparison with any cost value from `RESULTS.md` S3 or from Table II — those
   come from a different corpus, feature channel and evaluation protocol.
2. No claim about signalling / media-flow / semantic-channel robustness: this anchor
   has no such channels.
3. No cross-detector claim (only MLP was evaluated) and no confidence interval
   (two seeds only; no bootstrap was run for this branch).
4. No claim that the decision layer "beats" any synthetic-testbed baseline under codec
   stress — this branch evaluates only `@rule` and has no `@0.5` column.
5. The `clean` row is **not** a replication of the main protocol's absolute cost level;
   it is the reference condition of this separate subset.

## 4. Reproducibility and quarantine

- Per-condition feature caches: `codec_cache/{clean,g711_8k,opus_12k,opus_24k}_n600.npz`.
- Per-condition partial CSVs: `part_*.csv`; combined: `codec_stress.csv`; smoke tests:
  `smoke_*.csv` / `codec_smoke/` (diagnostics only, not reportable results).
- `verify_codec_stress.py` checks output/cache integrity, the shared calibration pair,
  agreement of the `clean` cache with `feats.npz`, unchanged released artifacts, and
  the no-merge guardrails on `RESULTS.md`.
- `feats.npz`, `real_runs.csv` and `real_summary.json` remain byte-identical to
  `backups/2026-11-14/`; the main experiment was not re-run.
- Known harmless warning: `run_real_check.py:168` converts a `requires_grad` tensor to
  a Python float inside `fit_temperature`. The same warning occurs in the main protocol;
  no numerical change was made to suppress it.

**Quarantine rule:** any manuscript / Response-to-Reviewer text using these numbers must
carry the non-comparability notice above, must describe only within-anchor relative
changes, and must not place them in the same table or sentence as Table II values.
