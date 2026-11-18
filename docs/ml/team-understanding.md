# PathSnap: team understanding and progress

Updated: 18 November 2026 (India time). Maintainer: Agent A.

This is the team's reading guide and progress log. It records what has actually happened, explains the scientific decisions, and identifies what remains. It is not a substitute for the original PDFs, experiment records, or the consolidated report. Update this file after meaningful findings, experiments, handoffs, and integration reviews.

## Current state

B created common bootstrap commit `cea374cbdedb1ac1028c7ab85d41a1f55a4e51e6`, including this document, and published separate A/B worktrees. Both agents accepted contract `0.1.0`, aggregate SHA-256 `efbc1d7adcb18d639edd7997ab6627f5103196f9756efdf017dc49c82457ffd4`. A synced B's reference-isolation amendment in commit `0a0e9c431b6e3cdb045d61eb186666a78c2903b1`.

A is working in `PathSnap_worktrees/llm-a` on branch `work/llm-a`. Initial parsing, geometry, candidate/features, alignment, graph/Viterbi, facade and diagnostic-export source has been written. The tested environment is pinned in commit `16b447a`; all 11 initial source tests passed. Committed-source EDA and diagnostic runs have now completed; their evidence paths are recorded below. No model has been trained and no integrated application has been verified by A. A diagnostic is for wiring, not a trained-model benchmark.

A maintains this guide and scientific source on its own branch, then supplies pinned commits for B to integrate. For new decisions see [science notes](../team/science-notes.md). The team-facing guide is now tracked in Git; the original bootstrap-pending note below is historical.

Official scoring semantics are still provisional. A sent the alignment/denominator question to B, who reported that the team must seek organizer clarification. No organizer answer has been verified.

## What we are building

PathSnap takes noisy GPS observations and reconstructs a route along a supplied road network. Laptop 1 runs the saved model, graph decoder, FastAPI backend, and isolated scorer. Laptop 2 runs the React interface and displays predictions and permitted aggregate metrics.

The intended prediction flow is:

1. Select a registered trip ID and load its GPS observations and road network.
2. Validate observations while preserving original row indices and graph IDs.
3. Find nearby candidate road segments using a spatial index.
4. Extract distance, direction, and movement features without reading references.
5. Apply saved preprocessing and a trained candidate relevance model.
6. Use HMM/Viterbi to select a plausible sequence through the directed graph.
7. Build geometry from real road segments, retaining disconnected pieces.
8. Only after prediction finishes, run the separate reference-based scorer.
9. Return the predicted route, statuses, timings, warnings, and permitted aggregate results.

A normalized candidate relevance score must not be described as calibrated confidence without evidence. References must never enter candidate generation, inference features, decoding, or evaluator-facing geometry.

## Responsibilities and coordination

| Owner | Work |
|---|---|
| Agent A | Data validation, EDA, target alignment, candidates/features, five classifiers, Bayesian tuning, HMM, scoring, artifacts, scientific plots/report section, Python dependencies |
| Agent B | Bootstrap/contracts, FastAPI transport, React UI, Folium maps, browser/integration checks, deployment, consolidated report, integration and main promotion |
| Team members | Understand and review the implementation, interpret measured results, verify the physical demonstration, and handle organizer/submission requirements |

Workers use separate worktrees. B integrates pinned, committed handoffs and promotes reviewed changes to `main`. Neither worker edits the other's owned files. An interface is accepted only after both workers acknowledge the same version and content hash.

The shared mailbox is outside Git at `/home/vismay-hs/Downloads/ML_Hackathon/.pathsnap_coordination/`. A's messages are under `messages/from-a/`, B's under `messages/from-b/`, and each maintains its own status file. These files exchange messages; they do not start or resume the other coding session.

## What the data files mean

| File | Meaning | Identifier rule |
|---|---|---|
| `.track` | Longitude, latitude, timestamp in seconds; no header | Original observation row index must survive cleaning |
| `.nodes` | Longitude, latitude; no header | Zero-based row index is node ID |
| `.arcs` | Directed from-node and to-node IDs | Zero-based row index is arc ID |
| `.route` | Chronological traversal sequence of reference arc IDs | Repeated occurrences are meaningful |

Arc IDs are local to each trip. Arc `12` in two different trips does not imply the same road. We will score candidate relevance using transferable geometric/motion features rather than train a global classifier over unrelated arc IDs.

The development root is `/home/vismay-hs/Downloads/ML_Hackathon/Student_folder`, configured with `PATHSNAP_DATA_ROOT`. Worktrees must use that absolute path. Raw files stay read-only. Reserved evaluator data is not currently provisioned; development data must never be silently substituted in evaluator mode.

## Findings from executed read-only inspection

These are actual initial checks across all available permitted trips, executed before a source worktree existed. They are preliminary terminal/mailbox evidence, not a committed reproducible EDA run. The EDA implementation must reproduce and retain the detailed records before report use.

| Check | Training | Student testing |
|---|---:|---:|
| Trips | 80 | 10 |
| Files checked | 320 | 40 |
| GPS observations | 208,417 | 19,160 |
| Network nodes, summed across trip files | 1,933,485 | 90,689 |
| Directed arcs, summed across trip files | 3,876,904 | 185,041 |
| Schema errors / noninteger graph or reference IDs | 0 / 0 | 0 / 0 |
| Nonfinite values / out-of-range graph or reference IDs | 0 / 0 | 0 / 0 |
| Invalid longitude/latitude ranges | 0 | 0 |
| Nonpositive timestamp steps | 0 | 0 |
| Exactly one-second steps | 96.5013% | 98.6214% |
| Maximum sampling gap, seconds | 153,064 | 210 |
| Zero-length arcs by identical endpoint coordinates | 100 | 6 |
| Consecutive identical GPS coordinate pairs | 6 | 0 |
| Nonadjacent consecutive reference-arc pairs | 13 | 1 |
| Trips containing those reference discontinuities | 10 | 1 |
| Repeated reference arc occurrences beyond first occurrence | 67 | 255 |

Graph connectivity inspection found disconnected components and directed asymmetry. We must retain supplied directions, reject or explicitly handle zero-length segment geometry, and expose gaps instead of drawing straight bridges. Summed graph counts do not establish distinct roads across trips. Coordinate range checks establish plausibility, not measurement accuracy.

The content fingerprint of all 360 permitted files is:

`1a27fe44527456ceacfb9f060f3d833a60ef7cdbf2eae44fbf030712e99a4ec1`

Definition: compute SHA-256 for each file, map dataset-relative file paths to those hashes, serialize the mapping as sorted compact JSON, then hash its UTF-8 bytes. This identifies the raw development inputs, not an experiment run or trained artifact.

## The supervision problem the team must understand

A `.route` row is a traversed arc, not a GPS observation label. The row counts differ. Zipping the files, stretching route rows to match GPS counts, or treating route membership as pointwise truth would yield misleading targets and scores.

A read-only diagnostic compared nearest reference-segment matching with a monotone dynamic program over ordered traversal occurrences. On training trip `00000069`, their selected arc IDs disagreed for 8.805% of observations; on looping student-test trip `00000056`, disagreement was 17.281%. The latter contains 255 repeated reference arc occurrences. This shows that ignoring chronology can change derived labels substantially; it does not prove the exploratory alignment is correct.

The pilot used an approximate local metric projection and squared distance residuals, with free start/end positions and forward occurrence skips. It did not enforce speed limits or prevent backward projected motion within one occurrence. It is method investigation, not a final target policy, trained model, or benchmark. A production alignment needs proper metric geometry, repeated-occurrence handling, ambiguity/residual diagnostics, and a clearly documented unmatched policy.

Official observation-to-route scoring semantics remain unresolved. Derived-label metrics must be labeled provisional unless organizers confirm the policy. Missing/ambiguous reference alignment must be counted and disclosed rather than silently removed.

## Planned experiments and how to interpret them

The initial five distinct classifiers are regularized Logistic Regression, distance-weighted KNN, Random Forest, Extra Trees, and HistGradientBoosting. This is a plan; none has run yet. Official scikit-learn, LightGBM, CatBoost, and Optuna documentation has been consulted. Additional boosting libraries have not been adopted or benchmarked.

Use trip-grouped cross-validation on the 80 training trips, with preprocessing fitted inside each training fold. Student testing is permitted development comparison, not an unbiased final test after repeated selection. Select using measured observation-level Macro F1, stability, probability usefulness, and runtime. HMM is a decoder, not a sixth trained classifier.

Metric definitions must distinguish observation-level road matching from binary candidate-row classification. Candidate misses must remain visible in accuracy accounting. Aggregate graph-local Macro F1 per trip under an explicit policy. Candidate-distribution log loss requires a stated covered-observation denominator and separate miss rate. Continuity must distinguish direct adjacency from a feasible connecting graph path; sequence performance needs an explicit definition.

After baselines, run genuine Bayesian optimization with grouped CV, retain actual trials and compute cost, compare tuned versus untuned, and compare classifier-only versus classifier plus HMM. Do not assume tuning or smoothing improves accuracy.

## Milestones and next actions

| Milestone | Intended evidence | Current status |
|---|---|---|
| M0 | Common Git base, separate worktrees, accepted interface hash | Completed contract handshake; both ACKs recorded in shared accepted-contract manifest |
| M1 | Real permitted-data prediction path and API/map vertical slice | A diagnostic passed all ten student-test trips and CLI/core parity; combined API/UI integration pending |
| M2 | Five measured models and application coverage | Not started |
| M3 | Bayesian trials, final assets, HMM and measured comparisons | Not started |
| M4 | Audited report, integrated checks and delivery readiness | Not started |

A's next actions are to review B's integration of the pinned M1 handoff, then profile a training-only pilot and implement the measured five-model comparison after milestone synchronization. B owns application and integration progress reporting; this file currently makes no claims about unreviewed B work.

External requirements still pending include organizer scoring clarification, reserved evaluator provisioning, actual two-physical-laptop demonstration, and public repository submission. Local preparation is not proof of those steps.

## Progress log

- **18 November 2026:** Read all five student PDFs, the full master/protocol/start-here, both role prompts, and all existing project/mailbox Markdown. Checked Git and applicable local instructions. Completed read-only 90-trip inventory, schema/coordinate/ID/timestamp validation, graph connectivity checks, content fingerprint, and three-trip alignment pilot. Sent messages `A-0001` through `A-0003` to B. No source changes, training runs, artifact exports, or integration claims.
- **18 November 2026:** Added this team guide at the user's request and prepared message `A-0004` asking B to include the exact document in bootstrap. Document remains uncommitted until that happens.

When updating this log, include source/run IDs and evidence paths for new results, separate implemented from executed and externally verified work, and correct stale status statements. Team members should review this guide and the recorded results before using its explanations in the report or viva. AI assistance must be disclosed as required by the event policy; it does not replace the team's understanding or actual experimentation.

- **18 November 2026:** Bootstrap/worktrees and bilateral contract acceptance completed. Continued in A's worktree. Wrote initial scientific modules and tests, an explicitly diagnostic artifact exporter, and the shared inference facade; validation remains pending dependency installation. Preliminary full-dataset candidate profiling gave 1,359,081 training candidate rows (1,362 empty observations) and 130,963 student-test candidate rows (none empty), using approximate local geometry at 100 m/top-8. These are budget estimates, not finalized coverage scores; missing reference arcs require separate aligned-label coverage accounting.

- **18 November 2026:** The isolated Python environment passed dependency compatibility checks and all 11 initial scientific tests. Published the direct pins and complete dependency lock in commit `16b447a`; sent B `A-0010` so application work can use the tested versions. No model training or integrated application acceptance is claimed.

- **18 November 2026 — M1 scientific evidence:** Reproducible EDA completed on all 90 permitted trips from source `e40733568bc39c41f771940469420d50b58e2929`; see `results/eda/initial-validation-v1/{metadata.json,trips.csv,file-hashes.json}`. The fingerprint matches the preliminary inspection. The explicitly geometric diagnostic completed all ten student-test trips (19,160 observations) from check source `9540ae6004a91d402bf24f35bbc3564cf2d0be7a`; see `results/experiments/m1-diagnostic-v1/{summary.json,checks.json}` and `artifacts/diagnostic-v1/manifest.json`. Core prediction took approximately 72–859 ms per trip in this run, excluding prior input loading and HTTP serialization. All boundary invariants passed; first-trip CLI/core arc/status/segment signatures matched. Scoring remains unavailable. Nearest-geometry choices produce many disconnected pieces (e.g. 1,022 on trip `00000000`); these are exposed, not bridged or called accurate. No trained-model or HMM benchmark results exist yet.
