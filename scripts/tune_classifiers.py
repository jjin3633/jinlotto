#!/usr/bin/env python3
"""Hyperparameter tuning for per-position classifiers.

Runs RandomizedSearchCV with TimeSeriesSplit per position and saves best estimators.
"""
import os
import logging
from pprint import pformat

try:
    from backend.app.services.data_service import DataService
    from backend.app.services.prediction_service import PredictionService
except Exception as e:
    print("Run from project root so imports resolve. Error:", e)
    raise

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
import joblib
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join('models')
os.makedirs(MODEL_DIR, exist_ok=True)


def tune():
    ds = DataService()
    df = ds.load_data()
    df = ds.preprocess_data(df)

    ps = PredictionService()
    features = ps._create_features(df)

    drop_cols = ['draw_number', 'draw_date', 'bonus_number'] + ps.number_columns
    X = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')
    X = X.fillna(0)

    param_dist = {
        'n_estimators': [100, 200, 400],
        'max_depth': [5, 10, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', 0.2, 0.5]
    }

    n_iter_search = 8
    tscv = TimeSeriesSplit(n_splits=5)

    for pos_idx, col in enumerate(ps.number_columns):
        logger.info(f"Tuning position {pos_idx} ({col})")
        y = df[col].astype(int)
        if len(y) < 80:
            logger.warning(f"Not enough samples for tuning position {pos_idx} (n={len(y)}). Skipping.")
            continue

        # Use single-process search on Windows to avoid multiprocessing issues
        clf = RandomForestClassifier(random_state=42, n_jobs=1)
        rs = RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=n_iter_search,
                                 cv=tscv, scoring='accuracy', n_jobs=1, random_state=42,
                                 verbose=1)

        rs.fit(X.values, y.values)
        logger.info(f"Best params for pos {pos_idx}: {pformat(rs.best_params_)}")
        best = rs.best_estimator_
        out_path = os.path.join(MODEL_DIR, f'position_{pos_idx}_clf_tuned.pkl')
        joblib.dump(best, out_path)
        logger.info(f"Saved tuned model: {out_path}")


if __name__ == '__main__':
    tune()


