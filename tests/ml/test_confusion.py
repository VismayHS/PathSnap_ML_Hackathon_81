import numpy as np
from src.evaluation.confusion import sparse_confusion


def test_sparse_local_classes_preserve_misses_without_unscorable_rows():
    r=sparse_confusion(np.array([3,3,5,8]),np.array([True,True,True,False]),np.array([3,-1,3,8]))
    assert r=={'entries':[[3,-1,1],[3,3,1],[5,3,1]],'scorable_observations':3,'correct':1}
