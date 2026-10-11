"""Contract and leakage checks using the shipped artifacts; no training required."""
import io
import json
import unittest
import numpy as np
import pandas as pd
from app import read_csv
from src.core import ROOT, load_bundle, predict, explain, validate_frame

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle()
        cls.frame = pd.read_csv(ROOT / 'data/samples/demo_flows.csv').head(5)

    def test_prediction_contract(self):
        out = predict(self.frame, self.bundle)
        self.assertEqual(len(out), 5)
        self.assertTrue(all(0 <= x['attack_score'] <= 1 for x in out))

    def test_labels_ids_ports_never_change_score(self):
        contaminated = self.frame.assign(Attack_type='fake', **{'Unnamed: 0': 999, 'id.orig_p': 22, 'id.resp_p': 80})
        self.assertEqual(predict(self.frame, self.bundle), predict(contaminated, self.bundle))

    def test_column_order_invariant(self):
        self.assertEqual(predict(self.frame, self.bundle), predict(self.frame[self.frame.columns[::-1]], self.bundle))

    def test_missing_feature_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            predict(self.frame.drop(columns=['proto']), self.bundle)

    def test_nonfinite_and_negative_rejected(self):
        for value in [np.inf, np.nan, -1]:
            bad = self.frame.copy(); bad.loc[0, 'flow_duration'] = value
            with self.assertRaises(ValueError): predict(bad, self.bundle)

    def test_unknown_category_flagged(self):
        new = self.frame.copy(); new.loc[0, 'service'] = 'unseen_service'
        self.assertIn('Unseen categories', predict(new, self.bundle)[0]['quality_warning'])

    def test_threshold_monotonicity(self):
        low = sum(r['decision'] == 'Review' for r in predict(self.frame, self.bundle, .2))
        high = sum(r['decision'] == 'Review' for r in predict(self.frame, self.bundle, .8))
        self.assertGreaterEqual(low, high)
        for threshold in [-1, 2, float('nan')]:
            with self.assertRaises(ValueError): predict(self.frame, self.bundle, threshold)

    def test_duplicate_csv_header_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            read_csv('a,a\n1,2\n')

    def test_row_limit_and_empty_rejected(self):
        for frame in [self.frame.iloc[:0], pd.concat([self.frame]*1001, ignore_index=True)]:
            with self.assertRaises(ValueError): predict(frame, self.bundle)

    def test_split_hashes_unique(self):
        manifest = pd.read_csv(ROOT / 'reports/split_manifest.csv', dtype={'feature_hash': str})
        self.assertFalse(manifest.feature_hash.duplicated().any())
        self.assertEqual(set(manifest.split), {'train', 'validation', 'test'})

    def test_explanation_consistent(self):
        explanation = explain(self.frame, 0, self.bundle)
        score = predict(self.frame, self.bundle)[0]['attack_score']
        self.assertAlmostEqual(explanation['attack_score'], score, places=5)
        self.assertTrue(explanation['features'])
        for feature in explanation['features']:
            self.assertNotIn(feature['feature'], ['Attack_type', 'Unnamed: 0', 'id.orig_p', 'id.resp_p'])

    def test_report_matches_saved_test_predictions(self):
        m = json.loads((ROOT / 'reports/metrics.json').read_text())
        p = pd.read_csv(ROOT / 'reports/test_predictions.csv')
        t = m['test'][m['selected_model']]
        attack = p.ground_truth.ne('Benign')
        self.assertEqual(int((attack & p.alert).sum()), t['tp'])
        self.assertEqual(int((~attack & p.alert).sum()), t['fp'])
        self.assertEqual(int((attack & ~p.alert).sum()), t['fn'])
        self.assertEqual(int((~attack & ~p.alert).sum()), t['tn'])

if __name__ == '__main__':
    unittest.main()
