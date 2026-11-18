# Report

The single consolidated technical report (Deliverables PDF, sections 2–7) is built from `sections/`.

| File | Owner | Content |
|---|---|---|
| `sections/front.md` | B, team fills names | title, team, contents |
| `sections/science.md` | A | EDA, models, HPO, HMM (Deliverables §2.2–5) |
| `sections/system.md` | B | Folium maps, API/UI/deployment (Deliverables §6–7) |
| `sections/integrity.md` | **team** | AI-assistance disclosure, in the team's own words |

Build: `python3 scripts/build_report.py`, which writes `report/PathSnap_Technical_Report.pdf`. It prints every `PENDING:` item still open.

Every number, table and figure must come from files committed in this repository. Team members should read, check and, where needed, rewrite the drafted sections in their own words before submitting, because the integrity policy requires that every member can explain every claim.
