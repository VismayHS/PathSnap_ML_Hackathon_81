# Scientific requirement audit

Audited against all five supplied PDFs and the master/protocol after M3. This document records scientific evidence; app/PDF/physical deployment acceptance remains separately reviewed.

| Requirement | Executed evidence | Status |
|---|---|---|
| Inventory all80train/10student trips, files, rows, types, coordinates, timestamps, extent, graph connectivity, references | `results/eda/initial-validation-v2`, source `src/data_processing/inspect.py` | Executed |
| Preserve local IDs and original rows; reject malformed rows; metric geometry | parser/geometry tests, all90trip EDA | Executed |
| Ordered reference occurrence alignment and explicit ambiguity/denominator policy | `src/evaluation/alignment.py`, `docs/ml/scoring-policy.md`, preparation counts | Executed, policy provisional |
| Reference-free candidates/features/inference, fold-fitted preprocessing and trip groups | pipeline/source separation, fold preprocessing/group tests, source/parity review | Executed |
| Five distinct model configurations, CV and student scores, fit/scoring times | `results/experiments/baselines-local-v1` and model-selection notes | Executed |
| Real Bayesian optimization and retained study |12TPE trials with4startup/8adaptive; `results/hpo/hgb-tpe-v1`, explicit interruption/recovery | Executed |
| Refit and portable trained assets | `artifacts/hgb-hmm-v1`, checksums, dependency/feature validation | Executed |
| HMM mechanism and trained comparison | known-optimum/unreachable/gap tests; real10trip x2facade runs; `results/hmm/hgb-hmm-v1` | Executed |
| Accuracy, precision, recall,F1,conditional loss,miss rate,continuity,observed-sequence metrics | canonical records and per-trip JSON; denominators retained | Executed |
| Confusion diagnostics without cross-trip ID pooling | `results/experiments/confusion-v1`; matrices reproduce all saved accuracies | Executed |
| Distance/heading/geometry-motion block ablation | Same fixed HGB parameters, five trip folds and sampling; `results/experiments/feature-ablation-v1` | Executed; descriptive, no retuning |
| Numerical graphs,per-model discussion,tuned/untuned,common-host timing,HMM regression case | `results/figures`, scientific report generator, selected-profile-v1 | Executed |
| Isolated aggregate-only scorer integrated with actual HTTP | M3 combined review:HTTP52/07 exact observation/metric parity; private-key scan and schemas pass | Executed |
| Development-only Folium handoff |10schema-valid exports;B generated10HTMLmaps, source/coordinate/piece review | Executed; complete map screenshot/PDF review withB |
| Scientific report reproducibility | `src/evaluation/scientific_report.py` generates `report/sections/science.md` from saved records | Executed; consolidated PDF review withB |
| Team understanding | `docs/ml/viva-notes.md`, team-understanding.md, methodology/reproduction notes | Prepared; team must review/defend |
| Reserved evaluator/official pointwise policy/two-physical-laptop demo | Explicit external limits in report/deployment docs | External/pending |

Read the HMM counterexample: trip00000007 accuracy decreased despite pooled improvement. Sequence scores are not full-route accuracy; graph continuity does not certify unavailable traffic restrictions. The conditional log-loss value stays the same after Viterbi because it describes classifier emissions, not a posterior distribution.

Model code is our implementation using standard library algorithms; ECC supplied manually applied workflow guidance only. The two additional user-linked papers are assessed in `additional-paper-notes.md`, with access limitations stated. No Kaggle/GPU/four-machine execution is claimed. Windows wheel availability was checked; execution on Windows remains separate.
