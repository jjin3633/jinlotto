#!/usr/bin/env python3
"""Model evaluation script

- Loads lotto data via DataService
- Builds features via PredictionService._create_features
- Trains per-position RandomForestClassifier with TimeSeriesSplit
- Computes top-1 and top-3 accuracy per fold and position
- Writes results to scripts/evaluation_results.csv
"""
import os
import sys
import csv
import logging
from datetime import datetime

try:
    from backend.app.services.data_service import DataService
    from backend.app.services.prediction_service import PredictionService
except Exception as e:
    print("Please run this script from the project root so imports resolve. Error:", e)
    sys.exit(1)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit
    import numpy as np
except Exception as e:
    print("scikit-learn is required to run evaluation. Install requirements. Error:", e)
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def topk_accuracy_score(probas, y_true, k=3):
    """Compute top-k accuracy from probability matrix.
    probas: ndarray (n_samples, n_classes)
    y_true: array-like (n_samples,)
    """
    topk = np.argsort(probas, axis=1)[:, ::-1][:, :k]
    matches = [int(y in topk_row) for y, topk_row in zip(y_true, topk)]
    return float(np.mean(matches))


def evaluate():
    ds = DataService()
    df = ds.load_data()
    df = ds.preprocess_data(df)

    ps = PredictionService()
    features = ps._create_features(df)

    # Prepare X (drop metadata and raw numbers)
    drop_cols = ['draw_number', 'draw_date', 'bonus_number'] + ps.number_columns
    X = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')

    results = []

    n_splits = 5
    tscv = TimeSeriesSplit(n_splits=n_splits)

    rng = list(range(1, 46))

    for pos_idx, col in enumerate(ps.number_columns):
        y = df[col].astype(int).to_numpy()
        X_vals = X.fillna(0).to_numpy()

        fold = 0
        top1_scores = []
        top3_scores = []

        for train_idx, test_idx in tscv.split(X_vals):
            fold += 1
            X_train, X_test = X_vals[train_idx], X_vals[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # require minimal training size
            if len(y_train) < 30:
                logger.warning(f"Not enough samples for pos {pos_idx} fold {fold}, skipping")
                continue

            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train, y_train)

            probas = clf.predict_proba(X_test)
            # map class ordering to original label index
            classes = clf.classes_
            # build full prob matrix indexed by number 1..45
            prob_matrix = np.zeros((probas.shape[0], 45))
            for i, c in enumerate(classes):
                if 1 <= int(c) <= 45:
                    prob_matrix[:, int(c) - 1] = probas[:, i]

            # compute top-1/top-3 using prob_matrix and true labels
            y_test_zero_based = y_test - 1
            top1 = topk_accuracy_score(prob_matrix, y_test_zero_based, k=1)
            top3 = topk_accuracy_score(prob_matrix, y_test_zero_based, k=3)
            top1_scores.append(top1)
            top3_scores.append(top3)

            logger.info(f"Pos {pos_idx} fold {fold} top1={top1:.4f} top3={top3:.4f}")

        if top1_scores:
            results.append({
                'position': pos_idx,
                'top1_mean': float(np.mean(top1_scores)),
                'top3_mean': float(np.mean(top3_scores)),
                'folds': len(top1_scores)
            })

    # Write CSV
    out_path = os.path.join('scripts', 'evaluation_results.csv')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['position', 'top1_mean', 'top3_mean', 'folds'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logger.info(f"Evaluation complete. Results written to {out_path}")


if __name__ == '__main__':
    evaluate()


