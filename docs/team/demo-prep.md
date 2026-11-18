# Demo and viva prep: start here

This is a study guide for the four of us. It assumes you know nothing about the project yet. Read it top to bottom once (about 30 minutes), then each person studies their own part in depth.

The assessment policy says marks cover "correctness, completeness, technical understanding, experimental rigour, reproducibility and the team's ability to explain its work", and **every** member may be asked about any part. So everyone learns section 2 (the whole story) and the numbers in section 3, and each person goes deep on one area from section 5.

---

## 1. What the evaluators will look at

| Thing | Where it is | Status |
|---|---|---|
| Public GitHub repo with all code | https://github.com/VismayHS/PathSnap_ML_Hackathon_81 | Done |
| Technical report PDF | [`report/PathSnap_Technical_Report.pdf`](../../report/PathSnap_Technical_Report.pdf) | Done, except one screenshot |
| Live two-laptop demo | [`docs/deployment/two-laptops.md`](../deployment/two-laptops.md) | **We must rehearse it** |
| Viva: questions to each of us | This file, then [`docs/ml/viva-notes.md`](../ml/viva-notes.md) | **We must prepare** |

**Still to do before evaluation:**
1. Rehearse the two-laptop demo once (section 4).
2. During that rehearsal, take a screenshot of Laptop 1's terminal showing the request logs. It is the only missing item in the report (the PENDING line in `report/sections/system.md`). Add it, rebuild the PDF, push.
3. Everyone reads sections 2 and 3; each person studies their area in section 5.
4. Read the AI-assistance statement in the report (`report/sections/integrity.md`). It says honestly that two AI coding sessions wrote the code under our direction. If asked, say so plainly. The policy forbids *hiding* AI use and *not understanding* the work. Using AI is not what it forbids.

---

## 2. The whole project in two minutes (everyone must be able to say this)

**The problem.** GPS on a car is noisy. The dots drift onto parallel streets, jump across buildings, and sometimes disappear for a while. Given a trip's noisy GPS dots and the road map around it, we work out **which road the car was actually on at each moment**. This is called *map matching*.

**The data.** Each trip is a folder with:
- the GPS track (time, latitude, longitude),
- the road network as *nodes* (points) and *arcs* (directed road pieces from one node to another),
- the reference `.route`: the true sequence of roads driven. We use it only for training and for scoring, never as an input to prediction.

There are 80 training trips, 10 student-test trips, and 10 reserved evaluator trips. Road IDs are local to each trip: "arc 12" in one trip has nothing to do with "arc 12" in another.

**Our pipeline, in five steps:**
1. **Clean and project.** Read the files and convert latitude/longitude into metres using a local map projection, because degrees are not metres.
2. **Candidates.** For each GPS dot, find nearby roads: up to the 8 closest arcs within 100 m. We use a fast spatial index (a KD-tree).
3. **Features.** For each (dot, candidate road) pair, compute:
   - distance from the dot to the road,
   - whether the car's heading matches the road's direction,
   - the road's length,
   - where along the road the dot falls,
   - speed,
   - time since the previous dot,
   - how much farther this road is than the nearest one.
4. **Classifier.** A trained model scores each candidate: "how likely is it that this is the right road?" We compared 5 models and picked **HistGradientBoosting**, then tuned it with **Bayesian optimisation** (Optuna).
5. **HMM + Viterbi.** Choosing the best road for each dot on its own gives a jumpy route. So we treat the trip as a Hidden Markov Model:
   - the hidden state is "which road the car is on",
   - the emission score is the classifier's score,
   - the transition score asks "can you actually drive from road A to road B in this time, and does the driving distance match how far the GPS moved?"

   Viterbi then finds the single best sequence of roads for the whole trip. This gives a connected, drivable route.

**The system.** Laptop 1 runs the model behind a **FastAPI** web server. Laptop 2 runs a **React** web page. The evaluator picks a trip there, the page asks Laptop 1 to predict it, and the page draws the route on a map with the accuracy. Scoring happens only on Laptop 1, and the true route is never sent to the browser.

---

## 3. Numbers to know by heart

**Final result on the 10 reserved evaluator trips** (run once, on the frozen system):
- **Top-1 accuracy 87.8%**: the share of GPS points matched to the correct road.
- **Macro F1 0.786**: the average over trips.
- **Route continuity 99.96%**: almost every consecutive pair of predicted roads is actually drivable.

**Five-model comparison** (training cross-validation Macro F1 is what we chose by):

| Model | CV Macro F1 | Student-test accuracy |
|---|---:|---:|
| Logistic Regression | 0.635 | 81.7% |
| KNN (distance-weighted) | 0.666 | 83.8% |
| Random Forest | 0.721 | 85.9% |
| Extra Trees | 0.703 | 85.3% |
| **HistGradientBoosting (chosen)** | **0.725** | 85.8% |

**Why HGB:** it had the best cross-validation score and was fast (about 26 s in total). Random Forest was very close, and it was slightly better on the student test, but we chose on CV, not on the test set. That is the correct practice.

**Bayesian tuning:** 12 Optuna TPE trials (4 random, then 8 guided by earlier trials). CV Macro F1 rose from 0.725 to **0.730**: small but real.

**The HMM's effect** (student test, same tuned classifier):

| | Classifier only | + HMM/Viterbi |
|---|---:|---:|
| Top-1 accuracy | 86.0% | **88.5%** |
| Macro F1 | 0.771 | **0.851** |
| Route continuity | 95.0% | **99.9%** |
| Route pieces (10 trips) | 974 | **28** |

**An honest weak spot:** on student trip `00000007`, the HMM made accuracy *worse* (94.8% to 88.3%). A "connected" route can still be the wrong road. We report this rather than hide it, which is a good thing to mention.

**Feature ablation:**
- distance only gives Macro F1 0.338,
- adding heading gives 0.666,
- all features give 0.771.

Heading matters a lot because a two-way road is two arcs in the same place.

---

## 4. The demo, step by step

The full guide is [`docs/deployment/two-laptops.md`](../deployment/two-laptops.md) (Linux/macOS and Windows commands). In short:

**Before you start:**
- Both laptops are on the **same network**. Campus Wi-Fi often blocks laptop-to-laptop traffic, so use a **phone hotspot**.
- Laptop 1 has the repo, the Python environment and the dataset folder.
- Laptop 2 has the repo and Node.

**Laptop 1 (model + API):**
```bash
export PATHSNAP_MODE=development            # or evaluator + PATHSNAP_EVALUATOR_ROOT for the reserved trips
export PATHSNAP_DATA_ROOT=/path/to/Student_folder
export PATHSNAP_BUNDLE_ROOT="$PWD/artifacts/hgb-hmm-v1"
export PATHSNAP_CORS_ORIGINS="http://<LAPTOP2-IP>:4173,http://localhost:4173,http://127.0.0.1:4173"
.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Find the laptop's IP with `ip addr` (Linux), `ipconfig` (Windows) or `ipconfig getifaddr en0` (macOS). Allow port 8000 through the firewall.

**Laptop 2 (UI):**
```bash
cd ui && npm ci
echo "VITE_PATHSNAP_API_URL=http://<LAPTOP1-IP>:8000" > .env.local
npm run build && npm run preview
```
Open `http://localhost:4173` in the browser.

**What to show, in about 3 minutes:**
1. The UI says **Connected, ready** and lists 10 trips. Point out the mode badge.
2. Pick a trip and click to reconstruct. The map shows the raw GPS dots and the predicted route, with accuracy, Macro F1 and continuity.
3. Turn to Laptop 1's terminal. The same **request ID** shown in the UI appears in the log lines (`predict_start`, `predict_done`, `scoring_done`). This proves the prediction ran on Laptop 1. **Take the screenshot for the report here.**
4. Open a Folium map from `maps/hgb-hmm-v1/` (for example `trip_00000091_student_test.html`) in a browser. It shows the GPS, the road network, the true route and our prediction as separate layers with a legend.
5. If asked about leakage: the browser never receives the true route, and the scorer runs only on the server, after prediction.

**If something breaks:** the "Can't reach the PathSnap server" message almost always means one of these:
- wrong IP,
- the firewall is blocking port 8000,
- the browser address is not in `PATHSNAP_CORS_ORIGINS`.

See the troubleshooting table in the deployment guide.

---

## 5. Split the viva topics between the four of us

The policy lists 11 areas the evaluators may ask about. Here is a suggested split; agree on it among yourselves. Each person should also be able to give the two-minute story in section 2.

| Person | Areas | Read |
|---|---|---|
| 1 | Dataset structure, preprocessing, feature engineering | Report §2 (science.md, first part), [`docs/ml/team-understanding.md`](../ml/team-understanding.md) |
| 2 | Five-model comparison, model selection, Bayesian tuning | Report §3–4, [`docs/ml/model-selection.md`](../ml/model-selection.md) |
| 3 | HMM, Viterbi, the results and their limits | Report §5, [`docs/ml/hmm-method.md`](../ml/hmm-method.md) |
| 4 | API, UI, Folium, two-laptop deployment | Report system section, [`api/README.md`](../../api/README.md), [`docs/deployment/two-laptops.md`](../deployment/two-laptops.md) |

Terms you don't know are in [`glossary.md`](glossary.md).

---

## 6. Likely questions, with short answers

**Data and preprocessing**
- *What is in a trip?*
  - A GPS track, a road network (nodes plus directed arcs) and a reference route.
  - The reference is a list of roads driven, not one label per GPS point. So we built an alignment step that assigns each GPS point its true road, for training and scoring only.
- *How did you clean the data?*
  - We validated every file; all coordinates were valid and timestamps always increased.
  - We projected to metres per trip and kept every original ID.
  - Bad rows in future inputs are flagged, not deleted.
  - Missing feature values are filled with medians learned only from training folds.
- *What patterns did you see?*
  - 96.5% of steps are exactly 1 second apart, but some gaps are huge (up to 42 hours in training). So we need gap handling: the HMM restarts after gaps over 30 s.
  - Some roads are visited twice, and some arcs have zero length.

**Features**
- *Why these features?*
  - Distance says how close the dot is to the road.
  - Heading separates the two directions of a two-way road.
  - Speed and time gap describe motion.
  - Projection fraction and length describe where on the road the dot falls.
  - The ablation proves heading and the motion features help (Macro F1 0.338 → 0.666 → 0.771).
- *Why not use the arc ID as a feature?* IDs mean nothing across trips, and using them would leak.

**Models**
- *Why five models?* They are genuinely different families:
  - linear (Logistic Regression),
  - neighbour-based (KNN),
  - bagged trees (Random Forest),
  - randomised trees (Extra Trees),
  - boosted trees (HGB).
- *What does the classifier predict?* For each (GPS dot, candidate road) pair: is this the right road, yes or no? We then pick the top-scored candidate per dot.
- *Loss function?* Binary log loss for all five.
- *How did you avoid leakage in cross-validation?*
  - GroupKFold by **whole trip**, 5 folds.
  - Neighbouring GPS points are almost identical, so splitting points randomly would cheat.
- *Overfitting?*
  - For HGB: fit accuracy 85.8%, CV 84.4%, student test 85.8%, so no strong overfitting.
  - The report gives this per model.

**Bayesian optimisation**
- *What is Bayesian about it?*
  - Optuna's TPE builds a model of which settings scored well and samples promising new ones.
  - Random search ignores past results; TPE uses them.
- *What did you search over?*
  - Iterations 60–180, leaves 7–31, minimum samples per leaf 15–80.
  - Learning rate 0.03–0.2 and L2 0.01–10, both on a log scale.
- *Objective and trials?* Mean held-out-trip Macro F1 over the same 5 folds; 12 trials.
- *Best trial?*
  - Trial 11: learning rate ≈ 0.123, 179 iterations, 31 leaves, minimum leaf 80, L2 ≈ 8.75.
  - Did it improve? Slightly: 0.725 to 0.730.

**HMM and Viterbi**
- *Hidden states?* The candidate roads (directed arcs) for each GPS dot.
- *Emission?* The classifier's normalised score for that candidate.
- *Transition?*
  - The penalty is the difference between the shortest driving distance from road A to road B (Dijkstra on the directed graph) and the straight GPS displacement.
  - Infeasible moves (faster than 65 m/s) are not allowed.
- *Gaps or no candidates?*
  - The route is split into separate pieces when there are no candidates, a gap over 30 s, or no drivable connection.
  - We never invent a road to bridge a gap.
- *What does Viterbi do?*
  - Dynamic programming: for each dot and each candidate, keep the best total score of any path ending there plus a back-pointer.
  - At the end, trace back the best path.
- *Did it help?*
  - Yes overall: accuracy 86.0% to 88.5%, continuity 95.0% to 99.9%, route pieces 974 to 28.
  - But not on every trip: trip 00000007 got worse.

**API and UI**
- *Endpoints?*
  - `GET /health` (ready?), `GET /trips` (the 10 allowed trips) and `POST /predict` with a trip ID.
  - Predict returns the route, a status per GPS point, timings and aggregate metrics.
- *How do you keep evaluator answers safe?*
  - Prediction code never reads the `.route` file.
  - A separate scorer reads it after prediction and returns only summary numbers.
  - The browser never gets the true route for evaluator trips.
- *What is CORS?* A browser security rule. The API must list the UI's address as allowed, which is why we set `PATHSNAP_CORS_ORIGINS`.
- *Folium?*
  - A Python library that makes interactive Leaflet maps.
  - Ours show GPS dots, road network, true route and predicted route as toggleable layers.
  - The code is in `src/visualisation/folium/`.

**Integrity**
- *Did you use AI?*
  - Yes, disclosed in the report.
  - Two AI coding sessions wrote the code and report under our direction.
  - All numbers come from real runs recorded in the repo.
- *Did you touch evaluator data?* Only one final run on the frozen system, with no exploration, training or tuning on it.

---

## 7. Quick hands-on practice (do this once, about 20 minutes)

Run the system yourselves before the evaluation, so nothing on screen surprises you:
1. Start the API and UI on one laptop (use `127.0.0.1` for both addresses) and reconstruct two trips.
2. Open one Folium map from `maps/hgb-hmm-v1/` and toggle its layers.
3. Open the PDF and find the five-model table, the tuning plot and the HMM comparison table.
4. Run the tests once: `.venv/bin/python -m pytest tests -q` (all should pass).
