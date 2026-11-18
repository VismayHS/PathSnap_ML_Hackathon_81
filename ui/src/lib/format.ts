import type { Metric, Prediction } from './api';

const METRIC_LABELS: Record<string, string> = {
  top1_accuracy: 'Top-1 accuracy',
  macro_f1: 'Macro F1',
  precision_macro: 'Precision (macro)',
  recall_macro: 'Recall (macro)',
  candidate_miss_rate: 'Candidate miss rate',
  route_continuity: 'Route continuity',
  log_loss: 'Log loss',
  scorable_observations: 'Scorable observations',
};

export const metricLabel = (name: string) =>
  METRIC_LABELS[name] ?? name.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());

export function metricValue(m: Metric): string {
  if (m.value === null) return 'Unavailable';
  if (m.unit === 'fraction') return `${(m.value * 100).toFixed(1)}%`;
  if (m.unit === 'count') return m.value.toLocaleString();
  if (m.unit === 'nats') return `${m.value.toFixed(3)} nats`;
  return m.unit ? `${m.value.toFixed(3)} ${m.unit}` : m.value.toFixed(3);
}

export const ms = (v: number | null | undefined) =>
  v === null || v === undefined ? '—' : v >= 1000 ? `${(v / 1000).toFixed(2)} s` : `${Math.round(v)} ms`;

export const STAGE_LABELS: Record<string, string> = {
  load_input: 'Load trip files',
  clean: 'Clean observations',
  candidates: 'Candidate roads',
  features: 'Features',
  model: 'Model scoring',
  decode: 'Decode route',
  geometry: 'Build geometry',
  predict_total: 'Pipeline total',
};

export const SCORE_KIND_LABEL: Record<Prediction['score_kind'], string> = {
  calibrated_probability: 'calibrated probability',
  normalized_score: 'normalised score, not a probability',
  none: 'no score',
};

export const DECODER_LABEL: Record<Prediction['model']['decoder'], string> = {
  hmm_viterbi: 'HMM / Viterbi',
  classifier_only: 'Classifier only (no HMM smoothing)',
  none: 'None',
};

export function summariseWarnings(warnings: Prediction['warnings']) {
  const byCode = new Map<string, { code: string; count: number; example: string; indices: number }>();
  for (const w of warnings) {
    const entry = byCode.get(w.code) ?? { code: w.code, count: 0, example: w.message, indices: 0 };
    entry.count += 1;
    entry.indices += w.observation_indices?.length ?? 0;
    byCode.set(w.code, entry);
  }
  return [...byCode.values()].sort((a, b) => b.count - a.count);
}

export const WARNING_LABELS: Record<string, string> = {
  gps_gap: 'GPS gaps',
  decoder_break: 'Route breaks (pieces not connected on the road graph)',
  no_candidates: 'Points with no nearby road',
  invalid_observations: 'Invalid GPS points removed',
  network_context_truncated: 'Road network display truncated',
  diagnostic_model: 'Diagnostic model in use',
};
