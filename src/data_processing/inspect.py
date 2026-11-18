"""Reproducible development-only EDA. Run: python -m src.data_processing.inspect --help."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from src.data_processing.raw import load_raw_trip, valid_coordinates
from src.data_processing.geometry import project_trip
from src.evaluation.reference import read_reference


def inspect(root: Path, output: Path):
    if output.exists():
        raise FileExistsError("Use a fresh output directory to preserve immutable EDA evidence")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    source_dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src", "configs/ml"], text=True).strip())
    rows, fingerprints = [], {}
    started = time.perf_counter()
    ids = {}
    for partition in ("train", "student_test"):
        ids[partition] = sorted(p.name for p in (root / partition).iterdir() if p.is_dir())
        for tid in ids[partition]:
            directory = root / partition / tid
            trip = load_raw_trip(directory, partition)
            geo = project_trip(trip)
            ref = read_reference(directory, len(trip.arcs))
            sizes = {}
            for suffix in ("track", "nodes", "arcs", "route"):
                path = directory / f"{tid}.{suffix}"
                data = path.read_bytes()
                fingerprints[path.relative_to(root).as_posix()] = hashlib.sha256(data).hexdigest()
                sizes[f"{suffix}_bytes"] = len(data)
            a, t = trip.arcs, trip.track
            graph = coo_matrix((np.ones(len(a)), (a[:, 0], a[:, 1])), shape=(len(trip.nodes),)*2).tocsr()
            weak = connected_components(graph, directed=True, connection="weak", return_labels=False)
            strong = connected_components(graph, directed=True, connection="strong", return_labels=False)
            pairs = set(map(tuple, a))
            reverse_count = sum((v, u) in pairs for u, v in a)
            dt = np.diff(t[:, 2])
            finite_dt = dt[np.isfinite(dt)]
            row = dict(partition=partition, trip_id=tid, observations=len(t), valid_observations=int(trip.valid.sum()),
                       invalid_coordinates=int((~valid_coordinates(t[:, :2])).sum()),
                       invalid_node_coordinates=int((~valid_coordinates(trip.nodes)).sum()),
                       nonfinite_values=int((~np.isfinite(t)).sum()+(~np.isfinite(trip.nodes)).sum()),
                       nodes=len(trip.nodes), arcs=len(a), zero_length_arcs=int((geo.length == 0).sum()),
                       weak_components=int(weak), strong_components=int(strong),
                       isolated_nodes=int(((graph.getnnz(0)+graph.getnnz(1)) == 0).sum()),
                       arcs_with_reverse=reverse_count, reference_occurrences=len(ref),
                       repeated_reference_occurrences=len(ref)-len(set(ref)),
                       reference_discontinuities=int((a[ref[:-1], 1] != a[ref[1:], 0]).sum()),
                       timestamp_steps=len(dt), exact_one_second_steps=int((dt == 1).sum()),
                       near_one_second_steps=int(np.isclose(dt, 1, rtol=0, atol=1e-6).sum()),
                       nonpositive_steps=int((dt <= 0).sum()), max_gap_s=float(finite_dt.max()) if len(finite_dt) else None,
                       median_step_s=float(np.median(finite_dt)) if len(finite_dt) else None,
                       consecutive_duplicate_coordinates=int(np.all(np.diff(t[:, :2], axis=0) == 0, axis=1).sum()),
                       min_lon=float(np.nanmin(t[:, 0])), min_lat=float(np.nanmin(t[:, 1])),
                       max_lon=float(np.nanmax(t[:, 0])), max_lat=float(np.nanmax(t[:, 1])), **sizes)
            rows.append(row)
            print(f"{partition}/{tid}: {len(t)} observations, {len(a)} directed arcs", flush=True)
    if set(ids['train']) & set(ids['student_test']):
        raise ValueError("Trip IDs overlap development partitions")
    summaries = {}
    sum_columns = ["observations", "valid_observations", "invalid_coordinates", "invalid_node_coordinates",
                   "nonfinite_values", "nodes", "arcs", "zero_length_arcs", "isolated_nodes",
                   "reference_occurrences", "repeated_reference_occurrences", "reference_discontinuities",
                   "timestamp_steps", "exact_one_second_steps", "near_one_second_steps", "nonpositive_steps",
                   "consecutive_duplicate_coordinates"]
    for part in ids:
        subset = [r for r in rows if r['partition'] == part]
        totals = {key: sum(r[key] for r in subset) for key in sum_columns}
        totals.update(trips=len(subset), files=4*len(subset), max_gap_s=max(r['max_gap_s'] for r in subset),
                      exact_one_second_fraction=totals['exact_one_second_steps']/totals['timestamp_steps'],
                      near_one_second_fraction=totals['near_one_second_steps']/totals['timestamp_steps'],
                      trips_with_reference_discontinuities=sum(r['reference_discontinuities'] > 0 for r in subset))
        summaries[part] = totals
    fingerprint = hashlib.sha256(json.dumps(fingerprints, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    metadata = dict(schema_version=1, source_git_sha=revision, source_dirty=source_dirty,
                    run_id=output.name, data_fingerprint=fingerprint,
                    fingerprint_definition="SHA256 of sorted compact JSON mapping dataset-relative paths to file SHA256",
                    partitions=ids, summaries=summaries, elapsed_s=time.perf_counter()-started,
                    dependencies={p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'pyproj']},
                    assumptions={'geometry': 'WGS84 local azimuthal-equidistant, always_xy; straight segments between supplied nodes',
                                 'reference': 'Traversal sequence, not row-aligned labels; repeated occurrences preserved',
                                 'zero_length': 'Retain graph topology and IDs; exclude from geometric candidates',
                                 'cleaning': 'Preserve rows with validity/reason masks; reject malformed graph topology',
                                 'evaluator': 'No evaluator path enumerated or read'})
    output.mkdir(parents=True)
    with (output / 'trips.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2, allow_nan=False)+'\n')
    (output / 'file-hashes.json').write_text(json.dumps(fingerprints, indent=2, sort_keys=True)+'\n')
    print(json.dumps(summaries, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inspect(args.data_root.resolve(), args.output)


if __name__ == '__main__':
    main()
