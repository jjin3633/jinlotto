#!/usr/bin/env python3
"""Show predict_proba for recent features and compute SHAP explanation for selected position models.

Outputs prob vectors (top 8) for each position and SHAP summary (top features) for chosen position(s).
"""
import os
import sys
import json
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from backend.app.services.data_service import DataService
    from backend.app.services.prediction_service import PredictionService
except Exception as e:
    print('Run from project root. Import error:', e)
    sys.exit(1)

try:
    import joblib
    import shap
except Exception as e:
    print('Required packages missing. Install shap and joblib. Error:', e)
    sys.exit(1)


def topk(vec, k=8):
    idx = np.argsort(vec)[::-1][:k]
    return [(int(i+1), float(vec[i])) for i in idx]


def main():
    ds = DataService()
    df = ds.load_data()
    df = ds.preprocess_data(df)

    ps = PredictionService()
    features = ps._create_features(df)
    # drop columns not used for training
    drop_cols = ['draw_number', 'draw_date', 'bonus_number'] + ps.number_columns
    X = features.drop(columns=[c for c in drop_cols if c in features.columns], errors='ignore')
    X = X.fillna(0)
    recent = X.tail(1)

    models_dir = os.path.join(os.getcwd(), 'models')
    prob_report = {}

    for pos in range(6):
        tuned_path = os.path.join(models_dir, f'position_{pos}_clf_tuned.pkl')
        default_path = os.path.join(models_dir, f'position_{pos}_clf.pkl')
        path = tuned_path if os.path.exists(tuned_path) else default_path
        if not os.path.exists(path):
            prob_report[f'position_{pos}'] = {'error': 'no model file'}
            continue
        clf = joblib.load(path)
        # predict_proba
        try:
            proba = clf.predict_proba(recent.values)[0]
        except Exception as e:
            prob_report[f'position_{pos}'] = {'error': str(e)}
            continue
        # map classes
        classes = clf.classes_
        vec = np.zeros(45)
        for i, c in enumerate(classes):
            if 1 <= int(c) <= 45:
                vec[int(c)-1] = float(proba[i])
        s = vec.sum()
        if s > 0:
            vec = vec / s

        prob_report[f'position_{pos}'] = {'top': topk(vec, k=8)}

    # SHAP for chosen positions
    shap_report = {}
    for pos in [1, 4]:
        path = os.path.join(models_dir, f'position_{pos}_clf_tuned.pkl')
        if not os.path.exists(path):
            path = os.path.join(models_dir, f'position_{pos}_clf.pkl')
        if not os.path.exists(path):
            shap_report[f'position_{pos}'] = {'error': 'no model file'}
            continue
        clf = joblib.load(path)
        # prepare X for SHAP: use feature matrix X computed earlier
        X_sample = X.tail(500)
        try:
            explainer = shap.TreeExplainer(clf)
            shap_values = explainer.shap_values(X_sample.values)
            # For multiclass, shap_values is list per class; compute mean abs across classes
            if isinstance(shap_values, list):
                mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
            else:
                mean_abs = np.abs(shap_values).mean(axis=0)
            feat_names = list(X_sample.columns)
            top_idx = np.argsort(mean_abs)[::-1][:20]
            top_feats = [(feat_names[i], float(mean_abs[i])) for i in top_idx]
            shap_report[f'position_{pos}'] = {'top_features': top_feats}
        except Exception as e:
            shap_report[f'position_{pos}'] = {'error': str(e)}

    out = {'prob': prob_report, 'shap': shap_report}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()


