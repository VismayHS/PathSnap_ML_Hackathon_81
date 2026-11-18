# PathSnap: Map-Matching and Route Reconstruction

**Technical Report**

**Course:** UE24CS352A Machine Learning, PES University (RR Campus)  
**Team:** PT-081, Section F (AIML 2024)  
**GitHub repository:** <https://github.com/VismayHS/PathSnap_ML_Hackathon_81>

**Team members**

| # | Name | SRN |
|---|---|---|
| 1 | VISMAY H S | PES1UG24AM325 |
| 2 | VISMAYA.G | PES1UG24AM326 |
| 3 | VUDUTHA KUNDHAN | PES1UG24AM327 |
| 4 | Y B HALLI VISWANATHAREDDY BHAVANA | PES1UG24AM328 |

The repository contains all source code (data processing, features, the five models, Bayesian tuning, HMM/Viterbi, API and UI), the trained model, every experiment record and figure, and the interactive Folium maps. Every result in this report can be checked against it.

### Summary

PathSnap reconstructs the road a vehicle actually drove from its noisy GPS trace. For every GPS point it finds the nearby candidate roads and scores each one with a trained classifier. A Hidden Markov Model with Viterbi decoding then chooses a connected, drivable route for the whole trip. We compared five classifiers and selected HistGradientBoosting, which we tuned with Bayesian optimisation (Optuna TPE). On the ten reserved evaluator trips, the final system matched **87.8%** of GPS points to the correct road, with **99.96%** route continuity. The model runs behind a FastAPI service on one laptop, and an evaluator uses it from a React web interface on a second laptop.

### Contents

1. Dataset understanding and exploratory data analysis
2. Model experimentation and comparison
3. Bayesian hyperparameter optimisation
4. HMM and Viterbi route reconstruction
5. Geographical visualisation using Folium
6. API, UI and deployment
7. Academic integrity and AI-assistance disclosure
