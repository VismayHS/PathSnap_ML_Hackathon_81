# PathSnap — Map-Matching & Route Reconstruction

UE24CS352A Machine Learning hackathon (PES University, RR Campus). Noisy GPS trajectories are matched to a road network with a candidate classifier followed by HMM/Viterbi decoding. The system is served by a FastAPI backend (Laptop 1) to an evaluator UI (Laptop 2).

## For the team

Plain-language status and explanations: [docs/team/](docs/team/README.md) (start with the progress log). Interfaces between components: [contracts/interfaces.md](contracts/interfaces.md).

## Repository layout

| Folder | Contents |
|---|---|
| `data/` | Raw trips by partition (git-ignored) |
| `notebooks/` | Dataset exploration / EDA |
| `src/data_processing/` | Loading, cleaning, candidate generation |
| `src/features/` | Feature engineering |
| `src/models/` | Training scripts for every model tried |
| `src/evaluation/` | Metrics, comparison tables, confusion matrices |
| `src/hpo/` | Bayesian hyperparameter optimisation |
| `src/hmm/` | HMM + Viterbi route reconstruction |
| `src/visualisation/` | Folium maps and plots |
| `configs/` | Experiment / model / HMM configs |
| `artifacts/` | Final model and inference assets |
| `results/` | CSVs, logs and figures behind every reported result |
| `maps/` | Interactive Folium HTML maps |
| `api/` | FastAPI backend (Laptop 1) |
| `ui/` | Evaluator UI (Laptop 2) |
| `report/` | Technical report PDF |
| `contracts/` | Versioned interfaces between pipeline, API and UI |
| `docs/team/` | Team-facing progress log and explanations |
| `scripts/` | Contract hash, deployment and report tooling |

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The raw dataset is **not** copied into the repo. It lives next to it in `../Student_folder/` (`train/`, `student_test/`). Point the code at it with an absolute path:

```bash
export PATHSNAP_DATA_ROOT=/absolute/path/to/Student_folder
# only when organisers provide the reserved trips:
export PATHSNAP_EVALUATOR_ROOT=/absolute/path/to/evaluator_trips
```

Evaluator mode never falls back to student-testing data.

## Execution

_To be filled in as the pipeline is built (EDA → features → models → HPO → HMM → export)._

## Deployment

_To be filled in: starting the API on Laptop 1 and the UI on Laptop 2._

## Data-leakage safeguards

- Evaluator-testing trips are not used for training, feature selection, model/hyperparameter choice or decoder tuning.
- Evaluator ground-truth routes stay server-side in the API and are never sent to the model input or the UI.
- No hardcoded predictions.
