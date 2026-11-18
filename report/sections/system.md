## 5. Geographical Visualisation using Folium

We built interactive Folium maps for all ten student-test trips with `src/visualisation/folium/make_maps.py`. Each map has five layers. Every layer can be switched on and off in the layer control and is named in the legend:

| Layer | How it is drawn |
|---|---|
| Raw GPS observations | Small hollow orange circles; hovering shows the point number and time |
| Road network near the trip | Thin grey lines |
| Reference route (development trips only) | Wide, translucent green line |
| Predicted route, classifier + HMM | Solid blue line |
| Predicted route, classifier only | Dashed purple line |

- **Extent:** each map zooms to the trip's GPS extent on an OpenStreetMap base map.
- **Route pieces:** every connected piece of a predicted route is drawn separately. Where the decoder had to break the route, the map shows a gap rather than a straight line across buildings.
- **Comparison:** seeing the GPS points, the reference and both predictions together makes it easy to see where the HMM corrects the classifier.

![Folium map, student-test trip 00000091](report/figures/system/folium-00000091.png)
<p class="caption">Figure 9. Folium map of student-test trip 00000091. The final classifier + HMM route (blue) follows the reference route (green) along the road network, through the noisy GPS points (orange).</p>

The interactive HTML maps are in `maps/hgb-hmm-v1/`, one per student-test trip. They are best viewed through a local web server (`python3 -m http.server 8001 --directory maps/hgb-hmm-v1`), because OpenStreetMap does not serve map tiles to files opened directly. The reserved evaluator trips are never mapped with their reference routes; the map generator refuses any partition other than training or student-test.

## 6. API, UI and Deployment

### 6.1 Architecture

```
Laptop 2: React UI                      Laptop 1: FastAPI + trained model
  GET /trips ───────────────────────►   list of allowed trip IDs
  POST /predict {trip_id} ──────────►   read .track / .nodes / .arcs (never .route)
                                        clean → candidates → features → classifier
                                        → HMM/Viterbi → route
                                        then, separately: score against the reference
  ◄─────────────────────────────────    route, point statuses, timings, metrics
```

**Backend (Laptop 1, `api/`).** A FastAPI service with three endpoints:

- `GET /health` reports whether the service is ready, its mode and the model it loaded.
- `GET /trips` lists the ten trips allowed in the current mode.
- `POST /predict` takes `{"trip_id": "…"}` and returns the predicted route, a status for every GPS point, per-stage timings and the accuracy metrics.

Key design points:

- **Mode is set on the server.** It is either *development* (student-test trips) or *evaluator* (the reserved trips). It is never chosen by the request, and evaluator mode never falls back to other data.
- **Model integrity is checked at startup.** The service verifies the model bundle's checksums and stays "not ready", with a reason, if anything is wrong.
- **Requests are handled safely.** Prediction runs in a background worker, one trip at a time, so the health check always responds. A second request during a prediction is politely refused (HTTP 429).
- **Scoring cannot leak into prediction.** Scoring happens only after the prediction is finished, in a separate scorer. The browser receives summary metrics only: never the reference route, per-point answers or correctness flags.
- **Every request is logged.** Each response carries a request ID, which Laptop 1's terminal logs together with the trip, the model version and the time spent in each stage.

**Frontend (Laptop 2, `ui/`).** A React and TypeScript web page with a Leaflet map:

- **Layout:** a side panel shows the connection status, the mode, the ten trips, a "Reconstruct route" button and the results. The rest of the screen is the map, with a layer control, a point inspector and route playback.
- **States:** every state has its own screen: connecting, server unreachable, not ready, evaluator data missing, running, and failed (with the request ID and a retry button).
- **Layouts:** the page works from desktop down to phone width.

![UI result](report/figures/system/ui-result-1440.png)
<p class="caption">Figure 10. The evaluator interface after reconstructing student-test trip 00000052 with the final model.</p>

![UI on a phone-sized screen](report/figures/system/ui-result-390.png){: style="max-height:95mm"}
![UI error state](report/figures/system/ui-error.png){: style="max-height:85mm"}
<p class="caption">Figure 11. Left: the same workflow at phone width. Right: the error state, showing the message, the request ID and a retry button (server error simulated in a browser test).</p>

### 6.2 Testing

| Check | Result |
|---|---|
| Python tests (data processing, features, models, HMM, scoring, API contract, leakage, Folium) | 49 passed |
| Browser tests (keyboard use, three screen sizes, errors, slow and stale responses, LAN origin, playback) | 14 passed against the live API |
| All ten student-test trips through the API with the final model | 10/10 returned HTTP 200, valid and scored, with no reference data in the response |

The slowest student-test trip (3,958 GPS points) takes 5.8 s on the server; most take one to two seconds.

### 6.3 Final evaluation on the reserved evaluator trips

The finished system was frozen and then run once on the ten reserved evaluator trips, through the API in evaluator mode. Scoring happened only on the server, after each prediction. Nothing was trained, tuned or selected using these trips.

| Trip | GPS points | Top-1 accuracy | Macro F1 | Route continuity | Route pieces | Server time |
|---|---:|---:|---:|---:|---:|---:|
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
| **All 10** | **19,674** | **87.8%** | **0.786** | **99.96%** | **23** | |

Overall, 17,280 of 19,674 GPS points were matched to the correct road. This is in line with the 88.5% on the student-test trips, which shows the model generalises to trips it has never seen. Four trips scored above 95%, and five were reconstructed as a single connected route.

![Evaluator mode](report/figures/system/ui-evaluator-result.png)
<p class="caption">Figure 12. The interface in evaluator mode, listing exactly the ten reserved trips, with trip 00000049 reconstructed and scored on the server. Only the prediction and the raw GPS points are drawn.</p>

### 6.4 Two-laptop deployment

The full guide, with Linux, macOS and Windows commands, is `docs/deployment/two-laptops.md`. In short:

- **Laptop 1** starts the API on all network interfaces: `uvicorn api.main:app --host 0.0.0.0 --port 8000`. It is configured through environment variables for the mode, the data folder, the model folder and the allowed browser address.
- **Laptop 2** builds the interface pointing at Laptop 1 (`VITE_PATHSNAP_API_URL=http://<Laptop-1-IP>:8000`) and serves it with `npm run preview`.

**API responses on the receiving laptop.** Laptop 1's terminal logs each request in four lines: start, prediction finished, scoring finished, and the HTTP response. The excerpt below was recorded with the interface opened over the laptop's Wi-Fi address (`10.20.205.114`) rather than `localhost`, so the request travelled through the network interface exactly as it does from Laptop 2. The same request ID appears in the interface.

```log
INFO pathsnap.api predict_start request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 mode=development model_version=hgb-hmm-v1
INFO pathsnap.api predict_done  request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 observations=874 matched=874 pieces=1 ...
INFO pathsnap.api scoring_done  request_id=4ad37b6b17e0e04409c65cc29014b1ef trip_id=00000091 status=scored scoring_ms=206.5
INFO pathsnap.api request       request_id=4ad37b6b17e0e04409c65cc29014b1ef client=10.20.205.114 method=POST path=/predict status=200 ms=877.7
```
