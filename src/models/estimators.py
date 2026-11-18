"""Five distinct candidate-relevance algorithms with fold-fitted preprocessing."""
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier

CONFIGS = {
 'logistic_regression': dict(C=1., solver='lbfgs', max_iter=500, random_state=81),
 'knn': dict(n_neighbors=15, weights='distance', algorithm='kd_tree', leaf_size=40, n_jobs=2),
 'random_forest': dict(n_estimators=64, max_depth=16, min_samples_leaf=8, random_state=81, n_jobs=2),
 'extra_trees': dict(n_estimators=64, max_depth=16, min_samples_leaf=8, random_state=81, n_jobs=2),
 'hist_gradient_boosting': dict(max_iter=100, max_leaf_nodes=15, min_samples_leaf=30,
                     learning_rate=.1, l2_regularization=1., early_stopping=False, random_state=81)
}
CLASSES = dict(logistic_regression=LogisticRegression, knn=KNeighborsClassifier,
              random_forest=RandomForestClassifier, extra_trees=ExtraTreesClassifier,
              hist_gradient_boosting=HistGradientBoostingClassifier)
FAMILIES = dict(logistic_regression='regularized linear', knn='instance based',
                random_forest='bagged randomized trees', extra_trees='extremely randomized trees',
                hist_gradient_boosting='histogram gradient boosting')
OBJECTIVES = dict(logistic_regression='L2-regularized binary log loss',
                 knn='distance-weighted neighbor class proportion; no fitted loss optimizer',
                 random_forest='bootstrap trees with Gini impurity splits',
                 extra_trees='random-threshold trees with Gini impurity splits',
                 hist_gradient_boosting='binary log loss with L2 leaf regularization')


def make_estimator(name, params=None):
    estimator = CLASSES[name](**{**CONFIGS[name], **(params or {})})
    steps = [('imputer', SimpleImputer(strategy='median', keep_empty_features=True))]
    if name in ('logistic_regression', 'knn'):
        steps.append(('scaler', StandardScaler()))
    return Pipeline([*steps, ('classifier', estimator)])
