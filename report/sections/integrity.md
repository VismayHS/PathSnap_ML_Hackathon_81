## Academic integrity and AI-assistance disclosure

**AI assistance was used substantially in this project, and we disclose it here as the event policy requires.**

**Tools and what they did.** The code, experiments, documentation and this report were produced with two AI coding-assistant sessions working in parallel, under our direction:

- **Agent A (science):** a second AI coding-assistant session that wrote and ran the data exploration, candidate generation, feature extraction, the five classifiers with grouped cross-validation, Bayesian hyperparameter optimisation, the HMM/Viterbi decoder, the scorer and the scientific sections of this report.
- **Agent B (application):** Claude Code (Anthropic) wrote the FastAPI service, the React evaluator interface, the Folium maps, the deployment guide, the report build and the system sections, and integrated both agents' work.
- The two sessions coordinated through files and reviewed each other's work before anything reached `main`. Claude in Chrome was used once to read the team allocation sheet from our email.

**What we did ourselves.** We chose the problem setup and repository, supplied the dataset and the reserved evaluator archive, directed the agents step by step, made the key decisions (for example, to train on one laptop rather than split across four), and checked the results as they were reported.

**Evidence and honesty.** Every number in this report comes from code and run records in the repository (run IDs, source commits, seeds and timings are stored with each result). Nothing was copied from other teams, and no other team's code, weights or results were used. The reserved evaluator trips were not used for exploration, training, tuning or model selection; they were run once on the frozen system, and only aggregate metrics are published. Pointwise scores use our provisional alignment policy until the organisers confirm the official definition.

**Our responsibility.** We take responsibility for this submission. Each team member is expected to understand and explain the method, the code and the results in the viva, using this report and the method notes in `docs/ml/`.
