"""Local WGS84 azimuthal-equidistant metre geometry, preserving graph row IDs."""
from dataclasses import dataclass
import numpy as np
from pyproj import CRS, Transformer
from .raw import RawTrip, valid_coordinates


@dataclass
class MetricGeometry:
    xy: np.ndarray
    nodes: np.ndarray
    start: np.ndarray
    delta: np.ndarray
    length: np.ndarray
    forward: Transformer
    inverse: Transformer
    crs: str


def project_trip(trip: RawTrip) -> MetricGeometry:
    valid = valid_coordinates(trip.track[:, :2])
    if not valid.any():
        raise ValueError("No valid coordinates for local projection")
    lon, lat = np.median(trip.track[valid, :2], axis=0)
    local = f"+proj=aeqd +lat_0={lat:.12f} +lon_0={lon:.12f} +datum=WGS84 +units=m +no_defs"
    crs = CRS.from_proj4(local)
    forward = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    xy = np.full((len(trip.track), 2), np.nan)
    xy[valid] = np.column_stack(forward.transform(*trip.track[valid, :2].T))
    nv = valid_coordinates(trip.nodes)
    nodes = np.full_like(trip.nodes, np.nan)
    nodes[nv] = np.column_stack(forward.transform(*trip.nodes[nv].T))
    start = nodes[trip.arcs[:, 0]]
    delta = nodes[trip.arcs[:, 1]] - start
    return MetricGeometry(xy, nodes, start, delta, np.linalg.norm(delta, axis=1), forward, inverse, local)


def project_segments(point, start, delta, length):
    """Exact planar refinement; candidates must have strictly positive finite length."""
    fraction = np.clip(np.sum((point - start) * delta, axis=1) / length**2, 0, 1)
    snapped = start + fraction[:, None] * delta
    return np.linalg.norm(point - snapped, axis=1), fraction, snapped
