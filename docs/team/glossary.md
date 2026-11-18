# Glossary

- **Trip** — one vehicle journey: a `.track` (GPS points), `.nodes` (road junction coordinates), `.arcs` (road segments between nodes) and, for development data, `.route` (reference sequence of arcs).
- **Arc / node ID** — row number in that trip's `.arcs` / `.nodes` file. Only meaningful inside the same trip.
- **Partition** — train (80), student_test (10), evaluator_test (10, reserved).
- **Candidate** — a nearby road segment that a GPS point could belong to.
- **Classifier** — model that scores how likely each candidate is the true road for a point.
- **Emission probability** — in the HMM, how well a GPS point fits a candidate (from the classifier score).
- **Transition probability** — how plausible it is to drive from one candidate to the next (from road-network distance vs. straight-line distance and time).
- **Viterbi** — algorithm that picks the single most likely sequence of road segments through all points.
- **Route continuity** — how often consecutive predicted segments are actually connected on the road graph.
- **Candidate miss** — the reference road was not among a point's candidates, so no model could pick it.
- **Macro F1** — F1 score averaged over road-segment classes so that frequent segments don't dominate.
- **Bayesian optimisation (TPE / Optuna)** — tuning hyperparameters by learning from previous trials which settings look promising.
- **Contract** — agreed data formats/function signatures between the science code and the app; versioned and hashed.
- **Worktree** — a second checkout of the same Git repo on a different branch, so A and B never edit the same folder.
- **Development mode / evaluator mode** — API serves student_test trips (development) or the reserved trips (evaluator). It never silently swaps one for the other.
