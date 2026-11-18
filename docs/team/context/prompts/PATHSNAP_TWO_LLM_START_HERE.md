# Run PathSnap with two coordinated LLMs

This is a prompt/workflow split, not a claim that implementation or experiments have run. Use two coding sessions with access to this same filesystem. The original student PDFs and `PATHSNAP_BUILD_PROMPT.md` remain the complete product and scientific specification.

## Which prompt goes to which session

- Give **LLM A** the entire file `PATHSNAP_LLM_A_PROMPT.md`.
- Give **LLM B** the entire file `PATHSNAP_LLM_B_PROMPT.md`.
- Both must read `PATHSNAP_TWO_LLM_PROTOCOL.md`, the full master prompt, and all five student PDFs.
- Start B first if convenient; A may start immediately and read/research while B completes the one-writer Git bootstrap. Neither needs to create additional agents.

All four prompt files live in `/home/vismay-hs/Downloads/ML_Hackathon/`. Communication happens in the shared absolute directory `/home/vismay-hs/Downloads/ML_Hackathon/.pathsnap_coordination/`, outside the repository and outside all worktrees. This directory is visible to both sessions on this machine. Two independent computers or isolated containers need a genuinely shared mounted folder or an explicit file-transfer transport; identical path strings alone do not share files.

## Balanced responsibility

| LLM A: scientific system | LLM B: application and delivery |
|---|---|
| Data inspection, EDA, cleaning, IDs/geometry | UI reference research, original design system |
| Supervision alignment, candidate generation, features | React/TypeScript UI, interactions, animation, accessibility |
| Five distinct models, grouped CV, model comparison | FastAPI transport, validation, errors, request logs |
| Bayesian tuning, artifacts, inference pipeline | Wiring A's pipeline and isolated scorer into the API |
| HMM/Viterbi and classifier-versus-HMM evaluation | Folium maps, browser testing, API/integration QA |
| Scientific metrics, actual comparison plots | Deployment, LAN workflow, report build and final PDF |
| Scientific report sections and methodology notes | System report sections, evidence assembly, integration |

This is approximately equal by responsibility and expected effort, rather than by line count. Training runtime is not human/agent workload. Use run profiling and the milestone check-ins to balance useful active work. A's scientific pipeline is substantial; B's full application, tests, maps, report assembly, and integration are substantial. Neither silently assigns new work to the other. Rebalance only entire unstarted tasks through an explicit two-party acknowledgement, with an updated file-owner record. Never have both editing the same file to chase a nominal 50/50 split.

## Shared milestones and acceptance

1. **M0 — Bootstrap and contracts:** B seeds the existing repository, creates worktrees, publishes paths; both agree to schemas, scoring semantics/status, ownership, and interface version.
2. **M1 — Executable vertical slice:** A supplies permitted-data loading and an explicitly labeled reference-free geometric diagnostic adapter, or an already trained initial model if available; B supplies a real FastAPI request and map UI. Diagnostic output is never called final ML inference or counted among the five models. Integrate early to expose interface problems.
3. **M2 — Scientific/application coverage:** A completes five measured baselines and selected-model reasoning; B completes researched UI, meaningful API tests, Folium generation, and responsive/error states against the integrated outputs. Commit partial scientific runs truthfully if needed; never invent metrics to meet a milestone.
4. **M3 — Final prediction path:** A completes Bayesian tuning, exported assets, HMM, real comparisons and scientific plots; B integrates final inference/scoring and profiles the API/browser flow.
5. **M4 — Submission readiness:** A supplies scientific report evidence and audits numeric claims; B assembles one PDF, verifies deployment, and audits the full submission. Both review the combined build and remaining blockers before final promotion.

Each milestone can contain several real worker commits. Their source and result history is retained. The combined milestone is reviewed and tested before its integration commit and before promotion to `main`. This reconciles incremental commit history with the requirement to check the joined work before accepting it.

## Current starting facts

- Project: `/home/vismay-hs/Downloads/ML_Hackathon/PathSnap_ML_Hackathon_81`.
- The project currently has a Git repository on `main` with **no initial commit** and scaffold files untracked. Recheck this when execution starts; the state may have changed.
- Dataset: `/home/vismay-hs/Downloads/ML_Hackathon/Student_folder`, with 80 training trips and 10 student-testing trips. The reserved evaluator dataset is absent.
- Do not begin two branches/worktrees from an unborn branch. B must first create the reviewed bootstrap commit.
- All worker worktrees use the **absolute dataset root**. The master's `../Student_folder` default does not resolve correctly from the nested worktree locations defined here.
- No branch, worktree, model, experiment, API, or UI is created merely by reading these prompts.

The detailed protocol specifies exclusive ownership, acknowledgement messages, artifact handoffs, contract changes, tests, and the exact merge procedure. Follow it; do not improvise a shared-checkout Git workflow.
