import { useEffect, useMemo, useState } from 'react';
import type { Prediction } from '../lib/api';
import { isPlottable } from './MapView';

export const RATES = [10, 60, 240] as const; // trip seconds per real second
export type Rate = (typeof RATES)[number];

/**
 * Route playback over the returned observations, in time order. This is a visualisation of
 * a finished prediction, not inference progress. The playhead jumps between observations and
 * never interpolates, so it cannot draw across a decoder break.
 */
export function usePlayback(prediction: Prediction | null) {
  const frames = useMemo(
    () =>
      prediction
        ? prediction.observations
            .filter((o) => o.t !== null && isPlottable(o))
            .map((o) => ({ index: o.index, t: o.t as number, segment: o.segment_id }))
            .sort((a, b) => a.t - b.t)
        : [],
    [prediction],
  );
  // State is owned by one prediction (request_id); a new prediction starts from a clean state.
  const key = prediction?.request_id ?? null;
  const [st, setSt] = useState<{ key: string | null; clock: number | null; playing: boolean }>({ key, clock: null, playing: false });
  const cur = st.key === key ? st : { key, clock: null, playing: false };
  const { clock, playing } = cur;
  const update = (patch: Partial<typeof st> | ((c: typeof st) => Partial<typeof st>)) =>
    setSt((prev) => {
      const base = prev.key === key ? prev : { key, clock: null, playing: false };
      return { ...base, ...(typeof patch === 'function' ? patch(base) : patch) };
    });
  const [rate, setRate] = useState<Rate>(60);
  const start = frames.length ? frames[0].t : 0;
  const end = frames.length ? frames[frames.length - 1].t : 0;

  useEffect(() => {
    if (!playing) return;
    const tick = 100;
    const id = window.setInterval(() => {
      setSt((prev) => {
        if (prev.key !== key || !prev.playing) return prev;
        const next = (prev.clock ?? start) + (rate * tick) / 1000;
        return next >= end ? { ...prev, clock: end, playing: false } : { ...prev, clock: next };
      });
    }, tick);
    return () => window.clearInterval(id);
  }, [playing, rate, start, end, key]);

  // Latest observation at or before the clock (binary search).
  const frame = useMemo(() => {
    if (clock === null || !frames.length) return null;
    let lo = 0;
    let hi = frames.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (frames[mid].t <= clock) lo = mid;
      else hi = mid - 1;
    }
    return { ...frames[lo], position: lo + 1, total: frames.length };
  }, [clock, frames]);

  return {
    available: frames.length > 1,
    playing,
    rate,
    setRate,
    frame,
    elapsed: clock === null ? 0 : clock - start,
    duration: end - start,
    toggle: () =>
      update((c) => (c.playing ? { playing: false } : { playing: true, clock: c.clock === null || c.clock >= end ? start : c.clock })),
    reset: () => update({ playing: false, clock: null }),
  };
}
