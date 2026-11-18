# PathSnap: team understanding and progress

Updated: 18 November 2026 (India time). Maintainer: Agent A.

This is the team's reading guide and progress log. It records what has actually happened, explains the scientific decisions, and identifies what remains. It is not a substitute for the original PDFs, experiment records, or the consolidated report. Update this file after meaningful findings, experiments, handoffs, and integration reviews.

## Current state

The instructions and available development data have been inspected. No model has been trained, no pipeline has been implemented, and no integrated application has been verified by A yet. The repository still has no initial commit. Agent B must create the common bootstrap commit, publish the worker paths, and propose the interface contract before dependent implementation starts.

This document was added to the repository directory at the user's request before worktrees existed. It is awaiting inclusion in B's bootstrap commit; it is not yet committed. After bootstrap, A maintains it in A's assigned worktree and hands off committed revisions for integration. No separate documentation branch is needed: the document travels with the reviewed scientific changes.

A has sent three findings/startup messages and a documentation handoff through the shared mailbox. No B reply was available at this update. A sent questions about official scoring semantics to B for organizer clarification; no organizer request or answer has been independently verified.

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
| M0 | Common Git base, separate worktrees, accepted interface hash | Waiting for B bootstrap and proposal |
| M1 | Real permitted-data prediction path and API/map vertical slice | Not implemented; a geometric diagnostic must be labeled clearly |
| M2 | Five measured models and application coverage | Not started |
| M3 | Bayesian trials, final assets, HMM and measured comparisons | Not started |
| M4 | Audited report, integrated checks and delivery readiness | Not started |

A's next actions are to review B's published contract, verify the common base/worktree and contract hashes, persist reproducible EDA, implement candidate/feature/alignment mechanics, and profile a training-only pilot before choosing the experiment budget. B owns application and integration progress reporting; this file currently makes no claims about unreviewed B work.

External requirements still pending include organizer scoring clarification, reserved evaluator provisioning, actual two-physical-laptop demonstration, and public repository submission. Local preparation is not proof of those steps.

## Progress log

- **18 November 2026:** Read all five student PDFs, the full master/protocol/start-here, both role prompts, and all existing project/mailbox Markdown. Checked Git and applicable local instructions. Completed read-only 90-trip inventory, schema/coordinate/ID/timestamp validation, graph connectivity checks, content fingerprint, and three-trip alignment pilot. Sent messages `A-0001` through `A-0003` to B. No source changes, training runs, artifact exports, or integration claims.
- **18 November 2026:** Added this team guide at the user's request and prepared message `A-0004` asking B to include the exact document in bootstrap. Document remains uncommitted until that happens.

When updating this log, include source/run IDs and evidence paths for new results, separate implemented from executed and externally verified work, and correct stale status statements. Team members should review this guide and the recorded results before using its explanations in the report or viva. AI assistance must be disclosed as required by the event policy; it does not replace the team's understanding or actual experimentation.
