## 2. Dataset Understanding

This scientific section uses only the supplied 80 training and ten student-testing trips. Reserved evaluator data were not available during development and were not inspected for EDA, training or selection. A separate frozen-system final validation is reported in the system section. Numerical tables below are generated from saved development JSON/CSV records by `src/evaluation/scientific_report.py`. Pointwise scores use the explicit **provisional** alignment policy `pathsnap-scoring-v0`; organizer clarification remains necessary.

### 2.1 Inventory, geometry and cleaning

| Partition | Trips | GPS observations | Nodes | Directed arcs |
|---|---:|---:|---:|---:|
| train | 80 | 208,417 | 1,933,485 | 3,876,904 |
| student_test | 10 | 19,160 | 90,689 | 185,041 |

All supplied GPS/node coordinates and numeric values passed validation; timestamps increased strictly. Exactly one-second steps account for 96.50% of training and 98.62% of student-testing steps, but maximum gaps are 153,064 s and 210 s respectively. Gap handling is therefore necessary. There are 100 training and six student-test zero-length arcs: these retain their original graph IDs and topology but cannot be geometric candidates. Supplied reference traversals contain 67/255 repeated occurrences and 13/1 nonadjacent successive arc pairs (train/student test). References must retain occurrence order and disconnected geometry.

Parsing preserves original row-based observation, node and arc IDs. Malformed physical rows fail explicitly instead of being silently skipped. Invalid observations in future inputs remain in place with validity/reason masks; inference does not silently delete them. Numeric feature imputation uses medians fitted only on fold training rows. No learned transformation sees validation or student-test rows during fitting.

Road geometry is a straight directed node-to-node segment, projected separately per trip using WGS84 local azimuthal-equidistant coordinates centered on the median valid GPS location. `always_xy` fixes longitude/latitude order. Physical calculations use metres; browser geometry stays WGS84 `[lon, lat]`. This avoids applying Euclidean distances to degrees. Directed connectivity follows supplied arcs; unavailable traffic rules and turn restrictions are not invented.

![Trip sizes and timestamp gaps](results/figures/data-quality-v1/trip-sizes-and-gaps.png)

*Figure 1. All 90 permitted trips, separated by partition. Maximum time gaps use a log scale. Source: `results/eda/initial-validation-v2/trips.csv`.*

### Network connectivity and geographic extent

| Partition | Weak components per trip (min–max) | Strong components per trip (min–max) | Longitude extent | Latitude extent |
|---|---:|---:|---|---|
| train | 1–421 | 2–1942 | -100.419 to 137.237 | -34.640 to 61.267 |
| student_test | 5–100 | 6–415 | -93.424 to 77.271 | 42.646 to 61.700 |

There were no isolated supplied nodes. Disconnected components make a single connected route unsafe as a default. Extents span different regions, supporting per-trip metric projections. Per-trip file sizes, IDs, components and timestamp statistics remain in the EDA CSV.

### 2.2 Reference alignment and candidate accounting

A `.route` file is a road traversal, not one label per GPS row. Offline supervision uses monotone dynamic programming over traversal occurrences, including nonconsecutive repeats. Free endpoints and forward skips allow unobserved intervening arcs. Costs combine capped squared metric projection residual (20 m scale, 100 m cap) and a directional penalty of two when motion is reliable. A valid observation is scorable only if its aligned residual is at most 100 m. Low geometric margins below3 m are diagnosed, not removed. This derived policy is not certified organizer ground truth.

| Partition | Original rows | Scorable | Unscorable | Candidate covered | Candidate misses |
|---|---:|---:|---:|---:|---:|
| train | 208,417 | 187,867 | 20,550 | 185,020 | 2,847 |
| student_test | 19,160 | 19,143 | 17 | 19,059 | 84 |

The substantial training unscorable count is a limitation, not discarded evidence. Accuracy includes all scorable candidate misses and unmatched rows as errors; a separate original-row score and raw/scorable counts expose the denominator. Alternative official alignment could change both scores and model rankings.

![Target coverage](results/figures/data-quality-v1/target-coverage.png)

*Figure 2. Complete row accounting under provisional alignment; candidate misses are retained in accuracy denominators. Source: `results/eda/preparation-v1/preparation.json`.*

Indexed candidate generation uses length-binned segment-midpoint cKDTrees, conservatively querying radius plus maximum half-segment length and then refining exact segment projections. Radius100 m/top8 and deterministic distance/arc-ID tie ordering are fixed across models. Features are constructed before reference access: metric and log distance, heading cosine/validity, log arc length, projection fraction, speed, time delta and distance excess over the nearest candidate. Trip-local IDs and references are excluded from features.

### 2.3 Leakage controls and metrics

Five seeded (81) GroupKFold splits hold out whole training trips: 64fit/16validation per fold and every one of the 80 training trips held out once. Fit observations are deterministically capped at 400 scorable rows per training trip; all their candidate rows are retained. Validation and student testing are unsampled. A median imputer is fitted inside every model pipeline; LR/KNN also use fold-fitted StandardScaler. Predictions load only track/nodes/arcs. A separate post-prediction scorer alone reads references, and returns only aggregates.

Accuracy is pooled over scorable observations; Macro F1, precision and recall average per-trip road-class macro values over truth union matched predictions. Unmatched predictions cause false negatives. Conditional log loss uses only observations whose aligned arc occurs in candidates and describes normalized relevance, not calibrated confidence. Candidate miss rate is reported separately. Sequence similarity is one minus normalized Levenshtein distance of compressed observed-arc runs, not full-route accuracy. Continuity is the proportion of consecutive valid pairs within 30 s with a feasible directed route under the fixed physical bound; unmatched pairs fail. There is no global road-class confusion matrix because arc IDs are trip-local.

## 3. Model Experimentation

Five distinct algorithms completed identical grouped comparisons, with source `623a20253e03fa16c1dbecd782b4abd85352789a` and local total elapsed time 554.69 s at two threads. Complete per-fold/per-trip records, warnings, configurations and fitted assets are retained under `results/experiments/baselines-local-v1`. No model is credited for the HMM decoder as an additional classifier.

| Model | Training CV trip Macro F1 | Student accuracy | Student trip Macro F1 | Total seconds |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.634800 | 0.817166 | 0.650309 | 24.08 |
| Distance-weighted KNN | 0.666337 | 0.837852 | 0.706329 | 302.73 |
| Random Forest | 0.721476 | 0.859009 | 0.765520 | 160.90 |
| Extra Trees | 0.702618 | 0.853262 | 0.735686 | 41.40 |
| HistGradientBoosting | 0.725219 | 0.857912 | 0.766924 | 25.57 |

| Model | Student precision | Student recall | Conditional log loss |
|---|---:|---:|---:|
| Logistic Regression | 0.682786 | 0.646737 | 0.573085 |
| Distance-weighted KNN | 0.738438 | 0.700882 | 0.865981 |
| Random Forest | 0.790284 | 0.764245 | 0.373154 |
| Extra Trees | 0.762655 | 0.732716 | 0.415473 |
| HistGradientBoosting | 0.791504 | 0.765144 | 0.360599 |

| Model | Family / key initial settings | Student continuity | Student scoring ms | Final refit ms |
|---|---|---:|---:|---:|
| Logistic Regression | regularized linear; {"C": 1.0, "max_iter": 500, "random_state": 81, "solver": "lbfgs"} | 0.935816 | 103.54 | 682.80 |
| Distance-weighted KNN | instance based; {"algorithm": "kd_tree", "leaf_size": 40, "n_jobs": 2, "n_neighbors": 15, "weights": "distance"} | 0.940516 | 20862.75 | 610.37 |
| Random Forest | bagged randomized trees; {"max_depth": 16, "min_samples_leaf": 8, "n_estimators": 64, "n_jobs": 2, "random_state": 81} | 0.949446 | 530.63 | 29516.68 |
| Extra Trees | extremely randomized trees; {"max_depth": 16, "min_samples_leaf": 8, "n_estimators": 64, "n_jobs": 2, "random_state": 81} | 0.949708 | 586.88 | 4899.45 |
| HistGradientBoosting | histogram gradient boosting; {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.1, "max_iter": 100, "max_leaf_nodes": 15, "min_samples_leaf": 30, "random_state": 81} | 0.950648 | 386.58 | 1172.81 |

Student scoring timings include saved preprocessing, estimator scoring and per-observation selection; exclude cached candidate/feature construction, graph routing and reference metrics. Full-facade timings appear in section 5. Final refit fits the sampled observations across all 80 training trips. The source JSON retains per-fold fit time and warnings.

![Five-model grouped comparison](results/figures/baselines-v1/training-cv-macro-f1.png)

*Figure 3. Training-CV means; error bars are standard deviations of five fold means, not confidence intervals or independent point-level uncertainty.*

![Student testing metrics](results/figures/baselines-v1/student-test-accuracy-f1.png)

*Figure 4. Pooled accuracy and mean trip Macro F1 answer different weighting questions. Student data describe generalization and are excluded from model selection.*

![Conditional loss](results/figures/baselines-v1/student-test-conditional-log-loss.png)

*Figure 5. Conditional candidate-distribution log loss, lower is better. Candidate misses remain separate.*

### 3.1 Logistic Regression

A compact linear baseline tests whether geometric evidence combines approximately linearly. L2 regularization limits coefficient growth; standardized features support stable optimization. It cannot express all interactions among heading, distance and local geometry.

Regularized binary log loss; C1,lbfgs,max_iter500.

Fit-sample accuracy 0.812933; held-out CV accuracy 0.814273; student accuracy 0.817166. Fit rows are sampled whereas evaluation is unsampled: the gap is descriptive evidence, not a controlled overfit estimate. A high training score alone does not establish generalization. Detailed fold warnings and metrics are retained in `logistic_regression.json`.

![Logistic Regression local-road confusion](results/experiments/confusion-v1/logistic_regression.png)

*Diagnostic matrix for student trip 00000052; both axes use the complete ordered set of trip-local road classes. Original arc IDs are listed in the adjacent class-order JSON. This is not a global cross-trip class matrix.*

### 3.2 Distance-weighted KNN

Distance-weighted neighbors can learn nonlinear local feature patterns with little fitted parameterization. Standardization is essential for its metric. Prediction retains the training rows and was costly on this workload; sparse neighborhoods can also give overconfident relevance.

15 distance-weighted neighbors; kd_tree,leaf_size40. No iterative fitted loss optimizer.

Fit-sample accuracy 0.981883; held-out CV accuracy 0.819170; student accuracy 0.837852. Fit rows are sampled whereas evaluation is unsampled: the gap is descriptive evidence, not a controlled overfit estimate. A high training score alone does not establish generalization. Detailed fold warnings and metrics are retained in `knn.json`.

![Distance-weighted KNN local-road confusion](results/experiments/confusion-v1/knn.png)

*Diagnostic matrix for student trip 00000052; both axes use the complete ordered set of trip-local road classes. Original arc IDs are listed in the adjacent class-order JSON. This is not a global cross-trip class matrix.*

### 3.3 Random Forest

Bagged randomized trees model nonlinear interactions and resist simple feature scaling problems. Depth and leaf-size limits constrain fit complexity. Its CV result was close to HGB, and student accuracy exceeded untuned HGB, but its measured training/evaluation cost was larger.

64 bootstrap trees; Gini splits,max_depth16,min_samples_leaf8,seed81.

Fit-sample accuracy 0.894524; held-out CV accuracy 0.841899; student accuracy 0.859009. Fit rows are sampled whereas evaluation is unsampled: the gap is descriptive evidence, not a controlled overfit estimate. A high training score alone does not establish generalization. Detailed fold warnings and metrics are retained in `random_forest.json`.

![Random Forest local-road confusion](results/experiments/confusion-v1/random_forest.png)

*Diagnostic matrix for student trip 00000052; both axes use the complete ordered set of trip-local road classes. Original arc IDs are listed in the adjacent class-order JSON. This is not a global cross-trip class matrix.*

### 3.4 Extra Trees

Genuinely randomized split thresholds offer a distinct ensemble and inexpensive fitting here. Extra randomization can reduce variance but may lose fine distance/heading boundaries. It was competitive but below RF/HGB on the predefined CV objective.

64 randomized-threshold trees; Gini splits,max_depth16,min_samples_leaf8,seed81.

Fit-sample accuracy 0.852929; held-out CV accuracy 0.837582; student accuracy 0.853262. Fit rows are sampled whereas evaluation is unsampled: the gap is descriptive evidence, not a controlled overfit estimate. A high training score alone does not establish generalization. Detailed fold warnings and metrics are retained in `extra_trees.json`.

![Extra Trees local-road confusion](results/experiments/confusion-v1/extra_trees.png)

*Diagnostic matrix for student trip 00000052; both axes use the complete ordered set of trip-local road classes. Original arc IDs are listed in the adjacent class-order JSON. This is not a global cross-trip class matrix.*

### 3.5 HistGradientBoosting

Sequential histogram trees model geometric-feature interactions with compact assets. Learning rate, leaf count, iterations and regularization require control. It led the predefined CV Macro F1 at low measured cost and was selected for TPE; the small lead over RF should not be treated as a statistically established universal advantage.

Binary log loss;100iterations,15leaves,min_samples_leaf30,learning_rate0.1,L2=1,early_stoppingFalse,seed81.

Fit-sample accuracy 0.857506; held-out CV accuracy 0.843671; student accuracy 0.857912. Fit rows are sampled whereas evaluation is unsampled: the gap is descriptive evidence, not a controlled overfit estimate. A high training score alone does not establish generalization. Detailed fold warnings and metrics are retained in `hist_gradient_boosting.json`.

![HistGradientBoosting local-road confusion](results/experiments/confusion-v1/hist_gradient_boosting.png)

*Diagnostic matrix for student trip 00000052; both axes use the complete ordered set of trip-local road classes. Original arc IDs are listed in the adjacent class-order JSON. This is not a global cross-trip class matrix.*

Per-model confusion matrices preserve original trip-local arc IDs and unmatched=-1 in the separate `results/experiments/confusion-v1` supplement. Each PNG shows the complete matrix for student trip 00000052; class-order JSON maps matrix indices back to original IDs. Counts are not pooled across different road networks. This visualization is diagnostic and does not determine the selected model.

### Controlled feature-block ablation

The final prompt audit added a small feature ablation using the same HGB parameters, five training-trip folds, fit sampling and unsampled validation/student testing. Distance-only uses distance, log distance and excess over the nearest candidate. The next block adds heading cosine/validity. Full features additionally include arc length, projection fraction, speed and elapsed time. All candidates are unchanged and references remain excluded from features.

| Feature block | CV trip Macro F1 | Student accuracy | Student trip Macro F1 | Conditional log loss |
|---|---:|---:|---:|---:|
| distance only | 0.345099 | 0.510578 | 0.338318 | 0.929764 |
| distance heading | 0.652364 | 0.829128 | 0.666377 | 0.481082 |
| full features | 0.729680 | 0.860367 | 0.770553 | 0.352425 |

![Measured feature ablation](results/experiments/feature-ablation-v1/feature-ablation.png)

The fixed-parameter results support adding orientation and the remaining geometry/motion block over distance alone. Pure geometric distance cannot distinguish co-located reverse-direction arcs. This is a descriptive ablation, not a separately tuned competition: parameters were previously selected for full features. The final increment bundles geometry and motion, so it does not isolate their individual causal effects. The two new variants took 45.06 s in total, including CV, refits and evaluation. They do not count as extra distinct algorithms and did not trigger any final model or decoder retuning. Source and complete per-fold/trip records: `results/experiments/feature-ablation-v1`.

## 4. Bayesian Hyperparameter Optimisation

Optuna4.3.0 TPESampler(seed81) executed12 real sequential trials: four random startup trials followed by eight adaptive TPE trials. The objective is mean held-out-trip Macro F1 over the exact same five training-group folds, sampling and features. No student-test or evaluator metric enters the objective. Search space: iterations60–180; leaves7–31; minimum samples per leaf15–80; learning rate0.03–0.2 logarithmic; L2 regularization0.01–10 logarithmic. There was no random-search substitution for Bayesian tuning and no pruning of difficult folds.

Best trial 11 had training-CV Macro F1 0.729680, compared with 0.725219 untuned. Best parameters: `{"l2_regularization": 8.75151377351353, "learning_rate": 0.12261991419637631, "max_iter": 179, "max_leaf_nodes": 31, "min_samples_leaf": 80}`. Its final classifier-only student accuracy is 0.860367 and trip Macro F1 0.770553. Selection uses CV, not that descriptive student-test change.

Completed trial compute sums 166.75 s at four threads. The original process ended unexpectedly with 143 after 11 completed trials while the final sampled trial was running. SQLite retained its parameters; explicit recovery reran exactly those parameters, without replacing completed trials or sampling extras. `recovery.json` records both source revisions. Recovery-invocation elapsed 25.63 s includes its final trial and refit; it is not total tuning time. Interrupted partial-trial compute is unavailable. Full SQLite storage,12 trial files,fold metrics and failures/recovery provenance are retained under `results/hpo/hgb-tpe-v1`.

![Actual TPE history](results/figures/final-v1/bayesian-trials.png)

*Figure 6. Actual complete trial values and running best; adaptive TPE begins after the first four startup trials.*

![Tuned versus untuned](results/figures/final-v1/tuned-untuned.png)

*Figure 7. Same training folds and objective; the improvement is modest. CV used for tuning is selection evidence, not an unbiased nested-CV estimate.*

The search ranges balance measured laptop cost with capacity: iteration count and learning rate govern boosting fit; leaf count and minimum leaf support control local complexity; L2 regularizes uncertain leaf estimates. Log scales cover learning-rate/regularization orders of magnitude with a limited12-trial budget. Early stopping remains disabled to avoid an internal observation-level holdout crossing trip-group boundaries.

### Tuned and untuned results under the same definitions

| HGB variant | CV Macro F1 | Student accuracy | Student Macro F1 | Log loss |
|---|---:|---:|---:|---:|
| Untuned | 0.725219 | 0.857912 | 0.766924 | 0.360599 |
| Tuned | 0.729680 | 0.860367 | 0.770553 | 0.352425 |

Common-host inference profile: untuned median 502.74 ms; tuned median 863.93 ms across all ten student trips, same four-thread limit, one warmup and three measured passes each. Boundary: saved preprocessing, model scores and per-observation normalization/selection; candidate preparation, graph decoding and reference metrics excluded. See `results/experiments/selected-profile-v1/summary.json`.

## 5. HMM and Viterbi

The hidden state is a directed candidate arc together with its projected position. Emission scores are clipped, per-observation normalized binary relevance from the selected fitted classifier. They are discriminative scores, not calibrated GPS likelihoods. Transition log scores penalize the absolute difference between feasible directed route distance and observed metric displacement, divided by 25 m. Directed travel includes source-arc remainder, a Dijkstra connector and target-arc prefix. No reverse edges are invented; small backward projection noise up to 15 m on the same arc is treated as stationary.

A 65 m/s bound plus 50 m slack limits travel for each observed time interval. Empty candidates, time gaps above 30 s, nonpositive time intervals and all-unreachable transitions terminate or restart the lattice. Log-space Viterbi uses backpointers and subtracts a common offset per step for stability. The recurrence maximizes previous log score plus transition score plus emission log score. Route geometry consists of actual observed and connecting arcs, with disconnected pieces kept separate. The hybrid scoring assumptions follow the map-matching framework of Newson and Krumm (2009), adapted to learned emissions; they do not claim calibrated generative probabilities or unavailable real-world traffic restrictions.

All decoder parameters were fixed before the student comparison. Each of the ten student-testing trips ran twice through the actual reference-free facade, followed by the isolated scorer. All prediction invariants and development visualization schemas passed. Classifier-only aggregate metrics matched the independent cached HPO evaluation to1e-12 for all six checked metrics.

| Metric | Tuned classifier only | Tuned classifier + HMM |
|---|---:|---:|
| top1 accuracy | 0.860367 | 0.885493 |
| macro f1 | 0.770553 | 0.851054 |
| precision macro | 0.794938 | 0.865255 |
| recall macro | 0.768745 | 0.856570 |
| candidate miss rate | 0.004388 | 0.004388 |
| route continuity | 0.949760 | 0.999164 |
| sequence arc similarity | 0.638746 | 0.855911 |
| log loss | 0.352425 | 0.352425 |

![Classifier and HMM comparison](results/figures/final-v1/classifier-hmm.png)

*Figure 8. Measured development scores under provisional alignment. Sequence similarity compares observed-arc runs, not a complete reference traversal.*

Conditional log loss is identical because it evaluates the same classifier emissions; a Viterbi path is not an HMM posterior. The HMM improved both pointwise and continuity metrics here, but direction ambiguity, missing candidates, network/reference mismatch and unmodeled traffic rules remain limitations.

Connected route pieces fell from 974 to 28. Full facade inference across ten trips took 5.06 s classifier-only and 10.70 s HMM on this host, excluding separate scoring. These are local measurements, not a LAN guarantee. The portable checksummed bundle is `artifacts/hgb-hmm-v1`. Both modes retain 19,160 original observations;19,143 are provisionally scorable,17 unscorable and84 scorable candidate misses.

Development-only GPS/network/reference/prediction exports are under `results/hmm/hgb-hmm-v1/visualisation`. They supply B’s separate Folium generator and never enter UI/API inference inputs. Reference geometry is restricted to these permitted development exports. API evaluation exposes aggregate metrics only.

### Scientific evidence and remaining limits

EDA source `86343842fd4c73c6dd1a15ed99a3da6098eab93f`; baseline source `623a20253e03fa16c1dbecd782b4abd85352789a`; initial HPO source `5af7e3ceacde3f793220f28aa336b8c1f4f008f8` plus explicit recovery; trained comparison source `cce3485c116f589d7aed9554fd573620eb6c4d66`. Full hashes, configuration, data fingerprint, dependencies, per-fold/trip records and feature policy are in those run directories and the artifact manifest. `results/experiments/source-revision-map.json` resolves earlier metadata-cleanup revisions without altering original run evidence.

Organizer confirmation of pointwise alignment and the two-physical-laptop demonstration remain external checks. Reserved evaluator data arrived after the serving prediction system was frozen at accepted M3; its separate final validation is reported in the system section with the exact frozen source identity. No model or decoder choices changed after that validation. Student-test gains alone do not establish evaluator performance. Team members are responsible for explaining the implementation.

Primary method reference: Paul Newson and John Krumm, *Hidden Markov Map Matching Through Noise and Sparseness*, ACM SIGSPATIAL GIS2009, https://www.microsoft.com/en-us/research/publication/hidden-markov-map-matching-noise-sparseness/. The user supplied an Uber Maps talk summary as background; no video was inspected. ECC was reviewed for development workflow guidance only, as documented in `docs/ml/ecc-review.md`; no third-party task implementation or model weights were copied.

### Counterexample: continuity does not guarantee a correct route

Student trip 00000007 is the observed exception: classifier accuracy 0.947563 fell to 0.882570 after HMM; trip Macro F1 changed from 0.958418 to 0.963147. Thus the pooled improvement is not an improvement on every trip. A connectivity prior can favor a coherent but incorrectly aligned route; identifying the specific cause here requires local reference/map review. We report the regression and did not adjust decoder parameters to this student-test case. See the two per-trip records and actual Folium layers.
