"""Development-only Folium maps (mandatory deliverable). Owner: B.

Reads A's DevVisualisation handoff files (contracts/artifacts.schema.json#/$defs/DevVisualisation),
which hold train/student_test trips only, and writes one interactive HTML map per trip, with layers:
raw GPS, nearby road network, reference route (development data only) and each predicted
decoder variant. Each route piece is its own line; gaps are never bridged.

    python -m src.visualisation.folium.make_maps --input results/hmm/visualisation/<run_id> --output maps/<run_id>

View the maps over HTTP so the OpenStreetMap tile servers accept the requests (they block file://):

    python3 -m http.server 8001 --directory maps/<run_id>     # then open http://localhost:8001/

The output contains development reference geometry, so it must never be served by the API or
copied into ui/. Evaluator trips are refused.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import folium
import jsonschema

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "contracts" / "artifacts.schema.json").read_text("utf-8"))
_VALIDATOR = jsonschema.Draft202012Validator({**SCHEMA, "$ref": "#/$defs/DevVisualisation"})

# Same palette as DESIGN.md; variants get distinct colour AND dash pattern.
COLORS = {"gps": "#C2410C", "network": "#7D8891", "reference": "#1E7F4F"}
VARIANT_STYLE = {
    "hmm_viterbi": {"color": "#1F4FD1", "dash": None, "label": "Predicted route (classifier + HMM)"},
    "classifier_only": {"color": "#8A3FFC", "dash": "8 6", "label": "Predicted route (classifier only)"},
    "none": {"color": "#1F4FD1", "dash": "2 6", "label": "Predicted route (diagnostic)"},
}


def _latlngs(coords):
    return [(lat, lon) for lon, lat in coords]  # wire [lon, lat] -> folium (lat, lon)


def build_map(doc: dict) -> folium.Map:
    errors = sorted(_VALIDATOR.iter_errors(doc), key=str)
    if errors:
        raise ValueError(f"invalid DevVisualisation for {doc.get('trip_id')}: {errors[0].message}")
    if doc["partition"] not in ("train", "student_test"):
        raise ValueError("Folium development maps accept train/student_test trips only")

    pts = [(lat, lon) for _, lon, lat, _ in doc["gps"] if lat is not None and lon is not None]
    fmap = folium.Map(tiles=None, control_scale=True, prefer_canvas=True)
    # OSM tiles need a Referer: open maps through a local web server (see module docstring), not
    # file://. Without tiles the map still shows every PathSnap layer, including the road network.
    folium.TileLayer("OpenStreetMap", name="Basemap (OpenStreetMap)", control=True).add_to(fmap)

    net = folium.FeatureGroup(name="Road network (nearby)", show=True)
    for seg in doc["network"]:
        folium.PolyLine(_latlngs(seg["coordinates"]), color=COLORS["network"], weight=1, opacity=0.6,
                        tooltip=f"arc {seg['arc_id']}").add_to(net)
    net.add_to(fmap)

    gps = folium.FeatureGroup(name="Raw GPS points", show=True)
    for idx, lon, lat, t in doc["gps"]:
        if lat is None or lon is None:
            continue
        folium.CircleMarker((lat, lon), radius=2, color=COLORS["gps"], weight=1, opacity=0.7, fill=True, fill_color="#ffffff",
                            fill_opacity=0.8, tooltip=f"obs {idx}" + (f", t={t:.0f} s" if t is not None else "")).add_to(gps)
    gps.add_to(fmap)

    if doc["reference"] is not None:
        ref = folium.FeatureGroup(name="Reference route (development data)", show=True)
        for piece in doc["reference"]["pieces"]:
            folium.PolyLine(_latlngs(piece), color=COLORS["reference"], weight=7, opacity=0.45).add_to(ref)
        ref.add_to(fmap)

    for variant, pred in doc["predictions"].items():
        style = VARIANT_STYLE.get(variant, {"color": "#20262B", "dash": "4 4", "label": f"Predicted route ({variant})"})
        group = folium.FeatureGroup(name=style["label"], show=True)
        for piece in pred["pieces"]:
            folium.PolyLine(_latlngs(piece), color=style["color"], weight=3.5, opacity=0.9,
                            dash_array=style["dash"]).add_to(group)
        group.add_to(fmap)


    if pts:
        lats, lons = zip(*pts)
        fmap.fit_bounds([(min(lats), min(lons)), (max(lats), max(lons))], padding=(20, 20))
    folium.LayerControl(collapsed=False).add_to(fmap)
    fmap.get_root().html.add_child(folium.Element(_legend(doc)))
    return fmap


def _legend(doc: dict) -> str:
    rows = [("●", COLORS["gps"], "Raw GPS points"), ("—", COLORS["network"], "Road network (nearby)")]
    if doc["reference"] is not None:
        rows.append(("▬", COLORS["reference"], "Reference route (development data)"))
    for variant in doc["predictions"]:
        st = VARIANT_STYLE.get(variant, {"color": "#20262B", "label": variant})
        rows.append(("━", st["color"], st["label"]))
    items = "".join(f'<div><span style="color:{c};font-weight:700">{s}</span> {lbl}</div>' for s, c, lbl in rows)
    title = (f"PathSnap development map: trip {doc['trip_id']} ({doc['partition']}), "
             f"model {doc['model_version']}, run {doc['run_id']}")
    return ('<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:#fff;padding:8px 10px;'
            'border-radius:8px;box-shadow:0 2px 8px rgba(32,38,43,.14);font:13px/1.4 sans-serif;max-width:360px">'
            f'<div style="font-weight:600;margin-bottom:4px">{title}</div>{items}'
            '<div style="color:#56616b;margin-top:4px">Gaps between predicted pieces are real decoder breaks, not drawn over. '
            'Basemap tiles load only when served over http (python3 -m http.server).</div></div>')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", required=True, type=Path, help="directory of DevVisualisation <trip_id>.json files")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = sorted(args.input.glob("*.json"))
    if not files:
        raise SystemExit(f"no DevVisualisation files in {args.input}")
    for f in files:
        doc = json.loads(f.read_text("utf-8"))
        out = args.output / f"trip_{doc['trip_id']}_{doc['partition']}.html"
        build_map(doc).save(str(out))
        print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")


if __name__ == "__main__":
    main()
