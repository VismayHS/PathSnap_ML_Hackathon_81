# Scientific reproduction commands

Run from the assigned A worktree or a reviewed integration checkout. Use a separate local `.venv` per checkout.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/ml -q
.venv/bin/python -m src.data_processing.inspect --data-root /home/vismay-hs/Downloads/ML_Hackathon/Student_folder --output results/eda/initial-validation-v1
```

EDA refuses to overwrite an existing output directory. Commit source before running evidence production; metadata records the source SHA and whether scientific source was dirty. Outputs include every trip's inventory/quality/connectivity statistics, per-file hashes, per-partition aggregates, elapsed time and package versions. These commands do not enumerate any evaluator directory.

Candidates, model fitting, Bayesian search and HMM commands will be added when implemented and actually executed. At this stage no models or benchmark metrics exist.

For exact transitive reproduction, install `requirements.lock.txt` instead of only the direct pins. See [environment.md](environment.md) for the actual compatibility checks.

The M1 vertical slice uses an explicitly labeled geometric diagnostic, not a trained model:

```bash
.venv/bin/python -m src.models.export --diagnostic --output artifacts/diagnostic-v1
.venv/bin/python -m src.evaluation.diagnostic_check --data-root /home/vismay-hs/Downloads/ML_Hackathon/Student_folder --bundle-root artifacts/diagnostic-v1 --output results/experiments/m1-diagnostic-v1
```

Diagnostic checks run every discovered student-test trip, validate the boundary invariants, reject `.route` access through `Path.open` during the prediction/scorer calls, verify unavailable scoring is explicit, and invoke the actual CLI to compare the first trip's selected-arc/status/segment signature. This is not an HTTP/UI/LAN test. CLI raw prediction output goes to ignored `data/processed/`; the committed summary contains counts, timings and hashes only. Export and check commands require fresh output paths.

## Completed five-model, TPE and trained decoder runs

From a locked Python3.12 environment, with a verified development cache:

```sh
python -m src.models.experiments --cache data/processed/candidate-v1 --output results/experiments/YOUR-NEW-BASELINE-RUN
python -m src.hpo.search --cache data/processed/candidate-v1 --output results/hpo/YOUR-NEW-TPE-RUN --trials 12 --threads 4
python -m src.hmm.compare --data-root /absolute/path/to/Student_folder --baseline results/experiments/baselines-local-v1/summary.json --hpo results/hpo/hgb-tpe-v1/summary.json --bundle-output artifacts/YOUR-NEW-BUNDLE --output results/hmm/YOUR-NEW-COMPARISON
python -m src.evaluation.export_records --source results/hmm/YOUR-NEW-COMPARISON/summary.json --output results/hmm/YOUR-NEW-COMPARISON/records.jsonl
```

Every output name must be fresh. The actual TPE study at `results/hpo/hgb-tpe-v1` contains all12 trial outcomes, SQLite storage, trial-level folds, final refit and `recovery.json`: its first process ended with143 during the last trial. The explicit `--complete-recorded-trial` recovery reran only that already TPE-sampled final configuration. It did not replace completed trials or sample additional candidates. Completed trial compute summed166.75s; final recovery invocation elapsed25.63s including its final trial and refit. The interrupted partial attempt's compute cost could not be recovered. Do not misreport25.63s as total tuning time.

The selected portable bundle is `artifacts/hgb-hmm-v1`. The entire training-only model-selection/HPO history remains separate from post-refit student-test comparisons. Development Folium inputs at `results/hmm/hgb-hmm-v1/visualisation` contain references and must never be copied into the UI/API static assets or used for evaluator export.
