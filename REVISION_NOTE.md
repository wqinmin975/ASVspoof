# Modification summary — ASVspoof-5 real-data anchor

*Revision date: 2026-11-14. Intended as an appendix to a Response-to-Reviewer
letter. This note describes changes to the anchor working directory only; it is
not a manuscript section.*

*Latest: **v1.1** (readability and consistency pass, same date; see §6). The
document it accompanies is `RESULTS.md` / `RESULTS.pdf` v1.1.*

## 1. No numerical change to released experimental outputs

`feats.npz`, `real_runs.csv` and `real_summary.json` are **byte-identical** to the
pre-revision copies archived in `backups/2026-11-14/` (verified by SHA-256).
No model of the main protocol was retrained, no `feats.npz` feature recomputed,
no sample re-drawn, and the ASVspoof5 main experiment was **not re-run**. Every
released experimental number is unchanged. (The separately executed
codec-stress branch trains its own MLP and recomputes features for a 600-utterance
subset; it is quarantined in `CODEC_STRESS_RESULTS.md` and is not part of these
released outputs.) New numbers added to the text (four F1 standard
deviations, the 140,950 / 47,400 / 93,550 corpus counts, 0.4485–0.5653) are
traceable to `real_summary.json`, the protocol file, or the local audio pool.

**One manuscript-side transcription correction** was made under the author's G06
ruling: the logistic ECE cell was set from `0.087` to **`0.0772 (0.019)`**,
matching `real_summary.json` `lr.ece.mean` = 0.0772400649 and `lr.ece.sd` =
0.018685 (temperature+bias calibration, the column's defined estimator). The
isotonic control values (`lr.ece_iso` = 0.0823, `mlp.ece_iso` = 0.0861) were
not adopted. This corrects a text-entry error only: **no simulation output was
rewritten and no re-run was performed**. The preceding † footnote and all
"pending confirmation" markers were removed. Prior revision states are retained
in `RESULTS.check.md` §1–§12 and in `backups/2026-11-14-g06/` (V3 paired record).

## 2. Code changes (comments, structure and metadata only)

| Item | Change | Numerical effect |
|---|---|---|
| `P1-3` | `featlib.py`: corrected the docstring that falsely declared a spectral-flux std dimension. The implementation always computed the flux mean twice (slot 7 duplicates slot 6). **Option A** adopted: comments only. | None — `feats.npz` unchanged. Option B (implementing a real flux std) would require re-running the entire chain and was **not** adopted. |
| `P1-1` | `extract_feats.py`: documented the corpus-level 785 speakers vs the subset-level 628 speakers, and the `flac_D_aa` display name ↔ `audio/flac_D` local directory mapping. Added named constants for seed / sample sizes (same values). | None — sampling logic untouched. |
| `P1-2` | `extract_feats.py`: added `write_sampling_metadata()` and a `--metadata-only` mode that writes `sampling_metadata.json` from the **existing** `feats.npz` without sampling or decoding. `feats.npz` and the sidecar are written as a pair on future full runs. | None — no re-sampling. |
| `P1-8` | `run_real_check.py`: removed the pass-only `fold_split()` stub and replaced it with `speaker_grouped_fold_split()`, called from `main()`. Same RNG (`default_rng(1000+seed)`), same `np.unique`/shuffle/`array_split` sequence. | None — equivalence verified against the original inline split for all 2 seeds × 5 folds (`True`); fold sizes match `real_runs.csv`. |
| `P1-7` | `run_real_check.py`: documented that `exp22_*` uses each fold's measured `yte.mean()`, not a fixed 0.22 prior. | None — comment only. |
| `P0-3` | `run_real_check.py`: rewrote the module docstring to state that these waveform-derived 50-dim features differ from the 4-channel synthetic-testbed feature set; no external table number is hardcoded. | None — comment only. |
| `P1-4` | `summarise.py`: added an explicit `STAT_METADATA` block and writes it to the separate sidecar `stat_metadata.json`. | None — `real_summary.json` keeps its original schema and values. |
| `P0-4` | `codec_stress.py`: repaired the scoring chain to reuse `run_real_check.fit_temperature()` with one shared (temperature, bias) pair fitted on a 15% clean holdout and applied to every condition; the previous chain thresholded raw logits directly and was not equivalent to the main protocol. Capped ffmpeg workers (`MAX_WORKERS = 4`, default 2), gave each condition its own bounded pool, lowered chunksize, and added per-condition `.npz` checkpoints plus a `--conds` subset switch for resuming after an OOM abort. Added an explicit non-comparability warning. | **Executed separately on 2026-11-14** under explicit author instruction (B01 exception): 8 rows in `codec_stress.csv`, four `(600, 50)` caches, results quarantined in `CODEC_STRESS_RESULTS.md`. Excluded from the S3 table and from Table II; only within-anchor relative degradation is reported. `verify_codec_stress.py` 9/9 PASS. |

**G04 arbitration (documented in `RESULTS.check.md` §12):** the external revision
plan asked for `stat_metadata` to be injected into the top level of
`real_summary.json` (P1-4) while simultaneously requiring all simulation outputs
to remain unchanged (P0-1 and the change-list table). We resolved this in favour
of P0-1: the metadata lives in a **separate sidecar**, and `real_summary.json`
stays byte-identical. `delta_ci95` remains a top-level key of that file.

We also did **not** adopt the four "revised" Python code blocks supplied with the
plan. They were pseudo-code rewrites that conflicted with the actual repository
(protocol column order, sampling order, feature values, the deliberately avoided
pipe-based decode, and a scipy re-implementation of the torch LBFGS calibration).
Applying them would have changed the released numbers. Minimal patches against
the real files were used instead; see §12 for the six conflicts.

## 3. Document changes (`RESULTS.md`)

- Structure reorganised as S1 Motivation/Provenance, S2 Data and protocol,
  S3 Results, S4 Boundary, S5 To-do, following the five-section skeleton.
- Added a **Provenance note**: "the paper", "Table II" and "the simulation" are
  not present in this workspace; the 60% attack prior is a post-hoc re-weighting
  target, not measured from this corpus.
- Distinguished **785 corpus-level** speakers from **628 subset-level** speakers
  (the actual fold-grouping population), and clarified that 628 is a derived
  quantity from non-speaker-stratified sampling.
- Recorded the three corpus scales: 140,950 protocol lines → 47,400 local FLACs →
  2,000 sampled utterances; all 2,000 IDs are in `feats.npz["fid"]`.
- Corrected the feature enumeration to `10 + 25 + 15 = 50` and disclosed the
  duplicated flux-mean dimension.
- Split the cost/F1 reading by detector: MLP −29.8% with F1 0.770 → 0.759;
  logistic regression −38.3% with F1 0.676 → 0.686. Stated that 29.8% is the
  **ratio of the 10-run means**, not the mean of per-run ratios.
- Added full statistical disclosure: population SD (ddof = 0), Δ definition,
  4,000 paired bootstrap resamples (seed 11), CI for MLP Δ only, 15% holdout with
  a 64-sample floor, `p* = c_FP/(c_FP+c_FN)`, and the fact that the threshold
  depends on the cost weights.
- Added F1 standard deviations (from `real_summary.json`), unified the cost unit
  to `per 1,000 calls`, and declared the equivalence of
  *decision layer / @rule / cost rule / p ≥ 0.2*.
- Clarified `exp60_*` as an external re-weighting target and `exp22_*` as a
  historical name using `yte.mean()`.
- Set the logistic ECE cell to **0.0772 (0.019)** under the author's G06 ruling,
  matching `lr.ece.mean` / `lr.ece.sd`; removed the † footnote, the S4 open-cell
  item and the S5 to-do item, and renumbered S5. This is a **manuscript
  transcription fix only** — no simulation output altered, no re-run required.
  Earlier states are preserved in `RESULTS.check.md` §1–§12 and the backups.
- States that the codec-stress script was repaired **and executed separately**
  on 2026-11-14; its results are quarantined in `CODEC_STRESS_RESULTS.md`,
  excluded from the S3 table and from Table II, with no waveform-codec metric
  merged into the main result tables.

## 4. New provenance artefacts

| File | Content |
|---|---|
| `sampling_metadata.json` | numpy 2.5.4, seed 2026, `n_bona` = 1000, `per_attack` = 125, sorted-filename rule, the shared-RNG consumption order, the A09→A16 shuffle order, 785 / 628 / 47,400 / 140,950 / 2,000 counts, the `featlib` comment-only note, and the end-to-end reproduction caveat. |
| `stat_metadata.json` | SD type, bootstrap seed/resamples/scope, calibration method and holdout, cost weights, threshold formula, Δ definition, runs/folds/seeds, cost unit, `exp22_*` naming note, and the location of `delta_ci95`. |
| `data/数据分析过程记录表.csv` | F-120 six-column process log (date / action / input version / parameters and seed / output location / anomaly and rollback decision), 23 rows including the header, including the W-07 permission row, the P0-1 transcription anomaly, the G04 arbitration, the codec-stress execution, the G06 close-out and the v1.1 pass. |
| `data/官方口径登记表.csv` | W-07 register, 22 rows including the header, each with the **old and new** wording in pairs (V3), reference item numbers, date and status; `W-07-19` closes out P0-1 and `W-07-20` records the v1.1 wording. |
| `backups/2026-11-14/` | Pre-revision copies of all 10 touched or released files. |
| `backups/2026-11-14-g06/` | Pre-G06-finalisation copies of `RESULTS.md`, `REVISION_NOTE.md`, `RESULTS.check.md` and the two registers. |
| `backups/2026-11-14-v11/` | Pre-v1.1 copies of `RESULTS.md`, `RESULTS.pdf`, `REVISION_NOTE.md`, `RESULTS.check.md` and the two registers. |
| `RESULTS.check.md` §12 / §13 / §14 | §12 G04 arbitration, verification results and the six rejected code-block conflicts; §13 the G06 author ruling, the three-question check, the six landing actions and the V3 close-out of P0-1; §14 the v1.1 readability pass, the completeness forensics, the per-item disposition table and the ECE-precision G04 ruling. |
| `CODEC_STRESS_RUNBOOK.md` | Local re-run commands (smoke → staged conditions → combined CSV), resume rules, acceptance criteria, the three non-comparability reasons and the no-merge guardrails, plus the 2026-11-14 execution record. |
| `verify_codec_stress.py` | Read-only validator: output/cache integrity, shared calibration, clean-feature-chain consistency, released-artifact hashes, and the S3/S4/standalone no-merge checks (9/9 PASS after the re-run). |
| `codec_stress.csv` + `codec_cache/` | Separate codec-stress branch: 8 rows (2 seeds × 4 conditions) and four `(600, 50)` per-condition feature caches. Not part of the released main outputs. |
| `CODEC_STRESS_RESULTS.md` | Standalone, quarantined write-up carrying the non-comparability notice; reports only within-anchor relative changes and lists what the numbers cannot support. |
| `build_results_pdf.py` + `RESULTS.pdf` | Reproducible v1.1 PDF build from `RESULTS.md`; auto table layout with nowrap cells, versioned footer and a machine-checkable no-wrap assertion. |

## 5. Resolved and outstanding items

**Resolved in this revision (V3 paired records; historical wording retained in
`RESULTS.check.md` and the backups):**

- **P0-1 logistic ECE.** *Earlier state:* manuscript cell `0.087†` with a footnote
  flagging an untraceable transcription anomaly and author confirmation pending.
  *Final state (2026-11-14, author G06 ruling):* the cell is `0.0772 (0.019)` =
  `lr.ece.mean` / `lr.ece.sd`; the † footnote, the S4 open-cell item and the S5
  to-do item were removed. The author's three checks confirmed no conflicting ECE
  description elsewhere in the manuscript, that Table II belongs to the separate
  synthetic testbed with a different feature set, and that the reviewer asked for
  the temperature+bias calibration ECE (not the isotonic one). No simulation
  output changed and no re-run was performed. See `RESULTS.check.md` §13 and
  `W-07-19`.
- **Codec-stress execution — status update (V3 paired record).** *Earlier state
  (this revision, 09:34):* execution deferred to separate compute resources; no
  results included. *Current state (2026-11-14, 09:53):* the repaired script was
  executed on this host under explicit author instruction (B01 exception).
  Results are in `codec_stress.csv` / `CODEC_STRESS_RESULTS.md`, quarantined from
  Table II and the S3 table. `CODEC_STRESS_RUNBOOK.md` holds the procedure and
  `verify_codec_stress.py` enforces the no-merge guardrails (9/9 PASS). The main
  experiment was not re-run and the three released artifacts remain byte-identical.
- **ECE column precision (V3 paired, resolved by disclosure).** *Earlier state
  (§13):* MLP `0.075` at three decimals vs logistic `0.0772` at four decimals,
  registered as a C-300 formatting item left to the author. *Current state
  (v1.1):* the author offered two options — unify at `0.077`, or explain in a
  table note. The **table-note option was adopted**: `RESULTS.md` table note (3)
  states the mixed precision is intentional, and the G06-corrected value is
  retained. The author may still flip to `0.077` with one instruction.

**Still outstanding:**

1. External references: the manuscript full text, Table II values, the simulation
   results, and any reviewer comments are not present in this workspace.
2. Optional P1-3 option B (a genuine flux-std feature) would change `feats.npz`
   and require re-running the full chain; deliberately deferred. §S5(6) now
   states explicitly that its effect on the reported conclusions has **not**
   been assessed — no robustness claim is made.
3. A logistic-regression Δ interval is not tabulated. A read-only recomputation
   with the same bootstrap method gives 95% CI **[987.8, 2066.6]** (MLP method
   check reproduces [665.3, 1036.1], matching the released `delta_ci95`).
   Whether to report it is an author / statistics-seat decision; adopting it
   also requires a paired update of `stat_metadata.json`.

## 6. v1.1 readability and consistency pass (2026-11-14, evening)

Triggered by an author review list on `RESULTS.pdf`. **No released number changed
and no experiment was run.** Full per-item disposition and forensics:
`RESULTS.check.md` §14.

- **Forensic finding first.** Several "abruptly truncated sentences", missing
  spaces and a garbled `@0.5` were traced to the reading/copy side, not to the
  files: every cited sentence is complete in both `RESULTS.md` and the PDF text
  layer (e.g. `…not in this workspace.`, `…computed but not tabulated.`,
  `…for the MLP Δ only.`). **Nothing was "completed"** — adding text would have
  duplicated words. The one genuine defect was typographic: the v1.0 table used
  fixed column widths, so the Δ cell wrapped into `853 [665,` / `1,036]` and
  every SD wrapped to a second line. That was fixed in the build script.
- **Document (`RESULTS.md` v1.1):** Δ written `853 [665, 1036]`; cost units
  moved to the table notes; notes added for the Δ definition and its positive
  direction, the logistic 38.3% reduction, the ECE precision difference and the
  AUPRC/AUROC sanity check; §S2 gained the expected-cost formula and the
  code-scope reason for the missing logistic interval; the 60% re-weighting
  figures moved to a labelled post-hoc note; the F1 trade-off quantified
  (≈852 cost units per 1,000 calls against F1 −0.011); §S4(1) gained an
  operational interface sentence; §S5 gained two explicit open items;
  cross-references unified as §S<n>; the Revision note moved to
  `Appendix A. Revision history` with a version line up front.
- **PDF (`RESULTS.pdf` v1.1):** 4 pages A4, all table cells on one line
  (verified in the text layer), rightmost ink at 549.9 pt inside the 16 mm
  margin, versioned footer and metadata, Chinese paths and § / Δ / ≈ intact.
  `build_results_pdf.py` is now a tracked, reproducible build script.
- **Guardrails intact:** `verify_codec_stress.py` 9/9 PASS — N1 still finds
  exactly two detector rows and no banned tokens in S3; N2 still finds the
  non-comparability and no-merge statements in S4. The three released artifacts
  remain byte-identical to `backups/2026-11-14/`.
