// The single place where wire [lon, lat] becomes Leaflet [lat, lon].
import type { LatLngBoundsExpression, LatLngExpression } from 'leaflet';
import type { LonLat } from '../lib/api';

export const toLatLng = ([lon, lat]: LonLat): LatLngExpression => [lat, lon];

export const lineToLatLngs = (coords: LonLat[]): LatLngExpression[] => coords.map(toLatLng);

/** Wire bounds are [west, south, east, north]. */
export const boundsToLatLng = ([w, s, e, n]: [number, number, number, number]): LatLngBoundsExpression => [
  [s, w],
  [n, e],
];
