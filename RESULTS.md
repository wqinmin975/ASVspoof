# Real-data anchor: ASVspoof5 dev, decision layer vs 0.5 threshold

*Version v1.1 — revised 2026-11-14. Revision history: Appendix A.*

## S1 Motivation and provenance

This experiment is a real-speech anchor for the relative benefit of the cost-aware
decision layer over a fixed 0.5 probability threshold, so that the claim does not
rest entirely on a synthetic testbed.

> **Provenance note.** References to "the paper", "Table II" and "the simulation"
> point to the main synthetic-testbed manuscript and its results, which are **not
> contained in this ASVspoof-5 anchor working directory**; their values are not
> reproduced here. The 60% attack-prior setting is a **post-hoc re-weighting target**,
> not a prior measured from this corpus.

## S2 Data and protocol

**Corpus.** ASVspoof5 dev, protocol `ASVspoof5.dev.track_1.tsv` (140,950 lines,
785 distinct speakers at **corpus level**). The manuscript display shard name
`flac_D_aa` corresponds to the local directory `audio/flac_D`, which holds
47,400 FLAC files; all 47,400 are present in the protocol, and 93,550 protocol
entries have no local audio. 8 attack families A09–A16.

**Subset.** 2,000 utterances: 1,000 bona fide + 1,000 spoof (125 per family),
speaker IDs from the protocol. All 2,000 file IDs are stored in `feats.npz["fid"]`,
so the folds, training and evaluation reproduce directly from that field.
Sampling used `default_rng(2026)` over `sorted(files)` **without speaker
stratification**, so the **628** distinct speakers it covers are a derived
quantity, not a design parameter — and these 628 (not the corpus-level 785) are
the population used for the speaker-grouped folds. Regenerating `feats.npz` from
raw protocol + FLAC additionally depends on the numpy version, the sorted filename
order and the shared RNG state; these are registered in `sampling_metadata.json`.

**Features.** A 50-dim vector derived only from the decoded waveform:
10 scalar statistics + 25 log-mel band energies + 15 MFCC coefficients (2..16)
= 50 dimensions. This is deliberately **NOT the 4-channel 50-feature space** of
the main synthetic simulation: a speech corpus has no signalling, media-flow or
dialogue-semantic channel. Note (P1-3, option A): the legacy feature docstring
declared a spectral-flux std dimension that was never implemented; slot 7
duplicates the slot-6 flux mean, so one of the 50 dimensions is duplicated.
Only the comment was corrected — `feats.npz` is unchanged.

**Protocol.** 5 speaker-grouped folds × 2 seeds = 10 runs per detector (grouped
over the 628 subset speakers); a 15% calibration holdout inside each training
fold (floor `max(64, int(0.15 * len(Xtr)))`); temperature+bias calibration; two
detectors (MLP, logistic regression).

**Cost.** Reported **per 1,000 calls**, with `c_FP = 5`, `c_FN = 20`. For a
single call the expected cost is
`E[cost] = c_FP · P(false alarm) + c_FN · P(miss)`; the tabulated values are
this quantity multiplied by 1,000. The corresponding cost-aware threshold is
`p* = c_FP/(c_FP + c_FN) = 5/25 = 0.2`.

**Decoders.** `@0.5` is the fixed threshold `p >= 0.5`; `@rule` (also written
*decision layer* / *cost rule* / `p >= 0.2`) is cost-aware decoding at `p*`.
These four terms denote the **same** decoder; the threshold is a function of the
chosen cost weights, not a tuned hyperparameter. ECE below is computed after
temperature+bias calibration; the isotonic control (`ece_iso`, `cost_iso`) was
computed but is **not tabulated**.

**Statistics.** Means over 10 runs, with the **population SD over the 10 runs**
in parentheses (implementation: `statistics.pstdev`, ddof = 0; see
`stat_metadata.json`). Δ = `cost @0.5 − cost @rule`, per 1,000 calls; a positive
Δ means the cost rule is cheaper. The bracketed 95% interval comes from 4,000
paired bootstrap resamples (seed 11) of the 10 **MLP** Δ runs only. The paired
bootstrap is implemented in `summarise.py` for the MLP Δ only — this is an
**implementation scope, not a statistical judgement** that a logistic-regression
interval is unnecessary; see §S5 for the open item. Aggregation settings are
registered in `stat_metadata.json`; the CI itself is the top-level key
`delta_ci95` of `real_summary.json`.

## S3 Results

| detector | AUPRC | AUROC | ECE | cost @0.5 | cost @rule | Δ | F1 @0.5 | F1 @rule |
|---|---|---|---|---|---|---|---|---|
| MLP | 0.867 (0.027) | 0.860 (0.015) | 0.075 (0.019) | 2,860 (355) | 2,008 (126) | 853 [665, 1036] | 0.770 (0.023) | 0.759 (0.028) |
| logistic | 0.690 (0.037) | 0.725 (0.024) | 0.0772 (0.019) | 3,886 (782) | 2,396 (195) | 1,490 | 0.676 (0.029) | 0.686 (0.033) |

**Notes on the table.** (1) All costs are **per 1,000 calls**; values in
parentheses are population SD over the 10 runs. Δ = `cost @0.5 − cost @rule`,
so **a positive Δ means the cost rule is cheaper**. (2) The bracketed 95% CI is
from 4,000 paired bootstrap resamples (seed 11) of the 10 MLP Δ runs; no CI is
reported for logistic regression (see §S2 Statistics). The logistic relative
cost reduction is **38.3%** (`1,490 / 3,886`), alongside the MLP's 29.8%.
(3) ECE is shown at three decimals for MLP (`0.075`) as originally reported,
and at four decimals for logistic regression (`0.0772`) to preserve the
G06-corrected value `lr.ece.mean` exactly; the mixed precision is intentional,
not a typo. (4) Sanity check: the MLP AUPRC (0.867) slightly exceeds its AUROC
(0.860). On this 1:1 sampled subset the AUPRC baseline is the positive rate
(≈ 0.5), not a low-prevalence prior, so this ordering is not anomalous.

**Reading.** On real-speech data, for the **MLP** detector the decision layer
reduces cost by **29.8%** relative to the 0.5 threshold (computed as
`mean Δ / mean cost @0.5 = 852.7 / 2,860.3`, from **unrounded** values; the
table shows the rounded `853 / 2,860`) while F1 falls slightly
(0.770 → 0.759). For **logistic regression** the relative reduction reaches
**38.3%**, but F1 **rises** (0.676 → 0.686). The percentage is a **ratio of the
10-run means, not the mean of per-run ratios**.

The F1 trade-off is explicit rather than hidden: for MLP the cost rule saves
≈ **852 cost units per 1,000 calls** at the price of an F1 drop of **0.011**
(0.770 → 0.759); for logistic regression both cost and F1 improve. This is
qualitatively consistent with the simulation-based claim, which is **not
verified here** because the simulation results are not in this workspace.

> **Note — post-hoc re-weighting (not a measured cost).** Expected cost
> re-weighted to a 60% attack prior, an external target rather than this
> corpus's measured prior (0.4485–0.5653 across folds): MLP **2,337 → 1,583**
> and logistic regression **3,109 → 1,977** per 1,000 calls (`@0.5 → @rule`).
> These are sensitivity figures, not measurements, and should not be quoted as
> observed costs. The `exp22_*` fields are reweighted to each fold's measured
> positive rate `yte.mean()`; the name is a historical artifact, **not** a fixed
> prior of 0.22, and those fields are not reported here.

## S4 Boundary (honesty statements)

1. **Feature space.** This anchor uses waveform-derived 50-dim features, NOT the
   4-channel multi-modal vector of the main synthetic simulation. No signalling,
   media-flow or dialogue-semantic inputs are present. The absolute cost level
   (~2,000 per 1,000 calls) is therefore **not quantitatively comparable** with
   Table II of that testbed: corpus and feature channel differ. **Operational
   reading:** this anchor supports only the *directional* conclusion that
   cost-aware decoding lowers relative cost; it does **not** support
   transferring absolute cost magnitudes to the main testbed.
2. **Codec stress.** The 2026-11-13 attempt did not run to completion — the host
   ran out of page-file space when ffmpeg was spawned with 6 workers. In this
   revision the script's scoring chain was repaired to reuse the main protocol's
   `fit_temperature` routine with one shared clean-holdout (temperature, bias)
   pair applied across all conditions, and ffmpeg concurrency was capped with
   per-condition checkpoints. The repaired script was **executed separately on
   2026-11-14** under explicit author instruction (n = 600, 2 seeds, 4 conditions).
   Its results are quarantined in `CODEC_STRESS_RESULTS.md`, were **not added to
   the S3 table**, and describe only within-anchor relative degradation across
   codec conditions. Because the feature channel, corpus prior and evaluation
   protocol differ, these metrics are **not quantitatively comparable** with the
   synthetic testbed and **must not be merged into the main result tables**.
   `verify_codec_stress.py` enforces these guardrails (9/9 checks PASS).
3. **Re-weighting.** `exp60_*` is a post-hoc target, not a measured cost; the
   measured test positive rate is 0.4485–0.5653. `exp22_*` and the isotonic
   control are computed but not tabulated.
4. **Bootstrap.** The 95% CI is computed for the MLP Δ only; see §S2 Statistics
   for the reason and §S5 for the pending logistic-regression interval.
5. **Speaker counts.** 785 (corpus level) and 628 (subset / fold-grouping level)
   are different populations; 628 is derived from non-stratified sampling.

## S5 To-do / open items

1. Codec stress was executed separately on 2026-11-14; results are quarantined
   in `CODEC_STRESS_RESULTS.md` and excluded from the S3 table (see §S4(2)).
   Procedure: `CODEC_STRESS_RUNBOOK.md`; read-only validator
   `verify_codec_stress.py` (9/9 PASS). No codec-stress metric is merged into
   Table II or the main result tables.
2. Reproducibility metadata: `sampling_metadata.json` (sampling environment) and
   `stat_metadata.json` (statistical settings), together with `feats.npz["fid"]`.
3. Process tracking: `data/数据分析过程记录表.csv` (F-120 six-column log) and
   `data/官方口径登记表.csv` (W-07 register); all changes are logged with
   old/new setting pairs.
4. External references still missing from this workspace: the manuscript full
   text, Table II values and the simulation results, plus any reviewer comments.
5. **Logistic-regression Δ interval.** `summarise.py` implements the paired
   bootstrap for MLP only. A read-only recomputation with the same method
   (seed 11, 4,000 resamples, 10 paired Δ runs) gives a 95% CI of
   **[987.8, 2066.6]**; reproducing the MLP interval with that same code yields
   [665.3, 1036.1], matching the released `delta_ci95`. **Not tabulated here** —
   whether to report it is an author / statistics-seat decision; adopting it
   would also require updating `stat_metadata.json`.
6. **P1-3 option B impact not assessed.** Implementing a genuine spectral-flux
   std would change `feats.npz` and require re-running the full ASVspoof5 chain;
   **not adopted** in this revision. The effect on the reported conclusions has
   **not been evaluated**, so no robustness claim is made for that feature
   defect. An impact assessment is an open item, not an implicit finding.

**Files.** `feats.npz` (features and the 2,000 file IDs), `real_runs.csv` (per run),
`real_summary.json` (aggregates and `delta_ci95`), `stat_metadata.json`,
`sampling_metadata.json`, `featlib.py`, `extract_feats.py`, `run_real_check.py`,
`summarise.py`, `codec_stress.py` (repaired and executed separately on
2026-11-14), `RESULTS.check.md`, `REVISION_NOTE.md`, `CODEC_STRESS_RUNBOOK.md`,
`verify_codec_stress.py`, `codec_stress.csv` and `codec_cache/` (separate
codec-stress branch, results in `CODEC_STRESS_RESULTS.md`), the two `data/*.csv`
registers, `build_results_pdf.py` and `RESULTS.pdf` (this document, v1.1).

## Appendix A. Revision history

> **v1.0 (2026-11-14, G06 finalisation).** Wording, units, scope, provenance
> and reproducibility disclosures; no simulation output was rewritten. The
> single manuscript-side value correction is the logistic ECE cell, set to
> `0.0772` = `real_summary.json` `lr.ece.mean` (0.0772400649) under the author's
> G06 ruling — a transcription fix, not a re-run and not a change to any released
> number. `feats.npz`, `real_runs.csv` and `real_summary.json` are byte-identical
> to the copies in `backups/2026-11-14/`. Previous draft: `RESULTS.md.bak`;
> findings, item numbers and the G04 arbitration record (including the §13 G06
> close-out): `RESULTS.check.md`; process log: `data/数据分析过程记录表.csv`
> (F-120); registered wording: `data/官方口径登记表.csv` (W-07);
> reviewer-facing summary: `REVISION_NOTE.md`.

> **v1.1 (2026-11-14, readability and consistency pass).** No released number
> changed. Changes: the Δ interval is written `853 [665, 1036]` (no thousands
> separator inside the interval) and the table is typeset so that no cell wraps;
> the cost unit moved to the table notes; Δ definition, its positive-direction
> reading, the 38.3% logistic reduction, the ECE precision difference and the
> AUPRC/AUROC sanity check are stated in the table notes; the expected-cost
> formula and the reason for the missing logistic interval are added in §S2;
> the 60% re-weighting figures moved to a clearly labelled post-hoc note; the
> F1 trade-off is quantified in the Reading paragraph; §S4(1) gained an
> operational interface sentence; §S5 gained two explicit open items; section
> cross-references unified as §S<n>; the revision note moved to this appendix
> and a version line added. Pre-v1.1 snapshot: `backups/2026-11-14-v11/`.
