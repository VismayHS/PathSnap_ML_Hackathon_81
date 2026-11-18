## 1. Dataset Understanding and Exploratory Data Analysis

### 1.1 What the data looks like

Each trip comes as a folder with four plain-text files:

- **`.track`**: the GPS readings, one per line, each with longitude, latitude and a timestamp.
- **`.nodes`**: points on the road map (junctions and bends), given as longitude and latitude.
- **`.arcs`**: road segments. Each one runs in a single direction from one node to another, so a two-way street appears as two arcs.
- **`.route`**: the true list of arcs the vehicle drove, in order. We used it only to create training labels and to score predictions. It is never an input to prediction.

Node and arc IDs are simply line numbers inside each trip, so arc 12 in one trip has nothing to do with arc 12 in another.

| Partition | Trips | GPS points | Nodes | Directed arcs | Used for |
|---|---:|---:|---:|---:|---|
| Training | 80 | 208,417 | 1,933,485 | 3,876,904 | Training, cross-validation and tuning |
| Student test | 10 | 19,160 | 90,689 | 185,041 | Comparing models |
| Evaluator (reserved) | 10 | 19,674 | — | — | One final run only |

All exploration in this section uses the training and student-test trips only. The reserved evaluator trips were not opened during development.

### 1.2 How we preprocessed the data

1. **Validation.** We parsed every file strictly and checked coordinates, numeric values and timestamps. Malformed rows raise an error instead of being skipped silently, and every original row index is kept, so predictions can always be traced back to the input.
2. **Missing values.** No GPS or node coordinates were missing or invalid in the 90 trips, and timestamps always increased. Motion features are undefined for the first point of a trip and when the vehicle is not moving. They are set to zero and marked with a "heading valid" flag, so the model knows the direction is unreliable. As a safety net, every model also includes a median imputer, fitted only on the training part of each cross-validation fold.
3. **Projection to metres.** Latitude and longitude are angles, so straight-line distances between them are meaningless. Each trip is projected onto a flat local map in metres, centred on the trip's own GPS points. Every distance in the system is measured in metres.
4. **Candidate roads.** For every GPS point we look up the roads within 100 m using a KD-tree spatial index over road midpoints, then measure the exact point-to-segment distance. We keep the 8 closest. On average a point has 6.5 candidates (training) to 6.8 (student test), and the correct road is among them for 99.6% of student-test points.
5. **Per-point labels.** The `.route` file lists roads, not one road per GPS point. An order-preserving alignment (dynamic programming) assigns each GPS point the reference road that best fits it in distance and direction. A point is used for training and scoring only if its aligned road is within 100 m. This gave 187,867 usable training points and 19,143 of the 19,160 student-test points.

### 1.3 What we observed

- **Sampling is regular, with occasional long gaps.** 96.5% of training steps and 98.6% of student-test steps are exactly one second, but the longest gaps are 153,064 s (training) and 210 s (student test). The decoder therefore had to handle gaps explicitly.
- **The road networks are large and fragmented.** A training trip's network splits into between 1 and 421 separate weakly connected pieces. A route cannot be assumed to be one connected line.
- **Trips cover very different parts of the world.** Longitudes range from −100° to 137°, which is why each trip gets its own projection.
- **Two-way streets make direction critical.** Both directions of a street sit in exactly the same place. Distance alone cannot tell them apart; the direction of travel can.
- **Some arcs have zero length** (100 in training, 6 in student test). They stay in the road graph but can never be a GPS candidate.

![Trip sizes and timestamp gaps](results/figures/data-quality-v1/trip-sizes-and-gaps.png){: style="max-width:80%"}
<p class="caption">Figure 1. Size of every trip and its largest time gap (log scale), training and student-test partitions.</p>

![Point coverage after alignment](results/figures/data-quality-v1/target-coverage.png){: style="max-width:80%"}
<p class="caption">Figure 2. For each partition: how many GPS points received a usable label, and how many of those have the correct road among their candidates.</p>

GPS trajectories and road networks are shown on the interactive Folium maps in Section 5.

### 1.4 Features and why we chose them

For every pair of a GPS point and a candidate road, we compute nine features:

| Feature | What it measures | Why it helps |
|---|---|---|
| Distance, log distance | How far the point is from the road | The true road is usually close |
| Distance beyond the nearest candidate | How much farther this road is than the closest one | Compares candidates against each other |
| Heading cosine, heading valid | Whether the vehicle moves in the road's direction | Separates the two directions of a street |
| Projection fraction | Where along the segment the point falls | Flags points that sit beyond the end of a road |
| Log road length | Short or long segment | Short connectors behave differently |
| Speed | Vehicle speed from consecutive points | Makes the heading more reliable |
| Time gap | Seconds since the previous point | Longer gaps mean more uncertainty |

Arc IDs are never used as features: they mean nothing across trips, and using them would leak information.

**A controlled check of the features.** We kept the final model and its settings fixed, and added the feature groups one at a time:

| Features used | CV Macro F1 | Student-test accuracy | Student-test Macro F1 |
|---|---:|---:|---:|
| Distance only | 0.345 | 51.1% | 0.338 |
| Distance + heading | 0.652 | 82.9% | 0.666 |
| All features | 0.730 | 86.0% | 0.771 |

Distance alone gets only about half the points right, because it cannot tell the directions of a street apart. Adding the heading is the biggest single improvement, and the motion and geometry features add a further 3 points.

## 2. Model Experimentation and Comparison

### 2.1 How the models were trained and compared

Each model answers one question: *given the features of a (GPS point, candidate road) pair, how likely is this the correct road?* For every point we then pick the candidate with the highest score.

- **Cross-validation.** 5-fold *grouped* cross-validation over the 80 training trips: each fold trains on 64 trips and validates on 16 unseen trips. Whole trips stay together, because neighbouring GPS points are nearly identical and splitting a trip would leak answers into validation.
- **Same conditions for every model.** The same features, the same five folds and the same random seed (81). To keep training time practical, each training trip contributes at most 400 points when fitting; validation and testing always use every point.
- **Testing.** Each model is then refit on all 80 training trips and run on the 10 student-test trips.
- **Selection rule.** The model is chosen on cross-validation Macro F1, decided in advance. The student-test results are reported but not used to choose.

**Metrics.**

- *Top-1 accuracy:* the share of GPS points assigned to the correct road.
- *Macro F1:* precision and recall averaged evenly over all roads in a trip, then over trips, so rarely used roads count as much as busy ones.
- *Log loss:* how well the scores separate correct from incorrect candidates, computed on points whose true road is among the candidates.
- *Route continuity:* the share of consecutive points whose predicted roads are actually connected on the road network.

The organisers had not specified the exact per-point scoring rule, so all scores use the alignment described in 1.2 (documented in `docs/ml/scoring-policy.md`).

### 2.2 Overall model comparison

| Model | Algorithm family | Key configuration | CV Macro F1 | Top-1 accuracy (test) | Macro F1 (test) | Log loss | Route continuity | Inference time |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | Linear | C = 1.0, lbfgs | 0.635 | 81.7% | 0.650 | 0.573 | 93.6% | 0.10 s |
| K-Nearest Neighbours | Instance-based | k = 15, distance-weighted | 0.666 | 83.8% | 0.706 | 0.866 | 94.1% | 20.9 s |
| Random Forest | Bagged trees | 64 trees, depth 16 | 0.721 | 85.9% | 0.766 | 0.373 | 94.9% | 0.53 s |
| Extra Trees | Randomised trees | 64 trees, depth 16 | 0.703 | 85.3% | 0.736 | 0.415 | 95.0% | 0.59 s |
| **HistGradient&shy;Boosting** | Boosted trees | 100 iterations, lr 0.1 | **0.725** | 85.8% | **0.767** | **0.361** | **95.1%** | 0.39 s |

"Test" means the 10 student-test trips. The CV standard deviation across the five folds is between 0.016 and 0.020 for every model. Inference time is the classifier's scoring time for all 10 test trips (candidate search and HMM decoding not included). Continuity is for the classifier alone, before HMM decoding (Section 4). The whole experiment (cross-validation, refit and testing) took 24 s for Logistic Regression, 26 s for HistGradientBoosting, 41 s for Extra Trees, 161 s for Random Forest and 303 s for KNN.

![Cross-validation Macro F1](results/figures/baselines-v1/training-cv-macro-f1.png){: style="max-width:75%"}
<p class="caption">Figure 3. Cross-validation Macro F1 of the five models (mean and standard deviation over five folds).</p>

![Student-test accuracy and Macro F1](results/figures/baselines-v1/student-test-accuracy-f1.png){: style="max-width:75%"}
<p class="caption">Figure 4. Student-test Top-1 accuracy and Macro F1 of the five models.</p>

![Log loss](results/figures/baselines-v1/student-test-conditional-log-loss.png){: style="max-width:75%"}
<p class="caption">Figure 5. Student-test log loss (lower is better).</p>

**Why HistGradientBoosting was selected.** It had the highest cross-validation Macro F1, which was our selection rule. It also had the lowest log loss and the best student-test Macro F1, and it was one of the two fastest models to train. Random Forest came very close in cross-validation but took about six times longer to train.

Training, cross-validation and student-test accuracy, used below to judge over- and under-fitting:

| Model | Training (fit points) | Cross-validation | Student test |
|---|---:|---:|---:|
| Logistic Regression | 81.3% | 81.4% | 81.7% |
| KNN | 98.2% | 81.9% | 83.8% |
| Random Forest | 89.5% | 84.2% | 85.9% |
| Extra Trees | 85.3% | 83.8% | 85.3% |
| HistGradientBoosting | 85.8% | 84.4% | 85.8% |

### 2.3 Logistic Regression

- **Why suitable:** a fast, simple baseline that tests whether the features combine roughly linearly into a good score.
- **Strengths and limitations:** quick to train and easy to interpret. However, a single linear boundary cannot capture interactions such as "close to the road *and* moving in its direction".
- **Hyperparameters:** C = 1.0 (L2 regularisation strength), solver lbfgs, up to 500 iterations. Features are standardised first.
- **Objective:** regularised binary log loss.
- **Student-test performance:** Top-1 accuracy 81.7%, Macro F1 0.650, log loss 0.573.
- **Over- or under-fitting:** training, CV and test accuracy are all about 81–82%. This is **under-fitting**: train and test scores are equal but low, because a linear boundary is too simple for this problem.

### 2.4 K-Nearest Neighbours

- **Why suitable:** it judges a candidate by how similar training examples were labelled. That can capture non-linear patterns without assuming any shape.
- **Strengths and limitations:** flexible and needs no training phase. However, it keeps every training example and searches them at prediction time, which made it the slowest model (303 s). It also needs carefully scaled features.
- **Hyperparameters:** 15 neighbours, weighted by distance, KD-tree search, leaf size 40. Features are standardised.
- **Objective:** none; KNN does not optimise a loss and simply stores the data.
- **Student-test performance:** Top-1 accuracy 83.8%, Macro F1 0.706, log loss 0.866 (the worst of the five).
- **Over- or under-fitting:** 98.2% training accuracy against 81.9% in CV. This is clear **over-fitting**: distance weighting lets each training point effectively vote for itself. The high log loss shows its scores are over-confident.

### 2.5 Random Forest

- **Why suitable:** many decision trees, each trained on a random sample, can model interactions between distance, heading and motion without any feature scaling.
- **Strengths and limitations:** accurate and robust. However, it is slower to train (161 s) and produces a larger model.
- **Hyperparameters:** 64 trees, maximum depth 16, at least 8 samples per leaf, Gini splits, seed 81.
- **Objective:** each tree split minimises Gini impurity; the forest averages the trees' votes.
- **Student-test performance:** Top-1 accuracy 85.9%, Macro F1 0.766, log loss 0.373.
- **Over- or under-fitting:** 89.5% training against 84.2% CV, so **mild over-fitting**. The depth and leaf-size limits keep it under control, and test accuracy (85.9%) matches CV.

### 2.6 Extra Trees

- **Why suitable:** like Random Forest, but split thresholds are chosen at random. This is a distinct ensemble that is faster and less prone to over-fitting.
- **Strengths and limitations:** fast to train (41 s) and low in variance. However, random thresholds can miss the fine distance and heading boundaries that matter here, which leaves it slightly below Random Forest.
- **Hyperparameters:** 64 trees, maximum depth 16, at least 8 samples per leaf, seed 81.
- **Objective:** Gini impurity on randomised splits.
- **Student-test performance:** Top-1 accuracy 85.3%, Macro F1 0.736, log loss 0.415.
- **Over- or under-fitting:** 85.3% training, 83.8% CV and 85.3% test. These are close together, so the fit is **good**, slightly less flexible than Random Forest.

### 2.7 HistGradientBoosting (selected)

- **Why suitable:** builds trees one after another, each correcting the errors of the previous ones. It learns feature interactions well, and binning the features into histograms makes it fast.
- **Strengths and limitations:** the best accuracy-to-cost balance of the five, and a small model file. However, it has several hyperparameters that need tuning (Section 3).
- **Hyperparameters (before tuning):** 100 boosting iterations, learning rate 0.1, 15 leaves per tree, at least 30 samples per leaf, L2 regularisation 1.0, no early stopping, seed 81.
- **Objective:** binary log loss.
- **Student-test performance:** Top-1 accuracy 85.8%, Macro F1 0.767, log loss 0.361.
- **Over- or under-fitting:** 85.8% training, 84.4% CV and 85.8% test. The values are very close, so there is **no meaningful over-fitting** and the model generalises well.

## 3. Bayesian Hyperparameter Optimisation

We tuned the selected HistGradientBoosting model with **Optuna**, a Python optimisation library, using its **TPE** (Tree-structured Parzen Estimator) method.

**Why Bayesian optimisation.** Each trial is a full five-fold cross-validation, so trials are expensive. Random or grid search ignore earlier results. TPE instead splits the completed trials into better and worse groups, and proposes new settings that resemble the better ones. That reaches good settings in fewer trials.

1. **Hyperparameters searched and their ranges:**

| Hyperparameter | What it controls | Range | Best value |
|---|---|---|---|
| `max_iter` | Number of boosting iterations (trees) | 60 – 180 | 179 |
| `max_leaf_nodes` | Size of each tree | 7 – 31 | 31 |
| `min_samples_leaf` | Minimum points in a leaf (guards against over-fitting) | 15 – 80 | 80 |
| `learning_rate` | Size of each tree's correction | 0.03 – 0.2, log scale | 0.123 |
| `l2_regularization` | Penalty that keeps leaf values small | 0.01 – 10, log scale | 8.75 |

2. **Objective:** mean cross-validation Macro F1 over the same five grouped folds used in Section 2. No student-test or evaluator data was used.
3. **Number of trials:** 12. The first 4 used random settings to explore; the next 8 were proposed by TPE from the earlier results.
4. **Best result:** trial 11 had a CV Macro F1 of 0.7297. The full search record (Optuna database and one file per trial) is in `results/hpo/hgb-tpe-v1/`.

![Optuna trial history](results/figures/final-v1/bayesian-trials.png){: style="max-width:75%"}
<p class="caption">Figure 6. Every trial's cross-validation Macro F1 and the best value so far. TPE-guided trials start after the first four.</p>

**Did the tuned model beat the untuned one?** Yes, on every measure, under the same folds, features and test trips:

| HistGradientBoosting | CV Macro F1 | Student-test Top-1 accuracy | Student-test Macro F1 | Log loss | Scoring time, all 10 trips (median of 3 runs) |
|---|---:|---:|---:|---:|---:|
| Untuned | 0.7252 | 85.8% | 0.767 | 0.361 | 503 ms |
| **Tuned** | **0.7297** | **86.0%** | **0.771** | **0.352** | 864 ms |

![Tuned vs untuned](results/figures/final-v1/tuned-untuned.png){: style="max-width:75%"}
<p class="caption">Figure 7. Tuned and untuned HistGradientBoosting under identical conditions.</p>

The gain is modest, which is expected: the default settings were already reasonable. The tuned model uses more and larger trees, which explains its higher inference time, but scoring all 10 student-test trips still takes under a second.

## 4. HMM and Viterbi Route Reconstruction

The classifier scores each GPS point on its own. On its own it can produce routes that jump between parallel streets from one second to the next. We therefore decode the whole trip with a Hidden Markov Model, which only allows drivable movements.

1. **Hidden states.** The candidate roads of each GPS point, each paired with the point's position along that road.
2. **Emission probabilities.** The tuned classifier's scores for a point's candidates, normalised to sum to one and used in log form. A road that fits the GPS point well gets a high emission score.
3. **Transition probabilities.** For each move from a previous candidate road to a current one, we compute the shortest *driving* distance on the directed road network (Dijkstra's algorithm, respecting one-way arcs). We compare it with the straight-line distance the GPS moved:

    `transition score = −|driving distance − GPS distance| / 25 m`

    When the two distances agree, the move is believable. Moves that would need more than 65 m/s, plus 50 m of slack for GPS noise, are impossible.
4. **Missing candidates and large gaps.** A point with no road within 100 m, or a time gap over 30 seconds, ends the current route piece; decoding restarts after it. We never invent a road to bridge a gap.
5. **Disconnected road segments.** If no current candidate can be reached from any previous candidate, the route is split at that point instead of drawing a straight line across buildings. Each piece is built only from real road segments.
6. **Viterbi decoding.** For every point and candidate, Viterbi keeps the best total score of any path ending there, plus a pointer to the previous road. At the end of each piece it follows the pointers back to recover the best sequence. The work is done in log space for numerical stability.

The decoder settings (25 m, 65 m/s, 30 s) were fixed before testing and never adjusted to the test results. The code is in `src/hmm/viterbi.py` and `src/hmm/graph.py`.

**Did HMM decoding improve the route?** Yes, clearly. Student-test trips, same tuned classifier:

| Metric | Classifier only | Classifier + HMM/Viterbi |
|---|---:|---:|
| Top-1 accuracy | 86.0% | **88.5%** |
| Macro F1 | 0.771 | **0.851** |
| Precision (macro) | 0.795 | **0.865** |
| Recall (macro) | 0.769 | **0.857** |
| Route continuity | 95.0% | **99.9%** |
| Separate route pieces (10 trips) | 974 | **28** |
| Inference time (10 trips) | 5.1 s | 10.7 s |

![Classifier only vs HMM](results/figures/final-v1/classifier-hmm.png){: style="max-width:75%"}
<p class="caption">Figure 8. Classifier-only predictions against classifier + HMM/Viterbi on the student-test trips.</p>

The HMM turns about 97 broken fragments per trip into about 3 connected pieces, and it raises accuracy and Macro F1 at the same time. The remaining breaks are real GPS gaps or points with no road nearby.

**Where HMM decoding did not help.** On student-test trip 00000007, accuracy fell from 94.8% to 88.3%, even though Macro F1 rose slightly (0.958 to 0.963). A connected route can still be connected along the wrong street, for example when two parallel roads are linked further along. We kept the decoder settings unchanged rather than fit them to this one trip. Across all ten trips the HMM's gain is clear.

The final model, the tuned classifier together with the decoder settings, is saved with checksums in `artifacts/hgb-hmm-v1/`.
