# PathSnap: presentation guide

**Team PT-081 · UE24CS352A Machine Learning hackathon · PES University**

This guide explains the whole project in plain language, for presenting it. No prior machine learning knowledge is assumed. Every number here comes from the project's saved results, and section 9 shows where to find the proof for each one.

---

## 1. The problem in one minute

A car's GPS is noisy. The recorded dots drift onto the street next door, jump over buildings, or go missing for a while.

**Our job:** take a trip's noisy GPS dots and the road map around it, and work out **which road the car was really on at each moment**. This task is called *map matching*.

**What we built:**

- **A machine learning pipeline** that does the map matching.
- **A server (Laptop 1)** that runs the trained model.
- **A web page (Laptop 2)** where an evaluator picks a trip and sees the reconstructed route and its accuracy on a map.

---

## 2. The dataset, and what we did with it

### What one trip contains

| File | What it is |
|---|---|
| `.track` | The GPS dots: time, latitude, longitude |
| `.nodes` | Points on the road map |
| `.arcs` | Road pieces, each going **one way** from one node to another (a two-way street is two arcs) |
| `.route` | The **true** list of roads the car drove. Used only to train and to score, never as an input when predicting |

### How the trips were split

| Group | Trips | GPS points | Used for |
|---|---:|---:|---|
| Training | 80 | 208,417 | Teaching the models, and tuning them |
| Student test | 10 | 19,160 | Comparing the models fairly |
| Evaluator (reserved) | 10 | 19,674 | One final run only, at the very end |

**Why three groups?** A model must be judged on trips it never learned from, just as an exam uses questions you haven't seen. The evaluator trips were kept completely untouched until the final run.

### What we did to the data, step by step

1. **Checked every file.**
    - All coordinates were valid, and the timestamps always increased.
    - 96.5% of GPS readings are exactly 1 second apart.
    - Some gaps are very long, so the system had to handle gaps.
2. **Converted to metres.** Latitude and longitude are angles, not distances. For each trip we converted them into a flat map measured in metres, so that "50 m from the road" really means 50 metres.
3. **Found candidate roads.**
    - For every GPS dot we listed the roads near it: up to the **8 closest roads within 100 m**.
    - A fast spatial index (a KD-tree) makes this quick.
    - The correct road was in this list for **99.6%** of student-test points.
4. **Made per-point labels.** The `.route` file lists the roads in order, not one road per GPS dot. So we wrote an alignment step that matches each dot to its true road, keeping the order. These labels are used only for training and scoring.
5. **Computed features** (section 3).

---

## 3. The features: what the model looks at

For every pair of (GPS dot, candidate road), we compute these clues:

| Feature | What it captures | Why it helps |
|---|---|---|
| Distance (and log distance) | How far the dot is from the road | The right road is usually close |
| Extra distance over the nearest road | How much farther this road is than the closest one | Compares candidates with each other |
| Heading agreement | Is the car moving in the road's direction? | Tells apart the two directions of the same street |
| Position along the road | Where on the road segment the dot falls | Spots dots that sit past the end of a road |
| Road length (log) | Short or long segment | Short connectors behave differently |
| Speed | How fast the car is moving | Speed makes the heading more reliable |
| Time gap | Seconds since the previous dot | Long gaps make the position less certain |

**Proof that the features matter.** We trained the same model three times with more and more features:

| Features used | Student-test accuracy | Macro F1 |
|---|---:|---:|
| Distance only | 51.1% | 0.338 |
| Distance + heading | 82.9% | 0.666 |
| **All features** | **86.0%** | **0.771** |

"Just pick the nearest road" gives only about half the points right. Adding the car's direction and motion is what makes the model good.

---

## 4. The five models we tried

Each model learns the same thing: given the clues for one (GPS dot, candidate road) pair, **how likely is this to be the right road?** For each dot we then take the top-scoring candidate.

**Parameters vs hyperparameters.**

- *Parameters* are what a model learns by itself from the data.
- *Hyperparameters* are the settings **we** choose before training, like the number of trees. They are the knobs we turn.

| # | Model | How it works, simply | Settings we used |
|---|---|---|---|
| 1 | **Logistic Regression** | Draws one straight-line boundary between "right road" and "wrong road" | C = 1.0 (regularisation strength), solver lbfgs, up to 500 iterations |
| 2 | **K-Nearest Neighbours (KNN)** | Finds the 15 most similar training examples and lets them vote, closer ones counting more | 15 neighbours, distance-weighted, KD-tree search |
| 3 | **Random Forest** | Builds 64 decision trees, each on a random sample of the data, and averages their votes | 64 trees, max depth 16, at least 8 samples per leaf |
| 4 | **Extra Trees** | Like Random Forest, but picks the split points at random, which makes it faster | 64 trees, max depth 16, at least 8 samples per leaf |
| 5 | **HistGradientBoosting (HGB)** | Builds trees one after another, each fixing the mistakes of the previous ones | 100 trees, learning rate 0.1, 15 leaves per tree, at least 30 samples per leaf, L2 = 1.0 |

**Fair comparison.**

- All five models use the same features and the same data splits, with fixed random seeds.
- All five are trained with the same loss: *log loss*, which punishes confident wrong answers.
- Logistic Regression and KNN also get their features rescaled, because they need it.

---

## 5. How we trained and tested

### Cross-validation: a fair practice exam

Testing a model on the data it learned from is like marking a student on questions they memorised. Instead we used **5-fold cross-validation**:

1. Split the 80 training trips into 5 groups of 16 trips.
2. Train on 4 groups (64 trips) and test on the 5th group (16 trips).
3. Repeat 5 times, so every group is the test group once.
4. Average the 5 scores. This is the **CV score**.

**Why split by whole trips?** GPS dots one second apart are almost identical. If dots from the same trip were in both the training and the testing part, the model would effectively see the answers. So whole trips are kept together (this is called *GroupKFold*).

To keep training fast, each training trip contributes at most 400 points when fitting. Testing always uses **every** point.

### The metrics, in simple words

| Metric | Meaning | Better is |
|---|---|---|
| **Top-1 accuracy** | % of GPS points matched to the correct road | Higher |
| **Macro F1** | Accuracy averaged fairly over every road in the trip, so rarely used roads count as much as common ones | Higher (max 1.0) |
| **Log loss** | How well the scores separate right from wrong roads; confident mistakes are punished hard | Lower |
| **Route continuity** | % of consecutive predicted roads that are actually connected and drivable | Higher |

### Results of the five models

| Model | CV Macro F1 | Student-test accuracy | Student-test Macro F1 | Log loss | Total time |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.635 | 81.7% | 0.650 | 0.573 | 24 s |
| KNN | 0.666 | 83.8% | 0.706 | 0.866 | 303 s |
| Random Forest | 0.721 | 85.9% | 0.766 | 0.373 | 161 s |
| Extra Trees | 0.703 | 85.3% | 0.736 | 0.415 | 41 s |
| **HistGradientBoosting** | **0.725** | 85.8% | **0.767** | **0.361** | **26 s** |

![Cross-validation Macro F1 of the five models](results/figures/baselines-v1/training-cv-macro-f1.png){: style="max-width:58%"}

### Why HistGradientBoosting won

- **Highest CV Macro F1 (0.725)**, and CV was the agreed rule for choosing.
- **Lowest log loss (0.361):** its scores separate right and wrong roads best.
- **Fast:** 26 s in total, against 161 s for Random Forest and 303 s for KNN.
- **Generalises well:** about 85.8% on training points, 84.4% in CV and 85.8% on the student test. These are close together, so it is not just memorising. Compare KNN: 98.2% on training points but only 81.9% in CV, a sign of memorising.

We chose using the CV score, not the student-test score, so the student test stays a fair, independent check.

---

## 6. Tuning: Bayesian optimisation with Optuna

### What "tuning" means

HGB has knobs: how many trees, how big each tree is, how fast it learns, and so on. Different knob settings give different accuracy. **Tuning** means searching for the best settings.

### The three ways to search

| Method | How it works | Problem |
|---|---|---|
| Grid search | Try every combination on a fixed grid | Far too many combinations |
| Random search | Try random settings | Ignores what earlier tries showed |
| **Bayesian optimisation** | **Learns from each try and picks the next settings in the most promising area** | (what we used) |

**An analogy.** You are adjusting a recipe. Random search changes the ingredients blindly every time. Bayesian optimisation remembers which batches tasted good and moves the next attempt towards those.

### Optuna and TPE

- **Optuna** is a Python library for tuning.
- **TPE** (Tree-structured Parzen Estimator) is the Bayesian method inside Optuna that we used.

Each time, TPE splits the trials so far into "good" and "bad" ones. It then picks new settings that look like the good ones and unlike the bad ones.

### Our tuning run

- **What was scored:** each trial was a full 5-fold cross-validation on the training trips only (CV Macro F1). The test trips were never used for tuning.
- **12 trials:** the first 4 used random settings to explore, and the next 8 were chosen by TPE from the earlier results.
- **The knobs searched:**

| Hyperparameter | Meaning | Range searched | Best value found |
|---|---|---|---|
| `max_iter` | Number of trees | 60 – 180 | 179 |
| `max_leaf_nodes` | Size of each tree | 7 – 31 | 31 |
| `min_samples_leaf` | Minimum data in a leaf (prevents over-fitting) | 15 – 80 | 80 |
| `learning_rate` | How big a correction each new tree makes | 0.03 – 0.2 (log scale) | 0.123 |
| `l2_regularization` | Penalty that keeps the model simple | 0.01 – 10 (log scale) | 8.75 |

"Log scale" means small values were explored as carefully as large ones, for example 0.01, 0.1, 1 and 10.

### The result

| | CV Macro F1 | Student-test accuracy | Student-test Macro F1 | Log loss |
|---|---:|---:|---:|---:|
| HGB before tuning | 0.7252 | 85.8% | 0.767 | 0.361 |
| **HGB after tuning** | **0.7297** | **86.0%** | **0.771** | **0.352** |

Tuning improved every measure. The best settings came from trial 11, one of the trials chosen by TPE.

![Optuna trial history: each dot is one trial, the line is the best so far](results/figures/final-v1/bayesian-trials.png){: style="max-width:58%"}

---

## 7. HMM and Viterbi: turning dots into a real route

### Why the classifier alone is not enough

The classifier judges each GPS dot **on its own**. That can produce a route that hops between parallel streets every few seconds, which no car can actually drive.

### The idea: a Hidden Markov Model (HMM)

| HMM part | In our project |
|---|---|
| **Hidden state** (what we can't see directly) | Which road the car is really on |
| **Observation** (what we can see) | The GPS dot |
| **Emission score:** how well this road fits this dot | The tuned classifier's score |
| **Transition score:** how believable is the move from road A to road B | Compare the **driving distance** along the road network (shortest path) with how far the **GPS moved**. If they agree, the move is believable. Impossible moves, such as faster than 65 m/s, are not allowed |

### Viterbi: finding the best whole route

Viterbi is a step-by-step method (dynamic programming):

1. For each GPS dot and each candidate road, remember the best total score of any route ending there, and which road came before it.
2. Move forward dot by dot, adding the emission and transition scores.
3. At the end, trace back from the best final road to get the full route.

**Gaps.** If there is a gap of more than 30 seconds, no candidate road, or no drivable connection, the route starts a new piece. We never invent roads to fill a gap.

### What the HMM achieved (student-test trips)

| | Classifier only | **Classifier + HMM (final)** |
|---|---:|---:|
| Top-1 accuracy | 86.0% | **88.5%** |
| Macro F1 | 0.771 | **0.851** |
| Route continuity | 95.0% | **99.9%** |
| Separate route pieces (10 trips) | 974 | **28** |

![Classifier only vs classifier + HMM](results/figures/final-v1/classifier-hmm.png){: style="max-width:58%"}

---

## 8. The final result

### On the 10 reserved evaluator trips

The finished system was frozen, then run **once** on the 10 reserved trips. Scoring happened only on the server, after the prediction.

| Measure | Result |
|---|---:|
| **Top-1 accuracy** | **87.8%** (17,280 of 19,674 GPS points correct) |
| Macro F1 | 0.786 |
| Route continuity | **99.96%** |

- **Generalisation:** 87.8% on never-seen trips is in line with the 88.5% on the student test, so the model was not tuned to one set of trips.
- **Best trips:** four trips scored above 95% (best: 98.1%), and five were reconstructed as a single connected route.

### The full pipeline, start to finish

```
GPS dots + road map
   → clean, convert to metres
   → find up to 8 nearby candidate roads per dot
   → compute 9 clues (features) per (dot, road) pair
   → tuned HistGradientBoosting scores every candidate
   → HMM + Viterbi picks the best connected route
   → route shown on the map; accuracy computed on the server
```

### The system you demonstrate

- **Laptop 1** runs a **FastAPI** server with the trained model. Its endpoints:
    - `/health`: is the server ready?
    - `/trips`: the list of trips.
    - `/predict`: run one trip.
    - Every request is logged with an ID.
- **Laptop 2** runs a **React** web page:
    - The evaluator picks one of the 10 trips.
    - The page draws the GPS dots and the predicted route on a map, with the scores.
    - The same request ID shows on both laptops.
- **Folium maps** (interactive maps made in Python) show the GPS dots, the road network, the true route and our route as layers that can be switched on and off.

![The evaluator page showing a reconstructed route and its scores](report/figures/system/ui-evaluator-result.png){: style="max-width:62%"}

---

## 9. Proof that all of this was done

Everything is in the public repository, **github.com/VismayHS/PathSnap_ML_Hackathon_81**. Each results folder also records the code version, random seed, settings and timings that produced it.

| Claim | Where the proof is |
|---|---|
| Dataset checks and plots | `results/eda/`, `results/figures/data-quality-v1/` |
| Data processing and features code | `src/data_processing/`, `src/features/candidate.py` |
| Five models trained and compared | `src/models/experiments.py`; results in `results/experiments/baselines-local-v1/` (one file per model) |
| Feature comparison (51% → 83% → 86%) | `results/experiments/feature-ablation-v1/` |
| Bayesian tuning with Optuna | `src/hpo/search.py`; `results/hpo/hgb-tpe-v1/` holds the Optuna database and all 12 trial files |
| HMM and Viterbi | `src/hmm/viterbi.py`, `src/hmm/graph.py`; results in `results/hmm/hgb-hmm-v1/` |
| The final trained model | `artifacts/hgb-hmm-v1/` (checked by the server at startup) |
| Final evaluator result | `results/system/evaluator-run-01-aggregate.json` |
| Server and web page | `api/` and `ui/` |
| Interactive Folium maps | `maps/hgb-hmm-v1/` (one per student-test trip) |
| Automated tests | Run `.venv/bin/python -m pytest tests -q`: 49 tests pass |
| Full technical report | `report/PathSnap_Technical_Report.pdf` |

---

## 10. The "why" questions, with short answers

**Why use machine learning at all, instead of the nearest road?**
The nearest road alone is right only about 51% of the time. Learning from direction and motion raises this to 86%, and the HMM to 88.5%.

**Why convert to metres?**
Latitude and longitude are angles. A degree of longitude covers a different distance in different places, so distances must be measured in metres.

**Why compare five different models?**
Each family learns differently: straight-line, nearest examples, averaged trees, random trees and boosted trees. Comparing them shows which suits this problem, backed by evidence.

**Why split cross-validation by whole trip?**
Neighbouring GPS dots are almost the same. Splitting inside a trip would let the model see the answers and inflate the score.

**Why choose by CV score and not by test score?**
The test trips must stay an independent check. If we chose by them, we would be tuning to the test.

**Why HistGradientBoosting?**
It had the best CV Macro F1 and the lowest log loss, and it was one of the fastest models.

**Why Bayesian optimisation instead of trying random settings?**
Each trial takes a full 5-fold cross-validation, so trials are expensive. Bayesian optimisation learns from earlier trials and reaches good settings in fewer tries.

**Why the HMM?**
The classifier judges dots one at a time. The HMM considers the whole trip and only allows drivable moves. Accuracy went from 86.0% to 88.5%, continuity from 95% to 99.9%, and route pieces from 974 to 28.

**Why does the true route never go to the web page?**
To prevent cheating, or "leakage". Prediction reads only the GPS and the road map. A separate scorer on the server compares the result with the true route afterwards and sends back only the summary numbers.

**Why two laptops?**
The brief requires it: one laptop serves the model, the other is the evaluator's screen. This shows the system works over a real network.
