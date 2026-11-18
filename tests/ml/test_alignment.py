from types import SimpleNamespace
import numpy as np
from src.evaluation.alignment import align_reference


def test_alignment_preserves_ordered_repeated_occurrences():
    # 0 -> 1 -> 0 traversal: arc 0 occurs twice, never zip route rows with GPS rows.
    trip = SimpleNamespace(track=np.array([[0, 0, i] for i in range(6)]), valid=np.ones(6, dtype=bool))
    geo = SimpleNamespace(xy=np.array([[2., 0], [8., 0], [8., 0], [2., 0], [2., 0], [8., 0]]),
                          start=np.array([[0., 0], [10., 0]]), delta=np.array([[10., 0], [-10., 0]]),
                          length=np.array([10., 10.]))
    result = align_reference(trip, geo, np.array([0, 1, 0]))
    assert len(result.arc_ids) == 6
    assert np.all(np.diff(result.occurrences) >= 0)
    assert result.scorable.all()
    assert np.array_equal(result.arc_ids, np.array([0, 1, 0])[result.occurrences])
