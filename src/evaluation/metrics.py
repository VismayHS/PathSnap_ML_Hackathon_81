"""Observation/sequence metrics for graph-local roads; never candidate-row binary F1."""
import time
import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from src.hmm.graph import RoadGraph
from src.hmm.viterbi import DEFAULT_CONFIG


def sequence_similarity(truth, prediction):
    """1-normalized Levenshtein distance between compressed observed-arc runs."""
    def runs(values):
        values = np.asarray(values, dtype=np.int64)
        return values[np.r_[True, values[1:] != values[:-1]]] if len(values) else values
    a, b = runs(truth), runs(prediction)
    denominator = max(len(a), len(b))
    if not denominator:
        return None, 0, 'no_scorable_arc_sequence'
    if len(a)*len(b) > 20_000_000:
        return None, denominator, 'sequence_scoring_budget_exceeded'
    previous = np.arange(len(b)+1)
    positions = np.arange(len(b)+1)
    for i, value in enumerate(a, 1):
        base = np.r_[i, np.minimum(previous[1:]+1, previous[:-1]+(b != value))]
        previous = np.minimum.accumulate(base-positions)+positions
    return float(1-previous[-1]/denominator), denominator, None


def observation_metrics(labels, scorable, prediction, candidate_arc_ids, row_observation, probabilities):
    mask = np.asarray(scorable, dtype=bool)
    n, original = int(mask.sum()), len(labels)
    correct = int((prediction[mask] == labels[mask]).sum())
    road_classes = np.union1d(labels[mask], prediction[mask][prediction[mask] >= 0])
    if n:
        precision, recall, f1, _ = precision_recall_fscore_support(labels[mask], prediction[mask],
                         labels=road_classes, average='macro', zero_division=0)
    else:
        precision = recall = f1 = None
    covered_rows = mask[row_observation] & (candidate_arc_ids == labels[row_observation])
    covered_obs = np.zeros(original, dtype=bool)
    covered_obs[row_observation[covered_rows]] = True
    covered = int(covered_obs.sum())
    loss_sum = float(-np.log(np.maximum(probabilities[covered_rows], 1e-12)).sum()) if covered else 0.
    seq, seq_n, seq_reason = sequence_similarity(labels[mask], prediction[mask])
    values = dict(top1_accuracy=correct/n if n else None, macro_f1=float(f1) if n else None,
                  precision_macro=float(precision) if n else None, recall_macro=float(recall) if n else None,
                  candidate_miss_rate=(n-covered)/n if n else None, log_loss=loss_sum/covered if covered else None,
                  sequence_arc_similarity=seq, scored_match_fraction_original=correct/original if original else None)
    return dict(values=values, counts=dict(original_observations=original, scorable_observations=n,
                  unscorable_observations=original-n, correct=correct, candidate_covered=covered,
                  candidate_misses=n-covered, road_classes=len(road_classes), sequence_length=seq_n),
                loss_sum=loss_sum, unavailable_reasons={'log_loss': 'no_covered_observations' if not covered else None,
                  'sequence_arc_similarity': seq_reason})


def continuity(data, prediction, selected_rows):
    graph = RoadGraph(data['arcs'], data['lengths'])
    dt = np.diff(data['track'][:, 2]); eligible = data['valid'][:-1] & data['valid'][1:] & (dt > 0) & (dt <= DEFAULT_CONFIG['gap_s'])
    connected = 0
    for j in np.flatnonzero(eligible):
        i = j+1
        if prediction[j] < 0 or prediction[i] < 0:
            continue
        limit = DEFAULT_CONFIG['max_speed_mps']*dt[j]+DEFAULT_CONFIG['gps_slack_m']
        distance, _ = graph.between(prediction[j], data['fractions'][selected_rows[j]], prediction[i],
                 data['fractions'][selected_rows[i]], limit, DEFAULT_CONFIG['stationary_projection_noise_m'])
        connected += np.isfinite(distance) and distance <= limit
    return dict(value=float(connected/eligible.sum()) if eligible.any() else None,
                numerator=int(connected), denominator=int(eligible.sum()))


def score_estimator(estimator, data, with_continuity=True):
    started = time.perf_counter(); X = data['X']; n = len(data['labels'])
    if len(X):
        classes = list(estimator.classes_)
        relevance = estimator.predict_proba(X)[:, classes.index(1)] if 1 in classes else np.zeros(len(X))
        relevance = np.maximum(relevance, 1e-12)
        sums = np.bincount(data['row_observation'], weights=relevance, minlength=n)
        probabilities = relevance/sums[data['row_observation']]
    else:
        relevance = probabilities = np.empty(0)
    prediction = np.full(n, -1, dtype=int); rows = np.full(n, -1, dtype=int)
    for i, (lo, hi) in enumerate(zip(data['offsets'][:-1], data['offsets'][1:])):
        if hi > lo:
            row = int(lo+np.argmax(relevance[lo:hi])); rows[i] = row
            prediction[i] = data['candidate_arc_ids'][row]
    inference_ms = (time.perf_counter()-started)*1000
    metrics = observation_metrics(data['labels'], data['scorable'], prediction,
                data['candidate_arc_ids'], data['row_observation'], probabilities)
    metrics['candidate_scoring_ms'] = inference_ms
    if with_continuity:
        c = continuity(data, prediction, rows); metrics['values']['route_continuity'] = c['value']
        metrics['counts']['continuity_connected'] = c['numerator']; metrics['counts']['continuity_pairs'] = c['denominator']
    metrics['metric_elapsed_ms'] = (time.perf_counter()-started)*1000-inference_ms
    return metrics


def aggregate(rows):
    total = lambda key: sum(r['counts'][key] for r in rows)
    n, covered = total('scorable_observations'), total('candidate_covered')
    mean = lambda key: float(np.mean([r['values'][key] for r in rows if r['values'].get(key) is not None])) if any(r['values'].get(key) is not None for r in rows) else None
    result = dict(top1_accuracy=total('correct')/n if n else None, macro_f1=mean('macro_f1'),
       precision_macro=mean('precision_macro'), recall_macro=mean('recall_macro'),
       candidate_miss_rate=total('candidate_misses')/n if n else None,
       log_loss=sum(r['loss_sum'] for r in rows)/covered if covered else None,
       sequence_arc_similarity=mean('sequence_arc_similarity'),
       scored_match_fraction_original=total('correct')/total('original_observations'),
       candidate_scoring_ms=sum(r['candidate_scoring_ms'] for r in rows), trips=len(rows),
       scorable_observations=n, original_observations=total('original_observations'),
       unscorable_observations=total('unscorable_observations'), candidate_covered=covered)
    if all('continuity_pairs' in r['counts'] for r in rows):
        pairs = total('continuity_pairs'); result['route_continuity'] = total('continuity_connected')/pairs if pairs else None
    return result
