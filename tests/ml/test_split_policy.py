import numpy as np
from sklearn.model_selection import GroupKFold


def test_trip_group_split_keeps_all_candidate_rows_together():
    groups = np.repeat(['00000001', '00000002', '00000003', '00000004', '00000005'], [4, 8, 3, 7, 6])
    seen = []
    for train, validation in GroupKFold(n_splits=5, shuffle=True, random_state=81).split(np.zeros((len(groups), 1)), groups=groups):
        assert not set(groups[train]) & set(groups[validation])
        for group in set(groups[validation]):
            assert np.array_equal(np.flatnonzero(groups == group), validation[groups[validation] == group])
        seen += list(set(groups[validation]))
    assert sorted(seen) == sorted(set(groups))
