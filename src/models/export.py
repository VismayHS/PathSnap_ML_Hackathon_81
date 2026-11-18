"""Portable checksummed bundle publication; no mutable latest alias."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import joblib
from src.contracts import CONTRACT_VERSION
from src.features.candidate import FEATURE_NAMES, FEATURE_VERSION
from src.hmm.viterbi import DEFAULT_CONFIG


def export_bundle(output, estimator=None, model_name='geometric_diagnostic', run_id='diagnostic-v1',
                  data_fingerprint='no-fitted-data-reference-free-diagnostic', config=None):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Choose a new immutable bundle directory')
    config = {'radius_m': 100., 'top_k': 8, **(config or {})}
    output.mkdir(parents=True)
    trained = estimator is not None
    feature_schema = dict(version=FEATURE_VERSION, names=list(FEATURE_NAMES), dtype='float32')
    (output/'feature-schema.json').write_text(json.dumps(feature_schema, indent=2)+'\n')
    (output/'decoder-config.json').write_text(json.dumps(DEFAULT_CONFIG, indent=2)+'\n')
    files = [('feature_schema', 'feature-schema.json'), ('hmm_config', 'decoder-config.json')]
    if trained:
        joblib.dump(estimator, output/'classifier.joblib', compress=3)
        files.append(('classifier', 'classifier.joblib'))
    manifest = dict(manifest_version=1, contract_version=CONTRACT_VERSION, model_version=run_id,
        model_kind='trained' if trained else 'diagnostic', model_family=model_name,
        decoder='hmm_viterbi' if trained else 'classifier_only', run_id=run_id,
        source_git_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        config_sha256=hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        data_fingerprint=data_fingerprint, features=[dict(name=n, dtype='float32') for n in FEATURE_NAMES],
        score_kind='normalized_score', score_normalization='Clip binary relevance to 1e-12; divide by observation candidate sum; not calibrated confidence',
        crs=dict(input='EPSG:4326', coordinate_order='lon,lat', metric='WGS84 local azimuthal-equidistant centered on median valid GPS; always_xy'),
        graph_assumptions=dict(directed=True, reverse_edges_added=False, arc_ids='original trip-local zero-based rows',
                               zero_length_arcs='retained for topology, excluded from geometric candidates', geometry='straight node-to-node segments'),
        candidate_policy=dict(radius_m=config['radius_m'], top_k=config['top_k'], index='length-binned midpoint cKDTree with exact projection refinement'),
        decoder_config=DEFAULT_CONFIG,
        dependencies={p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'pyproj', 'scikit-learn', 'joblib']},
        files=[dict(role=role, path=name, bytes=(output/name).stat().st_size,
                    sha256=hashlib.sha256((output/name).read_bytes()).hexdigest()) for role, name in files])
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export_bundle(args.output)


if __name__ == '__main__':
    main()
