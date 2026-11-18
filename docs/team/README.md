# Team guide — what is happening in PathSnap

This folder is for the human team. It explains, in plain language, how the project is being built, who/what is doing which part, and where to look. It is updated as work happens.

| File | What it is |
|---|---|
| [progress-log.md](progress-log.md) | Dated log of what was done, what is next, what is blocked. Read this first. |
| [glossary.md](glossary.md) | Terms used in code and messages (candidate, emission, Viterbi, partition, ...). |
| [science-notes.md](science-notes.md) | Running ML-side notes (written by A). |
| [../ml/team-understanding.md](../ml/team-understanding.md) | A's detailed scientific overview: data formats, validation findings, the label-alignment problem, planned models/metrics. |

## How the work is split

The build is done by two AI coding sessions working in parallel, coordinated through files. **This is AI assistance and must be disclosed as the event policy requires.** Every team member still needs to understand and be able to explain the code, experiments and results in the viva — use these notes, `contracts/interfaces.md` and `docs/ml/` to do that.

| Side | Owns |
|---|---|
| **A — science** | data loading/cleaning, EDA, candidate generation, features, the 5+ models, Bayesian tuning, HMM/Viterbi, metrics, plots, scientific report section |
| **B — application** | contracts between the parts, FastAPI backend, React UI, Folium maps, tests, deployment (two laptops), report assembly, merging the two sides |

Exact file ownership: [`contracts/ownership.md`](../../contracts/ownership.md).

## How code moves (Git)

```
main  ── accepted, tested milestones only (fast-forward from integration)
 ├─ work/llm-a        A's branch   (worktree: ../PathSnap_worktrees/llm-a)
 ├─ work/llm-b        B's branch   (worktree: ../PathSnap_worktrees/llm-b)
 └─ integration/mNN-attemptNN   B merges A + B here, runs all checks, then main fast-forwards
```

Milestones: **M0** contracts agreed → **M1** first end-to-end slice → **M2** five models + real UI/API → **M3** tuned model + HMM in the app → **M4** report + submission checks.

## The system in one picture

```
Laptop 2 (UI)                          Laptop 1 (API + model)
React app ──GET /trips──────────────►  FastAPI ── list allowed trip IDs
          ──POST /predict {trip_id}─►  load GPS + road network (never the reference route)
                                       → clean → candidate roads → features → trained model
                                       → HMM/Viterbi → predicted route
                                       → (separately) score against reference on the server
          ◄── route + aggregate metrics (no reference geometry, no per-point answers)
```

## Data rules everyone must follow

- 80 **train** trips: fitting, cross-validation, tuning. 10 **student_test** trips: comparing models. 10 **evaluator** trips: final demo only — never looked at or tuned on.
- The reference route (`.route`) never goes into prediction or the browser.
- No hardcoded predictions, no invented numbers or screenshots.
