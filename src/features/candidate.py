"""Transferable candidate relevance features; no graph-local ID or reference features."""
import numpy as np

FEATURE_NAMES = ('distance_m', 'log_distance', 'heading_cosine', 'heading_valid',
                 'log_length', 'projection_fraction', 'speed_mps', 'delta_t_s',
                 'distance_excess_over_nearest_m')
FEATURE_VERSION = 'candidate-geometry-v1'


def motion(trip, geometry):
    count = len(trip.track)
    direction = np.zeros((count, 2)); speed = np.zeros(count)
    elapsed = np.zeros(count); heading_valid = np.zeros(count)
    indices = np.flatnonzero(trip.valid)
    for rank, i in enumerate(indices):
        lo = indices[max(0, rank-2)]; hi = indices[min(len(indices)-1, rank+2)]
        dt = trip.track[hi, 2] - trip.track[lo, 2]
        displacement = geometry.xy[hi] - geometry.xy[lo]
        length = np.linalg.norm(displacement)
        if dt > 0:
            elapsed[i] = min(dt, 300)
            speed[i] = min(length/dt, 100)
        if 0 < dt <= 30 and length >= 3 and length/dt <= 80:
            direction[i] = displacement/length
            heading_valid[i] = 1
    return direction, speed, elapsed, heading_valid


def build_features(trip, geometry, candidates):
    direction, speed, elapsed, valid = motion(trip, geometry)
    blocks = []
    for i, c in enumerate(candidates):
        k = len(c.arc_ids)
        if not k:
            continue
        lengths = geometry.length[c.arc_ids]
        heading = geometry.delta[c.arc_ids] / lengths[:, None]
        cosine = np.clip(heading @ direction[i], -1, 1)
        blocks.append(np.column_stack((c.distances, np.log1p(c.distances), cosine,
                      np.full(k, valid[i]), np.log1p(lengths), c.fractions,
                      np.full(k, speed[i]), np.full(k, elapsed[i]), c.distances-c.distances.min())))
    return np.concatenate(blocks).astype(np.float32) if blocks else np.empty((0, len(FEATURE_NAMES)), dtype=np.float32)
