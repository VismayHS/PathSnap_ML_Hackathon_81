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
}: {
  prediction: Prediction | null;
  visible: LayerVisibility;
  selected: number | null;
  onSelect: (index: number | null) => void;
  fitToken: number;
}) {
  const map = useMap();
  const renderer = useMemo(() => L.canvas({ padding: 0.3, tolerance: 4 }), []);
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
          renderer, color: C.network, weight: 1, opacity: 0.7, interactive: false,
        }).addTo(g.network);
      }
      for (const f of prediction.route.features) {
        // Each piece is its own polyline: gaps between pieces are never bridged.
        L.polyline(lineToLatLngs(f.geometry.coordinates), {
          renderer, color: C.route, weight: 4, opacity: 0.9, lineCap: 'round', lineJoin: 'round', interactive: false,
        }).addTo(g.route);
      }
      for (const o of prediction.observations) {
        if (o.lon === null || o.lat === null) continue;
        const bad = o.status === 'no_candidate' || o.status === 'unmatched';
        const marker = bad
          ? L.circleMarker([o.lat, o.lon], { renderer, radius: 4, color: C.alert, weight: 2, fill: false, dashArray: '2 2' })
          : L.circleMarker([o.lat, o.lon], { renderer, radius: 2.5, color: C.gps, weight: 1.25, fill: true, fillColor: '#ffffff', fillOpacity: 1 });
        marker.on('click', () => onSelect(o.index));
        marker.addTo(bad ? g.unmatched : g.gps);
      }
    }
    groups.current = g;
    return () => {
      for (const layer of Object.values(g)) layer.remove();
      groups.current = null;
    };
  }, [prediction, renderer, onSelect]);

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
    if (!o || o.lon === null || o.lat === null) return;
    const group = L.layerGroup();
    if (o.snapped) {
      L.polyline([[o.lat, o.lon], toLatLng(o.snapped)], { color: C.ink, weight: 1.5, dashArray: '3 3', interactive: false }).addTo(group);
      L.circleMarker(toLatLng(o.snapped), { radius: 4, color: C.route, weight: 2, fillColor: C.route, fillOpacity: 1, interactive: false }).addTo(group);
    }
    L.circleMarker([o.lat, o.lon], { radius: 7, color: C.ink, weight: 2, fill: false, interactive: false }).addTo(group);
    group.addTo(map);
    selectedRef.current = group;
  }, [selected, prediction, map]);

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

export function observationAt(prediction: Prediction | null, index: number | null): Observation | null {
  if (!prediction || index === null) return null;
  return prediction.observations[index] ?? null;
}
