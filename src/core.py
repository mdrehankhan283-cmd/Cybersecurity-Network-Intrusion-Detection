"""Shared schema, model scoring and inference contract."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
BENIGN = {'MQTT_Publish', 'Thing_Speak', 'Wipro_bulb'}
EXCLUDED = {'Unnamed: 0', 'Attack_type', 'id.orig_p', 'id.resp_p'}
CATEGORICAL = ['proto', 'service']

def signed_log1p(x):
    return np.sign(x) * np.log1p(np.abs(x))

def load_bundle():
    # Load only this project's locally generated, trusted artifact.
    return joblib.load(ROOT / 'models/netguard.joblib')

def validate_frame(frame, bundle):
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError('CSV must contain at least one flow.')
    if len(frame) > 5000:
        raise ValueError('Maximum 5,000 flows per request. Split larger files.')
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names are not allowed.')
    features = bundle['features']
    missing = [c for c in features if c not in frame]
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing[:10]))
    out = frame.loc[:, features].copy()
    for c in features:
        if c in CATEGORICAL:
            if out[c].isna().any() or out[c].astype(str).str.strip().eq('').any():
                raise ValueError(f'{c}: empty values are not allowed.')
            out[c] = out[c].astype(str)
        else:
            try:
                out[c] = pd.to_numeric(out[c], errors='raise').astype(float)
            except (ValueError, TypeError):
                raise ValueError(f'{c}: all values must be numeric.') from None
            if not np.isfinite(out[c].to_numpy()).all():
                raise ValueError(f'{c}: missing or infinite values are not allowed.')
            if (out[c] < 0).any():
                raise ValueError(f'{c}: expected non-negative values for this dataset schema.')
    return out

def predict(frame, bundle, threshold=None):
    threshold = bundle['threshold'] if threshold is None else float(threshold)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Threshold must be between 0 and 1.')
    x = validate_frame(frame, bundle)
    probability = bundle['detector'].predict_proba(x)[:, 1]
    family_prob = bundle['family_model'].predict_proba(x)
    classes = bundle['family_model'].classes_
    attack_idx = np.flatnonzero(classes != 'Benign')
    best = attack_idx[family_prob[:, attack_idx].argmax(axis=1)]
    pred_family = classes[best]
    alerts = probability >= threshold
    rows = []
    for i, (_, row) in enumerate(x.iterrows()):
        unknown = [c for c in CATEGORICAL if row[c] not in bundle['categories'][c]]
        outside = [c for c, stats in bundle['reference'].items()
                   if row[c] < stats['min'] or row[c] > stats['max']]
        rows.append({'flow_id': i + 1, 'attack_score': round(float(probability[i]), 6),
                     'decision': 'Review' if alerts[i] else 'No alert',
                     'candidate_family': str(pred_family[i]) if alerts[i] else '—',
                     'family_score': round(float(family_prob[i, best[i]]), 6) if alerts[i] else None,
                     'proto': str(row['proto']), 'service': str(row['service']),
                     'flow_duration': float(row['flow_duration']),
                     'fwd_pkts_tot': float(row['fwd_pkts_tot']),
                     'bwd_pkts_tot': float(row['bwd_pkts_tot']),
                     'quality_warning': '; '.join(([f'Unseen categories: {", ".join(unknown)}'] if unknown else []) +
                        ([f'{len(outside)} numeric features outside training range'] if outside else []))})
    return rows

def explain(frame, index, bundle):
    """One-at-a-time perturbation sensitivity; deliberately not SHAP/causality."""
    x = validate_frame(frame, bundle)
    if not 0 <= index < len(x):
        raise ValueError('Flow index is out of range.')
    row = x.iloc[[index]].copy()
    base = float(bundle['detector'].predict_proba(row)[0, 1])
    features = bundle['explain_features']
    variants = pd.concat([row.copy() for _ in features], ignore_index=True)
    for i, c in enumerate(features):
        variants.loc[i, c] = bundle['benign_medians'][c]
    scores = bundle['detector'].predict_proba(variants)[:, 1]
    result = [{'feature': c, 'observed': float(row.iloc[0][c]),
               'benign_reference': float(bundle['benign_medians'][c]),
               'score_change': round(base - float(s), 6)} for c, s in zip(features, scores)]
    return {'attack_score': base, 'method': 'Single-feature sensitivity to a benign training median',
            'caveat': 'Positive means replacing this feature reduced the score. Correlated features and implausible combinations can distort this diagnostic. This is not SHAP or a causal explanation.',
            'features': sorted(result, key=lambda d: abs(d['score_change']), reverse=True)}
