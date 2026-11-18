from types import SimpleNamespace
import numpy as np
from src.data_processing.candidates import SegmentIndex
from src.data_processing.geometry import project_segments


def test_index_matches_brute_force_and_keeps_original_ids():
    rng = np.random.default_rng(81)
    start = rng.normal(0, 1000, (1000, 2)); delta = rng.normal(0, 400, (1000, 2))
    start[0] = [0, 0]; delta[0] = [100000, 0]; delta[1] = 0
    length = np.linalg.norm(delta, axis=1)
    geo = SimpleNamespace(start=start, delta=delta, length=length)
    index = SegmentIndex(geo)
    for point in [np.array([50000, 1]), *rng.normal(0, 1000, (100, 2))]:
        ids = np.flatnonzero(length > 0)
        dist, _, _ = project_segments(point, start[ids], delta[ids], length[ids])
        good = dist <= 100
        expected = ids[good][np.lexsort((ids[good], dist[good]))[:8]]
        assert index.query(point).arc_ids.tolist() == expected.tolist()
    assert index.query([50000, 1]).arc_ids.tolist() == [0]
    assert not len(index.query([np.nan, 1]).arc_ids)


def test_reverse_arcs_remain_distinct_and_ties_are_stable():
    geo = SimpleNamespace(start=np.array([[0., 0.], [10., 0.]]),
                          delta=np.array([[10., 0.], [-10., 0.]]), length=np.array([10., 10.]))
    result = SegmentIndex(geo).query(np.array([5., 2.]))
    assert result.arc_ids.tolist() == [0, 1]
    assert result.fractions.tolist() == [.5, .5]
    assert result.distances.tolist() == [2., 2.]
