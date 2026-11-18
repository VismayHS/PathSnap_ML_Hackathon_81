# Requirements traceability

Each row maps a requirement from the student materials to where it is implemented, how it is checked, and its current status. Status values are **Done**, **Partial**, **Not started** and **External/pending**. A row is Done only when the evidence is in the repository. A owns the scientific rows and verifies them. B assembles this document.

Sources (PDF section numbers):
- **MG** = Main Guidelines
- **DE** = Dataset Exploration
- **MT** = Models and Training Guidelines
- **DL** = Deliverables
- **AP** = Assessment and Plagiarism Policy

Last updated: 2026-11-18, after M4 (`main` `499c5ef`).

## Mandatory: system and architecture

| # | Requirement | Source | Implementation | Evidence / check | Owner | Status |
|---|---|---|---|---|---|---|
| S1 | Laptop 1 hosts the classifier, HMM/Viterbi, road network and server-side evaluation | MG §3 | `api/`, `src/pipeline.py`, `src/evaluation/service.py` | `tests/api`, M1 integration record | B/A | Done: trained hgb-hmm-v1 bundle served (M3) |
| S2 | Laptop 2 UI shows ten trip options, sends the selected trip, shows route and results | MG §3, §6 | `ui/` | Playwright `ui/tests/workflow.spec.ts` | B | Done for development data; evaluator trips are External/pending |
| S3 | FastAPI backend | MG §4.9, MT §5 | `api/main.py` | `tests/api` (20) | B | Done |
| S4 | API computes accuracy with internal reference data | MG §6.8 | `src/evaluation/service.py`, called after prediction | `tests/api` call order | A/B | Done: isolated aggregate scorer, all 10 student-test trips scored via HTTP (M3) |
| S5 | Ground truth stays server-side, never in the model or UI | MG §6, AP §7 | explicit serializer `api/serialize.py`, schema `additionalProperties:false` | leakage tests and live scan of 10 trips | B | Done (re-check at M3) |
| S6 | No hardcoded predictions or API bypass; API logs shown on the receiving laptop | MG §6, AP §7 | structured request/stage logs in `api/main.py`, `api/service.py` | `api.log` in the M1 evidence | B | Done; the physical demo is pending |
| S7 | Works for all ten reserved trips | MG §6 | evaluator mode via `PATHSNAP_EVALUATOR_ROOT` | `results/system/evaluator-run-01-aggregate.json`, report Figure S5 | B/A | Done on one machine (physical LAN pending) |

## Mandatory: data

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| D1 | Partitions: 80 train / 10 student test / 10 evaluator, with no trip split across partitions | DE §7 | `configs/ml/data.json`, `src/data_processing/raw.py` | `results/eda/initial-validation-v2` | A | Done for available data |
| D2 | Evaluator data untouched during development and never used for training or selection | DE §7, AP §7 | separate root, no fallback | `tests/api::test_evaluator_mode_unconfigured_never_substitutes` | A/B | Done (procedural) |
| D3 | Exploration: counts, sizes, types, missing values, timestamps, extent, graph size/connectivity, anomalies, reference structure | DE §4 | `src/data_processing/inspect.py` | `results/eda/initial-validation-v2`, `results/figures/data-quality-v1`, report section 2 | A | Done |
| D4 | Projected or geodesic distance, justified | DE §5 | `src/data_processing/geometry.py` (local AEQD) | `tests/ml/test_raw_geometry.py` | A | Done |
| D5 | Learned preprocessing fitted on training data only | DE §7 | `src/models/experiments.py` (fold-fitted) | `tests/ml/test_fold_preprocessing.py` | A | Done |

## Mandatory: models and evaluation

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| M1 | Train and compare at least 5 models | MT §2, §4; AP §3; DL §3 | `src/models/` | `results/experiments/baselines-local-v1` | A | Done |
| M2 | Use the 80 train trips for fitting/CV and the 10 student-test trips for comparison | MT §4 | grouped CV | `results/experiments/baselines-local-v1/summary.json` | A | Done |
| M3 | Record configs, seeds, logs, train/inference time | MT §4 | `results/experiments/` | run metadata (SHA, seed, fingerprint, timings) | A | Done |
| M4 | Metrics: accuracy, precision, recall, F1, confusion matrix, log loss, Top-1, candidate miss rate, continuity, sequence, timings | MT §5 | `src/evaluation/` | `src/evaluation/metrics.py`, `docs/ml/scoring-policy.md` | A | Done (policy provisional pending organisers) |
| M5 | Bayesian HPO with group-aware CV; trials retained; tuned vs untuned | MT §7, AP §3, DL §4 | `src/hpo/` | `results/hpo/hgb-tpe-v1` (12 trials, tuned vs untuned) | A | Done |
| M6 | HMM/Viterbi: hidden states, emissions, transitions, gaps, invalid transitions, classifier-only vs HMM comparison | MT §8–9, DL §5 | `src/hmm/` | `results/hmm/hgb-hmm-v1` (classifier vs HMM on 10 trips) | A | Done |

## Mandatory: deliverables

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| R1 | Public GitHub repository with all code, organised folders, README with install/run/deploy | DL §1 | repository, `README.md`, `docs/deployment/two-laptops.md` | the repo is public and pushed | B | Done |
| R2 | Saved model weights and configs (within size limits) | DL §1 | `artifacts/hgb-hmm-v1` | checksummed manifest, verified at API startup | A | Done |
| R3 | No secrets committed | DL §1 | `.gitignore`, pre-push scans | scan before each push | B | Done |
| R4 | One consolidated PDF report following DL §2–7 | DL §1–2 | `report/`, `scripts/build_report.py` | `report/PathSnap_Technical_Report.pdf` (24 pages), reviewed by A and B at M4 | B (A science) | Partial: only team-owned fields (names/SRN, final SHA, AI statement) and the LAN screenshot remain |
| R5 | EDA in report: preprocessing, patterns, features, missing values, trajectory and network plots, ≥1 Folium map, partition named | DL §2.2 | A plots + B Folium | report section 2, figures S1–S2 | A/B | Done |
| R6 | Comparison table, a subsection per model, required plots | DL §3 | A | report section 3, confusion matrices | A | Done (incl. feature ablation) |
| R7 | HPO section | DL §4 | A | report section 4 | A | Done |
| R8 | HMM section with classifier vs HMM | DL §5 | A | report section 5 | A | Done |
| R9 | Folium maps: GPS, network, reference, predicted; legend, layers, extent; HTML or code committed | DL §6 | `src/visualisation/folium/make_maps.py` | `maps/hgb-hmm-v1/` (10 trips), report figures S1–S2 | B | Done |
| R10 | UI screenshots and API response screenshots on the receiving laptop's terminal | DL §7 | — | UI screenshots (report S3–S4), single-machine API log excerpt | B | Partial: physical-LAN terminal screenshot pending |

## Mandatory: integrity

| # | Requirement | Source | Implementation | Status |
|---|---|---|---|---|
| I1 | Independent work, no shared code or weights across teams | AP §4, MG §11 | — | Team responsibility |
| I2 | No fabricated metrics, graphs or results; every number traceable | AP §5, DL §8 | run IDs, source SHAs, evidence manifests | Ongoing |
| I3 | Disclose AI assistance as the event policy requires | DL §8 rule 5 | `docs/team/README.md`, `docs/team/context/` | Partial: needs the team's statement in the report |
| I4 | Every member can explain the work (viva) | AP §5–6 | `docs/team/`, `docs/ml/` notes | Team responsibility |

## External and pending items

- Organisers to clarify the official pointwise scoring and alignment semantics (metrics are labelled provisional until then).
- Reserved evaluator trips: received and run once on the frozen system (aggregate results recorded).
- Two-physical-laptop demonstration and real terminal screenshots.
- Team AI-assistance disclosure wording in the report.
