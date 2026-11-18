# Scientific references consulted

Accessed 18 November 2026. These are method/library references, not other teams' code or artifacts. No pretrained task weights or copied map-matching implementation has been adopted. Package versions in `requirements.txt` are selected compatibility pins; they are not claims about the latest release.

| Primary reference | Use and status |
|---|---|
| https://scikit-learn.org/stable/modules/ensemble.html | Compared Random Forest, Extra Trees and histogram boosting behavior; planned actual experiments will decide selection. |
| https://scikit-learn.org/stable/modules/cross_validation.html#group-k-fold | Trip-group isolation for train-only CV; preprocessing must fit within folds. |
| https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html | Reviewed histogram boosting configuration and early-stopping concerns; avoid a random observation holdout across trips. |
| https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html | Distance-weighted neighbor baseline and inference cost considerations. |
| https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html | Considered optional boosting; not adopted or benchmarked. Docs caution that class weighting affects probability estimates. |
| https://catboost.ai/docs/en/concepts/python-reference_catboostclassifier | Considered optional boosting; not adopted or benchmarked. First fetch timed out; second succeeded. |
| https://github.com/optuna/optuna | Official README and MIT license link inspected. Optuna selected as an intended optimization dependency; no search run yet. |
| https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html | Reviewed TPE's good/bad density model and startup trials; a future search must include actual model-based trials beyond startup. |
| https://pyproj4.github.io/pyproj/stable/api/transformer.html | Coordinate transformations and explicit `always_xy=True` to preserve longitude/latitude order. |
| https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query_ball_point.html | Exact midpoint-tree broad-phase queries (`eps=0`, bounded worker count) with independent physical segment refinement. |

The task-specific parsing, candidate-index completeness bound, features, reference alignment, graph routing and decoder source are independently implemented here. Their correctness and measured results require the retained test/experiment evidence; reading documentation alone is not an experiment.

## Additional workflow and HMM references

- [affaan-m/ECC](https://github.com/affaan-m/ECC), inspected revision `3f14a103a8694e51c1df9a806217a6d0b5f7a6f7`, MIT. Manually applied research-first, verification-loop and concrete code-review guidance; see [the exact scope and results](ml/ecc-review.md). No installer/global configuration or runtime library added.
- Newson and Krumm (2009), [official paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/map-matching-ACM-GIS-camera-ready.pdf), sections 3–4: primary HMM map-matching reference for graph-distance discrepancy and Viterbi. See [our implementation notes and differences](ml/hmm-method.md). No paper code, data, fitted parameters or reported accuracy was adopted as our own.
- User-provided Uber Maps talk summary: secondary background only, no URL supplied; no video inspection claimed.
