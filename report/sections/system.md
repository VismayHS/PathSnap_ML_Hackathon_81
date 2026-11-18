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
<p class="caption">Figure S2. Student-test trip 00000007, the trip where HMM decoding lowered Top-1 accuracy (see the HMM section). The classifier-only (dashed purple) and HMM (blue) layers can be compared with the reference.</p>

Interactive HTML maps: `maps/<run_id>/trip_<id>_<partition>.html`. Regenerate them with `python -m src.visualisation.folium.make_maps --input results/hmm/visualisation/<run_id> --output maps/<run_id>`.

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

### Two-laptop deployment

The step-by-step guide is `docs/deployment/two-laptops.md`. In short:

- **Laptop 1** runs `uvicorn api.main:app --host 0.0.0.0 --port 8000` with `PATHSNAP_DATA_ROOT`, `PATHSNAP_BUNDLE_ROOT`, `PATHSNAP_MODE` and `PATHSNAP_CORS_ORIGINS` set.
- **Laptop 2** builds the UI with `VITE_PATHSNAP_API_URL=http://<Laptop-1-IP>:8000` and serves it with `npm run preview`.

Excerpt of the receiving-end API log from the single-machine run above. Each request ID appears in the UI:

```
INFO pathsnap.api predict_start request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 mode=development model_version=hgb-hmm-v1
INFO pathsnap.api predict_done  request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 observations=2503 matched=2503 pieces=3 ...
INFO pathsnap.api scoring_done  request_id=612076a8a4404356b4eb822e3e7bf131 trip_id=00000000 status=scored scoring_ms=484.7
INFO pathsnap.api request       request_id=612076a8a4404356b4eb822e3e7bf131 client=127.0.0.1 method=POST path=/predict status=200 ms=1660.0
```

PENDING: screenshot of Laptop 1's terminal while Laptop 2 makes requests over the LAN (Deliverables §7). This must be a real capture from the two-laptop setup; the excerpt above is from a single machine.
