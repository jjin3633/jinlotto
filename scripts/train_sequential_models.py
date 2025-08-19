#!/usr/bin/env python3
"""Train sequential (dependent) classifiers: each position model uses previous positions as features.

Saves models to models/seq_position_{i}.pkl
"""
import os
import logging
import joblib

try:
    from backend.app.services.data_service import DataService
    from backend.app.services.prediction_service import PredictionService
except Exception as e:
    print("Run from project root so imports resolve. Error:", e)
    raise

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

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

    drop_cols = ['draw_number', 'draw_date', 'bonus_number']
    base_X = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')
    base_X = base_X.fillna(0)

    # We'll train sequentially: for pos 0..5, X includes base_X + previous number columns
    for pos_idx, col in enumerate(ps.number_columns):
        logger.info(f"Training sequential classifier for pos {pos_idx} ({col})")

        X = base_X.copy()
        # include previous true labels as features during training
        for prev in range(pos_idx):
            prev_col = ps.number_columns[prev]
            X[f'prev_{prev_col}'] = df[prev_col]

        y = df[col].astype(int)
        if len(y) < 50:
            logger.warning(f"Not enough data for pos {pos_idx}, skipping")
            continue

        # simple split for quick check
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)
        clf.fit(X_train, y_train)

        train_score = clf.score(X_train, y_train)
        test_score = clf.score(X_test, y_test)
        logger.info(f"Pos {pos_idx} train_acc={train_score:.4f} test_acc={test_score:.4f}")

        path = os.path.join(MODEL_DIR, f'seq_position_{pos_idx}.pkl')
        joblib.dump(clf, path)
        logger.info(f"Saved sequential model: {path}")


if __name__ == '__main__':
    train()


