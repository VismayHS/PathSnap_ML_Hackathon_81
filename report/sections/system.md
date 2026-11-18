## Geographical Visualisation using Folium

The Folium maps are made by `src/visualisation/folium/make_maps.py` from development-only visualisation exports (train or student-test trips only). Each map has five layers, each switchable in a layer control and named in a legend:

| Layer | Encoding |
|---|---|
| Raw GPS observations | small hollow orange circles; the tooltip gives the observation index and time |
| Road network near the trajectory | thin grey lines |
| Reference route (development data only) | wide translucent green line |
| Predicted route, classifier + HMM | solid blue line |
| Predicted route, classifier only | dashed purple line |

Each connected piece of a predicted route is drawn as its own line. Where the decoder breaks the route (no legal connection on the directed road graph), the map shows a gap instead of a straight line across buildings. The map fits its bounds to the trip's GPS extent. The basemap is OpenStreetMap, credited on the map.

![Folium map, student-test trip 00000091](report/figures/system/folium-00000091.png)
<p class="caption">Figure S1. Folium development map of student-test trip 00000091 (model hgb-hmm-v1). The classifier + HMM route (blue) follows the reference route (green) along the road network. Captured from <code>maps/hgb-hmm-v1/</code> served over HTTP.</p>

![Folium map, student-test trip 00000007](report/figures/system/folium-00000007.png)
<p class="caption">Figure S2. Student-test trip 00000007, the trip where HMM decoding lowered Top-1 accuracy (see the HMM section). At this zoom the map shows the overall route, not individual arc assignments or direction errors; the quantitative counterexample in the HMM section is the evidence, and the overlap seen here does not prove every assignment is correct.</p>

Interactive HTML maps: `maps/<run_id>/trip_<id>_<partition>.html`. Regenerate them with `python -m src.visualisation.folium.make_maps --input results/hmm/<run_id>/visualisation --output maps/<run_id>` (for the final model: `results/hmm/hgb-hmm-v1/visualisation`). View them over HTTP (`python3 -m http.server 8001 --directory maps/<run_id>`), because OpenStreetMap blocks tiles for `file://`.

Evaluator trips are never mapped. The generator rejects any partition other than train or student-test, and the evaluator UI never receives reference geometry.

## API, UI and Deployment

### Architecture

```
Laptop 2: React UI                      Laptop 1: FastAPI
  GET /trips ───────────────────────►   allowlisted trip IDs
  POST /predict {trip_id} ──────────►   load .track/.nodes/.arcs (never .route)
                                        clean > candidates > features > model
                                        > HMM/Viterbi > route geometry
                                        then, separately: scorer reads reference
  ◄─────────────────────────────────    route, statuses, timings, aggregate metrics
```

**Backend (`api/`).** The backend has three endpoints:

- `GET /health` gives readiness, the mode and the model identity.
- `GET /trips` lists the allowed trip IDs for the configured mode.
- `POST /predict` takes `{"trip_id": "…"}`.

How it works:

- The mode (`development` = student-test trips, `evaluator` = reserved trips) is server configuration and never a request field. Evaluator mode never falls back to student-test data.
- Requests are checked against the partition's allowlist.
- At startup the service checks the model bundle's manifest: its schema, contract version and the SHA-256 of every file. Any failure leaves the service running but "not ready", with a reason.
- Prediction runs in a worker thread, one at a time, so `/health` stays responsive. A second request while one is running gets HTTP 429.
- Scoring runs only after the prediction finishes, through a separate scorer. A scoring failure yields "metrics unavailable", never a failed prediction.
- Responses are mapped field by field, so no reference arcs, per-point labels or correctness masks can reach the browser. The JSON schema rejects unknown fields.
- Every response carries an `X-Request-ID`, and Laptop 1 logs that ID with the trip, model version and per-stage timings.

**Frontend (`ui/`).** The frontend is built with React, TypeScript, Vite and Leaflet:

- One left panel holds the connection state, the mode badge, the ten trips, the "Reconstruct route" action and the results. The rest of the screen is the map, with a layer control, an observation inspector and route playback.
- Coordinates arrive as `[lon, lat]` and are converted once for Leaflet.
- Each route piece is drawn separately.
- An earlier request's late response can never overwrite a newer selection.
- All states are designed: connecting, unreachable, not ready, evaluator data not configured, running, failed (with the request ID) and diagnostic model.
- The design research and decisions are in `docs/ui-research.md` and `DESIGN.md`.

![UI result at 1440 px](report/figures/system/ui-result-1440.png)
<p class="caption">Figure S3. Evaluator UI after reconstructing student-test trip 00000052 with the trained model (hgb-hmm-v1, development mode). Real run on one machine (API at 127.0.0.1:8000); scoring policy provisional.</p>

![UI on a 390 px screen](report/figures/system/ui-result-390.png){: style="max-width:45%"}
![UI error state](report/figures/system/ui-error.png){: style="max-width:52%"}
<p class="caption">Figure S4. Left: the same workflow at phone width. Right: a failed request (a mocked server error in the browser test) showing the message, the request ID and a retry.</p>

### Verification

| Check | Result | Evidence |
|---|---|---|
| API contract, errors, leakage, readiness, Folium generator (pytest) | 22 passed, within 48 combined Python tests at M3 | `tests/api`, `tests/integration` |
| Browser workflows (Playwright: keyboard, 1440/1366/390 px, errors, stale responses, server change, plain-HTTP LAN origin, playback, keyboard inspection) | 13 passed against the live trained API | `ui/tests/workflow.spec.ts` |
| All ten student-test trips through HTTP with the trained bundle | 10/10: HTTP 200, schema-valid, scored, no reference or label fields | `results/system/m3-predict-all.json` |
| HTTP and offline pipeline agree | Per-trip metrics for trips 00000077 and 00000091 equal A's offline comparison; A checked every observation for trips 00000052 and 00000007 | M3 integration record |

Server-side time per request, trained model, development mode, one machine:

| Trip | HTTP | Scored | Route pieces | Server time (ms) |
|---|---|---|---|---|
| 00000000 | 200 | scored | 3 | 1,541 |
| 00000007 | 200 | scored | 1 | 849 |
| 00000009 | 200 | scored | 5 | 1,275 |
| 00000040 | 200 | scored | 2 | 2,035 |
| 00000052 | 200 | scored | 1 | 215 |
| 00000056 | 200 | scored | 6 | 5,828 |
| 00000065 | 200 | scored | 4 | 899 |
| 00000076 | 200 | scored | 2 | 2,076 |
| 00000077 | 200 | scored | 3 | 3,644 |
| 00000091 | 200 | scored | 1 | 987 |

The slowest trip (00000056, 3,958 points) takes 5.8 s. The UI allows up to 180 s and shows no fake progress while waiting.

### Final evaluation on the reserved trips

The 10 reserved evaluator trips were run once on the frozen accepted M3 system (`main` `603b42f`, bundle `hgb-hmm-v1`), before the M4 documentation was promoted, through the API in evaluator mode. Scoring happened only on the server, after prediction. Nothing was explored, trained, tuned or selected using these trips. A re-verified every trip independently, read-only. The later UI metric-layout fix was cosmetic only. Source: `results/system/evaluator-run-01-aggregate.json`. Provisional scoring policy `pathsnap-scoring-v0`.

| Trip | Points | Top-1 accuracy | Macro F1 | Route continuity | Route pieces | Server time |
|---|---|---|---|---|---|---|
| 00000015 | 6,854 | 79.0% | 0.426 | 99.94% | 5 | 2.8 s |
| 00000017 | 1,346 | 87.5% | 0.764 | 99.93% | 2 | 2.3 s |
| 00000023 | 458 | 91.3% | 0.669 | 100.00% | 1 | 0.4 s |
| 00000030 | 654 | 81.8% | 0.759 | 100.00% | 1 | 0.8 s |
| 00000049 | 2,642 | 98.1% | 0.952 | 99.96% | 2 | 2.0 s |
| 00000059 | 1,031 | 91.0% | 0.763 | 100.00% | 1 | 1.3 s |
| 00000067 | 916 | 95.5% | 0.879 | 100.00% | 1 | 0.6 s |
| 00000073 | 1,144 | 95.8% | 0.896 | 100.00% | 6 | 1.1 s |
| 00000087 | 1,399 | 98.1% | 0.960 | 100.00% | 1 | 2.7 s |
| 00000094 | 3,230 | 88.5% | 0.794 | 99.94% | 3 | 3.6 s |
| **All 10** | **19,674** | **87.8%** (pooled) | **0.786** (mean) | **99.96%** (pooled) | **23** | |

![Evaluator mode](report/figures/system/ui-evaluator-result.png)
<p class="caption">Figure S5. The UI in evaluator mode: exactly the ten reserved trips, with trip 00000049 reconstructed and scored on the server. Only the prediction and raw GPS are drawn; no evaluator reference geometry reaches the browser.</p>

### Two-laptop deployment

The step-by-step guide is `docs/deployment/two-laptops.md`. In short:

- **Laptop 1** runs `uvicorn api.main:app --host 0.0.0.0 --port 8000` with `PATHSNAP_DATA_ROOT`, `PATHSNAP_BUNDLE_ROOT`, `PATHSNAP_MODE` and `PATHSNAP_CORS_ORIGINS` set.
- **Laptop 2** builds the UI with `VITE_PATHSNAP_API_URL=http://<Laptop-1-IP>:8000` and serves it with `npm run preview`.

Excerpt of the receiving-end API log from the single-machine run above. Each request ID appears in the UI:

```log
INFO pathsnap.api predict_start request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 mode=development model_version=hgb-hmm-v1
INFO pathsnap.api predict_done  request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 observations=2503 matched=2503 pieces=3 ...
INFO pathsnap.api scoring_done  request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 status=scored scoring_ms=484.7
INFO pathsnap.api request       request_id=612076a8a4404356b4eb822e3e7bf131 client=127.0.0.1 method=POST path=/predict status=200 ms=1660.0
```

**Network check on the Wi-Fi interface (2026-11-18).** As a rehearsal on one laptop, the API listened on all interfaces (`--host 0.0.0.0`). The built UI was served by `npm run preview` and opened in Chrome at the laptop's Wi-Fi address (`http://10.20.205.114:4173`), not `localhost`. That is a non-secure plain-HTTP origin, just like Laptop 2 on a LAN. Two trips were reconstructed with no browser errors, and the request IDs in the UI matched the server log, which recorded the client by its Wi-Fi address:

```log
INFO pathsnap.api predict_start request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 mode=development model_version=hgb-hmm-v1
INFO pathsnap.api predict_done  request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 observations=874 matched=874 pieces=1 ...
INFO pathsnap.api scoring_done  request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 status=scored scoring_ms=206.5
INFO pathsnap.api request       request_id=4ad37b6b17e0e04409c65cc29014b1ef client=10.20.205.114 method=POST path=/predict status=200 ms=877.7
```

This exercises the LAN code path (network interface, CORS for a non-localhost origin, request IDs without `crypto.randomUUID`). It does not replace the demonstration on two physical laptops.

PENDING: screenshot of Laptop 1's terminal while Laptop 2 makes requests over the LAN (Deliverables §7). This must be a real capture from the two-laptop setup; the excerpt above is from a single machine.
