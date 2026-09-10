"""XGBoost hyperparameter optimization via RandomizedSearchCV with stratified CV.

When the training data is class-imbalanced and SMOTE is used, SMOTE must be
applied INSIDE each cross-validation fold, not once before splitting into
folds. Resampling first and then doing plain K-fold on the resampled set
lets synthetic minority samples (near-duplicates of real ones) land in a
fold's training partition while their "parent" sample sits in that same
fold's validation partition, leaking information across the split and
inflating CV scores — which then misleads hyperparameter selection itself,
picking parameters that look best on leaked folds rather than parameters
that generalize. This module avoids that via an imblearn Pipeline, which
re-fits SMOTE fresh inside every fold.
"""
import logging

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from scipy.stats import randint, uniform
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from xgboost import XGBClassifier

from app.config import settings

logger = logging.getLogger(__name__)

PARAM_DISTRIBUTIONS = {
    "clf__n_estimators": randint(100, 500),
    "clf__max_depth": randint(3, 9),
    "clf__learning_rate": uniform(0.01, 0.19),
    "clf__subsample": uniform(0.6, 0.4),
    "clf__colsample_bytree": uniform(0.6, 0.4),
    "clf__min_child_weight": randint(1, 10),
    "clf__gamma": uniform(0, 5),
    "clf__reg_alpha": uniform(0, 2),
    "clf__reg_lambda": uniform(0, 2),
}


def tune_xgboost(X_train, y_train, n_iter: int = 30, cv_folds: int = 5, apply_smote: bool = True):
    """Run RandomizedSearchCV over XGBoost hyperparameters.

    X_train/y_train must be the ORIGINAL training split (not pre-resampled
    by SMOTE) — when `apply_smote` is True, SMOTE is applied fresh inside
    each CV fold by the pipeline below, then the whole pipeline is refit on
    all of X_train/y_train for the final estimator (scikit-learn's default
    RandomizedSearchCV `refit=True` behavior).

    Returns (best_estimator, best_params, best_score) where best_estimator
    is a plain, already-fitted XGBClassifier (the pipeline's "clf" step) —
    not a pipeline — ready to persist and pass to shap.TreeExplainer.
    """
    base_model = XGBClassifier(random_state=settings.random_state, eval_metric="logloss")
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=settings.random_state)

    steps = [("smote", SMOTE(random_state=settings.random_state))] if apply_smote else []
    steps.append(("clf", base_model))
    pipeline = ImbPipeline(steps)

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=n_iter,
        scoring="f1",
        cv=cv,
        random_state=settings.random_state,
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)

    best_clf_params = {k.replace("clf__", ""): v for k, v in search.best_params_.items()}
    logger.info("Best XGBoost params: %s (leak-free CV F1=%.4f)", best_clf_params, search.best_score_)

    best_estimator = search.best_estimator_.named_steps["clf"]
    return best_estimator, best_clf_params, search.best_score_
