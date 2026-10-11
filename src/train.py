"""Deterministic split, validation-only selection, and one held-out evaluation."""
import hashlib
import json
import platform
import time
import warnings
import numpy as np
import pandas as pd
import sklearn
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (average_precision_score, roc_auc_score, confusion_matrix,
    precision_score, recall_score, f1_score, fbeta_score, balanced_accuracy_score,
    classification_report, precision_recall_curve, roc_curve)
from sklearn.inspection import permutation_importance
from .core import ROOT, BENIGN, EXCLUDED, CATEGORICAL, signed_log1p
from .download import main as download

SEED = 42

def dump(name, obj):
    (ROOT / 'reports' / name).write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')

def metrics(y, score, threshold):
    pred = score >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {k: float(v) for k, v in {
        'average_precision': average_precision_score(y, score), 'roc_auc': roc_auc_score(y, score),
        'precision': precision_score(y, pred, zero_division=0), 'recall': recall_score(y, pred),
        'f1': f1_score(y, pred), 'f2': fbeta_score(y, pred, beta=2),
        'balanced_accuracy': balanced_accuracy_score(y, pred),
        'false_positive_rate': fp / max(1, tn + fp), 'threshold': threshold}.items()} | {
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp), 'n': len(y)}

def choose_threshold(y, score):
    candidates = np.unique(np.r_[np.linspace(0.01, 1, 100), score])
    # Empirical validation FPR <= 1%; it is a selection target, not an SLA.
    records = [metrics(y, score, t) for t in candidates]
    eligible = [r for r in records if r['false_positive_rate'] <= .01]
    if not eligible:
        return 1.0, False
    best = max(eligible, key=lambda r: (r['f2'], r['precision'], r['threshold']))
    return best['threshold'], True

def prep(features, linear=False):
    numeric = [c for c in features if c not in CATEGORICAL]
    steps = [('impute', SimpleImputer(strategy='median'))]
    if linear:
        steps += [('log', FunctionTransformer(signed_log1p, feature_names_out='one-to-one')),
                  ('scale', StandardScaler())]
    return ColumnTransformer([('numeric', Pipeline(steps), numeric),
                              ('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL)])

def main():
    for name in ['reports', 'models', 'data/samples', 'reports/figures']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    download()
    raw_path = ROOT / 'data/raw/RT_IOT2022'
    raw = pd.read_csv(raw_path)
    features = [c for c in raw if c not in EXCLUDED]
    family = raw.Attack_type.where(~raw.Attack_type.isin(BENIGN), 'Benign')
    # Hash only the model-visible vector. Exact matches never cross splits.
    hashes = pd.util.hash_pandas_object(raw[features], index=False).astype(str)
    groups = pd.DataFrame({'hash': hashes, 'family': family})
    conflicting = groups.groupby('hash').family.nunique()
    conflict_hashes = set(conflicting[conflicting > 1].index)
    good = ~hashes.isin(conflict_hashes)
    keep = good & ~hashes.duplicated()
    x = raw.loc[keep, features].reset_index(drop=True)
    labels = family[keep].reset_index(drop=True)
    h = hashes[keep].reset_index(drop=True)
    ids = np.arange(len(x))
    train, remainder = train_test_split(ids, test_size=.4, stratify=labels, random_state=SEED)
    val, test = train_test_split(remainder, test_size=.5, stratify=labels.iloc[remainder], random_state=SEED)
    assert not (set(h.iloc[train]) & set(h.iloc[val]) or set(h.iloc[train]) & set(h.iloc[test]) or set(h.iloc[val]) & set(h.iloc[test]))
    y = (labels != 'Benign').astype(int)
    audit = {'raw_rows': len(raw), 'model_features': len(features), 'excluded_columns': sorted(EXCLUDED),
             'conflicting_hashes': len(conflict_hashes), 'conflict_rows_removed': int((~good).sum()),
             'duplicate_rows_removed': int((good & hashes.duplicated()).sum()), 'unique_rows_used': len(x),
             'seed': SEED, 'split_method': '60/20/20 stratified by collapsed family after feature-vector deduplication',
             'overlapping_feature_hashes': 0, 'raw_class_counts': raw.Attack_type.value_counts().to_dict(),
             'splits': {name: {'n': len(idx), 'families': labels.iloc[idx].value_counts().to_dict()}
                        for name, idx in [('train', train), ('validation', val), ('test', test)]}}
    dump('data_audit.json', audit)
    train_ids, val_ids = set(train), set(val)
    pd.DataFrame({'feature_hash': h, 'split': ['train' if i in train_ids else 'validation' if i in val_ids else 'test' for i in ids]}).to_csv(ROOT / 'reports/split_manifest.csv', index=False)
    dump('source.json', {'name': 'RT-IoT2022', 'url': 'https://archive.ics.uci.edu/dataset/942/rt-iot2022',
         'doi': '10.24432/C5P338', 'license': 'CC BY 4.0', 'archive_sha256': hashlib.sha256((ROOT / 'data/raw/rt-iot2022.zip').read_bytes()).hexdigest(),
         'csv_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
         'note': 'Downloaded file labels/counts are authoritative; the landing-page normal-label description differs.'})
    candidates = {
       'Majority baseline': Pipeline([('prep', prep(features)), ('model', DummyClassifier(strategy='prior'))]),
       'Logistic regression': Pipeline([('prep', prep(features, True)), ('model', LogisticRegression(max_iter=2000, class_weight='balanced', random_state=SEED))]),
       'Random forest': Pipeline([('prep', prep(features)), ('model', RandomForestClassifier(n_estimators=180, max_depth=20, min_samples_leaf=2, class_weight='balanced_subsample', n_jobs=2, random_state=SEED))])}
    validation = {}
    for name, model in candidates.items():
        start = time.time()
        model.fit(x.iloc[train], y.iloc[train])
        score = model.predict_proba(x.iloc[val])[:, 1]
        threshold, met = choose_threshold(y.iloc[val], score)
        validation[name] = metrics(y.iloc[val], score, threshold) | {'fpr_target_met': met, 'fit_seconds': round(time.time() - start, 3)}
        print(name, validation[name], flush=True)
    eligible_names = [n for n in candidates if n != 'Majority baseline' and validation[n]['fpr_target_met']]
    if not eligible_names:
        eligible_names = [n for n in candidates if n != 'Majority baseline']
    selected = max(eligible_names, key=lambda n: validation[n]['f2'])
    detector = candidates[selected]
    threshold = validation[selected]['threshold']
    family_model = Pipeline([('prep', prep(features)), ('model', RandomForestClassifier(n_estimators=140, max_depth=22,
                 min_samples_leaf=1, class_weight='balanced_subsample', n_jobs=2, random_state=SEED))])
    family_model.fit(x.iloc[train], labels.iloc[train])
    test_results = {name: metrics(y.iloc[test], model.predict_proba(x.iloc[test])[:, 1], validation[name]['threshold']) for name, model in candidates.items()}
    scores = detector.predict_proba(x.iloc[test])[:, 1]
    family_predictions = family_model.predict(x.iloc[test])
    family_report = classification_report(labels.iloc[test], family_predictions, output_dict=True, zero_division=0)
    per_family = {}
    for label in sorted(labels.unique()):
        subset = labels.iloc[test].to_numpy() == label
        per_family[label] = {'n': int(subset.sum()), 'alert_rate': float((scores[subset] >= threshold).mean())}
    # Fixed-model, row bootstrap: this does not capture training/domain uncertainty.
    rng = np.random.default_rng(SEED)
    boots = []
    yt = y.iloc[test].to_numpy()
    for _ in range(300):
        b = rng.integers(0, len(test), len(test))
        boots.append([average_precision_score(yt[b], scores[b]), recall_score(yt[b], scores[b] >= threshold),
                      ((scores[b] >= threshold) & (yt[b] == 0)).sum() / max(1, (yt[b] == 0).sum())])
    intervals = {k: np.quantile(np.asarray(boots)[:, i], [.025, .975]).tolist() for i, k in enumerate(['average_precision', 'recall', 'false_positive_rate'])}
    results = {'selected_model': selected, 'threshold': threshold, 'validation': validation, 'test': test_results,
               'per_family_detection': per_family, 'family_classification': family_report, 'bootstrap_95_percent': intervals,
               'notes': ['Test never used for training, model choice or threshold choice.',
                         'Bootstrap intervals assume independent held-out rows; capture correlation is not represented.',
                         'Random split cannot establish future-time, unseen-device or external-network generalization.',
                         'Scores are uncalibrated model scores, not incident probabilities.']}
    dump('metrics.json', results)
    # Global diagnostic on validation only, not a feature-selection step.
    pv = permutation_importance(detector, x.iloc[val], y.iloc[val], scoring='average_precision', n_repeats=3, random_state=SEED, n_jobs=2)
    importance = pd.DataFrame({'feature': features, 'mean_ap_drop': pv.importances_mean, 'std_ap_drop': pv.importances_std}).sort_values('mean_ap_drop', ascending=False)
    importance.to_csv(ROOT / 'reports/permutation_importance.csv', index=False)
    numeric = [c for c in features if c not in CATEGORICAL]
    benign_train = x.iloc[train][y.iloc[train].to_numpy() == 0]
    bundle = {'detector': detector, 'family_model': family_model, 'features': features, 'threshold': threshold,
              'selected_model': selected, 'sklearn_version': sklearn.__version__,
              'categories': {c: sorted(x.iloc[train][c].unique().tolist()) for c in CATEGORICAL},
              'reference': {c: {'min': float(x.iloc[train][c].min()), 'max': float(x.iloc[train][c].max())} for c in numeric},
              'benign_medians': benign_train[numeric].median().to_dict(),
              'explain_features': [c for c in importance.feature if c in numeric][:15]}
    joblib.dump(bundle, ROOT / 'models/netguard.joblib', compress=3)
    dump('schema.json', {'required_features': features, 'categorical': CATEGORICAL,
                         'numeric': numeric, 'ignored_columns': sorted(EXCLUDED),
                         'accepted_categories': bundle['categories'], 'maximum_rows': 5000})
    # A balanced illustration of held-out families, not representative prevalence.
    demo_idx = pd.DataFrame({'idx': test, 'family': labels.iloc[test].to_numpy()}).groupby('family', group_keys=False).sample(frac=1, random_state=SEED).groupby('family').head(25)['idx'].to_numpy()
    rng.shuffle(demo_idx)
    x.iloc[demo_idx].to_csv(ROOT / 'data/samples/demo_flows.csv', index=False)
    pd.DataFrame({'flow_id': range(1, len(demo_idx)+1), 'ground_truth': labels.iloc[demo_idx].to_numpy()}).to_csv(ROOT / 'data/samples/demo_labels.csv', index=False)
    pd.DataFrame({'feature_hash': h.iloc[test].to_numpy(), 'ground_truth': labels.iloc[test].to_numpy(), 'attack_score': scores,
                  'alert': scores >= threshold, 'family_prediction': family_predictions}).to_csv(ROOT / 'reports/test_predictions.csv', index=False)
    dump('environment.json', {'python': platform.python_version(), 'sklearn': sklearn.__version__, 'numpy': np.__version__, 'pandas': pd.__version__, 'joblib': joblib.__version__})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    precision, recall, _ = precision_recall_curve(yt, scores)
    axes[0].plot(recall, precision, color='#0d9488'); axes[0].set(xlabel='Recall', ylabel='Precision', title='Held-out precision–recall')
    axes[0].axhline(yt.mean(), linestyle='--', color='gray', label='Attack prevalence'); axes[0].legend()
    cm = confusion_matrix(yt, scores >= threshold)
    axes[1].imshow(cm, cmap='Blues'); axes[1].grid(False)
    for (i, j), v in np.ndenumerate(cm): axes[1].text(j, i, str(v), ha='center', va='center', color='white' if v > cm.max()/2 else 'black', fontsize=16)
    axes[1].set(xticks=[0,1], yticks=[0,1], xticklabels=['No alert','Alert'], yticklabels=['Benign','Attack'], title='Confusion matrix', xlabel='Decision', ylabel='True label')
    top = importance.head(8).iloc[::-1]
    axes[2].barh(top.feature, top.mean_ap_drop, color='#0d9488'); axes[2].set(title='Validation permutation importance', xlabel='Average precision decrease')
    fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/evaluation.png', dpi=160); plt.close(fig)
    print('COMPLETE', selected, 'test:', test_results[selected], flush=True)

if __name__ == '__main__':
    main()
