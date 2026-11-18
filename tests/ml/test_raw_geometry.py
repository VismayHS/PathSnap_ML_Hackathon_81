from pathlib import Path
import numpy as np
import pytest
from src.data_processing.raw import load_raw_trip
from src.data_processing.geometry import project_trip


def make_trip(tmp_path):
    p = tmp_path / "00000001"
    p.mkdir()
    (p / "00000001.track").write_text("10 50 1\nnan 50 2\n10.0001 50 1\n10.0002 50 3\n")
    (p / "00000001.nodes").write_text("10 50\n10.001 50\n10.001 50\n")
    (p / "00000001.arcs").write_text("0 1\n1 0\n1 2\n")
    return p


def test_reference_free_load_preserves_rows_and_zero_arcs(tmp_path):
    trip = load_raw_trip(make_trip(tmp_path), "train")
    assert trip.trip_id == "00000001"
    assert trip.valid.tolist() == [True, False, False, True]
    assert trip.arcs.tolist() == [[0, 1], [1, 0], [1, 2]]
    # No .route exists: prediction inputs must still load.
    geo = project_trip(trip)
    assert 70 < geo.length[0] < 73
    assert geo.length[2] == 0
    lon, lat = geo.inverse.transform(*geo.nodes[1])
    assert lon == pytest.approx(10.001, abs=1e-9)
    assert lat == pytest.approx(50, abs=1e-9)


def test_fractional_graph_ids_rejected(tmp_path):
    p = make_trip(tmp_path)
    (p / "00000001.arcs").write_text("0.5 1\n")
    with pytest.raises(ValueError, match="integers"):
        load_raw_trip(p, "train")
