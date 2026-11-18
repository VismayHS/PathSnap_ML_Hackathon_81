# Measured baseline comparison and selection

Source: `623a20253e03fa16c1dbecd782b4abd85352789a`. Evidence: `results/experiments/baselines-local-v1/summary.json`. Five complete grouped-CV and student-testing runs took 554.69 seconds locally with two threads.

| Model | Training CV trip Macro F1 | Student accuracy | Student trip Macro F1 | Total seconds |
|---|---:|---:|---:|---:|
| logistic_regression | 0.634800 | 0.817166 | 0.650309 | 24.08 |
| knn | 0.666337 | 0.837852 | 0.706329 | 302.73 |
| random_forest | 0.721476 | 0.859009 | 0.765520 | 160.90 |
| extra_trees | 0.702618 | 0.853262 | 0.735686 | 41.40 |
| hist_gradient_boosting | 0.725219 | 0.857912 | 0.766924 | 25.57 |

Select HistGradientBoosting for Bayesian tuning because it has the highest mean held-out-trip road-class Macro F1 on the fixed 80-trip training CV. Its advantage over Random Forest is small, so this is a measured development choice, not universal superiority. Random Forest has higher student-test accuracy; student-test results are descriptive and are not the selection objective. HGB is also much cheaper in this measured run.

All five use the same five trip-group folds, candidate policy, feature set, and deterministic cap of 400 scorable fit observations per training trip. Validation and student testing are unsampled. Preprocessing is fitted inside each fold. Candidate misses count as errors. Macro F1 averages trip-local road-class Macro F1; pooled accuracy weights observations. Log loss is conditional on candidate coverage. Reference alignment remains provisional pending organizer clarification.

These are untuned classifier-only results. Bayesian tuning, trained-model HMM comparisons, final artifact export and final scientific report remain pending. The geometric M1 API bundle remains a diagnostic until final assets are integrated.
