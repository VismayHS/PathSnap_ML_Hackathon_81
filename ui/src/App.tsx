import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError, defaultApiBase, rememberApiBase, type Health, type Prediction, type Trips } from './lib/api';
import {
  DECODER_LABEL, metricLabel, metricValue, ms, SCORE_KIND_LABEL, STAGE_LABELS, summariseWarnings, WARNING_LABELS,
} from './lib/format';
import { MapView, observationAt, type LayerKey, type LayerVisibility } from './map/MapView';
import { RATES, usePlayback, type Rate } from './map/usePlayback';

type Conn =
  | { state: 'checking' }
  | { state: 'unreachable'; error: ApiError }
  | { state: 'connected'; health: Health; trips: Trips | null; tripsError: ApiError | null };

type Run =
  | { state: 'idle' }
  | { state: 'running'; tripId: string }
  | { state: 'done'; prediction: Prediction }
  | { state: 'failed'; tripId: string; error: ApiError };

const LAYERS: { key: LayerKey; label: string; swatch: string }[] = [
  { key: 'route', label: 'Predicted route', swatch: 'sw-route' },
  { key: 'gps', label: 'Raw GPS points', swatch: 'sw-gps' },
  { key: 'unmatched', label: 'Unmatched or invalid points', swatch: 'sw-unmatched' },
  { key: 'network', label: 'Road network (nearby)', swatch: 'sw-network' },
];

export default function App() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [draftBase, setDraftBase] = useState(apiBase);
  const [conn, setConn] = useState<Conn>({ state: 'checking' });
  const [tripId, setTripId] = useState<string | null>(null);
  const [run, setRun] = useState<Run>({ state: 'idle' });
  const [visible, setVisible] = useState<LayerVisibility>({ network: true, route: true, gps: true, unmatched: true });
  const [selected, setSelected] = useState<number | null>(null);
  const [fitToken, setFitToken] = useState(0);
  const [layersOpen, setLayersOpen] = useState(true);
  const inflight = useRef<AbortController | null>(null);
  const seq = useRef(0);

  const [connNonce, setConnNonce] = useState(0);
  const recheck = () => {
    setConn({ state: 'checking' });
    setConnNonce((n) => n + 1);
  };

  useEffect(() => {
    let cancelled = false;
    void loadConnection(apiBase).then((c) => {
      if (!cancelled) setConn(c);
    });
    return () => {
      cancelled = true;
    };
  }, [apiBase, connNonce]);

  const reconstruct = useCallback(async () => {
    if (!tripId) return;
    inflight.current?.abort();
    const controller = new AbortController();
    inflight.current = controller;
    const mySeq = ++seq.current;
    setSelected(null);
    setRun({ state: 'running', tripId }); // clears the previous route from map and panel
    try {
      const prediction = await api.predict(apiBase, tripId, controller.signal);
      if (mySeq !== seq.current) return; // a newer request owns the screen
      setRun({ state: 'done', prediction });
    } catch (e) {
      const err = e as ApiError;
      if (mySeq !== seq.current || err.code === 'superseded') return;
      setRun({ state: 'failed', tripId, error: err });
    }
  }, [apiBase, tripId]);

  // Abort any in-flight request, invalidate late responses, and clear the screen's result.
  const resetRun = (nextTrip: string | null) => {
    inflight.current?.abort();
    seq.current++;
    setTripId(nextTrip);
    setSelected(null);
    setRun({ state: 'idle' });
  };

  const chooseTrip = (id: string) => {
    if (id !== tripId) resetRun(id);
  };

  const onSelect = useCallback((i: number | null) => setSelected(i), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setSelected(null);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const prediction = run.state === 'done' ? run.prediction : null;
  const health = conn.state === 'connected' ? conn.health : null;
  const trips = conn.state === 'connected' ? conn.trips : null;
  const canRun = !!health?.ready && !!tripId && run.state !== 'running';
  const obs = observationAt(prediction, selected);
  const playback = usePlayback(prediction);

  return (
    <div className="app">
      <a className="skip" href="#trips-section">Skip to trip selection</a>
      <aside className="panel" aria-label="PathSnap controls">
        <header className="panel-head">
          <h1>PathSnap</h1>
          <p className="sub">Reconstructs a vehicle's route on the road network from noisy GPS.</p>
          <ConnectionLine conn={conn} apiBase={apiBase} />
        </header>

        {conn.state === 'unreachable' && (
          <section className="block notice notice-error" aria-live="polite">
            <p><strong>Can't reach the PathSnap server</strong> at <code>{apiBase}</code>.</p>
            <p className="hint">Check that the API is running on Laptop 1 and that this address uses Laptop 1's LAN IP, not localhost.</p>
            <button className="btn" onClick={recheck}>Retry connection</button>
          </section>
        )}

        <details className="block server">
          <summary>Server address</summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const b = draftBase.trim().replace(/\/$/, '');
              rememberApiBase(b);
              resetRun(null); // a new server means a new trip allowlist: drop all prior context
              setApiBase(b);
              recheck();
            }}
          >
            <label htmlFor="api-base">API URL</label>
            <div className="row">
              <input id="api-base" name="api-base" type="url" autoComplete="off" value={draftBase} onChange={(e) => setDraftBase(e.target.value)} spellCheck={false} placeholder="http://192.168.1.10:8000" />
              <button className="btn" type="submit">Connect</button>
            </div>
          </form>
        </details>

        {health && !health.ready && (
          <section className="block notice notice-warn" aria-live="polite">
            <p><strong>The server is up but not ready.</strong></p>
            <ul className="reasons">{health.not_ready_reasons.map((r) => <li key={r}><code>{r}</code></li>)}</ul>
          </section>
        )}

        {conn.state === 'connected' && conn.tripsError && (
          <section className="block notice notice-warn">
            <p>{conn.tripsError.message}</p>
          </section>
        )}

        {trips && (
          <section className="block" id="trips-section" tabIndex={-1}>
            <div className="mode-line">
              <h2 id="trips-label">Trips</h2>
              <span className={trips.mode === 'development' ? 'badge badge-dev' : 'badge badge-eval'}>
                {trips.mode === 'development' ? 'Development data' : 'Evaluator data'}
              </span>
            </div>
            <p className="hint">{trips.partition_label}, {trips.count} available</p>
            <div className="trip-grid" role="radiogroup" aria-labelledby="trips-label">
              {trips.trip_ids.map((id) => (
                <label key={id} className={`trip ${id === tripId ? 'is-selected' : ''}`}>
                  <input type="radio" name="trip" value={id} checked={id === tripId} onChange={() => chooseTrip(id)} />
                  <span className="mono" translate="no">{id}</span>
                </label>
              ))}
            </div>
            <button className="btn btn-primary" disabled={!canRun} aria-busy={run.state === 'running'} onClick={() => void reconstruct()}>
              {run.state === 'running' ? 'Reconstructing…' : tripId ? 'Reconstruct route' : 'Select a trip'}
            </button>
            {!health?.ready && <p className="hint">Reconstruction is unavailable until the server is ready.</p>}
          </section>
        )}

        <section className="block results" aria-live="polite" aria-busy={run.state === 'running'}>
          {run.state === 'idle' && trips && <p className="hint">Choose a trip, then reconstruct to see its predicted route.</p>}
          {run.state === 'running' && <p className="status">Running pipeline for trip <span className="mono">{run.tripId}</span>…</p>}
          {run.state === 'failed' && (
            <div className="notice notice-error">
              <p><strong>Reconstruction failed for trip <span className="mono">{run.tripId}</span>.</strong> {run.error.message}</p>
              {run.error.requestId && <p className="hint">Request ID <span className="mono">{run.error.requestId}</span></p>}
              <button className="btn" onClick={() => void reconstruct()}>Try again</button>
            </div>
          )}
          {prediction && (
            <>
              <Results p={prediction} />
              <form
                className="inspect-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  const v = Number(new FormData(e.currentTarget).get('obs'));
                  if (Number.isInteger(v) && v >= 0 && v < prediction.observation_count) setSelected(v);
                }}
              >
                <label htmlFor="obs-index">Inspect observation</label>
                <div className="row">
                  <input id="obs-index" name="obs" type="number" min={0} max={prediction.observation_count - 1} defaultValue={0} autoComplete="off" />
                  <button className="btn" type="submit">Show on map</button>
                </div>
                <p className="hint">Or click any GPS point on the map. Esc closes the details.</p>
              </form>
            </>
          )}
        </section>
      </aside>

      <main className="stage">
        <MapView prediction={prediction} visible={visible} selected={selected} onSelect={onSelect} fitToken={fitToken} playhead={playback.frame?.index ?? null}>
          <div className="map-tools">
            {playback.available && (
              <div className="playback" role="group" aria-label="Route playback">
                <button className="btn btn-map" onClick={playback.toggle} aria-pressed={playback.playing}>
                  {playback.playing ? 'Pause' : 'Play route'}
                </button>
                <button className="btn btn-map" onClick={playback.reset} disabled={!playback.frame}>Reset</button>
                <label className="rate">
                  <span className="visually-hidden">Playback speed</span>
                  <select value={playback.rate} onChange={(e) => playback.setRate(Number(e.target.value) as Rate)}>
                    {RATES.map((r) => <option key={r} value={r}>{r}× speed</option>)}
                  </select>
                </label>
                {playback.frame && (
                  <span className="play-status" aria-live="off">
                    {Math.round(playback.elapsed)} / {Math.round(playback.duration)} s, point #{playback.frame.index}
                  </span>
                )}
              </div>
            )}
            <button className="btn btn-map" onClick={() => setFitToken((n) => n + 1)} disabled={!prediction}>Fit route</button>
          </div>
          <fieldset className={`layers ${layersOpen ? '' : 'is-collapsed'}`}>
            <legend>
              <button type="button" className="layers-toggle" aria-expanded={layersOpen} onClick={() => setLayersOpen((o) => !o)}>
                Layers
              </button>
            </legend>
            {layersOpen &&
              LAYERS.map((l) => (
                <label key={l.key} className="layer">
                  <input
                    type="checkbox"
                    checked={visible[l.key]}
                    onChange={(e) => setVisible((v) => ({ ...v, [l.key]: e.target.checked }))}
                  />
                  <span className={`sw ${l.swatch}`} aria-hidden="true" />
                  {l.label}
                </label>
              ))}
          </fieldset>
          {obs && prediction && (
            <section className="inspector" aria-label={`Observation ${obs.index}`}>
              <div className="inspector-head">
                <h3>Observation <span className="mono">#{obs.index}</span></h3>
                <div className="inspector-nav">
                  <button className="btn btn-ghost" onClick={() => setSelected(Math.max(0, obs.index - 1))} disabled={obs.index === 0} aria-label="Previous observation">Prev</button>
                  <button className="btn btn-ghost" onClick={() => setSelected(Math.min(prediction.observation_count - 1, obs.index + 1))} disabled={obs.index >= prediction.observation_count - 1} aria-label="Next observation">Next</button>
                  <button className="btn btn-ghost" onClick={() => setSelected(null)} aria-label="Close observation details">Close</button>
                </div>
              </div>
              <dl className="kv">
                <dt>Time</dt><dd>{obs.t === null ? '—' : `${obs.t.toFixed(0)} s`}</dd>
                <dt>Status</dt><dd>{obs.status.replace('_', ' ')}{obs.reason ? ` (${obs.reason.replace(/_/g, ' ')})` : ''}</dd>
                <dt>Predicted arc</dt><dd className="mono">{obs.arc_id ?? '—'}</dd>
                <dt>Distance to road</dt><dd>{obs.distance_m === null ? '—' : `${obs.distance_m.toFixed(1)} m`}</dd>
                <dt>Candidates</dt><dd>{obs.candidate_count}</dd>
                <dt>Score</dt><dd>{obs.score === null ? '—' : obs.score.toFixed(3)} <span className="hint">({SCORE_KIND_LABEL[prediction.score_kind]})</span></dd>
                <dt>GPS</dt><dd className="mono">{obs.lat === null || obs.lon === null ? 'not available' : `${obs.lat.toFixed(6)}, ${obs.lon.toFixed(6)}`}</dd>
              </dl>
            </section>
          )}
        </MapView>
      </main>
    </div>
  );
}

async function loadConnection(base: string): Promise<Conn> {
  try {
    const health = await api.health(base);
    try {
      return { state: 'connected', health, trips: await api.trips(base), tripsError: null };
    } catch (e) {
      return { state: 'connected', health, trips: null, tripsError: e as ApiError };
    }
  } catch (e) {
    return { state: 'unreachable', error: e as ApiError };
  }
}

function ConnectionLine({ conn, apiBase }: { conn: Conn; apiBase: string }) {
  const [label, cls] =
    conn.state === 'checking' ? ['Connecting…', 'dot-wait']
      : conn.state === 'unreachable' ? ['Not connected', 'dot-bad']
        : conn.health.ready ? ['Connected, ready', 'dot-ok'] : ['Connected, not ready', 'dot-warn'];
  return (
    <p className="conn" role="status">
      <span className={`dot ${cls}`} aria-hidden="true" />
      {label}<span className="hint mono conn-addr">{apiBase.replace(/^https?:\/\//, '')}</span>
    </p>
  );
}

function Results({ p }: { p: Prediction }) {
  const counts = { matched: 0, no_candidate: 0, unmatched: 0, invalid: 0 };
  for (const o of p.observations) counts[o.status] += 1;
  const matched = counts.matched;
  const warnings = summariseWarnings(p.warnings);
  return (
    <>
      <h2>Trip <span className="mono">{p.trip_id}</span></h2>
      {p.model.kind === 'diagnostic' && (
        <p className="notice notice-warn">Diagnostic geometric model, not the trained classifier. Results only check the wiring.</p>
      )}
      <dl className="kv">
        <dt>Model</dt><dd>{p.model.family} <span className="hint mono">{p.model.version}</span></dd>
        <dt>Decoder</dt><dd>{DECODER_LABEL[p.model.decoder]}</dd>
        <dt>Observations</dt>
        <dd>
          {matched.toLocaleString()} matched of {p.observation_count.toLocaleString()}
          {counts.no_candidate + counts.unmatched + counts.invalid > 0 && (
            <span className="hint">
              {' '}({[
                counts.no_candidate && `${counts.no_candidate} no nearby road`,
                counts.unmatched && `${counts.unmatched} unmatched`,
                counts.invalid && `${counts.invalid} invalid`,
              ].filter(Boolean).join(', ')})
            </span>
          )}
        </dd>
        <dt>Route pieces</dt><dd>{p.route.features.length.toLocaleString()}</dd>
        <dt>Server time</dt><dd>{ms(p.timings.request_ms)}</dd>
      </dl>

      <h3>Evaluation</h3>
      {p.evaluation.status === 'unavailable' ? (
        <p className="hint">Metrics unavailable: {p.evaluation.unavailable_reason ?? 'no reason given'}.</p>
      ) : (
        <>
          <dl className="kv metrics">
            {p.evaluation.metrics.map((m) => (
              <div key={m.name} className="metric">
                <dt title={m.denominator_policy}>{metricLabel(m.name)}</dt>
                <dd>
                  {metricValue(m)}
                  {m.numerator !== null && m.denominator !== null && (
                    <span className="hint"> {m.numerator.toLocaleString()} / {m.denominator.toLocaleString()}</span>
                  )}
                  {m.value === null && m.unavailable_reason && <span className="hint"> — {m.unavailable_reason}</span>}
                </dd>
              </div>
            ))}
          </dl>
          <p className="hint">
            Scoring policy <span className="mono">{p.evaluation.policy_id}</span>
            {p.evaluation.policy_status === 'provisional' ? ' (provisional, pending organiser confirmation)' : ''}. Computed on the server
            after prediction.
          </p>
        </>
      )}

      {warnings.length > 0 && (
        <>
          <h3>Warnings</h3>
          <ul className="warnings">
            {warnings.map((w) => (
              <li key={w.code}>
                <span>{WARNING_LABELS[w.code] ?? w.code}</span> <span className="count">× {w.count.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <details className="timings">
        <summary>Pipeline timings</summary>
        <dl className="kv">
          {Object.entries(p.timings.pipeline_ms).map(([k, v]) => (
            <div key={k} className="metric"><dt>{STAGE_LABELS[k] ?? k}</dt><dd>{ms(v)}</dd></div>
          ))}
          <div className="metric"><dt>Scoring</dt><dd>{ms(p.timings.scoring_ms)}</dd></div>
          <div className="metric"><dt>Whole request (server)</dt><dd>{ms(p.timings.request_ms)}</dd></div>
        </dl>
      </details>
      <p className="hint">Request ID <span className="mono" translate="no">{p.request_id}</span> (matches the Laptop 1 API log)</p>
    </>
  );
}
