"""Reference-free public facade shared by CLI and API. No .route access here."""
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import numpy as np
from src.contracts import (BundleInfo, DataNotConfiguredError, InvalidTripIdError,
    ModelNotReadyError, NetworkSegment, ObservationPrediction, PipelineWarning,
    PredictionResult, RouteArc, RoutePiece, TripDataUnavailableError, TripInput,
    UnknownTripError, CONTRACT_VERSION, validate_trip_id_syntax)
from src.data_processing.raw import load_raw_trip
from src.data_processing.geometry import project_trip
from src.data_processing.candidates import SegmentIndex
from src.features.candidate import FEATURE_NAMES, build_features
from src.hmm.graph import RoadGraph
from src.hmm.viterbi import DEFAULT_CONFIG, decode, normalized_scores


@dataclass
class ModelBundle:
    info: BundleInfo
    manifest: dict
    estimator: object = None


def partition_root(mode, settings):
    if mode == 'development':
        root = Path(settings.data_root)/'student_test'
    elif mode == 'evaluator' and settings.evaluator_root is not None:
        root = Path(settings.evaluator_root)
    else:
        raise DataNotConfiguredError('The selected data partition is not configured')
    if not root.is_dir():
        raise DataNotConfiguredError('The selected data partition is not configured')
    return root.resolve()


def list_trip_ids(mode, settings):
    root = partition_root(mode, settings)
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.is_symlink()
                  and p.resolve().parent == root and _valid_name(p.name))


def _valid_name(name):
    try:
        validate_trip_id_syntax(name)
        return True
    except InvalidTripIdError:
        return False


def load_prediction_input(trip_id, mode, settings):
    validate_trip_id_syntax(trip_id)
    root = partition_root(mode, settings)
    if trip_id not in list_trip_ids(mode, settings):
        raise UnknownTripError('Unknown trip in the selected partition')
    directory = root/trip_id
    for suffix in ('track', 'nodes', 'arcs'):
        path = directory/f'{trip_id}.{suffix}'
        if path.is_symlink() or path.resolve().parent != directory:
            raise TripDataUnavailableError('Trip input is unavailable')
    started = time.perf_counter()
    try:
        raw = load_raw_trip(directory, 'student_test' if mode == 'development' else 'evaluator_test')
        if not raw.valid.any():
            raise ValueError('No valid observations')
    except (OSError, ValueError, IndexError) as exc:
        raise TripDataUnavailableError('Trip input is missing, invalid or has no valid observations', detail=str(exc)) from exc
    return TripInput(trip_id, mode, raw.partition, len(raw.track), len(raw.nodes), len(raw.arcs),
                     payload={'raw': raw, 'load_input_ms': (time.perf_counter()-started)*1000})


def load_model_bundle(settings):
    from jsonschema import Draft202012Validator
    import joblib
    root = Path(settings.bundle_root).resolve()
    try:
        data = (root/'manifest.json').read_bytes()
        manifest = json.loads(data)
        schema = json.loads((Path(__file__).resolve().parent.parent/'contracts/artifacts.schema.json').read_text())
        Draft202012Validator({**schema, '$ref': '#/$defs/BundleManifest'}).validate(manifest)
        if manifest['contract_version'] != CONTRACT_VERSION:
            raise ValueError('Incompatible contract version')
        expected = [f['name'] for f in manifest['features']]
        if expected != list(FEATURE_NAMES):
            raise ValueError('Incompatible ordered feature schema')
        paths = {}
        for entry in manifest['files']:
            path = (root/entry['path']).resolve()
            if not path.is_relative_to(root) or path == root:
                raise ValueError('Artifact path escapes bundle')
            content = path.read_bytes()
            if len(content) != entry['bytes'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
                raise ValueError('Artifact checksum or length mismatch')
            paths[entry['role']] = path
        policy = manifest['candidate_policy']
        if not 0 < policy['radius_m'] <= 1000 or not 1 <= policy['top_k'] <= 32:
            raise ValueError('Unbounded candidate policy')
        for package, version in manifest['dependencies'].items():
            if importlib.metadata.version(package) != version:
                raise ValueError(f'Incompatible dependency: {package}')
        estimator = None
        if manifest['model_kind'] == 'trained':
            # Only locally produced, checksummed bundles are trusted: joblib is not an untrusted upload format.
            estimator = joblib.load(paths['classifier'])
            if estimator.n_features_in_ != len(FEATURE_NAMES):
                raise ValueError('Estimator feature count mismatch')
        info = BundleInfo(manifest['model_version'], manifest['model_kind'], manifest['model_family'],
                          manifest['decoder'], manifest['run_id'], hashlib.sha256(data).hexdigest())
        return ModelBundle(info, manifest, estimator)
    except Exception as exc:
        if isinstance(exc, ModelNotReadyError):
            raise
        raise ModelNotReadyError('Model assets are missing or incompatible', detail=str(exc)) from exc


def predict_trip(trip_input, bundle, options):
    started = time.perf_counter(); timings = {}
    if bundle.info.model_kind == 'diagnostic' and trip_input.mode != 'development':
        raise ModelNotReadyError('A diagnostic model is available only in development mode')
    raw = trip_input.payload['raw']
    timings['load_input'] = trip_input.payload.get('load_input_ms', 0.)
    stage = time.perf_counter(); geometry = project_trip(raw)
    timings['clean'] = (time.perf_counter()-stage)*1000
    stage = time.perf_counter(); index = SegmentIndex(geometry)
    policy = bundle.manifest['candidate_policy']
    candidates = index.generate(raw, policy['radius_m'], policy['top_k'])
    timings['candidates'] = (time.perf_counter()-stage)*1000
    stage = time.perf_counter(); features = build_features(raw, geometry, candidates)
    timings['features'] = (time.perf_counter()-stage)*1000
    stage = time.perf_counter()
    if bundle.estimator is None:
        relevance = None
    elif len(features):
        classes = list(bundle.estimator.classes_)
        relevance = bundle.estimator.predict_proba(features)[:, classes.index(1)]
    else:
        relevance = np.empty(0)
    probabilities = []; offset = 0
    for c in candidates:
        k = len(c.arc_ids)
        values = np.exp(-.5*(c.distances/20.)**2) if relevance is None else relevance[offset:offset+k]
        probabilities.append(normalized_scores(values)); offset += k
    timings['model'] = (time.perf_counter()-stage)*1000
    stage = time.perf_counter(); graph = RoadGraph(raw.arcs, geometry.length)
    cfg = {**DEFAULT_CONFIG, **bundle.manifest['decoder_config']}
    effective_decoder = 'classifier_only' if bundle.info.model_kind == 'diagnostic' else options.decoder
    if effective_decoder == 'hmm_viterbi':
        result = decode(raw, geometry, candidates, probabilities, graph, cfg)
        choices, segments, breaks = result.choices, result.segments, result.breaks
    else:
        choices = np.array([int(np.argmax(p)) if len(p) else -1 for p in probabilities])
        segments = np.full(len(choices), -1, dtype=int); breaks = []
    timings['decode'] = (time.perf_counter()-stage)*1000
    stage = time.perf_counter()
    route, segment_ids, geometry_breaks = _route(raw, geometry, candidates, choices, segments, graph, cfg)
    warnings = []
    for i, reason in [*breaks, *geometry_breaks]:
        warnings.append(PipelineWarning('gps_gap' if reason == 'gps_gap' else 'decoder_break', reason, (int(i),)))
    if bundle.info.model_kind == 'diagnostic':
        warnings.append(PipelineWarning('diagnostic_model', 'Reference-free geometric diagnostic; no trained classifier'))
    invalid = tuple(map(int, np.flatnonzero(~raw.valid)))
    missing = tuple(i for i, c in enumerate(candidates) if raw.valid[i] and not len(c.arc_ids))
    if invalid:
        warnings.append(PipelineWarning('invalid_observations', f'{len(invalid)} observations invalid; original indices retained', invalid))
    if missing:
        warnings.append(PipelineWarning('no_candidates', f'{len(missing)} observations outside candidate policy', missing))
    observations = []
    for i, c in enumerate(candidates):
        selected = int(choices[i]); arc_id = None; lon = lat = distance = score = None
        status = 'invalid' if not raw.valid[i] else 'no_candidate' if not len(c.arc_ids) else 'unmatched'
        reason = raw.reasons[i] if status == 'invalid' else 'outside_candidate_radius' if status == 'no_candidate' else 'no_decoded_state'
        if selected >= 0:
            arc_id = int(c.arc_ids[selected]); lon, lat = map(float, geometry.inverse.transform(*c.snapped[selected]))
            distance = float(c.distances[selected]); score = float(probabilities[i][selected]); status = 'matched'; reason = None
        row = [_finite(v) for v in raw.track[i]]
        observations.append(ObservationPrediction(i, *row, status, int(segment_ids[i]) if selected >= 0 else None,
                          arc_id, lon, lat, distance, score, len(c.arc_ids), reason))
    context_ids = sorted({int(arc) for c in candidates for arc in c.arc_ids}) if options.include_network_context else []
    truncated = len(context_ids) > options.max_network_segments
    context = tuple(NetworkSegment(arc, int(raw.arcs[arc, 0]), int(raw.arcs[arc, 1]),
                        tuple(map(tuple, raw.nodes[raw.arcs[arc]].tolist())))
                    for arc in context_ids[:max(0, options.max_network_segments)])
    if truncated:
        warnings.append(PipelineWarning('network_context_truncated', 'Display network capped; inference unchanged'))
    coords = raw.track[raw.valid, :2]
    bounds = (*map(float, coords.min(0)), *map(float, coords.max(0)))
    timings['geometry'] = (time.perf_counter()-stage)*1000
    timings['predict_total'] = (time.perf_counter()-started)*1000
    evidence = dict(raw=raw, geometry=geometry, candidates=candidates, probabilities=probabilities, graph=graph, decoder_config=cfg)
    return PredictionResult(raw.trip_id, trip_input.mode, bundle.info.model_version, bundle.info.model_kind,
            bundle.info.model_family, effective_decoder, 'normalized_score', len(raw.track), tuple(observations),
            tuple(route), context, f'Union of inference candidate arcs within {policy["radius_m"]} m/top-{policy["top_k"]} per valid observation',
            truncated, bounds, timings, tuple(warnings), scorer_evidence=evidence)


def _finite(value):
    return float(value) if np.isfinite(value) else None


def _route(raw, geometry, candidates, choices, segments, graph, cfg):
    pieces = []; output_segments = np.full(len(choices), -1, dtype=int); breaks = []
    current_arcs = []; current_coords = []; first = last = previous_i = None
    piece_id = -1
    def finish():
        if current_arcs:
            pieces.append(RoutePiece(piece_id, first, last, tuple(current_arcs), tuple(current_coords)))
    def append(arc_id, role):
        if current_arcs and current_arcs[-1].arc_id == arc_id:
            if role == 'observed':
                current_arcs[-1] = RouteArc(arc_id, role)
            return
        coords = [tuple(map(float, p)) for p in raw.nodes[raw.arcs[arc_id]]]
        if current_coords and current_coords[-1] == coords[0]:
            current_coords.extend(coords[1:])
        else:
            current_coords.extend(coords)
        current_arcs.append(RouteArc(arc_id, role))
    for i, selected in enumerate(choices):
        if selected < 0:
            continue
        c = candidates[i]; aid = int(c.arc_ids[selected]); connector = (); reason = None
        if previous_i is not None:
            dt = raw.track[i, 2]-raw.track[previous_i, 2]
            if i != previous_i+1 or not 0 < dt <= cfg['gap_s']:
                reason = 'gps_gap'
            elif segments[i] >= 0 and segments[previous_i] >= 0 and segments[i] != segments[previous_i]:
                reason = 'decoder_restart'
            else:
                pc = candidates[previous_i]; ps = choices[previous_i]
                distance, connector = graph.between(int(pc.arc_ids[ps]), pc.fractions[ps], aid,
                    c.fractions[selected], cfg['max_speed_mps']*dt+cfg['gps_slack_m'], cfg['stationary_projection_noise_m'])
                if not np.isfinite(distance):
                    reason = 'unreachable'
        if previous_i is None or reason:
            finish(); piece_id += 1; current_arcs = []; current_coords = []; first = i
            if reason:
                breaks.append((i, reason))
        for arc in connector if reason is None else ():
            append(int(arc), 'connector')
        append(aid, 'observed'); last = i; previous_i = i; output_segments[i] = piece_id
    finish()
    return pieces, output_segments, breaks


def main():
    import argparse
    import dataclasses
    from src.contracts import PipelineSettings, PredictOptions
    parser = argparse.ArgumentParser(description='Reference-free CLI; same facade used by the HTTP service')
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--bundle-root', type=Path, required=True)
    parser.add_argument('--trip', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    settings = PipelineSettings(args.data_root, args.bundle_root)
    prediction = predict_trip(load_prediction_input(args.trip, 'development', settings),
                              load_model_bundle(settings), PredictOptions())
    public = {f.name: getattr(prediction, f.name) for f in dataclasses.fields(prediction) if f.name != 'scorer_evidence'}
    if args.output.exists():
        raise FileExistsError('Use a new prediction output path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(public, default=lambda o: dataclasses.asdict(o), allow_nan=False)+'\n')
    print(json.dumps({'trip_id': prediction.trip_id, 'model_kind': prediction.model_kind,
                      'observations': prediction.observation_count, 'route_pieces': len(prediction.route),
                      'timings_ms': prediction.timings_ms}))


if __name__ == '__main__':
    main()
