# PathSnap evaluator UI — design system

**Surface mode:** Operate (Impeccable). The evaluator is completing a task, so precision and familiarity matter more than expression. Research and the layout choice are in [docs/ui-research.md](docs/ui-research.md).

## Users and scene

- **Primary:** a hackathon evaluator at Laptop 2, usually in a lit hall, possibly projected. It is their first time seeing the tool, and they have a few minutes and ten trips to choose from.
- **Secondary:** team members demonstrating it and answering questions from what is on screen.
- **Job:** pick a trip → reconstruct → see whether the predicted route follows the GPS along real roads → read honest aggregate results → try another trip.

## Screen hierarchy

1. The **map**, which is the largest element and always visible, with real geometry only.
2. The **Reconstruct route** action, which is the only filled accent button on the screen.
3. The **trip choice**: the ten IDs from `/trips`, with the active mode shown above them.
4. **Results**: model identity, metrics with denominators, timings and warnings.
5. **Connection/readiness** and the server address, which stay small, in the header area of the panel.

## Direction

The page is a cartographic instrument. The trajectory and road geometry give the page its character. The chrome is quiet ink on paper. The one place to be bold is the map's route ink: the predicted route is the only saturated line, and the primary button uses the same blue so that pressing it visibly "draws" that colour.

Things deliberately not used: cards for every statistic, eyebrow labels, gradient or glass, dark-by-default, violet, monospace as a costume (mono appears only on trip IDs and coordinates, which are data), and emoji or glyph icons. Icons are inline SVGs with a 1.5 px stroke.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--ink` | `#20262B` | primary text |
| `--ink-2` | `#56616B` | secondary text (5.9:1 on `--panel`) |
| `--paper` | `#EEF1F2` | app background and map backdrop when tiles fail |
| `--panel` | `#FFFFFF` | left panel, overlays |
| `--rule` | `#D3D9DD` | 1 px separators, control borders |
| `--route` | `#1F4FD1` | predicted route, primary action, focus ring, selection |
| `--gps` | `#C2410C` | raw GPS points (hollow circles) |
| `--network` | `#7D8891` | nearby road network (hairline) |
| `--alert` | `#B42318` | unmatched/no-candidate points (×), errors |
| `--dev-bg` / `--dev-ink` | `#FFF1C2` / `#6B4E00` | development-mode badge |
| `--ok` | `#1E7F4F` | ready status dot (always paired with text) |

**Type:** IBM Plex Sans (400/500/600) for everything, and IBM Plex Mono 400 for trip IDs, arc IDs and coordinates. Both are self-hosted via `@fontsource` (OFL) so the LAN demo needs no CDN. The scale is fixed rem at ratio about 1.2: 12 / 13 / 14 (base) / 16 / 19 / 23 px. `font-variant-numeric: tabular-nums` applies to all numbers. Sentence case throughout, with no all-caps labels.

**Spacing** is on a 4 px base: 4, 8, 12, 16, 24, 32. **Radii:** 6 px for controls, 8 px for map overlays, 0 for the panel (it is flush with the edges). **Elevation:** only map overlays get a shadow (`0 2px 8px rgb(32 38 43 / .14)`). The panel is separated by a 1 px rule.

## Controls

- **Primary button:** filled `--route`, white text, 40 px tall, full panel width. Its label always names the action: "Reconstruct route", then "Reconstructing…" (disabled, `aria-busy`), then back to "Reconstruct route".
- **Trip choice:** a native radio group styled as a 2-column grid of ID tiles (mono). The selected tile gets a `--route` border and tint, and arrow keys move between tiles (native radio behaviour).
- **Layer toggles:** native checkboxes, each with a swatch that encodes the layer's shape: a hollow dot for GPS, a hairline for network, a 4 px solid line for route, and × for unmatched.
- **Every interactive element** has a hover, `:focus-visible` (2 px `--route` outline, offset 2), active and disabled state.

## States (all designed, none generic)

| State | What the user sees |
|---|---|
| API unreachable | The panel says "Can't reach the PathSnap server at `<url>`" with a **Retry** button and a one-line LAN hint. Trips are not shown. The map keeps its basemap. |
| Model not ready | The service is connected, and the panel shows the server's `not_ready_reasons`. Reconstruct is disabled with the reason. |
| Evaluator data not configured | "Reserved evaluation trips are not configured on the server." Student-test trips are never offered as a substitute. |
| Initial | The trips are listed, none is selected, and the button says "Select a trip". The map shows the basemap at a neutral view. |
| Loading | The button is busy. The previous result is **cleared from the map and the panel** (no stale route is shown as current), and a text status says "Running pipeline for trip 00000056…". There is no fake progress. |
| Success | The layers are drawn and the map fits to the route bounds. Results show the model, metrics, timings, warnings and the request ID. |
| Request failed / timeout | The error code message from the envelope, the request ID, and **Try again**. |
| Diagnostic model | A persistent badge, "Diagnostic geometric model — not the trained classifier". |

## Motion

The base is 160 ms with `cubic-bezier(.2,.8,.2,1)` for hover, selection and the inspector opening. Map fit uses Leaflet's own pan animation and is disabled under `prefers-reduced-motion`. Route playback (optional, user-started) steps through observations in time order and pauses at decoder breaks. No entrance animations, no animated backgrounds.

## Map layer conventions

- Coordinates arrive as `[lon, lat]` and are converted to Leaflet `[lat, lon]` in one adapter (`ui/src/map/geo.ts`).
- Layers are drawn bottom to top: network, then predicted route, then GPS points, then unmatched markers, then the pinned observation.
- Each route piece is its own polyline. Gaps between pieces are never bridged.
- Rendering uses Leaflet's canvas renderer for points (up to about 19k).
- The basemap is OpenStreetMap tiles with attribution. If tiles fail (offline LAN), the `--paper` backdrop and all API geometry still render, and a small notice says the basemap is unavailable.

## Responsive

- **≥ 1024 px:** a 336 px panel on the left and the map filling the rest.
- **761–1023 px:** a 300 px panel.
- **≤ 760 px:** the map on top at 55vh, then the panel below it, scrollable. The layers overlay collapses to a toggle button.
- The checked sizes are 1440×900, 1366×768 and 390×844.
