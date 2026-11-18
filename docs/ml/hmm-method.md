# HMM implementation notes

The user's summary of Karan Parikh's Uber Maps talk is useful background, but no video URL was supplied and no claim is made that the video was inspected. A primary reference was checked: Paul Newson and John Krumm, *Hidden Markov Map Matching Through Noise and Sparseness* (ACM SIGSPATIAL GIS 2009), [official publication](https://www.microsoft.com/en-us/research/publication/hidden-markov-map-matching-noise-sparseness/) and [paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/map-matching-ACM-GIS-camera-ready.pdf). Sections 3–4 discuss candidate road states, geometric emissions, route-distance discrepancy transitions, Viterbi and broken lattices.

Our implementation uses directed graph arcs as supplied and candidate states containing the projected position on each arc. `RoadGraph.between` includes the remainder of the source segment, a legal shortest path, and the initial part of the target segment. Large backward movement on the same directed arc requires a real cycle. Up to 15 m of backward projection is interpreted as stationary GPS noise, not a newly added reverse road.

Transitions use a negative absolute difference between directed travel distance and observation displacement, divided by a fixed preliminary 25 m scale. Elapsed time imposes a preliminary physical travel bound (65 m/s plus 50 m slack); gaps above 30 s restart the sequence. These are our explicit initial configuration choices, not fitted values copied from the paper. Their real-data behavior still needs evaluation.

Final emissions will come from the selected trained candidate classifier, clipped and normalized within each observation. This is a normalized relevance distribution, not calibrated confidence. The M1 diagnostic uses geometric relevance and classifier-only selection; it does not demonstrate the final trained-classifier HMM.

`viterbi.py` evaluates the recurrence in log space with per-step offsets, backpointers and termination. Empty candidates, large gaps and all-unreachable transitions end the current block and restart separately. Returned route pieces are built from actual graph arcs and legal connectors. Tiny-graph tests passed, including a known optimum and unreachable restart. No real-data HMM accuracy improvement is claimed yet.

## Executed trained comparison

The final fixed decoder was evaluated on all ten student-testing trips in `results/hmm/hgb-hmm-v1/summary.json`. Tuned HGB classifier-only accuracy was 0.860367 and HMM accuracy 0.885493; mean trip Macro F1 was 0.770553 versus 0.851054. Legal continuity rose from 0.949760 to 0.999164 and observed-arc sequence similarity from 0.638746 to 0.855911. These are provisional alignment scores, not official evaluator results. No decoder parameters were selected using student-test performance.

Conditional log loss stays identical between modes because it measures the same normalized classifier emission distribution. The Viterbi path is not an HMM posterior distribution. Connected route pieces dropped from 974 to 28; remaining gaps are preserved. Actual full-facade inference totals were about 5.06s classifier-only and 10.70s HMM across the ten trips on this host; these include graph/candidate/features/geometry stages and exclude separate scoring. They are measured local timings, not a deployment guarantee.
