# Progress log

Newest first. Each entry: what happened, why, what's next. Times are local (IST).

## 2026-11-18 — M0 bootstrap (B)

- Read all five PDFs, the master build prompt and the two-LLM protocol.
- Checked the dataset: `Student_folder/train` (80 trips) and `Student_folder/student_test` (10 trips). Track files have 262–19,313 GPS points; road networks have 649–307,392 arcs per trip. Evaluator trips are not present yet (expected — organisers provide them).
- Git: repo had no commits; identity set to VismayHS (repo-local, user-approved).
- Wrote the **proposed contract 0.1.0** — how the science code and the app talk to each other: `contracts/interfaces.md`, `contracts/http.schema.json`, `contracts/artifacts.schema.json`, `src/contracts.py`, plus a clearly-synthetic example response.
- Next: bootstrap commit → create A/B worktrees → send the proposal to A → wait for A's review/ACK before building on it.
