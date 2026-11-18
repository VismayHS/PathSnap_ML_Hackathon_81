# Two-laptop deployment

This guide is for whoever sets up the demo. **Laptop 1** runs the model, the data and the FastAPI service. **Laptop 2** runs the evaluator UI in a browser. Both laptops must be on the same LAN (Wi-Fi or a phone hotspot).

```
Laptop 2 (browser UI :4173) ──HTTP──► Laptop 1 (FastAPI :8000) ── model bundle + trip files
```

The status column below separates what has been checked on one machine from what has not yet been done on two physical laptops.

| Check | Status |
|---|---|
| API and UI on one machine (localhost), all 10 student-test trips, browser tests | Verified at every milestone (M1–M4 integration records) |
| UI over a plain `http://<LAN-IP>` origin | Code path tested with `crypto.randomUUID` disabled. The physical LAN run is **pending**. |
| Two physical laptops on a LAN | **Pending**: run the checklist at the end |
| Reserved evaluator trips | Received. Run once on one machine in evaluator mode (results in `results/system/evaluator-run-01-aggregate.json`) |

## Laptop 1: model and API

Requirements: Python 3.12, the repository, the trip data folder, and the trained model bundle `artifacts/hgb-hmm-v1` (in the repository).

**Linux / macOS**

```bash
cd PathSnap_ML_Hackathon_81
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt

# Find this laptop's LAN IP (Laptop 2 needs it)
hostname -I                     # Linux;  macOS: ipconfig getifaddr en0

export PATHSNAP_MODE=development                          # or 'evaluator' for the reserved trips (see below)
export PATHSNAP_DATA_ROOT="/absolute/path/to/Student_folder"
export PATHSNAP_BUNDLE_ROOT="$PWD/artifacts/hgb-hmm-v1"   # the final trained model
# Every browser origin the UI is opened from (scheme, host and port). This replaces the default list.
export PATHSNAP_CORS_ORIGINS="http://<LAPTOP2-IP>:4173,http://localhost:4173,http://127.0.0.1:4173,http://<LAPTOP2-IP>:5173,http://localhost:5173"
# evaluator mode only:
# export PATHSNAP_MODE=evaluator
# export PATHSNAP_EVALUATOR_ROOT="/absolute/path/to/evaluator_test"

.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Windows (PowerShell)**

```powershell
cd PathSnap_ML_Hackathon_81
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock.txt

ipconfig                        # the "IPv4 Address" of the Wi-Fi adapter is the LAN IP

$env:PATHSNAP_MODE = "development"
$env:PATHSNAP_DATA_ROOT = "C:\absolute\path\to\Student_folder"
$env:PATHSNAP_BUNDLE_ROOT = "$PWD\artifacts\hgb-hmm-v1"
$env:PATHSNAP_CORS_ORIGINS = "http://<LAPTOP2-IP>:4173,http://localhost:4173,http://127.0.0.1:4173,http://<LAPTOP2-IP>:5173,http://localhost:5173"
# evaluator mode only:
# $env:PATHSNAP_MODE = "evaluator"
# $env:PATHSNAP_EVALUATOR_ROOT = "C:\absolute\path\to\evaluator_test"

.venv\Scripts\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

`$env:` variables last only for that PowerShell window, so start the API from the same window. When Windows asks, allow Python on **Private** networks.

`--host 0.0.0.0` makes the API listen on the LAN interface. Leave this terminal visible: the evaluator must be able to see the request logs (`request_id=… trip_id=… stages_ms=…`).

Check it from Laptop 1:

```bash
curl http://127.0.0.1:8000/health      # "ready": true
curl http://127.0.0.1:8000/trips       # the 10 trip IDs for the active mode
```

On Windows PowerShell 5.1, type `curl.exe` instead of `curl` (plain `curl` is an alias for `Invoke-WebRequest`).

## Laptop 2: UI

Requirements: Node 20 or newer and the repository. Fonts are bundled, so the UI needs no internet. Map tiles need internet, but the route, GPS points and road network still display without it.

**Linux / macOS**

```bash
cd PathSnap_ML_Hackathon_81/ui
npm ci
echo "VITE_PATHSNAP_API_URL=http://<LAPTOP1-IP>:8000" > .env.local
npm run build
npm run preview          # serves on http://0.0.0.0:4173
```

**Windows (PowerShell)**

```powershell
cd PathSnap_ML_Hackathon_81\ui
npm ci
Set-Content -Path .env.local -Value "VITE_PATHSNAP_API_URL=http://<LAPTOP1-IP>:8000" -Encoding ascii
npm run build
npm run preview
```

Use `Set-Content -Encoding ascii`, not `>` or `-Encoding utf8`. In Windows PowerShell 5.1, `>` writes UTF-16 and `utf8` adds a byte-order mark, and Vite then silently ignores the setting (checked: a BOM-prefixed `.env.local` produced a build without the URL). If in doubt, skip `.env.local` and set the address in the UI under **Server address**.

Open `http://localhost:4173` on Laptop 2 (or `http://<LAPTOP2-IP>:4173`). Whichever address you use must be listed in Laptop 1's `PATHSNAP_CORS_ORIGINS`. You can also change the address without rebuilding: open **Server address** in the panel and enter `http://<LAPTOP1-IP>:8000`, or add `?api=http://<LAPTOP1-IP>:8000` to the URL.

## Firewall and network troubleshooting

| Symptom in the UI | Likely cause and fix |
|---|---|
| "Can't reach the PathSnap server" | Wrong IP, the API isn't running, the browser address is not in `PATHSNAP_CORS_ORIGINS`, or Laptop 1's firewall is blocking port 8000. Linux: `sudo ufw allow 8000/tcp`. Windows: allow Python on *Private* networks. macOS: allow incoming connections for Python. |
| Works with `curl` on Laptop 2 but not in the browser | CORS: add Laptop 2's exact origin (scheme, IP and port) to `PATHSNAP_CORS_ORIGINS` and restart the API. |
| Campus Wi-Fi blocks device-to-device traffic (client isolation) | Use a phone hotspot or a travel router. |
| "The server is up but not ready" | Read the listed reasons. `bundle_manifest_missing` means `PATHSNAP_BUNDLE_ROOT` is wrong. `data_not_configured` means the data root is wrong or evaluator data hasn't been provided. |
| "Basemap tiles unavailable" | There is no internet. This is harmless: all PathSnap geometry still shows. |

From Laptop 2, `curl http://<LAPTOP1-IP>:8000/health` should return JSON.

## Demo-day checklist (physical laptops)

1. Laptop 1: `/health` shows `"ready": true` and the expected `mode`.
2. Laptop 2: the UI shows "Connected, ready" and exactly 10 trips, with the mode badge correct (Development or Evaluator data).
3. Reconstruct one trip. The request ID shown in the UI appears in Laptop 1's terminal log.
4. Try every trip once. Note the server time and any errors.
5. Take screenshots of the UI and of Laptop 1's terminal for the report. These must be real captures.

## Evaluator mode safety

- Evaluator mode reads only `PATHSNAP_EVALUATOR_ROOT`. If that is missing, the API reports "not configured" and **never** falls back to the student-test trips.
- Reference routes stay on Laptop 1. The browser receives only predictions and aggregate metrics.
- A diagnostic bundle is refused in evaluator mode.
