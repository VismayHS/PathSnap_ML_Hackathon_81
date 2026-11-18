# Progress log

Newest first. Each entry: what happened, why, what's next. Times are local (IST).

## 2026-11-18, about 13:30: M4 accepted; the report PDF is on `main`

- **M4 (`499c5ef`)** is on `main`: the feature ablation, the final science wording (evaluator data was not used during development; the final run is reported separately in the system section), pooled continuity 99.96%, and the evaluation-panel layout fix.
- **Final checks before promotion:** 49 Python tests, contract hash unchanged, UI type check, lint and build, 14/14 browser tests against the live API, all 10 trips returning 200, a 24-page PDF with no rows split across pages, and no broken links. A reviewed it independently and gave its ACK.
- **The built report** is committed at `report/PathSnap_Technical_Report.pdf`. Rebuild it after the team fills in its fields: `.venv/bin/python scripts/build_report.py`.
- **Team still needs to:** fill in names and SRNs (`report/sections/front.md`), the final commit SHA, and the AI-assistance statement (`report/sections/integrity.md`); run the two-laptop rehearsal and add the real terminal screenshot (`report/sections/system.md`); then rebuild the PDF.

## 2026-11-18, about 13:00: final evaluation on the reserved trips, then M4

- **Evaluator data arrived** (`evaluator_test.zip`). It was extracted outside the repo, its 10 trip IDs were checked for overlap with the development trips (none), and **nobody explored it**.
- **The frozen system ran it once in evaluator mode** (`main` `603b42f`): **87.8% Top-1 accuracy** (17,280 of 19,674 points), mean trip Macro F1 0.786, pooled continuity 99.96%, 23 route pieces. A verified every trip independently. All 10 trips were scored on the server, and only aggregates are stored (`results/system/evaluator-run-01-aggregate.json`). Nothing was tuned afterwards.
- **M4 (promoted after the evaluation run):** feature ablation (distance only 0.345 → plus heading 0.652 → all features 0.730 CV Macro F1), the corrected science section, the combined report PDF, and the README with screenshots and every guide.
- **UI fix (cosmetic, after the evaluation):** an evaluation-panel layout bug (numbers wrapping one character per line), found in the evaluator screenshots, is fixed and covered by a new browser test.
- **Team still needs to:** add names and SRNs, write the AI-assistance statement, run the two-laptop rehearsal with real terminal screenshots, and prepare for the viva with `docs/ml/viva-notes.md`.

## 2026-11-18, about 12:50: M2 and M3 accepted; the trained model is live in the demo

- **M2 (`fbd0df0`):** all five models were trained with 5-fold grouped cross-validation on the 80 training trips (about 9 min) and tested on the 10 student-test trips. HistGradientBoosting was selected for the best CV Macro F1 (0.725) and log loss. See `docs/ml/model-selection.md`.
- **M3 (`603b42f`):** 12 Optuna TPE trials took CV Macro F1 from 0.7252 to 0.7297. One trial was interrupted and completed from its recorded parameters, and this is documented. On the student-test trips, classifier + HMM reaches **88.5% Top-1 accuracy** (86.0% without the HMM), Macro F1 0.851, and 99.9% route continuity. The route has 28 pieces instead of 974. On trip 00000007 the HMM made accuracy worse, and the report says so.
- **The app** now runs the trained model: all 10 trips are scored in 0.2–5.8 s each. Folium maps exist for all 10 trips (`maps/hgb-hmm-v1/`).
- **Training ran only on the user's laptop.** It was faster than splitting across four laptops. The multi-laptop guide stays optional.
- **The README** is now a complete front page, with results, screenshots and how to run and reproduce everything.
- **Now (M4):** A is adding a required feature ablation. Early result: distance features alone reach CV Macro F1 0.345, against 0.725 with all features. Then the combined report PDF gets its final audit.
- **Team to-do:** names and SRNs in the report, your own AI-assistance statement, a two-laptop rehearsal with real terminal screenshots, and reading `docs/ml/viva-notes.md`.

## 2026-11-18 — M1 accepted: first end-to-end slice on `main` (`6bd8e8c`)

- **What works:** Laptop 1 API plus the Laptop 2 UI on the 10 student-test trips. Pick a trip, reconstruct, see the predicted route over the GPS and nearby roads, inspect individual points, and play the route back. Every trip returns in under about 1 s.
- **Important:** the model behind it is a *diagnostic* that snaps each point to the nearest road. It is **not** one of the five trained models, the UI says so, and accuracy metrics are switched off until the real scorer exists.
- **Checks run:** 34 Python tests, 13 browser tests (keyboard use, small screens, errors, stale responses, LAN-safe request IDs), all 10 trips over real HTTP, and A's independent review of the merged code.
- **A (science):** five-model pilot measured (each model fits in 0.05–1.7 s on 8 trips), and the full five-model cross-validation baseline is running locally (estimated 5–15 min). A four-laptop training kit is being built, including Windows instructions for the teammate's RTX 4060 laptop.
- **Still pending outside our control:** organiser clarification of the official accuracy definition, the reserved evaluator trips, a real two-laptop LAN test, and real terminal screenshots for the report.
- **How to run it:** [docs/deployment/two-laptops.md](../deployment/two-laptops.md).

## 2026-11-18 — M0 bootstrap (B)

- Read all five PDFs, the master build prompt and the two-LLM protocol.
- Checked the dataset: `Student_folder/train` (80 trips) and `Student_folder/student_test` (10 trips). Track files have 262–19,313 GPS points; road networks have 649–307,392 arcs per trip. Evaluator trips are not present yet (expected — organisers provide them).
- Git: repo had no commits; identity set to VismayHS (repo-local, user-approved).
- Wrote the **proposed contract 0.1.0** — how the science code and the app talk to each other: `contracts/interfaces.md`, `contracts/http.schema.json`, `contracts/artifacts.schema.json`, `src/contracts.py`, plus a clearly-synthetic example response.
- Next: bootstrap commit → create A/B worktrees → send the proposal to A → wait for A's review/ACK before building on it.
