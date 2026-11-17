# ASVspoof5 real-data anchor — reproducible code and released artefacts

This repository contains the analysis code and the lightweight released artefacts supporting the study
**"Cost-Aware Accept/Reject Decisions for Managed Voice Services: Thresholding Calibrated Posteriors by Error Cost"**.
All reported numbers in the manuscript are traceable to the files listed in `RESULTS.md` and the artefact register
(Appendix of the manuscript); a SHA-256-anchored reproduction guard is implemented in `extension_v2.py`.

English summary: 50-d waveform-only features on the ASVspoof5 dev track-1 subset (2,000 utterances,
1,000 bona fide + A09–A16 at 125 each); 5 speaker-grouped folds × 2 seeds; temperature+bias calibration on a
15% holdout; cost-optimal threshold p* = c_FP/(c_FP+c_FN) with c_FP=5, c_FN=20 (1:4, p*=0.2).

## Contents

**Analysis pipeline (Python)**
- `featlib.py` — 50-d waveform feature extraction (pure numpy).
- `extract_feats.py` — batch extraction over the ASVspoof5 protocol TSV. Needs local paths and the corpus.
- `run_real_check.py` — folds, model training, decoding; main entry point for the released run.
- `summarise.py` — aggregation, bootstrap CI and summary JSON.
- `extension_diagnostics.py`, `extension_codec.py`, `extension_v2.py` — isolated diagnostic / revision re-runs;
  `extension_v2.py` enforces a reproduction guard against the released artefacts before any sensitivity experiment.
- `codec_stress.py`, `verify_codec_stress.py` — codec-transcode branch (quarantined from the main table) and its
  read-only 9/9 PASS verification.
- `make_figures_v2.py`, `build_results_pdf.py` — figure and result-document generation.

**Released / revision artefacts**
- `real_runs.csv` (20 released per-run rows), `real_summary.json` (aggregates and CI fields).
- `stat_metadata.json`, `sampling_metadata.json` — sidecars recording SD convention, bootstrap setup, seeds/order.
- `extension_runs.csv`, `extension_summary.json`, `extension_codec.csv` — diagnostic outputs.
- `extension_v2_runs.csv`, `extension_v2_summary.json`, `extension_v2_figdata.json`,
  `extension_v2_family.csv`, `extension_v2_run.log` — revision sensitivity outputs (paired CIs, cost-ratio sweep,
  local t-DCF, slot-7 ablation, ECE bin sensitivity). Released artefacts are **not** modified.
- `RESULTS.md`, `RESULTS.check.md`, `RESULTS.pdf`, `REVISION_NOTE.md`, `CODEC_STRESS_RESULTS.md`,
  `CODEC_STRESS_RUNBOOK.md` — released result document, check log and codec branch write-up.
- `fig1_cost.pdf` … `fig5_reliability.pdf` — the five manuscript figures.
- `part_*.csv` — per-condition caller-level cost tables.

## Not included (and why)

- **ASVspoof5 audio (6.3 GB), official protocol TSVs (~89 MB), and the derived feature file `feats.npz`.**
  These are distributed under the ASVspoof5 corpus licence and are **not** redistributed here. Obtain the corpus
  and protocols from the organisers (<https://www.asvspoof.org/>) and accept their terms; regenerate features
  with `extract_feats.py`. The manuscript's data-availability statement says release of derived files follows the
  corpus licence — this repository is the code/aggregate-results companion, not a corpus mirror.
- **Manuscript LaTeX sources.** They are under review; authors will provide them on request after the decision.

## Reproducing

Dependencies: Python 3, `numpy`, `torch`, `matplotlib` (standard library for the rest).

1. Download the ASVspoof5 development set and the dev track-1 protocol TSV from the organisers.
2. `extract_feats.py` and `codec_stress.py` contain **absolute paths from the original workstation**
   (`D:\\ace\\语义攻击\\asvspoof5_check\\...`); set `PROTO`/`AUDIO` to your local paths before running.
   All other scripts take relative paths and run in place.
3. Order: `extract_feats.py` → `run_real_check.py` → `summarise.py` → `extension_v2.py` → `make_figures_v2.py`.
   Run from the directory containing the released artefacts.
4. `extension_v2.py` will abort unless the ten released per-run rows and the aggregate summary match within
   `1e-6` — this is intentional: sensitivity results are only meaningful on the frozen baseline.

## Licence and citation

Code: released for academic use under the MIT licence (see `LICENSE`). Data: subject to the ASVspoof5 corpus
licence; no corpus data or derived features are redistributed here.

If you use this code, cite the ASVspoof5 overview paper:
X. Wang et al., "ASVspoof 5: Crowdsourced Speech Data, Deepfakes, and Adversarial Attacks at Scale,"
Proc. ASVspoof Workshop, Kos Island, Greece, 2024, doi:10.21437/ASVspoof.2024-1.
