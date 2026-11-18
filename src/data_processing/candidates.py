"""Reference-free spatial candidates with complete segment broad-phase bounds."""
from dataclasses import dataclass
import numpy as np
from scipy.spatial import cKDTree
from .geometry import project_segments


@dataclass
class Candidates:
    arc_ids: np.ndarray
    distances: np.ndarray
    fractions: np.ndarray
    snapped: np.ndarray


def empty_candidates():
    return Candidates(np.empty(0, dtype=np.int64), np.empty(0), np.empty(0), np.empty((0, 2)))


class SegmentIndex:
    """Length-binned midpoint trees, exact refinement, deterministic distance/ID ties.

    A point within r of a segment lies within r+length/2 of its midpoint.
    Querying each bin with its largest half-length cannot omit an eligible arc.
    Zero-length arcs stay in the graph but have no candidate geometry.
    """
    def __init__(self, geometry):
        self.geometry = geometry
        ids = np.flatnonzero(np.isfinite(geometry.length) & (geometry.length > 0))
        buckets = np.floor(np.log2(np.maximum(geometry.length[ids] / 2, 1))).astype(int)
        self.trees = []
        for bucket in np.unique(buckets):
            selected = ids[buckets == bucket]
            midpoints = geometry.start[selected] + geometry.delta[selected] / 2
            self.trees.append((selected, cKDTree(midpoints), float(geometry.length[selected].max()/2)))

    def query(self, point, radius_m=100., top_k=8):
        if radius_m <= 0 or top_k < 1:
            raise ValueError("Candidate radius and top_k must be positive")
        if not np.isfinite(point).all():
            return empty_candidates()
        selected = []
        for ids, tree, half in self.trees:
            hits = tree.query_ball_point(point, radius_m + half + 1e-8, eps=0, workers=1)
            if hits:
                selected.append(ids[np.asarray(hits, dtype=int)])
        if not selected:
            return empty_candidates()
        ids = np.concatenate(selected)
        g = self.geometry
        distance, fraction, snapped = project_segments(point, g.start[ids], g.delta[ids], g.length[ids])
        keep = np.flatnonzero(distance <= radius_m)
        keep = keep[np.lexsort((ids[keep], distance[keep]))[:top_k]]
        return Candidates(ids[keep], distance[keep], fraction[keep], snapped[keep])

    def generate(self, trip, radius_m=100., top_k=8):
        return [self.query(point, radius_m, top_k) if valid else empty_candidates()
                for point, valid in zip(self.geometry.xy, trip.valid)]
