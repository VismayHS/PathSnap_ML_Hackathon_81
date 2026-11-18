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
