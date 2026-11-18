# UI reference research

Researched 2026-11-18 by B. Scope: what the PathSnap evaluator screen needs, which is narrow. The evaluator picks one of ten trips, runs the reconstruction, looks at the predicted route against the raw GPS, reads a few honest metrics, and picks another trip. These products are references for that interaction only. PathSnap copies no code, branding or assets from them, and no dataset content was uploaded to any of them.

## Sources and what was actually observed

| Product | Accessed (2026-11-18) | How | Limits |
|---|---|---|---|
| Kepler.gl | [User guides index](https://docs.kepler.gl/docs/user-guides), [Trip layer](https://docs.kepler.gl/docs/user-guides/c-types-of-layers/k-trip), [Time playback](https://docs.kepler.gl/docs/user-guides/h-playback), [Interactions](https://docs.kepler.gl/docs/user-guides/g-interactions), and the live demo [kepler.gl/demo/nyctrips](https://kepler.gl/demo/nyctrips), opened in Chrome and screenshotted | Docs text plus one live screen | The split-map and layer-panel doc pages returned 404, so split-map behaviour comes from the index only. The screenshot is not committed because it is third-party UI. |
| Felt | [Dashboards platform page](https://felt.com/platform/dashboards) (fetch failed), [Tour the interface](https://help.felt.com/getting-started/tour-the-interface.md), [Dashboards components](https://help.felt.com/dashboards-and-apps/components.md), [Legend](https://help.felt.com/layers/legend.md) | Official help-centre text | No live dashboard opened, because dashboards need a Business plan. The observations below are documented UI, not inspected screens. |
| Fused Workbench | [Workbench overview](https://docs.fused.io/workbench/overview/), [Workbench intro](https://docs.fused.io/guide/getting-started/workbench-intro) | Docs text | Workbench needs an account, so it was not opened. The Map Builder and Canvas sub-pages returned 404. |
| deck.gl | Not needed. | — | Payloads are at most about 19k points plus a capped network context (≤6000 segments), which a Leaflet canvas renderer handles. One map renderer only. |

### Kepler.gl — observed live screen (nyctrips demo)

- About 80% of the width is map. A dark left panel about 260 px wide (at 1512 px) holds icon tabs for Layers, Filters, Interactions and Base map, then a dataset row, then a **Layers** list. Each layer row has a colour stripe, a name, the layer type in small text, an eye toggle, a kebab menu and a chevron to expand. Below the list sit "Layer blending" and "Map overlay blending" selects.
- A thin vertical icon toolbar on the right edge holds map settings, 3D, legend, draw, locale, compass and zoom +/−. A dismissible dataset description card sits top right. The scale bar is bottom left and the attribution bottom right.
- From the docs: the **Trip layer** animates `[lon, lat, alt, t]` LineStrings, with playback speed in a bottom control and a trail-length slider. **Playback** is a bottom timeline with a histogram, a speed menu (1×/2×/4×) and a Reset for a narrowed range. **Tooltips** show on hover and can be pinned by clicking, with a field-selection menu. Brushing and tooltip are mutually exclusive. A coordinate readout can follow the cursor.

### Felt — documented interface

- There are five parts. The **top toolbar** has the map name and actions. The **legend is the left panel**, with layers, swatches, an eye on hover to hide, a double-click to zoom to a layer, and Alt-click to show only that layer. A **detail panel on the right** opens on selection. A **table** sits at the bottom. The **map** is in the middle.
- Dashboard **components live under their layer in the legend**: Statistic (one number), Bar chart, Histogram, Line chart, Filter and Time series. "Update based on view" is **off by default**, so a statistic summarises the whole layer unless the user opts in. Each component reads one attribute.

### Fused Workbench — documented interface

- Canvas holds UDFs as draggable cards connected into workflows, with results beside them. Map View is a "GIS-style layer view" where each UDF is a layer you toggle like QGIS. The workbench also has a File Explorer and AI chat.

## Patterns PathSnap takes, adapted

| Pattern (source) | PathSnap decision |
|---|---|
| The map gets most of the area, with a single left panel (Kepler, Felt) | The map takes everything right of a single 336 px left panel. There is no right-hand rail, so the map keeps its width at 1366×768. |
| The legend is the layer control: swatch, name, eye toggle (Felt, Kepler) | One compact **Layers** block overlaid on the map's top-right corner. Each row is a real `<input type="checkbox">` with a swatch that also differs by **shape/dash** (dots, hairline, solid line, dashed gap marker), so colour is not the only cue. There is no separate legend. |
| Each statistic summarises one attribute and states its scope (Felt Statistic, "update based on view" off) | Metrics are a plain definition list, not cards. Each row gives a name, a value, an `n/denominator` and the policy, and it says "provisional" when the scoring policy is. Values never depend on the viewport. |
| Hover shows details and click pins them (Kepler tooltip pin) | Clicking a GPS point **pins** an observation inspector showing the index, time, status, arc ID, snapped distance and score with its kind. Hovering only highlights. Esc unpins it. |
| Time playback with explicit speed and Reset (Kepler) | Optional **route playback** after prediction walks the observed points in time order, with Play/Pause/Reset and 1×/4×/16× speeds. It stops at decoder breaks instead of drawing across them, and it is disabled under reduced motion until the user starts it. |
| Fit to layer by double-clicking it (Felt) | A **Fit route** button, plus **Reset view** to the trip's bounds. |
| Workspace layers mirror processing outputs (Fused) | The layer names map one-to-one to pipeline outputs: Raw GPS, Road network (nearby), Predicted route, Unmatched points. The panel shows the pipeline's own stage timings from the response. |

## Patterns rejected and why

- **Split maps and 3D** (Kepler): there is only one prediction to compare against its own GPS input. A second map would halve the map area for no evaluation benefit. A classifier-only vs HMM comparison belongs in the Folium development maps and the report, not on the evaluator screen.
- **Dark basemap and glow** (Kepler demo): it suits density-heatmap storytelling. Here the evaluator reads thin road lines in a lit room, so a light neutral basemap with dark ink is more legible.
- **Charts, histograms and filters** (Felt dashboards): each request has one trip and a handful of aggregate numbers. Charts would be ornamental, so the numbers are text with units.
- **Canvas, code editor, AI chat and file explorer** (Fused): these are out of scope for an evaluator tool and explicitly excluded by the brief.
- **Brushing and coordinate-follow** (Kepler): these are low value. The inspector shows coordinates for the pinned point instead.

## Layout sketches compared

```
A. Trip rail + map + inspector                B. One left panel + map (chosen)
┌────┬───────────────────────┬──────┐         ┌──────────┬────────────────────────────┐
│Trip│                       │Insp- │         │ PathSnap │                    [Layers]│
│list│          map          │ector │         │ ● dev    │                            │
│    │                       │metric│         │ Trips    │            map             │
│    │                       │      │         │ ▢▢▢▢▢    │                            │
│    │                       │      │         │[Reconstr]│                            │
│    │                       │      │         │ Results  │ ┌Observation #812┐         │
└────┴───────────────────────┴──────┘         │ metrics  │ └────────────────┘ [fit]   │
                                              └──────────┴────────────────────────────┘
```

**A** puts trips and results on opposite sides of the map. The evaluator's eye has to cross the map twice per trip, and at 1366 px two rails leave about 900 px of map. **B** follows the evaluator's sequence top to bottom in one column (mode → trip → Reconstruct → results), and the map stays the largest element. The observation inspector floats over the map's bottom-left only while a point is pinned. On small screens (≤ 760 px) B stacks as map (55vh) then panel, which A cannot do without hiding a rail. **B is implemented.**
