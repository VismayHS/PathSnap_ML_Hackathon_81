# Requirements traceability

Each row maps a requirement from the student materials to where it is implemented, how it is checked, and its current status. Status values are **Done**, **Partial**, **Not started** and **External/pending**. A row is Done only when the evidence is in the repository. A owns the scientific rows and verifies them. B assembles this document.

Sources (PDF section numbers):
- **MG** = Main Guidelines
- **DE** = Dataset Exploration
- **MT** = Models and Training Guidelines
- **DL** = Deliverables
- **AP** = Assessment and Plagiarism Policy

Last updated: 2026-11-18, M1 integration.

## Mandatory: system and architecture

| # | Requirement | Source | Implementation | Evidence / check | Owner | Status |
|---|---|---|---|---|---|---|
| S1 | Laptop 1 hosts the classifier, HMM/Viterbi, road network and server-side evaluation | MG §3 | `api/`, `src/pipeline.py`, `src/evaluation/service.py` | `tests/api`, M1 integration record | B/A | Partial: diagnostic model only until M3 |
| S2 | Laptop 2 UI shows ten trip options, sends the selected trip, shows route and results | MG §3, §6 | `ui/` | Playwright `ui/tests/workflow.spec.ts` | B | Done for development data; evaluator trips are External/pending |
| S3 | FastAPI backend | MG §4.9, MT §5 | `api/main.py` | `tests/api` (20) | B | Done |
| S4 | API computes accuracy with internal reference data | MG §6.8 | `src/evaluation/service.py`, called after prediction | `tests/api` call order | A/B | Partial: the scorer currently returns "unavailable" |
| S5 | Ground truth stays server-side, never in the model or UI | MG §6, AP §7 | explicit serializer `api/serialize.py`, schema `additionalProperties:false` | leakage tests and live scan of 10 trips | B | Done (re-check at M3) |
| S6 | No hardcoded predictions or API bypass; API logs shown on the receiving laptop | MG §6, AP §7 | structured request/stage logs in `api/main.py`, `api/service.py` | `api.log` in the M1 evidence | B | Done; the physical demo is pending |
| S7 | Works for all ten reserved trips | MG §6 | evaluator mode via `PATHSNAP_EVALUATOR_ROOT` | — | B/A | External/pending (data not provided) |

## Mandatory: data

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| D1 | Partitions: 80 train / 10 student test / 10 evaluator, with no trip split across partitions | DE §7 | `configs/ml/data.json`, `src/data_processing/raw.py` | `results/eda/initial-validation-v2` | A | Done for available data |
| D2 | Evaluator data untouched during development and never used for training or selection | DE §7, AP §7 | separate root, no fallback | `tests/api::test_evaluator_mode_unconfigured_never_substitutes` | A/B | Done (procedural) |
| D3 | Exploration: counts, sizes, types, missing values, timestamps, extent, graph size/connectivity, anomalies, reference structure | DE §4 | `src/data_processing/inspect.py` | `results/eda/initial-validation-v2` | A | Partial: plots and connectivity tables pending |
| D4 | Projected or geodesic distance, justified | DE §5 | `src/data_processing/geometry.py` (local AEQD) | `tests/ml/test_raw_geometry.py` | A | Done |
| D5 | Learned preprocessing fitted on training data only | DE §7 | M2 training code | — | A | Not started |

## Mandatory: models and evaluation

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| M1 | Train and compare at least 5 models | MT §2, §4; AP §3; DL §3 | `src/models/` | — | A | Not started (pilot in progress) |
| M2 | Use the 80 train trips for fitting/CV and the 10 student-test trips for comparison | MT §4 | grouped CV | — | A | Not started |
| M3 | Record configs, seeds, logs, train/inference time | MT §4 | `results/experiments/` | — | A | Not started |
| M4 | Metrics: accuracy, precision, recall, F1, confusion matrix, log loss, Top-1, candidate miss rate, continuity, sequence, timings | MT §5 | `src/evaluation/` | `docs/ml/scoring-policy.md` (provisional) | A | Partial: policy only |
| M5 | Bayesian HPO with group-aware CV; trials retained; tuned vs untuned | MT §7, AP §3, DL §4 | `src/hpo/` | — | A | Not started |
| M6 | HMM/Viterbi: hidden states, emissions, transitions, gaps, invalid transitions, classifier-only vs HMM comparison | MT §8–9, DL §5 | `src/hmm/` | `tests/ml/test_graph_viterbi.py` (mechanics) | A | Partial |

## Mandatory: deliverables

| # | Requirement | Source | Implementation | Evidence | Owner | Status |
|---|---|---|---|---|---|---|
| R1 | Public GitHub repository with all code, organised folders, README with install/run/deploy | DL §1 | repository, `README.md`, `docs/deployment/two-laptops.md` | the repo is public and pushed | B | Partial: README run section to finish |
| R2 | Saved model weights and configs (within size limits) | DL §1 | `artifacts/` | — | A | Not started (only the diagnostic bundle exists) |
| R3 | No secrets committed | DL §1 | `.gitignore`, pre-push scans | scan before each push | B | Done |
| R4 | One consolidated PDF report following DL §2–7 | DL §1–2 | `report/` | — | B (A science) | Not started |
| R5 | EDA in report: preprocessing, patterns, features, missing values, trajectory and network plots, ≥1 Folium map, partition named | DL §2.2 | A plots + B Folium | — | A/B | Not started |
| R6 | Comparison table, a subsection per model, required plots | DL §3 | A | — | A | Not started |
| R7 | HPO section | DL §4 | A | — | A | Not started |
| R8 | HMM section with classifier vs HMM | DL §5 | A | — | A | Not started |
| R9 | Folium maps: GPS, network, reference, predicted; legend, layers, extent; HTML or code committed | DL §6 | `src/visualisation/folium/make_maps.py` | `tests/integration/test_folium_maps.py` (synthetic) | B | Partial: generator ready, needs A's dev-vis export |
| R10 | UI screenshots and API response screenshots on the receiving laptop's terminal | DL §7 | — | screenshots exist from localhost runs; physical LAN pending | B | Partial |

## Mandatory: integrity

| # | Requirement | Source | Implementation | Status |
|---|---|---|---|---|
| I1 | Independent work, no shared code or weights across teams | AP §4, MG §11 | — | Team responsibility |
| I2 | No fabricated metrics, graphs or results; every number traceable | AP §5, DL §8 | run IDs, source SHAs, evidence manifests | Ongoing |
| I3 | Disclose AI assistance as the event policy requires | DL §8 rule 5 | `docs/team/README.md`, `docs/team/context/` | Partial: needs the team's statement in the report |
| I4 | Every member can explain the work (viva) | AP §5–6 | `docs/team/`, `docs/ml/` notes | Team responsibility |

## External and pending items

- Organisers to clarify the official pointwise scoring and alignment semantics (metrics are labelled provisional until then).
- Reserved evaluator trips.
- Two-physical-laptop demonstration and real terminal screenshots.
- Team AI-assistance disclosure wording in the report.
