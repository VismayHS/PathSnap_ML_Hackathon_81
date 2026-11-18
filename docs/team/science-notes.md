# Scientific work: running team notes

Read [the scientific overview and progress log](../ml/team-understanding.md) for architecture, data findings, terminology and pending work. This page records new implementation decisions without duplicating that guide.

## 18 November 2026: first source implementation

B created the common Git base and A's isolated worktree. A is implementing strict data loading and reproducible EDA before any model training. Parsing preserves every original observation/node/arc row. Invalid observations receive a mask and reason, rather than disappearing. Invalid graph IDs cause a clear error.

Geometry uses a local azimuthal-equidistant projection in metres, based on WGS84, with explicit longitude/latitude order. Every trip gets its own projection because the dataset spans several countries and both hemispheres. Raw angular distances are unsuitable as physical distances. Zero-length arcs retain their graph IDs/topology but cannot be geometric candidates.

The candidate-index prototype completed all 90 permitted trips: roughly 1.36 million training candidate rows at an exploratory 100 m radius/top-8 policy. This estimate informs the training budget; it is not a frozen policy or a benchmark result. The prototype also matched brute force on 200 synthetic queries, including a long segment and zero-length exclusion. Production candidate code will need equivalent checks in the committed test suite.

The initial scientific tests now pass (11 tests, 0.98 seconds); the environment smoke checks passed and pins were committed as `c8ad49a`. A has begun the pure facade and explicit diagnostic bundle; post-prediction scoring currently reports unavailable because the scientific scorer is not yet production-validated. This deliberately does not fabricate metrics while integration starts.

## M1: real diagnostic evidence is available

The saved EDA record covers all 90 permitted trips and matches the initial fingerprint. The saved diagnostic summary covers all ten student-test trips and 19,160 observations. Each observation retains its original index; all boundary checks and a first-trip CLI/core signature comparison passed. These checks establish executable wiring, not accuracy.

The nearest-geometric diagnostic has many direction/connectivity breaks: trip `00000000` has 1,022 separate route pieces. We preserve these pieces because connecting them artificially would misrepresent the road graph. It also illustrates why the trained relevance model and graph decoder need measured comparisons. The M1 bundle is never accepted in evaluator mode, and its score panel must show unavailable metrics with a diagnostic explanation. See `results/experiments/m1-diagnostic-v1/summary.json`.

B offered optional Kaggle compute via the user. Local candidate memory/profile looks feasible; A will profile model fitting locally before deciding if remote compute is warranted. No data has been uploaded or external login requested.

The user requested commit-message metadata cleanup. Public revision references above use the new history; original immutable run/manifest source IDs are resolved by `results/experiments/source-revision-map.json`, which verifies byte-identical source trees. Numerical evidence is unchanged.

## Parser review correction

The initial numeric loader could silently skip blank/comment rows because that is NumPy's default behavior. That would risk changing row-based IDs for malformed files. The parser now rejects malformed physical rows explicitly and disables comment skipping; invalid numeric GPS coordinates such as NaN still retain their original observation row and validity mask. The scientific suite now passes 14 tests, including three new malformed-row regression cases. Real development checks are being rerun from the correction's committed source before a replacement handoff.

## M2: five measured models

The complete baseline ran in 554.69 seconds. [Model selection](../ml/model-selection.md) links the saved results and comparison table. HistGradientBoosting leads training CV Macro F1 and is selected for genuine Bayesian tuning. Training was local; no Kaggle/GPU run or four-laptop execution is claimed. Per the updated user preference, distributed training is optional and will be used only if a measured full tuning trial exceeds about two minutes or projected tuning exceeds about thirty minutes. The API still uses the M1 diagnostic pending final-model integration.
