#!/usr/bin/env python3
"""Train per-position RandomForestClassifier models and save them to models/.

Usage: python scripts/train_classifiers.py
"""
import os
import logging

try:
    from backend.app.services.data_service import DataService
    from backend.app.services.prediction_service import PredictionService
except Exception as e:
    print("Run this from project root so imports resolve. Error:", e)
    raise

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join('models')
os.makedirs(MODEL_DIR, exist_ok=True)


def train():
    ds = DataService()
    df = ds.load_data()
    df = ds.preprocess_data(df)

    ps = PredictionService()
    features = ps._create_features(df)

    drop_cols = ['draw_number', 'draw_date', 'bonus_number'] + ps.number_columns
    X = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')
    X = X.fillna(0)

    for pos_idx, col in enumerate(ps.number_columns):
        logger.info(f"Training classifier for position {pos_idx} ({col})")
        y = df[col].astype(int)

        if len(y) < 50:
            logger.warning(f"Not enough samples for position {pos_idx} (n={len(y)}). Skipping.")
            continue

        # time-based split: use last 20% as test for quick check
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        clf.fit(X_train, y_train)

        # quick eval
        train_score = clf.score(X_train, y_train)
        test_score = clf.score(X_test, y_test)
        logger.info(f"Pos {pos_idx} train_acc={train_score:.4f} test_acc={test_score:.4f}")

        model_path = os.path.join(MODEL_DIR, f'position_{pos_idx}_clf.pkl')
        joblib.dump(clf, model_path)
        logger.info(f"Saved classifier: {model_path}")


if __name__ == '__main__':
    train()


