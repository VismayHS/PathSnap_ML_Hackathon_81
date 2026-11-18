# M2 training plan and controls

M2 starts under the explicit overlap agreement B-0010/A-0020. M1 integrates pinned A revision `cc3e4ab`; later M2 commits do not change that snapshot. After B publishes accepted M1, A will merge it normally into its clean worker branch, preserving deliberately overlapping commits (no reset/rebase).

The committed preparation command constructs candidates/features before reading references. It caches labels separately for offline development training/evaluation only. The inference facade never reads these caches or references. Every original observation remains represented by candidate offsets, labels/scorable masks and original indices.

Use five trip-grouped folds on all 80 training trips. Within each fit, a deterministic sample of at most 400 scorable observations per training trip controls cost; their complete candidate rows stay together. Keep all scorable validation/student-test observations, including candidate misses and unmatched outcomes, in accuracy accounting. Do not inject reference arcs into candidate sets. Record original, scorable, unscorable, covered and low-margin counts separately.

The initial algorithms are regularized Logistic Regression, distance-weighted KNN, Random Forest, Extra Trees and HistGradientBoosting. Learned preprocessing fits inside each fold. A training-only 8-trip/2-trip pilot measures real fit/scoring cost before the full run. One runner uses at most two threads, leaving resources for B's API/browser checks. Kaggle is optional; no data upload or login is needed at present.

The reference alignment remains provisional. A read-only training diagnosis found 20,550 of 208,417 observations outside the current scorable policy: 19,992 were over 100 m from every supplied reference segment, and 558 additional cases were near a reference but incompatible with the ordered alignment. Full reproducible preparation records will establish the final count table. These observations are not silently deleted from the data or inference; report their accounting alongside conditional derived-label scores.

No trained-model selection or benchmark claim is made by this plan. Select only after recording every model's measured grouped CV and development results.
