# PathSnap end-to-end build prompt

Copy the text below into the coding agent that will implement the project. Run it with this workspace available. This prompt specifies work to perform; it does not claim experiments, deployment, or training have already happened.

For the two-LLM execution requested for this project, begin with `PATHSNAP_TWO_LLM_START_HERE.md` and give each session its own `PATHSNAP_LLM_A_PROMPT.md` or `PATHSNAP_LLM_B_PROMPT.md`. Both read this complete master specification and `PATHSNAP_TWO_LLM_PROTOCOL.md`. The shared protocol refines file ownership, worktree paths, communication, documentation destinations, and Git integration; do not have both sessions independently implement this whole prompt in one checkout. All original student-material, scientific, design, integrity, and final-audit requirements remain mandatory.

---

Act as a senior ML engineer, geospatial engineer, full-stack engineer, and product designer. Implement PathSnap completely in the existing project, following the supplied student materials and producing a distinctive, polished evaluator interface. Complete the real ML system as well as the frontend. Make reasonable implementation decisions autonomously, verify them, and keep an honest record of completed work and external blockers.

## 1. Read the authoritative materials first

Workspace: `/home/vismay-hs/Downloads/ML_Hackathon`

Project: `PathSnap_ML_Hackathon_81/`

Available dataset: `/home/vismay-hs/Downloads/ML_Hackathon/Student_folder/`, alongside the project and student-materials folders. Use this existing dataset directly; the training and student-testing data are already present.

Read every page of all five documents in `PathSnap_student_materials/` before implementation:

- `Main Guidelines.pdf`
- `Dataset Exploration.pdf`
- `Models and Training Guidelines.pdf`
- `Deliverables.pdf`
- `Assessment and Plagiarism Policy.pdf`

Inspect applicable `AGENTS.md` files, existing source, READMEs, dependency files, and git status. Preserve existing useful work and the established folder structure. The project scaffold contains README placeholders and Python requirements; inspect current implementation status rather than assuming a working pipeline exists. The dataset is available separately in the sibling `Student_folder/` directory.

Create a requirements traceability document mapping each mandatory requirement to its source document/page, implementation location, validation evidence, and status. Distinguish mandatory requirements from recommendations and your own design choices. Recheck the actual PDFs rather than treating this prompt as a replacement for them. Clarify genuine contradictions instead of silently inventing an official interpretation.

The required final submissions are exactly two: a public GitHub repository and one consolidated technical report PDF. Supporting maps, logs, artifacts, screenshots, and report sources belong within the repository. The materials also mention a first evaluation phase before lunch; prioritize a truthful demonstrable vertical slice and maintain a readiness checklist without assuming an unstated deadline.

### Maintain an honest, useful commit history throughout

Create a local Git commit after each completed, coherent implementation milestone and meaningful verified fix. Do this during development, rather than leaving all work for one final commit. Inspect the existing repository and branch first; initialize Git inside `PathSnap_ML_Hackathon_81/` only if necessary, preserve existing history and user changes, and stage the intended files explicitly. Do not create a parent repository that accidentally includes `Student_folder/`.

Use short descriptive messages such as `feat(data): validate trip files and preserve original IDs`, `feat(models): record grouped baseline comparisons`, or `fix(hmm): handle unreachable candidate sequences`. Explain significant design decisions, checks performed, and limitations in commit bodies where helpful. Keep each commit reviewable and internally consistent, including related configuration, documentation, and relevant tests. A meaningful step may span several files; do not create a commit for every tiny edit or unrelated bundle.

Suggested commit boundaries, adapted to actual progress:

1. Requirements mapping, dataset configuration, and reproducible setup.
2. Raw-data validation, permitted-data EDA, and provenance records.
3. Reference alignment contract, candidate generation, and feature engineering.
4. Shared training/evaluation infrastructure and distinct baseline model implementations.
5. Actual model comparisons, selected-model justification, and result-backed plots.
6. Bayesian search, saved trials, tuned-model comparison, and final inference assets.
7. HMM/Viterbi implementation, edge-case checks, and measured decoder comparison.
8. FastAPI contracts, isolated scoring, readiness, and receiving-end logs.
9. UI reference research, original design system, and application shell.
10. Real map interactions, API integration, state handling, and responsive/accessibility fixes.
11. Two-laptop deployment documentation and integration verification.
12. Folium/report evidence, consolidated PDF, and final requirements audit.

Split or combine boundaries when the actual change requires it, and add later fix/polish commits as findings arise. Never manufacture history by backdating commits, creating empty milestones, claiming unexecuted experiments, or rewriting prior history to make unfinished work look complete. Do not amend, squash, reset, force-push, or overwrite unrelated changes unless explicitly requested. Use the configured Git identity; if unavailable, report the exact issue without inventing an author.

Record the source revision, dataset partition/fingerprint, configuration, and run ID in experiment metadata so results can be traced to the implementation that produced them. Keep immutable run records, including failed attempts where relevant. Distinguish source revision from any later commit that adds result files. Before each commit, review the staged diff, check for raw data/secrets/protected labels/oversized outputs, and run relevant validation. If a milestone intentionally adds failing checks or has an external blocker, state that truthfully instead of claiming it passed. Finish with a concise `git log` summary and clean-status or explicitly explained remaining changes. Push only within existing user authorization; preserving local history does not require publishing.

## 2. Explore and use these repositories deliberately

Read the current official README, relevant skill files, compatibility requirements, and license before adopting anything. Record the actual version or commit, files/components used, purpose, and attribution in `docs/repository-references.md`. Do not claim a skill was executed when you only read its guidance. Do not assume every repo is a package to install or an application dependency. Use project-local integration where suitable; preserve existing agent configuration.

Design and engineering guidance:

1. [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill): use the relevant frontend taste guidance for art direction, hierarchy, consistency, and visual inspection. Adapt website-oriented advice to a dense geospatial application; marketing heroes, stock photos, and full-screen storytelling sections are not requirements here.
2. [pbakaus/impeccable](https://github.com/pbakaus/impeccable): use applicable critique, audit, accessibility, responsive hardening, and polish workflows. Verify the actual current command syntax for the active coding tool.
3. [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md): use its frontend craft guidance to develop deliberate typography, composition, and interaction details.
4. [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills): consult applicable React performance, composition, and web interface review guidance.
5. [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail): apply its simplicity and reuse principles. Prefer readable modules, existing dependencies, and native browser features over unnecessary abstractions. Simplicity must preserve every hackathon requirement.
6. [affaan-m/ECC](https://github.com/affaan-m/ECC): use relevant planning, research, verification, and code review guidance. This is the verified repository intended by the misspelled `affan-m/ecc/tree` reference. Do not install an entire agent configuration collection merely to use one workflow.
7. [ruvnet/ruflo](https://github.com/ruvnet/ruflo): explore its engineering orchestration capabilities and document whether they materially help. Treat it as optional development tooling, not the map-matching model, frontend framework, or a requirement to add LLM inference, RAG, or agents to the delivered application. Follow the active environment's delegation rules; a sequential implementation is valid when sufficient.

Frontend and verification sources:

8. [DavidHDev/react-bits](https://github.com/DavidHDev/react-bits): select only a few components whose actual source fits the interface, such as a restrained entrance or selection transition. Use compatible TypeScript variants and retain applicable notices. Check its actual license, including Commons Clause terms; do not describe it as plain MIT or assume paid Pro assets are available.
9. [motiondivision/motion](https://github.com/motiondivision/motion): use if an animation library is warranted. Prefer CSS for simple states and one main animation approach. Do not add several animation engines for similar effects.
10. [PaulLeCam/react-leaflet](https://github.com/PaulLeCam/react-leaflet): consider for the interactive React map and data-driven layers.
11. [radix-ui/primitives](https://github.com/radix-ui/primitives): consider for accessible dialogs, tabs, tooltips, and menus where native elements do not suffice. Style them consistently with the project's design system.
12. [microsoft/playwright](https://github.com/microsoft/playwright): use for meaningful browser workflow checks and visual inspection.

Mandatory geographical output and tuning tools:

13. [python-visualization/folium](https://github.com/python-visualization/folium): generate the required Folium development maps and report evidence. A React map does not replace this requirement.
14. [optuna/optuna](https://github.com/optuna/optuna): consider a documented Bayesian strategy such as TPE for the chosen model, retaining the full search history.

Use standard ML/geospatial libraries appropriately, while independently developing this team's task-specific processing, features, experiments, and integration. Do not copy another team's implementation, trained weights, configurations, derived datasets, results, or report. Explore additional repositories only to solve a concrete missing need and record why they are useful. Repository count is not a success metric.

When guidance conflicts, the supplied task and student materials govern. Maintain one product design system. Do not blend incompatible aesthetic prescriptions or let third-party defaults expand the scope.

## 3. Preserve the required system architecture

Laptop 1 runs the trained classifier, preprocessing, candidate generation, road graph, HMM/Viterbi decoder, FastAPI service, and isolated server-side scoring.

Laptop 2 runs the evaluator-facing React UI. It obtains the ten reserved evaluation-trip IDs from the backend, sends the selected ID to FastAPI, and displays the returned prediction and permitted aggregate results.

Prediction must follow this flow:

`trip ID -> raw GPS + road network -> cleaning -> candidates -> features -> saved preprocessing -> selected trained model -> emissions -> HMM/Viterbi -> predicted segments + road geometry -> isolated server-side evaluation -> response -> UI`

The prediction path must not load `.route` files or receive reference-derived information. Scoring receives completed predictions separately and reads references through its own restricted interface. Evaluator labels must never enter features, model inputs, candidate generation, decoder parameters, frontend assets, map HTML, downloadable files, or API responses. Aggregate scoring results required by the guide may be returned; evaluator reference paths and per-observation correctness masks must not be returned.

Use React + TypeScript + Vite unless existing working code justifies another choice. Keep FastAPI as required. Make API addresses configurable, validate request/response schemas, and keep inference logic reusable outside HTTP handlers.

## 4. Inspect the actual dataset and protect partitions

The specified partitions are 80 training trips, 10 student-testing trips, and 10 evaluator-testing trips. Use training trips for fitting and group-aware cross-validation; student-testing trips for permitted development comparison; evaluator-testing trips only for final evaluation after freezing the system.

The current verified workspace layout is:

```text
/home/vismay-hs/Downloads/ML_Hackathon/
├── PATHSNAP_BUILD_PROMPT.md
├── PathSnap_student_materials/          # Five authoritative PDFs
├── PathSnap_ML_Hackathon_81/            # Implement the project here
└── Student_folder/                     # Existing raw development dataset
    ├── train/                         # 80 trips, 320 files
    │   └── <trip_id>/
    │       ├── <trip_id>.track
    │       ├── <trip_id>.nodes
    │       ├── <trip_id>.arcs
    │       └── <trip_id>.route
    └── student_test/                  # 10 trips, 40 files
        └── <trip_id>/                 # Same four-file naming pattern
```

An initial filesystem inventory confirmed all four expected files exist and are nonempty for all 90 development trips, with no overlapping trip IDs between the two partitions. This verifies file presence only; still perform the full content, schema, geographical, timestamp, graph, and reference validation required below. No evaluator-testing directory is currently present in `Student_folder/`.

Resolve the default development dataset root from the project root as `../Student_folder`, independent of the process working directory. Provide a documented override such as `PATHSNAP_DATA_ROOT`; use its `train/` and `student_test/` subdirectories. Configure a separate explicit evaluator root, such as `PATHSNAP_EVALUATOR_ROOT`, only when organizers provide that partition. Do not silently fall back from a missing evaluator root to student-testing data.

Keep the supplied raw files in place and treat them as read-only. Do not require copying them into the scaffold's suggested `data/raw/` location. Update the project's README, data README, configuration, and commands to reflect the actual sibling dataset location. Save derived development data under the project's ignored `data/processed/` folder and retain permitted results, logs, plots, and artifacts in their established folders. Never serve the raw dataset root as frontend static content or commit raw files by accident.

Begin real development EDA, target-alignment investigation, model training, HPO, decoder evaluation, and Folium generation using these existing permitted files. Do not stop at scaffolding or describe the development dataset as missing. The unavailable reserved evaluator partition only blocks final reserved-trip evaluation and its corresponding evidence.

For development UI/API integration, provide an explicit development mode backed by `student_test/`, visibly identified as student-testing data. Its current trip IDs are `00000000`, `00000007`, `00000009`, `00000040`, `00000052`, `00000056`, `00000065`, `00000076`, `00000077`, and `00000091`; discover them from the configured partition rather than hardcoding this list in application logic. Preserve leading zeros by treating IDs as strings. These ten trips must never be relabeled as the ten reserved evaluator trips. In evaluator mode, report unconfigured data honestly until the reserved partition is provisioned, then list its actual ten allowed IDs.

Do not inspect evaluator contents during development, perform evaluator EDA, tune against evaluator results, or include evaluator references in public outputs. Build development tests with training/student-testing trips and clearly identified synthetic fixtures. Obtain final evaluator trip identifiers through the approved manifest or backend provisioning process without exploring their protected contents.

Verify raw file formats rather than guessing:

- `.track`: headerless whitespace-separated longitude, latitude, timestamp in seconds.
- `.nodes`: headerless longitude, latitude; original zero-based row index is node ID.
- `.arcs`: headerless integer from-node and to-node columns; original zero-based row index is arc ID.
- `.route`: chronological sequence of traversed arc IDs, not necessarily one label per GPS observation.

Treat identifiers as graph-local unless actual permitted-data inspection establishes otherwise. Never train a global road-ID classifier that assumes unrelated per-trip arc IDs have the same meaning. Preserve original IDs through filtering, graph construction, candidate ordering, serialization, and decoding.

Inventory permitted trips, file availability/sizes, observation counts, schemas, missing values, invalid coordinates, duplicated timestamps, ordering, sampling gaps, geographical bounds, graph size, connectivity, isolated nodes, and reference availability. The nominal 1 Hz sampling and approximate 97% one-second steps are supplied expectations to verify, not measured results to claim.

Use justified projected metre coordinates or geodesic calculations. Document longitude/latitude versus latitude/longitude conventions at each library boundary. Verify graph directionality from supplied information; do not add reverse edges without evidence. Record cleaning decisions and maintain an index mapping to original observations so rows are never silently lost.

## 5. Resolve supervision and evaluation semantics before training

Investigate how a reference route can be associated with GPS observations. Never zip `.track` and `.route` rows, stretch the route by row count, treat route membership as sufficient pointwise truth, or assume a reference is physically error-free.

For permitted development data, implement and explain a defensible route-constrained alignment if observation labels must be derived. Preserve chronological traversal, repeated arcs, loops, ambiguity, and unmatched observations. Keep reference-based target construction isolated from reference-free feature and candidate generation. Document that resulting targets are derived reference labels and assess alignment limitations.

Define the scoring contract: observation alignment, valid/scorable masks, unmatched handling, candidate misses, graph-local label treatment, macro averaging, and sequence metrics. Apply identical definitions to every model and both decoder variants. If official pointwise scoring semantics remain unspecified, request organizer clarification and clearly label provisional metrics. Do not claim an arbitrary alignment method is an official accuracy definition.

Use a model formulation that generalizes to unseen trip graphs, such as candidate relevance scoring from geometry and motion features. Specify its training target and convert scores into a documented observation-level selection distribution. Do not mistake candidate-row binary F1 for observation-level road-segment Macro F1 or a binary relevance score for a calibrated multiclass probability.

Generate candidates from GPS and graph information alone using a suitable spatial index and justified radius/top-k strategy. Never inject a missing reference arc into candidates to improve measured coverage. Evaluate candidate coverage separately.

Consider defensible features such as perpendicular distance to a segment, projection fraction, heading agreement when movement supports it, segment orientation/length, elapsed time, speed estimates, and reference-free local geometry. Fit scalers, imputers, feature selectors, calibration, and any learned transformations inside each training fold.

## 6. Train and compare at least five real models

Train at least five distinct algorithms with meaningful configurations across several families. Choose strong methods appropriate to engineered candidate-level geospatial/tabular features and a small number of independent trips. The preferred initial five-model plan is:

| Model | Role and reason to investigate | Implementation considerations |
|---|---|---|
| Regularized Logistic Regression | Interpretable linear baseline for distance, heading, and motion features | Fold-fitted scaling/imputation; convergence checks; evaluate class weighting instead of assuming it helps |
| Distance-weighted KNN | Instance-based nonlinear baseline testing local similarity | Fold-fitted scaling; control memory/inference cost; choose neighborhood size from training validation |
| Random Forest | Nonlinear interactions and an ensemble baseline | Control depth/leaf sizes; record feature importance cautiously; assess probability quality and latency |
| Extra Trees | An alternative randomized ensemble to compare generalization and runtime against Random Forest | Use genuinely distinct estimator/training behavior, not a renamed Random Forest configuration; assess leaf regularization |
| HistGradientBoostingClassifier | Efficient gradient-boosted nonlinear candidate scorer using the existing scikit-learn dependency | Investigate learning rate, iterations, leaf complexity, minimum leaf samples, and regularization; keep any early-stopping holdout trip-aware |

This replaces the earlier basic shortlist; a single Decision Tree may be an additional interpretability diagnostic, but need not displace a more useful ensemble experiment. Nearest-road and a geometrical HMM can provide extra non-ML baselines, but do not count as one of five trained classifiers. A tuned version of one algorithm or classifier-plus-HMM also does not count as a separate distinct ML algorithm.

Research the current official [scikit-learn ensemble documentation](https://scikit-learn.org/stable/modules/ensemble.html), [LightGBM classifier documentation](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html), and [CatBoost classifier documentation](https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier). Consider LightGBM or CatBoost as an additional stronger contender, or as a documented replacement for a planned baseline, if dataset size, feature types, install compatibility, and measured compute budget justify it. Their reputation does not establish that they outperform the simpler models on these trips. Keep at least five distinct trained/evaluated models and document every model actually attempted, including justified failures. Do not add multiple boosting libraries or large neural/GNN/transformer architectures merely for appearances.

Before large runs, profile permitted-data counts and graph sizes, estimate candidate-row volume, and time a small training-only pilot. Choose an explicit feasible experiment budget; aim for five trip-grouped folds when practical, documenting any justified alternative. Compare models on the same split manifests, inference inputs, coverage policy, and metrics. Any class/negative sampling should be train-only, documented, and consistently evaluated against the unchanged validation candidate sets. Avoid selecting different evaluation subsets to flatter different models.

Select the final classifier using measured CV Macro F1 as the justified primary criterion, then fold stability, student-testing evidence, probability quality, and end-to-end decoder runtime. Where statistically close, prefer the simpler/faster model with reliable inference. Investigate weak candidate coverage or target alignment before spending more trials on a classifier that cannot fix those bottlenecks. Save a short `docs/model-selection.md` explaining the recommended algorithms, observed tradeoffs, final choice, and rejected alternatives. Do not declare any method the best before running the experiments.

Use trip-grouped CV on the 80 training trips, with candidate rows for an observation and all observations for a trip kept together. Save seeds, split manifests, model configurations, feature schema, package versions, fold results, training/inference times, and artifacts. Keep negative sampling and calibration within training folds where applicable.

Use a suitable spatial index such as a segment bounding-box tree with exact metre-based point-to-segment refinement, rather than scanning every road for every observation. Choose the index after profiling and add a geometry dependency only when useful. Use shortest-path algorithms appropriate to nonnegative physical graph edge lengths, with bounded searches/caching where sound. Tune candidate radius/top-k and HMM transition/gap parameters only on permitted development data. Evaluate distance-only, added heading/motion features, and classifier-plus-HMM with a small justified ablation set to establish which methods help. If decoder tuning uses CV scores, keep its fitting/selection inside the corresponding training split; do not optimize against the fold being reported as held out.

Report observation-level Top-1 Accuracy, Macro F1, precision, recall, applicable Log Loss, candidate miss rate, route continuity, sequence-level performance, and timing. Define each denominator and aggregation. Include all relevant observations in headline accuracy accounting; separately show any conditional-on-candidate-coverage score. Never hide candidate misses by dropping them.

For graph-local arc labels, use a justified per-trip evaluation/aggregation or namespaced representation instead of merging unrelated arc IDs across trips. State macro averaging clearly. Define sequence performance and continuity explicitly, including how a valid connecting graph path differs from two directly adjacent arcs. Report unsolved gaps honestly.

For Log Loss, specify whether it measures candidate relevance or the observation-level candidate distribution. Candidate-set loss cannot directly score absent reference arcs: separately report misses and explicitly define any conditional loss or justified unmatched-state treatment. State N/A with reasons when a metric is inapplicable. Apply one consistent definition across comparable models.

Create an actual comparison table with algorithm family, configuration, CV Macro F1, student-testing Top-1 Accuracy and Macro F1, Log Loss, route continuity, and inference time, plus relevant precision/recall and timing detail. Select the model from measured generalization, stability, probability usefulness, speed, and decoder compatibility. Do not predeclare a winner or promise a target accuracy.

For every model actually tried, retain its code and results and document suitability, strengths/limitations, initial hyperparameters, loss/objective, observed performance, and evidence of overfitting/underfitting. Acknowledge repeated use of student-testing data as development selection, not an unbiased final test.

## 7. Perform real Bayesian hyperparameter optimization

After baseline comparison, optimize the selected promising model with a genuine documented Bayesian strategy, not a grid/random search relabeled Bayesian. Use trip-grouped CV on training trips and the justified Macro F1 objective consistent with the report.

Record search distributions, objective, seed, budget, actual completed/pruned/failed trial counts, parameters, scores, runtime, and best trial. Persist a resumable study and export its trial table. Refit with the chosen configuration and compare tuned versus untuned CV Macro F1, student-testing Top-1 Accuracy, Macro F1, applicable Log Loss, and inference time using the same partitions and definitions. Report if tuning did not improve performance.

Freeze all model, candidate-generation, feature, threshold, and decoder choices before reserved final evaluation. Export required model/preprocessing artifacts, feature order/types, probability transformation, spatial settings, HMM parameters, and reproducible metadata.

## 8. Implement HMM and Viterbi correctly

Hidden states must preserve each observation's candidate-to-arc correspondence, including projected position when needed. Derive emissions consistently from the selected model's outputs and document normalization or calibration. A normalized relevance score is not automatically calibrated confidence.

Model transitions using road-network feasibility, distance along the graph, observation displacement, and elapsed time. Account for partial distances from/to projected positions, directed travel, remaining on the same arc, reachable intermediate arcs, GPS noise, and feasible movement. Cache expensive graph computations where useful without caching canned final predictions.

Implement Viterbi in log space with stable numerical handling, initialization, recurrence, backpointers, and termination. Define explicit behavior for empty candidates, impossible transitions, all-unreachable states, stationary observations, invalid time deltas, and long GPS gaps. Segment or restart decoding when justified; expose gaps instead of inventing connected roads or straight-line bridges.

Return a per-observation status and predicted arc for matchable relevant observations, preserving original indices. Distinguish chosen observation arcs from connecting road paths used for visualization. Build route geometry from actual graph segments and legal connectors.

Compare classifier-only versus classifier-plus-HMM on permitted development data. Report pointwise metrics, defined sequence performance, continuity, runtime, successes, and failure cases. Do not assert that smoothing always improves accuracy.

## 9. Build a real FastAPI service

Use clear typed contracts, for example:

- `GET /health`: service availability and readiness without sensitive file paths.
- `GET /trips`: allowed trip IDs and safe display metadata from the configured operating mode. Explicit development mode lists student-testing trips; evaluator mode lists only the separately provisioned reserved trips. Keep the mode visible and never substitute one partition for another.
- `POST /predict` with `{ "trip_id": "..." }`: validate the allowlisted ID and run the complete saved-artifact inference pipeline.

If actual runtime warrants jobs, expose a small documented job/status/result flow. Otherwise use a simple request flow. Show progress stages only when reported by the server; never animate fabricated percentages.

Responses should include a request ID, model version, predicted geometry, permitted GPS/network geometry, observation statuses, elapsed timings, warnings, and allowed aggregate metrics. Use documented coordinate order and units. Return unavailable metrics as null with a reason, not zero or a fabricated score.

Load artifacts safely at startup, report missing/incompatible assets explicitly, validate filesystem access through registered trip IDs, and keep reference evaluation isolated from inference. Configure CORS for the actual Laptop 2 origin. Prevent stale or out-of-order responses from overwriting a newer trip selection.

Log incoming requests, trip IDs, model version, pipeline stages/timings, completion, and failures on Laptop 1. The evaluator must be able to observe real receiving-end API logs. Never put raw labels in frontend-facing errors or logs served to the browser.

Hold backend implementation to the same standard as the interface: clearly separated loading, prediction, decoding, scoring, and transport modules; validated artifact/schema versions; deterministic configuration; bounded request work; and useful error responses with request IDs. Do not run expensive CPU inference directly inside an `async` handler in a way that blocks the event loop; select a simple appropriate synchronous endpoint/thread or bounded worker strategy and verify readiness/health remain responsive. Profile cold startup, feature construction, model inference, graph transitions, decoding, serialization, and complete request time. Optimize measured bottlenecks, prevent duplicate submissions and unbounded job buildup, and keep predictions reproducible across CLI/API execution. Do not introduce queues, microservices, authentication, or databases unless a concrete requirement warrants them.

## 10. Design a distinctive evaluator workspace

Write a short `DESIGN.md` before styling: intended users, screen hierarchy, typography, spacing, color tokens, surfaces, borders, controls, motion, and map-layer conventions.

### Research real geospatial interfaces before choosing the design

Review the following official public references and their accessible product screenshots/demos. These are interaction references to study, not templates to copy or additional services to depend on:

- [Kepler.gl user guides](https://docs.kepler.gl/docs/user-guides): study its point/line/trip layers, layer visibility, tooltips, legends, time playback, and split-map comparison. Decide which limited subset directly helps evaluate a reconstructed trajectory.
- [Felt map dashboards](https://felt.com/platform/dashboards): study the relationship between map, compact statistics, filters, and feature details, and how the visible data context stays understandable when exploring.
- [Fused Workbench](https://docs.fused.io/workbench/overview/): study how a geospatial workspace relates layers, outputs, and workflow context. Use its data-workspace organization only where it benefits this focused evaluator task; do not import a code editor, workflow canvas, or AI chat into PathSnap.
- [deck.gl](https://github.com/visgl/deck.gl): inspect examples only if route/point volume makes renderer performance a real issue. Keep the simpler React Leaflet approach if it meets actual needs; do not install two map renderers for visual prestige.

Create `docs/ui-research.md` with the exact URLs, access dates, screenshots or observed UI details where accessible, useful patterns, unsuitable patterns, and the specific original PathSnap decisions they inform. If a live demo or screenshot cannot be accessed, state that limitation instead of claiming visual inspection. Inspect product screens, not only promotional landing pages. Do not upload the supplied dataset to external reference products. Preserve source attribution for any reused assets or licensed component code.

Compare two lightweight layout sketches, such as a left trip rail with a right inspector versus a consolidated left control panel with a bottom results strip. Choose one based on the evaluator's actual sequence: select a trip, reconstruct, inspect the route, understand results, and choose another trip. Implement one coherent original direction; do not combine every reference's panels, colors, and animations. Make a real-data vertical slice early and use screenshots to judge whether the interface communicates the problem well before polishing the rest.

Design direction: a precise cartographic instrument for inspecting trajectories. Give the map most of the working area; use a compact application header, a clear trip-selection rail, a primary “Reconstruct route” action, and a focused results inspector. Use typography, alignment, thoughtful density, and meaningful data to create character.

Start with a restrained neutral surface, high-contrast text, one coherent action accent, and distinct accessible route colors. Choose a readable sans family and tabular numeric styling; keep font assets available on the demo network. Define design tokens rather than scattering arbitrary values. Use borders and elevation selectively, avoiding repetitive floating cards for every statistic.

The opening view should make trip selection and reconstruction immediately obvious. Include:

- Exactly the ten provisioned evaluator-trip choices when final evaluation data is configured; no invented IDs or filler trips when unavailable. While developing against the existing dataset, show the ten real student-testing choices in clearly labeled development mode.
- Clear connection/readiness state and configured server address where useful.
- Raw GPS points, road network, and predicted-route layers, with labels, legend, toggles, fit-to-route, and reset controls.
- Selected-observation inspection using permitted prediction data, never evaluator labels or correctness masks.
- Results with accurately named accuracy metrics, continuity, processing time, model identity, and useful gap/candidate warnings.
- Keyboard-operable controls, visible focus, contrast, accessible names, clear units, and non-color distinctions for map layers.
- Responsive layout that retains a usable map on smaller screens and long-content/overflow handling.
- Proper initial, loading, success, empty, missing-artifact, timeout, API-disconnected, and failed-request states with actionable messages.

Keep development evidence separate from final evaluation mode. Development views/maps may show train/student-test references; final evaluator views, exports, and embedded Folium content must never show evaluator reference geometry. Optional experiment views must read real recorded development outputs rather than hardcoded tables.

Avoid generic AI dashboard styling: decorative gradient blobs, neon glow, glass panels everywhere, oversized empty heroes, meaningless metric cards, ornamental charts, excessive pill controls, and vague marketing copy. Do not add unrelated login, billing, chat, or social features.

Use an explicit quality bar: no placeholder/fake metrics in normal operation; no dead controls; no unlabeled icon-only actions; no default component-library styling left unexplained; no clipped trip IDs or units; and no stale prior-trip results presented as the current prediction. Give dense information clear typography and grouping, keep the primary action easy to find, and ensure the map is useful before and after a request. Design actual empty/error states with the same care as the success screen. Use purposeful illustration or assets only if they explain the task; real trajectories and road geometry should supply the main visual identity.

Polish the whole user journey, frontend and backend together. Inspect at representative laptop sizes such as 1366×768 and 1440×900 and a small viewport around 390 px wide. Verify map resize after panels open/close, fit bounds without obscuring the route, consistent selected-trip context, legible layers at different zooms, and synchronized observation inspection. Fix visual regressions by comparing actual before/after screenshots. Ask whether a first-time evaluator can select a trip, run inference, and interpret results without a walkthrough; simplify the flow where they cannot.

## 11. Make animation functional and restrained

Use subtle hover/focus feedback, clear selection changes, inspector transitions, and optional route playback based on returned geometry. Target short transitions around 120–220 ms where appropriate, honor reduced-motion preferences, and keep interaction responsive.

If using React Bits, select and customize a small suitable interaction. Do not turn the evaluation screen into a component gallery. Avoid animated backgrounds and expensive effects that compete with the map. Keep heavy map updates outside unrelated renders; use canvas rendering, geometry simplification for display, or lazy loading only where justified, preserving full-resolution predictions for scoring.

Route playback is visualization after prediction, not fake inference progress. It must have pause/reset controls and must never interpolate across disconnected graph gaps as though they were valid roads.

## 12. Produce mandatory Folium maps and real plots

Generate Folium HTML maps from actual permitted development trips showing raw GPS, road geometry, reference route where available, and predicted route. Use distinguishable layers, legend, labels, appropriate bounds/zoom, and layer controls. Include classifier-only versus HMM layers when useful.

Retain map-generation code and interactive HTML or reproducible generation instructions. Include at least one representative exported view/screenshot in the PDF. Keep development maps out of evaluator-facing serving paths when they contain references.

Generate CV Macro F1 comparisons, student-testing Top-1 Accuracy/Macro F1 comparisons, applicable Log Loss plots, tuned/untuned comparisons, and decoder comparisons from saved results. Include relevant model-specific visual evidence for every trained model. Confusion matrices are useful optional diagnostics; produce epoch training/validation loss plots only for models that actually generate such histories. Do not fabricate learning curves for trees, KNN, or other algorithms without epoch histories.

## 13. Deliver reproducibility and two-laptop operation

Keep processing, features, models, evaluation, HPO, HMM, visualization, API, UI, configs, artifacts, results, maps, notebooks, and report in the existing corresponding folders. Add shared utilities only where they have a clear purpose.

Provide verified commands for environment setup, permitted-data validation, EDA, feature preparation, baseline training, HPO, final fitting/export, decoder evaluation, map/plot generation, API startup, UI startup/build, and report generation. Use `python3` where `python` is unavailable. Lock frontend dependencies and record/pin a tested compatible Python environment after checking it.

Document Laptop 1 binding to its LAN interface, Laptop 2 using Laptop 1's LAN IP rather than `localhost`, actual ports, CORS, firewall/network troubleshooting, and health checks. Keep model/data processing on Laptop 1. Avoid dependence on online CDNs for critical UI assets. Provide graceful base-map tile failure so locally served graph/prediction geometry remains inspectable; obey tile-provider licensing and usage policies.

Include final inference assets subject to repository size constraints. If large artifacts need another supported distribution mechanism, provide exact versions/checksums and evaluator-accessible acquisition instructions. Keep protected data, evaluator references, secrets, and credentials out of public commits.

Prepare the repository for the required public submission and report any remaining push/accessibility step honestly. Do not publish a repository or change its visibility without appropriate user authorization. Local preparation alone is not evidence of a public submission.

## 14. Generate one evidence-backed technical report PDF

Follow the structure required by `Deliverables.pdf`, including its sections 2–7:

- Dataset understanding/EDA: preprocessing, findings, feature choices and reasons, missing values, trajectory/network plots, Folium evidence, partition used for every analysis.
- Model experimentation: consolidated comparison table and a separate subsection for every model tried covering suitability, strengths/limitations, initial configuration, objective/loss, real student-testing metrics, overfit/underfit evidence, and relevant visualizations.
- Bayesian optimization: search space, objective, actual trials, best configuration, compute cost, and tuned/untuned comparison under identical definitions.
- HMM/Viterbi: hidden states, emissions, transitions, recurrence/implementation, candidate gaps, disconnected roads, GPS gaps, and measured classifier-only versus HMM outcomes.
- Geographical visualization: representative actual Folium maps with layer conventions, reference limitations, and reproducible interactive artifacts/code.
- API/UI/deployment: actual working UI screenshots and successful receiving-laptop API terminal evidence, plus architecture and two-laptop reproduction instructions.

Every number, table, chart, and technical claim must trace to actual repository evidence. Generate tables/plots from saved experiment records to avoid transcription drift. Mark missing evidence explicitly in drafts; do not manufacture terminal screenshots or experimental conclusions. Verify the produced PDF opens, contains the required sections, and has readable figures without clipping.

Support the team's own interpretation and review. Do not submit generic AI-written conclusions as independently conducted analysis. State assistance as required by the event policy and provide concise implementation notes that help every member explain preprocessing, supervision, models, HPO, HMM, evaluation, API, UI, limitations, and reproducibility during the viva.

## 15. Verify meaningful correctness and completion

Test high-risk behavior: parsing and index preservation; coordinate order/metre distances; trip-group split isolation; fold-fitted preprocessing; reference-free candidates/features/inference; candidate-to-arc mappings; probability edge cases; tiny-graph Viterbi with a known optimum; impossible transitions and empty candidates; gap handling; metric denominators; and API contracts.

On permitted development trips, run real end-to-end inference from UI selection through HTTP and the saved model/decoder to the displayed route and metrics. Verify request IDs in the UI correspond to Laptop 1 logs. Use Playwright/browser inspection for desktop and small-screen layouts, keyboard flows, reduced motion, loading/errors/retry, layer controls, long text, stale-response handling, and console errors. Run Python checks and frontend lint/type/build checks appropriate to the implementation.

Use permitted data to exercise the same ten-choice interaction before final evaluation. After freezing the system and only within authorized final evaluation, verify it serves all ten reserved trips. Never use final evaluator smoke-test results to tune the model, parameters, thresholds, UI correctness annotations, or predictions. If two physical laptops or final evaluator access are unavailable, record those checks as pending; a local integration test does not prove a LAN demonstration occurred.

Run the applicable Impeccable critique/audit/polish workflow and React/web-interface review, fix substantive findings, and retain a concise validation record. Inspect real screenshots rather than assuming a successful build command proves design quality.

The real training and student-testing dataset is available in `../Student_folder` relative to the project root. Use it to execute the required development experiments and integration checks. If additional required data, scoring clarification, compute, credentials, artifacts, or hardware are unavailable, identify the exact blocker early, continue independent useful work, and leave reproducible commands. Keep missing evaluator provisioning separate from available development work. Synthetic fixtures may validate mechanics but must be clearly separated and never count as the five real experiments, measured benchmark results, final evaluator runs, or submission evidence. Do not call the project complete while mandatory work remains.

Finish with what was built, real commands run and outcomes, measured results with evidence paths, artifact/report locations, remaining blockers, and exact two-laptop startup instructions. Distinguish implemented, executed, and externally verified work.

Include the actual milestone commit history, model-selection rationale, UI research/design decisions, backend timing evidence, and remaining visual/functional issues in this final handoff. Verify that claims of “polished,” “working,” and “best model” are supported respectively by inspected screens, executed end-to-end checks, and recorded comparative experiments.

## 16. Final improvement instruction

Before declaring completion, reread all five student-material PDFs and audit the implementation, UI, ML pipeline, experiments, HPO, HMM/Viterbi, API, Folium maps, saved artifacts, deployment, public-repository readiness, consolidated report, meaningful commit history, model/method selection, and UI research/design quality against the requirements traceability document. Improve the build wherever required. If any instruction or necessary integration detail was missed, implement and verify the correction within the authorized scope. Fix inconsistencies between code, results, report, and demonstrated behavior; preserve independent work and evaluator-label isolation. Never conceal an omission with invented data, metrics, screenshots, or completion claims. Clearly identify any externally blocked requirement and the exact action needed to finish it.
