# Shared protocol for LLM A and LLM B

## Scope and precedence

Read all five PDFs, the master `PATHSNAP_BUILD_PROMPT.md`, your role prompt, and this protocol completely. The student materials govern task correctness. This protocol refines the master's single-agent ownership, documentation, communication, paths, and Git workflow for two workers. Do not implement the whole master independently in both sessions. Master responsibilities are assigned below; all original scientific, design, integrity, evidence, and final improvement requirements remain mandatory.

Use exactly two worker sessions. B coordinates interfaces/integration; this does not authorize B to override A's scientific findings. Both independently check the other's boundary outputs. A statement of equal effort does not justify duplicated ownership, fake experiments, or unnecessary features.

## Paths and runtime isolation

```text
WORKSPACE=/home/vismay-hs/Downloads/ML_Hackathon
REPO=/home/vismay-hs/Downloads/ML_Hackathon/PathSnap_ML_Hackathon_81
BUS=/home/vismay-hs/Downloads/ML_Hackathon/.pathsnap_coordination
A_WORKTREE=/home/vismay-hs/Downloads/ML_Hackathon/PathSnap_worktrees/llm-a
B_WORKTREE=/home/vismay-hs/Downloads/ML_Hackathon/PathSnap_worktrees/llm-b
INTEGRATION_WORKTREE=/home/vismay-hs/Downloads/ML_Hackathon/PathSnap_worktrees/integration
PATHSNAP_DATA_ROOT=/home/vismay-hs/Downloads/ML_Hackathon/Student_folder
```

Treat these as task-specific variable names, not instructions to replace `HOME` or `CODEX_HOME`. B publishes actual paths if existing worktrees/branch names require safe alternatives. Resolve PDFs and master prompt from the absolute workspace path. Source operations run in the assigned worktree, never from the parent dataset directory.

Use separate local virtual environments and node installations in the appropriate worktree, with ignored caches. Do not edit a shared `.venv`, global agent configuration, or another session's files. Agree via messages on integration API/UI ports and process ownership; record PID/port before starting servers, and stop only processes you started. Do not run two resource-heavy model training/search jobs concurrently without A coordinating CPU/RAM budgets.

## File ownership — one writer per tracked file

| Owner | Exclusive implementation paths |
|---|---|
| A | `src/data_processing/**`, `src/features/**`, `src/models/**`, `src/evaluation/**`, `src/hpo/**`, `src/hmm/**` |
| A | `src/pipeline.py`, `src/__init__.py`, additional shared ML utilities agreed in `contracts/ownership.md` |
| A | `src/visualisation/plots/**`, `notebooks/**`, `configs/ml/**`, `configs/hmm/**` |
| A | `artifacts/**`, `data/README.md`, ignored `data/processed/**`, `results/eda/**`, `results/experiments/**`, `results/hpo/**`, `results/hmm/**`, `results/figures/**` |
| A | `requirements.txt`, Python lock/packaging files such as `pyproject.toml` if introduced, root Python test configuration |
| A | `tests/ml/**`, `report/sections/science.md`, `docs/ml/**`, `docs/repository-references-ml.md` |
| B | `api/**`, `ui/**`, `src/contracts.py`, `contracts/**`, `configs/api/**` |
| B | `src/visualisation/folium/**`, `maps/**`, `tests/api/**`, `tests/integration/**`, browser tests under `ui/**` |
| B | root `README.md`, `.gitignore`, `.env.example`, `DESIGN.md`, `docs/ui-research.md`, `docs/deployment/**`, `docs/repository-references.md`, `docs/repository-references-app.md` |
| B | `docs/requirements-traceability.md`, `docs/validation/**`, `scripts/**` for deployment/integration/report assembly |
| B | `report/**` except A's `report/sections/science.md`; `results/system/**`; root CI/deployment configuration if justified |

Within mixed directories, the specific exceptions above win. B owns the pre-existing shared parent READMEs `src/visualisation/README.md`, `configs/README.md`, and `results/README.md`. A can provide requested wording by message, without editing them. B owns the root `tests/conftest.py` if required; keep ML-specific fixtures in `tests/ml/conftest.py`. A's Python dependency/config ownership applies to dependencies needed by B too; B sends requests and A updates the canonical files promptly. B owns `ui/package.json` and its lockfile. Avoid a root workspace-wide formatter that rewrites the other worker's files.

Before using any unlisted root/shared path, ask its owner or record and acknowledge new ownership in `contracts/ownership.md`. For the master's single-file outputs, use A's `docs/ml/model-selection.md` and methodology documents, A's scientific repository reference fragment, and B's assembled top-level reference/traceability documents. B assembles the consolidated report from A's science section and B's system section without rewriting A's numerical conclusions. A reviews generated scientific pages and requests corrections through messages.

An initial bootstrap is the only exception: before either worker begins implementation, B may commit the reviewed pre-existing scaffold and shared contract files to establish a common starting point. This does not make B the author of pre-existing user content and does not transfer subsequent file ownership.

## Communication without write races

Use the shared directory `BUS`, which is outside Git worktrees. Do not put raw data, protected evaluator labels, credentials, or large result binaries into messages. Use separate immutable message files rather than both editing a single shared chat log.

```text
.pathsnap_coordination/
  bootstrap.json                # B only; initial status is not_started
  messages/from-a/               # A writes; B reads
  messages/from-b/               # B writes; A reads
  status/a.json                  # A writes only
  status/b.json                  # B writes only
  handoffs/a/                    # A writes immutable manifests
  handoffs/b/                    # B writes immutable manifests
  integration/                  # B writes validation/integration manifests
```

Give each message an increasing sender-local sequence and unique message ID, e.g. `A-0001-contract-review.json`. Write to a temporary file in the same directory, then atomically rename it to the final unique filename; readers ignore temporary files. Never overwrite a delivered message or edit the peer's message/status. Update your own status atomically too. Messages contain:

```json
{
  "id": "A-0001-contract-review",
  "from": "A",
  "to": "B",
  "type": "PROPOSAL",
  "milestone": "M0",
  "reply_to": null,
  "contract_version": "0.1.0",
  "summary": "Describe the concrete proposal or evidence",
  "details": {"paths": [], "commit_sha": null},
  "requires_ack": true
}
```

Supported types: `PROPOSAL`, `ACK`, `QUESTION`, `ANSWER`, `BLOCKER`, `STATUS`, `HANDOFF`, `REVIEW`, `CHANGE_REQUEST`, `INTEGRATION_RESULT`. An ACK names the exact message ID, contract content/hash or handoff SHA, and acceptance/conditions. Silence is not agreement. Only the sender of an actual review writes that review; never impersonate the peer or create a fake acknowledgement.

Poll the peer's new messages before starting a task, before/after long tool calls or training phases, before a commit/handoff, and when blocked. Use bounded waits, normally no more than 30 seconds per poll, with concise user progress updates during long work. If no reply is available, continue independent owned work; do not finalize dependent behavior without an actual answer. Before ending a session, publish exact state, pending questions, next commands, branch SHA, and blockers. Resume from files and history, not memory alone. Files carry messages but do not run the other model; both sessions must remain active or be resumed to respond.

## M0: bootstrap and contract handshake

1. B rechecks `git status`, current branch, existing commits, worktrees, and identity. Preserve unrelated changes. The observed starting repo had no initial commit. If still unborn, review and commit only the provided scaffold and safe coordination/contracts documentation inside the project; never blindly `git add .`. If identity is missing, report it; do not invent credentials or authors.
2. B creates initial `contracts/ownership.md`, `contracts/interfaces.md`, `contracts/http.schema.json`, `contracts/artifacts.schema.json`, a versioned sample fixture, and `src/contracts.py`. The initial interface is a proposal, not an approved contract. No trained artifact or experiment is required for this bootstrap.
3. B creates branches `work/llm-a` and `work/llm-b` from the same reviewed bootstrap SHA in the two separate worktrees using `git worktree add -b`. Verify a branch/path does not already exist before creation; never overwrite it. Reserve the original checkout for B's main-branch promotion only.
4. B atomically publishes actual paths, branch names, base SHA, contract version/hash, and `status: ready_for_contract_review` in `bootstrap.json`, and sends A a proposal message.
5. A verifies the base/path setup and reads the proposal, flags scientific/geometry/scoring issues, and sends a concrete review. B reviews A's feedback, makes contract changes on B's branch only, and advertises the new exact commit/hash.
6. For amended B-owned contract files, A may obtain just those reviewed paths from B's exact committed SHA using a path-scoped `git restore --source <SHA> -- <agreed-contract-paths>` followed by its own explicit sync commit. Check for local modifications first. Do not merge all B work merely to get a schema. Only the contract owner changes their contents. If no amendment is needed, the original common bootstrap already supplies them.
7. Both send explicit ACKs naming the same contract version and hash. B records the ACK message IDs and actual contract hashes in an accepted-contract manifest. Only then start dependent implementation. Independent EDA/reference research may proceed while awaiting ACK.

Do not begin two implementations against different guesses. Contract revisions later use the same proposal/review/ACK process. The owner updates the canonical file, consumers synchronize the exact committed paths, and both adjust tests before another integration handoff. Use backward-compatible additions where possible; a breaking change requires a version bump and both parties' acknowledgement.

Make the contract hash reproducible: B maintains `contracts/current-manifest.json` listing the version and SHA-256 of each agreed boundary file, using sorted repository-relative paths. Include the Python boundary types, interface spec, HTTP/artifact schemas, and named fixture files; exclude the manifest itself and review/ACK messages. Compute the aggregate hash from the UTF-8 bytes of `json.dumps({"version": version, "files": file_hashes}, sort_keys=True, separators=(",", ":"))`. Both independently recompute file and aggregate hashes, rather than trusting a version label alone. Do not use timestamps or workstation paths as hash inputs. Update the manifest whenever included boundary content changes.

## Initial boundary specification to finalize together

These are design requirements for the M0 contract, not claims that an implementation exists. B authors exact Python types and JSON schemas; A reviews their scientific suitability. Publish signatures, error cases, optional fields, and examples so no consumer guesses names or units.

### A's Python facade, called by B

- `src.pipeline.load_model_bundle(settings) -> ModelBundle`: validate artifact versions, feature schema, and configuration once at service startup; clear not-ready failure if assets are absent.
- `src.pipeline.load_prediction_input(trip_id, mode, settings) -> TripInput`: load only `.track`, `.nodes`, `.arcs` through an allowlisted partition; preserve string IDs and original observation indices. This function never loads a `.route` file.
- `src.pipeline.predict_trip(trip_input, bundle, options) -> PredictionResult`: pure inference with explicit inputs/configuration, no reference lookup or network dependency, no hidden runtime re-training. Produce matched/unmatched observation states and real route geometry.
- `src.evaluation.service.evaluate_completed_prediction(prediction, scoring_settings) -> EvaluationSummary`: separate post-prediction operation that alone accesses a reference route and applies the agreed scoring policy. A owns this scorer; B calls it after inference. Neither HTTP serialization nor frontend code receives the route/observation-level truth.

B owns shared serializable boundary types in `src/contracts.py`. A owns internal estimator/graph implementations behind these types. Do not leak pandas/geopandas/networkx/sklearn objects into HTTP contracts. `ModelBundle` may be opaque/private to A; publish the startup facade needed by B without serializing it. Agree concrete settings/options types at M0. CLI and API must call the same core prediction code. Keep scoring failure separate from prediction success so a missing reference produces unavailable metrics with a reason rather than a fabricated score.

### HTTP contract, implemented and owned by B

- `GET /health`: version, service status, model readiness, configured `development` or `evaluator` mode. A live service may be not ready; define HTTP status behavior in the schema.
- `GET /trips`: active mode and actual allowed string trip IDs. Development lists the ten existing `student_test` IDs. Unconfigured evaluator mode returns an explicit not-configured response, never student-test substitution.
- `POST /predict`: `{ "trip_id": "00000000" }` with the server-selected mode. No arbitrary filesystem paths, reference labels, runtime hyperparameter tweaking, or user-supplied evaluation mode switches in the request. Start with a simple synchronous contract; introduce jobs only through a reviewed contract change if measured runtime warrants them.
- Define predictable `404` unknown-trip, `422` invalid-input, `503` missing/unready model/data and a safe internal-error envelope. Only advertise cancellation/timeouts/stage events when actually supported. Include a correlation/request ID in logs and responses.

Response schema must specify: `schema_version`, `request_id`, `mode`, `trip_id`, `model_version`, observation count, predicted observation records, predicted geometry, permitted raw GPS/road geometry if returned, timing breakdown, warnings, and aggregate evaluation summary. Scored metrics carry a nullable value, denominator/count policy, units where applicable, and unavailable reason. Distinguish selected-model score from calibrated probability. Define which arrays preserve input order and how invalid/dropped original observations are represented.

All wire geometry uses WGS84 longitude/latitude `[lon, lat]`, times use explicitly documented seconds, distances metres, and timings milliseconds. GeoJSON uses `[lon, lat]`; Leaflet adapters convert once to `[lat, lon]`. Disconnected predicted pieces use separate `MultiLineString` parts or individual line features, never artificial straight connecting lines. Define bounds order explicitly. IDs are strings for trips and graph-local integer arc/node IDs within a trip. No `NaN`/infinity JSON. No raw references, correctness masks, or evaluator-ground-truth geometry in schemas, fixtures derived from evaluator data, HTML, downloads, or browser state.

### Artifact and experiment contracts

A publishes a versioned artifact manifest containing trained model identity/type, preprocessing paths, relative file paths, SHA-256 checksums, feature names/order/types, graph/CRS assumptions, candidate policy, score normalization, decoder configuration, dependency versions, source Git revision, configuration hash, permitted-data fingerprint, and run ID. B validates startup compatibility instead of assuming an artifact filename or independently reimplementing preprocessing. Use relative paths inside portable bundles and a configured bundle root; no absolute workstation paths embedded in final artifacts.

A also publishes a documented results schema with per-model/fold/trip metrics, partition, metric definitions, timings, tuned/untuned status, and decoder variant. B's plots/maps/report assembly consume actual records and metadata. A owns numerical plots; B does not recompute or reinterpret a number differently in the report. A-approved scoring semantics must distinguish candidate misses, pointwise labels, per-trip macro aggregation, and sequence metrics. If organizer clarification is pending, label the contract's policy provisional instead of silently declaring it official.

Agree a separate development-only visualization handoff containing permitted train/student-test GPS/network/reference/prediction geometry and partition/run provenance for B's Folium generator. It must not be returned by the evaluator HTTP contract or implemented as a general evaluator-reference export. Keep this handoff and its readers separate from prediction inputs and evaluator-facing static directories. B can render supplied development reference geometry without reproducing A's label-alignment or scoring algorithm.

For UI/API work before A's model is ready, B may use the shared versioned synthetic schema fixture in tests/development-only tooling. It must be clearly marked synthetic, contain no invented benchmark claims, and never serve as a normal or evaluator prediction fallback. The first executable diagnostic M1 path must be explicitly labeled and later disabled/replaced for final mode. Final acceptance requires A's actual trained model and HMM.

## Handoffs and evidence

Each worker publishes an immutable manifest in their own handoff directory with milestone, full commit SHA, base SHA, contract version/hash, owned changed files, tests/commands and real outcomes, artifact/result relative paths and hashes, known failures/blockers, and review requests. Commit source before a run where possible; record that source SHA, and distinguish the later result-publication SHA. Use no mutable `latest` path as the sole identity of experimental evidence.

Small permitted artifacts/results belong on A's branch and arrive through integration. For oversized assets, A supplies an immutable checksummed directory/snapshot accessible to integration plus configured path and documented final distribution plan. B must verify hashes before using it. Do not import live mutable modules from A's worktree into B's production app or symlink another worktree's transient outputs into the final build.

Publish `READY_FOR_INTEGRATION` only after a real commit and appropriate local checks. Both workers freeze that milestone's code/artifacts until integration succeeds or a fix is requested. Continue read-only review/research or agree a new milestone; do not change pinned evidence in place. The peer sends a review naming the exact SHA and any blockers. Handoff means reviewable, not automatically approved.

## Git integration — B is the only integrator

Workers commit only in their assigned worktrees/branches. A never switches branches in B's checkout or the original project. B never stages/commits A's uncommitted work. No shared-index commits, broad cherry-picks, rebases, squash/amend, force-push, or history rewrites. Contracts shared by exact-path synchronization may have identical content in both branches; verify merges against the common accepted content.

For each milestone:

1. Obtain A and B handoff SHAs, matching acknowledged contract versions/hashes, owner-clean diffs, and peer reviews. Capture the current accepted `main` SHA. Both source branches should have started from that accepted milestone base. B verifies no uncommitted changes in integration and original checkouts.
2. In the separate integration worktree, create a **new named attempt branch** such as `integration/m01-attempt01` from the exact **B handoff SHA**. That already includes B's committed changes. Do not start a pending merge of B followed by a pending merge of A: Git does not support stacking two unfinished merges.
3. Run `git merge --no-ff --no-commit <A_HANDOFF_SHA>` in this integration checkout. This combines A's work with B's pinned work and stops before the integration commit. If already up to date, verify ancestry/content and record that situation instead of inventing a merge.
4. Inspect the complete diff against the previous accepted base and the merged index. Resolve a mechanical conflict only after checking both intended contents. Semantic/scientific/contract conflicts go back to their owners through messages; never take an entire “ours” or “theirs” side blindly. Record why a resolution preserves both sides.
5. Before committing the integration, run the combined checks: Python correctness/contract/API checks, UI lint/type/build, real permitted-data API/UI inference, leakage safeguards, and stage-appropriate scientific/visual evidence. M1/M2 checks may explicitly have not-yet-implemented final features; M4 requires all available-data mandatory checks. Collect a peer review of the actual merged state using the immutable handoff evidence and read-only integration checkout. A sends a new ACK/REVIEW for the combined state, not just its original branch.
6. If tests fail, preserve logs outside the checkout and ask the owner for a source-branch fix. Abort the pending merge with `git merge --abort` after protecting any diagnostic evidence. Never reset a worker branch or fix scientific code only in an integration checkout. Once new handoff SHAs/reviews arrive, start a new attempt branch from the new B SHA and repeat. Do not promote a failing combined state.
7. When checks and both reviews pass, B creates the integration merge commit. Its body lists both source SHAs, contract version/hash, checks and limitations. This preserves meaningful worker history. Branch commits already existed for review; the joined code is tested before this integration commit.
8. Only then, in the clean original project checkout, B promotes via `git merge --ff-only <INTEGRATION_BRANCH>`. If `main` changed meanwhile or fast-forward is impossible, stop promotion and investigate; do not force it. Build a fresh reviewed integration attempt including the changed accepted base as necessary.
9. Publish the accepted commit SHA and tests in a `INTEGRATION_RESULT` message. With their own clean worktrees, A and B each use `git merge --ff-only <ACCEPTED_SHA>` to synchronize their respective worker branch. The accepted merge contains both handoff commits, so this is normally a fast-forward. Verify ancestry first; if a worker continued committing despite the milestone freeze, request a safe explicit merge plan instead of resetting/rebasing it.
10. Both confirm synchronization before starting the next milestone. Reuse/clean up integration worktrees only after checking their status and preserving history/evidence. Keep useful branches until final delivery; do not delete user branches or worktrees.

Review untracked files after tests, so caches and temporary screenshots are not accidentally staged. Commit relevant permitted evidence to its owner branch and rerun the integration process if required. Final artifact/reported metric changes must be traceable, not quietly copied into `main` after acceptance. No push/publication/visibility changes beyond existing authorization.

## Full requirement coverage and final gates

| Master requirement | Primary | Reviewer / boundary |
|---|---|---|
| Read PDFs, integrity, traceability | Both read; B assembles traceability | A supplies scientific mappings; each verifies own rows |
| Git milestones | Both worker commits | B integrates; A reviews combined build |
| Repository research | A ML methods; B UI/application tooling | B assembles references without false usage claims |
| Dataset paths, partitions, IDs, EDA | A | B checks API allowlisting/mode/serialization |
| Label alignment, features, candidates | A | B tests inference boundary never receives reference labels |
| Five models, grouped CV, Bayesian tuning | A | B verifies complete recorded evidence for report |
| HMM, route geometry, decoder comparison | A | B renders actual disconnections; A checks maps |
| FastAPI and isolated post-hoc scoring | B transport; A scorer | Both review one end-to-end request and logs |
| UI research/design/animations/accessibility | B | A checks scientific labels and interpretation |
| Folium | B | A supplies actual permitted geometry/references and reviews |
| Numerical comparison plots | A | B incorporates exact artifacts and captions |
| Inference assets/dependencies | A | B validates portable startup/load errors |
| Two-laptop deployment and browser checks | B | A verifies CLI/API parity; real hardware checks labeled pending if absent |
| Consolidated technical report | A scientific sections; B system sections/build | A audits scientific pages; both review final PDF |
| Submission readiness and final improvements | Both | B owns final integrated handoff; no invented completion |

Final acceptance requires five actual distinct model experiments, retained Bayesian trials, actual tuned/untuned and classifier/HMM comparisons, saved inference assets, working integrated FastAPI and UI against permitted trips, real logs, Folium evidence, complete consolidated report, clear LAN commands, and meaningful commit history. Reserved evaluator provisioning, actual two-physical-laptop checks, organizer scoring clarification, or public publishing remain explicitly pending if unavailable. Do not let these block independent permitted-data work, and do not claim them done.

Before final handoff, both reread all five PDFs and the master prompt, audit every traceability row, improve missing/weak pieces within their ownership, communicate any cross-boundary fixes, integrate and verify them, and identify exact external blockers. One worker's “done” message never certifies the other's work or the entire project.
