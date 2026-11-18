# Data access

Use the existing read-only development dataset with `PATHSNAP_DATA_ROOT=/home/vismay-hs/Downloads/ML_Hackathon/Student_folder`. It contains `train/<trip_id>/` and `student_test/<trip_id>/`; do not copy raw files into Git. An explicit absolute override is required for nested worktrees.

Each trip has headerless `.track` (longitude, latitude, seconds), `.nodes` (longitude, latitude), `.arcs` (directed node-row IDs), and `.route` (chronological reference arc traversal). Original row indices are identifiers, not disposable DataFrame indices. A reference route is not an observation label table.

Prediction loading reads only `.track`, `.nodes`, and `.arcs`. Reference access lives separately under `src/evaluation/`. Offline EDA/target construction may use permitted references; the runtime scorer sees them only after prediction completes. No reserved evaluator contents are inspected during development. Evaluator provisioning requires an explicit separate root and must never fall back to student testing.

Derived data belongs in ignored `data/processed/`. Small aggregate EDA evidence belongs in `results/eda/<run_id>/`, retaining source revisions and dataset fingerprints.
