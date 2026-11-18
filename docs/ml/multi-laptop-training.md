# Optional independent laptop training

The complete five-model baseline already ran locally in 554.69 seconds. Local tuning is the current plan. Use this kit only when the coordinator assigns work; copying data and setting up four machines can take longer than these baseline jobs. These are 30 finite independent baseline tasks (25 CV folds plus five all-training refits), not an indefinite background training service. HPO tasks require a separate coordinated study and are not implemented by this worker.

## Common environment and inputs

Wait for the coordinator to publish an immutable `training-kit-v1` tag after integration. Do not move an existing tag. Clone `https://github.com/VismayHS/PathSnap_ML_Hackathon_81.git`, fetch tags, and create your own branch from that tag:

```sh
git fetch origin --tags
git switch -c results/laptop-1-kit-v1 training-kit-v1
```

Substitute your assigned number (1–4) in branch and output names. Linux/macOS shell:

```sh
KIT_SOURCE=$(git rev-parse training-kit-v1)
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip check
```

Windows PowerShell, with Python 3.12 installed:

```powershell
$KIT_SOURCE = git rev-parse training-kit-v1
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock.txt
.venv\Scripts\python -m pip check
```

The lock excludes uvloop on Windows and includes Windows colorama. Package wheel availability was checked against official PyPI metadata; actual Windows installation and fitting remain to be checked on the receiving machine. The Windows RTX 4060 laptop runs these five sklearn models on its CPU. The worker does not use its GPU.

Privately copy the coordinator's complete `data/processed/candidate-v1` directory, including its index and sampling manifest. Do not upload this cache or raw data to public Git. It contains development references as well as features. Alternatively rebuild from the unchanged permitted Student_folder:

```sh
.venv/bin/python -m src.models.prepare --data-root /absolute/path/to/Student_folder --cache data/processed/candidate-v1 --evidence data/processed/cache-build-laptop-1-v1
```

Use the Windows Python path in PowerShell and quote paths containing spaces. Evaluator files must never enter this process. The raw development fingerprint must be `1a27fe44527456ceacfb9f060f3d833a60ef7cdbf2eae44fbf030712e99a4ec1`. Worker verification compares numeric cache contents, feature schema, sampling, splits, package versions and frozen source, not NPZ ZIP timestamps. If a cross-platform rebuild differs, use the common verified cache; do not change expected hashes to bypass verification.

## Assigned queue

Run verification first, substituting your laptop number:

```sh
.venv/bin/python -m src.models.worker --cache data/processed/candidate-v1 --laptop laptop-1 --kit-source "$KIT_SOURCE" --verify-only
```

Then run exactly your queue (one of these four commands):

```sh
.venv/bin/python -m src.models.worker --cache data/processed/candidate-v1 --laptop laptop-1 --kit-source "$KIT_SOURCE" --threads 2 --output results/experiments/laptop-1-kit-v1
.venv/bin/python -m src.models.worker --cache data/processed/candidate-v1 --laptop laptop-2 --kit-source "$KIT_SOURCE" --threads 2 --output results/experiments/laptop-2-kit-v1
.venv/bin/python -m src.models.worker --cache data/processed/candidate-v1 --laptop laptop-3 --kit-source "$KIT_SOURCE" --threads 2 --output results/experiments/laptop-3-kit-v1
.venv/bin/python -m src.models.worker --cache data/processed/candidate-v1 --laptop laptop-4 --kit-source "$KIT_SOURCE" --threads 2 --output results/experiments/laptop-4-kit-v1
```

PowerShell uses the same arguments with `.venv\Scripts\python` and `$KIT_SOURCE`. Two threads is the common reference setting; use more only by coordinator agreement. The queue manifest uses measured baseline task costs on the original laptop. Its estimates do not promise runtime on other hardware.

A successful process writes `summary.json` with `status: complete`, complete task entries, provenance and sealed file hashes. Keep all files, including `models/`. JSON/JSONL hashes normalize CRLF to LF for Git portability; model binaries are hashed byte for byte. Failures are saved and produce a nonzero exit. Preserve failed/interrupted folders. Retry coordinator-approved task IDs using `--only TASK-ID ...` and a fresh output name such as `laptop-1-kit-retry-v1`; never overwrite evidence. Only one successful copy of each task may enter collection. When the finite queue ends, report completion and wait for new assigned work.

Commit only your own completed run directory:

```sh
git add results/experiments/laptop-1-kit-v1
git diff --cached --name-only
git commit -m "Record laptop 1 baseline training results"
git push -u origin results/laptop-1-kit-v1
```

Do not commit source changes, caches, raw data, local environments or credentials. If you cannot push, transfer the complete run directory privately to the coordinator.

## Coordinator collection

Review fetched results branches to ensure they touch only their unique run directories, then merge those branches. After all 30 tasks have exactly one successful return:

```sh
.venv/bin/python -m src.models.collect --kit-source "$KIT_SOURCE" --runs results/experiments/laptop-1-kit-v1 results/experiments/laptop-2-kit-v1 results/experiments/laptop-3-kit-v1 results/experiments/laptop-4-kit-v1 --output results/experiments/collected-kit-v1
```

Include any accepted retry folder as another `--runs` argument. Collection refuses mismatched source/input/split/sample/cache identities, changed or extra files, missing tasks and duplicate successful tasks. Retain failure history. Compare predictive metrics across machines, but profile latency on one reference host before making speed claims. These scripts have local tests; four physical laptops have not been executed or verified merely by publishing this guide.
