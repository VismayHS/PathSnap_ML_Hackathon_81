"""Development-only candidate/features/derived-target cache and grouped split manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from sklearn.model_selection import GroupKFold
from src.data_processing.raw import load_raw_trip
from src.data_processing.geometry import project_trip
from src.data_processing.candidates import SegmentIndex
from src.features.candidate import FEATURE_NAMES, FEATURE_VERSION, build_features
from src.evaluation.reference import read_reference
from src.evaluation.alignment import align_reference
from src.models.provenance import raw_development_fingerprint


def prepare(root, cache, evidence, config, fingerprint):
    if cache.exists() or evidence.exists():
        raise FileExistsError('Use fresh cache and evidence directories')
    actual_fingerprint = raw_development_fingerprint(root)
    if actual_fingerprint != fingerprint:
        raise ValueError('Raw permitted dataset differs from the expected fingerprint')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    cache.mkdir(parents=True); evidence.mkdir(parents=True)
    started = time.perf_counter(); records = []; sampling = {}
    for partition in ['train', 'student_test']:
        (cache/partition).mkdir()
        for directory in sorted((root/partition).iterdir()):
            if not directory.is_dir():
                continue
            tick = time.perf_counter(); trip = load_raw_trip(directory, partition); geo = project_trip(trip)
            policy = config['candidate_policy']
            candidates = SegmentIndex(geo).generate(trip, policy['radius_m'], policy['top_k'])
            features = build_features(trip, geo, candidates)
            # Reference access occurs only after the entire reference-free X/candidate construction.
            reference = read_reference(directory, len(trip.arcs))
            aligned = align_reference(trip, geo, reference)
            sizes = np.array([len(c.arc_ids) for c in candidates]); offsets = np.r_[0, np.cumsum(sizes)]
            row_observation = np.repeat(np.arange(len(trip.track)), sizes)
            arcs = np.concatenate([c.arc_ids for c in candidates])
            fractions = np.concatenate([c.fractions for c in candidates])
            distances = np.concatenate([c.distances for c in candidates])
            target = (arcs == aligned.arc_ids[row_observation]).astype(np.int8)
            eligible = np.flatnonzero(aligned.scorable)
            if partition == 'train':
                seed = config['seed'] + int(hashlib.sha256(trip.trip_id.encode()).hexdigest()[:8], 16)
                rng = np.random.default_rng(seed)
                selected = np.sort(rng.choice(eligible, min(len(eligible), config['train_observation_cap_per_trip']), replace=False))
                sampling[trip.trip_id] = selected.tolist()
            covered = np.array([aligned.arc_ids[i] in c.arc_ids for i, c in enumerate(candidates)]) & aligned.scorable
            path = cache/partition/f'{trip.trip_id}.npz'
            np.savez_compressed(path, X=features, y=target, row_observation=row_observation,
                candidate_arc_ids=arcs, fractions=fractions, distances=distances, offsets=offsets,
                labels=aligned.arc_ids, scorable=aligned.scorable, low_margin=aligned.low_margin,
                residuals_m=aligned.residuals_m, reference=reference, track=trip.track,
                arcs=trip.arcs, lengths=geo.length, xy=geo.xy, valid=trip.valid)
            record = dict(partition=partition, trip_id=trip.trip_id, observations=len(trip.track),
                scorable=int(aligned.scorable.sum()), unscorable=int((~aligned.scorable).sum()),
                covered=int(covered.sum()), candidate_misses=int((aligned.scorable & ~covered).sum()),
                low_margin_scorable=int((aligned.low_margin & aligned.scorable).sum()),
                candidate_rows=len(features), positive_candidate_rows=int(target[aligned.scorable[row_observation]].sum()),
                cache_path=path.relative_to(cache).as_posix(), cache_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                elapsed_s=time.perf_counter()-tick)
            records.append(record); print(json.dumps(record), flush=True)
    train_ids = [r['trip_id'] for r in records if r['partition'] == 'train']
    test_ids = [r['trip_id'] for r in records if r['partition'] == 'student_test']
    assert not set(train_ids) & set(test_ids)
    folds = []
    splitter = GroupKFold(n_splits=config['folds'], shuffle=True, random_state=config['seed'])
    for fold, (fit, valid) in enumerate(splitter.split(np.zeros((len(train_ids), 1)), groups=train_ids)):
        folds.append(dict(fold=fold, train=[train_ids[i] for i in fit], validation=[train_ids[i] for i in valid]))
    assert sorted(t for f in folds for t in f['validation']) == sorted(train_ids)
    metadata = dict(schema_version=1, source_git_sha=source, data_fingerprint=fingerprint,
        feature_version=FEATURE_VERSION, feature_names=list(FEATURE_NAMES), config=config,
        config_sha256=hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        records=records, folds=folds, student_test_ids=test_ids, elapsed_s=time.perf_counter()-started)
    text = json.dumps(metadata, indent=2, allow_nan=False)+'\n'
    (cache/'index.json').write_text(text); (evidence/'preparation.json').write_text(text)
    (evidence/'training-observation-sampling.json').write_text(json.dumps(sampling, indent=2)+'\n')
    (cache/'training-observation-sampling.json').write_text(json.dumps(sampling)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('configs/ml/experiments.json'))
    parser.add_argument('--eda-metadata', type=Path, default=Path('results/eda/initial-validation-v2/metadata.json'))
    args = parser.parse_args()
    prepare(args.data_root, args.cache, args.evidence, json.loads(args.config.read_text()),
            json.loads(args.eda_metadata.read_text())['data_fingerprint'])


if __name__ == '__main__':
    main()
