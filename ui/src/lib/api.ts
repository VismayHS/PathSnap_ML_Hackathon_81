// Wire types mirror contracts/http.schema.json (contract 0.1.0). Coordinates are [lon, lat].

export type Mode = 'development' | 'evaluator';
export type LonLat = [number, number];

export interface ModelIdentity {
  version: string;
  kind: 'trained' | 'diagnostic';
  family: string;
  decoder: 'hmm_viterbi' | 'classifier_only' | 'none';
  run_id: string;
}

export interface Health {
  schema_version: string;
  service: string;
  api_version: string;
  status: 'ok' | 'degraded';
  ready: boolean;
  mode: Mode;
  data_configured: boolean;
  model: ModelIdentity | null;
  not_ready_reasons: string[];
}

export interface Trips {
  mode: Mode;
  partition_label: string;
  trip_ids: string[];
  count: number;
}

export type ObservationStatus = 'matched' | 'no_candidate' | 'invalid' | 'unmatched';

export interface Observation {
  index: number;
  lon: number | null;
  lat: number | null;
  t: number | null;
  status: ObservationStatus;
  segment_id: number | null;
  arc_id: number | null;
  snapped: LonLat | null;
  distance_m: number | null;
  score: number | null;
  candidate_count: number;
  reason: string | null;
}

export interface LineFeature<P> {
  type: 'Feature';
  geometry: { type: 'LineString'; coordinates: LonLat[] };
  properties: P;
}

export interface RouteProps {
  segment_id: number;
  first_index: number;
  last_index: number;
  arc_ids: number[];
  arc_roles: ('observed' | 'connector')[];
}

export interface Metric {
  name: string;
  value: number | null;
  unit: string | null;
  numerator: number | null;
  denominator: number | null;
  denominator_policy: string;
  unavailable_reason: string | null;
}

export interface Prediction {
  schema_version: string;
  request_id: string;
  mode: Mode;
  partition_label: string;
  trip_id: string;
  model: ModelIdentity;
  score_kind: 'calibrated_probability' | 'normalized_score' | 'none';
  observation_count: number;
  observations: Observation[];
  route: { type: 'FeatureCollection'; features: LineFeature<RouteProps>[] };
  network: {
    type: 'FeatureCollection';
    policy: string;
    truncated: boolean;
    features: LineFeature<{ arc_id: number; from_node: number; to_node: number }>[];
  };
  bounds: [number, number, number, number];
  timings: { pipeline_ms: Record<string, number>; scoring_ms: number | null; request_ms: number };
  warnings: { code: string; message: string; observation_indices: number[] | null }[];
  evaluation: {
    status: 'scored' | 'unavailable';
    policy_id: string;
    policy_status: 'provisional' | 'agreed';
    metrics: Metric[];
    unavailable_reason: string | null;
  };
  synthetic: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number | null,
    readonly requestId: string | null,
    readonly retryable: boolean,
  ) {
    super(message);
  }
}

const STORAGE_KEY = 'pathsnap.apiBase';

export function defaultApiBase(): string {
  const fromQuery = new URLSearchParams(window.location.search).get('api');
  if (fromQuery) return fromQuery.replace(/\/$/, '');
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
  } catch {
    /* storage unavailable: fall through */
  }
  const fromEnv = import.meta.env.VITE_PATHSNAP_API_URL as string | undefined;
  return (fromEnv || `http://${window.location.hostname}:8000`).replace(/\/$/, '');
}

export function rememberApiBase(base: string): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, base);
  } catch {
    /* ignore */
  }
}

/** 32 hex chars. crypto.randomUUID only exists in secure contexts, and Laptop 2 opens the UI
 * over plain http://<LAN-IP>, so fall back to getRandomValues (available everywhere). */
export function newRequestId(): string {
  const c = globalThis.crypto;
  if (c && typeof c.randomUUID === 'function') return c.randomUUID().replace(/-/g, '');
  const bytes = new Uint8Array(16);
  if (c && typeof c.getRandomValues === 'function') c.getRandomValues(bytes);
  else for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

async function request<T>(
  base: string,
  path: string,
  init: RequestInit & { timeoutMs: number; signal?: AbortSignal },
): Promise<T> {
  const requestId = newRequestId();
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort('timeout'), init.timeoutMs);
  init.signal?.addEventListener('abort', () => controller.abort('superseded'), { once: true });
  const fail = (status: number | null, rid: string): ApiError => {
    const reason = controller.signal.reason;
    if (reason === 'superseded') return new ApiError('Superseded by a newer request.', 'superseded', status, rid, false);
    if (reason === 'timeout')
      return new ApiError(`No complete response from the server within ${Math.round(init.timeoutMs / 1000)} s.`, 'timeout', status, rid, true);
    return status === null
      ? new ApiError(`Can't reach the PathSnap server at ${base}.`, 'unreachable', null, rid, true)
      : new ApiError(`The server sent an unreadable response (HTTP ${status}).`, 'bad_response', status, rid, false);
  };
  // The timer stays armed until the body is fully read and parsed.
  try {
    let response: Response;
    try {
      response = await fetch(`${base}${path}`, {
        ...init,
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-Request-ID': requestId, ...(init.headers ?? {}) },
      });
    } catch {
      throw fail(null, requestId);
    }
    const rid = response.headers.get('X-Request-ID') ?? requestId;
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw fail(response.status, rid);
    }
    if (!response.ok) {
      const env = body as { request_id?: string; error?: { code: string; message: string; retryable: boolean } };
      const err = env.error;
      throw new ApiError(
        err?.message ?? `HTTP ${response.status}`, err?.code ?? 'http_error', response.status,
        env.request_id ?? rid, err?.retryable ?? false,
      );
    }
    return body as T;
  } finally {
    window.clearTimeout(timer);
  }
}

export const api = {
  health: (base: string, signal?: AbortSignal) => request<Health>(base, '/health', { method: 'GET', timeoutMs: 8000, signal }),
  trips: (base: string, signal?: AbortSignal) => request<Trips>(base, '/trips', { method: 'GET', timeoutMs: 8000, signal }),
  predict: (base: string, tripId: string, signal?: AbortSignal) =>
    request<Prediction>(base, '/predict', {
      method: 'POST',
      body: JSON.stringify({ trip_id: tripId }),
      timeoutMs: 180000,
      signal,
    }),
};
