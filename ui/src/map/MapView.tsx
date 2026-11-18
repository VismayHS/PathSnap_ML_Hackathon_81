import L from 'leaflet';
import { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import type { Observation, Prediction } from '../lib/api';
import { boundsToLatLng, lineToLatLngs, toLatLng } from './geo';

export type LayerKey = 'network' | 'route' | 'gps' | 'unmatched';
export type LayerVisibility = Record<LayerKey, boolean>;

// Values mirror DESIGN.md tokens; Leaflet canvas styles cannot read CSS variables.
const C = { route: '#1F4FD1', gps: '#C2410C', network: '#7D8891', alert: '#B42318', ink: '#20262B' };
const DEFAULT_VIEW: L.LatLngExpression = [49.87, 8.65];

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function PredictionLayers({
  prediction,
  visible,
  selected,
  onSelect,
  fitToken,
  playhead,
}: {
  prediction: Prediction | null;
  visible: LayerVisibility;
  selected: number | null;
  onSelect: (index: number | null) => void;
  fitToken: number;
  playhead: number | null;
}) {
  const map = useMap();
  // One pane + canvas per layer so stacking is explicit: the route sits above the GPS points
  // (readable at overview zoom) but ignores the pointer, so points underneath stay clickable.
  const r = useMemo(() => {
    const panes: [LayerKey | 'selected', number, boolean][] = [
      ['network', 400, false], ['gps', 410, true], ['route', 420, false], ['unmatched', 430, true], ['selected', 440, false],
    ];
    const out = {} as Record<LayerKey | 'selected', L.Canvas>;
    for (const [name, z, interactive] of panes) {
      const pane = map.getPane(`ps-${name}`) ?? map.createPane(`ps-${name}`);
      pane.style.zIndex = String(z);
      pane.style.pointerEvents = interactive ? 'auto' : 'none';
      out[name] = L.canvas({ pane: `ps-${name}`, padding: 0.3, tolerance: 4 });
    }
    return out;
  }, [map]);
  const groups = useRef<Record<LayerKey, L.LayerGroup> | null>(null);
  const selectedRef = useRef<L.Layer | null>(null);

  // Build layers once per prediction (heavy), toggle visibility separately (cheap).
  useEffect(() => {
    const g: Record<LayerKey, L.LayerGroup> = {
      network: L.layerGroup(),
      route: L.layerGroup(),
      gps: L.layerGroup(),
      unmatched: L.layerGroup(),
    };
    if (prediction) {
      for (const f of prediction.network.features) {
        L.polyline(lineToLatLngs(f.geometry.coordinates), {
          renderer: r.network, color: C.network, weight: 1, opacity: 0.7, interactive: false,
        }).addTo(g.network);
      }
      for (const f of prediction.route.features) {
        // Each piece is its own polyline: gaps between pieces are never bridged.
        L.polyline(lineToLatLngs(f.geometry.coordinates), {
          renderer: r.route, color: C.route, weight: 4, opacity: 0.85, lineCap: 'round', lineJoin: 'round', interactive: false,
        }).addTo(g.route);
      }
      for (const o of prediction.observations) {
        if (!isPlottable(o)) continue; // non-finite / out-of-range coordinates are never sent to Leaflet
        let marker: L.CircleMarker;
        if (o.status === 'matched') {
          marker = L.circleMarker([o.lat!, o.lon!], { renderer: r.gps, radius: 2.5, color: C.gps, weight: 1, opacity: 0.75, fill: true, fillColor: '#ffffff', fillOpacity: 0.9 });
        } else if (o.status === 'invalid') {
          // removed by cleaning (e.g. bad timestamp) but has a usable position: grey, distinct from unmatched
          marker = L.circleMarker([o.lat!, o.lon!], { renderer: r.unmatched, radius: 3, color: C.network, weight: 1.5, fill: false, dashArray: '1 2' });
        } else {
          marker = L.circleMarker([o.lat!, o.lon!], { renderer: r.unmatched, radius: 4, color: C.alert, weight: 2, fill: false, dashArray: '2 2' });
        }
        marker.on('click', () => onSelect(o.index));
        marker.addTo(o.status === 'matched' ? g.gps : g.unmatched);
      }
    }
    groups.current = g;
    return () => {
      for (const layer of Object.values(g)) layer.remove();
      groups.current = null;
    };
  }, [prediction, r, onSelect]);

  useEffect(() => {
    const g = groups.current;
    if (!g) return;
    (['network', 'route', 'gps', 'unmatched'] as LayerKey[]).forEach((k) => {
      if (visible[k]) g[k].addTo(map);
      else g[k].remove();
    });
  }, [visible, map, prediction]);

  useEffect(() => {
    if (!prediction) return;
    map.fitBounds(boundsToLatLng(prediction.bounds), { padding: [32, 32], animate: !reducedMotion() });
  }, [prediction, fitToken, map]);

  useEffect(() => {
    selectedRef.current?.remove();
    selectedRef.current = null;
    if (!prediction || selected === null) return;
    const o = prediction.observations[selected];
    if (!o || !isPlottable(o)) return;
    const group = L.layerGroup();
    if (o.snapped) {
      L.polyline([[o.lat!, o.lon!], toLatLng(o.snapped)], { renderer: r.selected, color: C.ink, weight: 1.5, dashArray: '3 3', interactive: false }).addTo(group);
      L.circleMarker(toLatLng(o.snapped), { renderer: r.selected, radius: 4, color: C.route, weight: 2, fillColor: C.route, fillOpacity: 1, interactive: false }).addTo(group);
    }
    L.circleMarker([o.lat!, o.lon!], { renderer: r.selected, radius: 7, color: C.ink, weight: 2, fill: false, interactive: false }).addTo(group);
    group.addTo(map);
    selectedRef.current = group;
  }, [selected, prediction, map, r]);

  // Playback marker: moves between observed positions only (no interpolation across gaps).
  const headRef = useRef<L.CircleMarker | null>(null);
  useEffect(() => {
    const o = prediction && playhead !== null ? prediction.observations[playhead] : null;
    if (!o || !isPlottable(o)) {
      headRef.current?.remove();
      headRef.current = null;
      return;
    }
    const at: L.LatLngExpression = o.snapped ? toLatLng(o.snapped) : [o.lat!, o.lon!];
    if (!headRef.current) {
      headRef.current = L.circleMarker(at, {
        renderer: r.selected, radius: 7, color: '#ffffff', weight: 2.5, fillColor: C.route, fillOpacity: 1, interactive: false,
      }).addTo(map);
    } else headRef.current.setLatLng(at);
  }, [playhead, prediction, map, r]);

  // Leaflet needs a size recalculation when the panel layout changes.
  useEffect(() => {
    const ro = new ResizeObserver(() => map.invalidateSize({ animate: false }));
    ro.observe(map.getContainer());
    return () => ro.disconnect();
  }, [map]);

  return null;
}

function TileStatus({ onError }: { onError: () => void }) {
  return (
    <TileLayer
      url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      maxZoom={19}
      eventHandlers={{ tileerror: onError }}
    />
  );
}

export function MapView(props: {
  prediction: Prediction | null;
  visible: LayerVisibility;
  selected: number | null;
  onSelect: (index: number | null) => void;
  fitToken: number;
  playhead: number | null;
  children?: React.ReactNode;
}) {
  const [tilesFailed, setTilesFailed] = useState(false);
  return (
    <div className="map-shell">
      <MapContainer center={DEFAULT_VIEW} zoom={12} className="map" preferCanvas zoomControl attributionControl>
        <TileStatus onError={() => setTilesFailed(true)} />
        <PredictionLayers {...props} />
      </MapContainer>
      {tilesFailed && (
        <p className="map-note" role="status">
          Basemap tiles unavailable on this network. Road network and route still come from the server.
        </p>
      )}
      {props.children}
    </div>
  );
}

export function isPlottable(o: Observation): boolean {
  return (
    o.lon !== null && o.lat !== null && Number.isFinite(o.lon) && Number.isFinite(o.lat) &&
    Math.abs(o.lon) <= 180 && Math.abs(o.lat) <= 90
  );
}

export function observationAt(prediction: Prediction | null, index: number | null): Observation | null {
  if (!prediction || index === null) return null;
  return prediction.observations[index] ?? null;
}
