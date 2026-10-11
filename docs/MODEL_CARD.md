# Model card — NetGuard v1

| Field | Value |
|---|---|
| Intended use | Educational/research analysis of RT-IoT2022-compatible completed flow records |
| Primary model | Random forest, 180 trees, depth ≤20, minimum leaf 2 |
| Secondary model | Random forest, 140 trees, known attack-family suggestion |
| Features | 79 numeric + proto/service; no row ID, labels or ports |
| Training cohort | 10,957 deduplicated, non-conflicting records |
| Decision threshold | 0.531748169685, validation-selected |
| Score interpretation | Uncalibrated class score, not incident probability |
| Test support | 3,653 patterns: 1,262 attack, 2,391 benign |
| Recall / FPR | 99.45% / 1.25% |
| Family macro-F1 | 0.8564 |
| Explainability | Validation permutation importance; per-flow one-feature median sensitivity |
| Runtime | Python 3.12; exact package versions in requirements.txt |

## Out of scope

Raw packet inference, online capture, arbitrary flow schemas, zero-day detection,
production SLAs, calibrated incident probabilities, automatic blocking and attribution
to a human or organization are not supported claims.

## Known weaknesses

Lab context, potential near-duplicate/capture correlation, changed prevalence after
deduplication, removed ambiguous groups, protocol/service shortcuts, few examples
of several attacks, unknown future traffic and no validated live feature adapter.
NMAP_FIN_SCAN family recall is 0/1 on test. The source-class description on the UCI
landing page differs from the downloaded file; this project follows the actual CSV.

Quality flags are limited to unseen categories and numeric values outside training
ranges. Being in range does not establish that an observation is in distribution.
A no-alert decision does not establish safety. Family suggestion scores can be low
and are separate from the binary attack score.

## Reproduction and governance

Source hashes, feature-hash split membership and runtime metadata are stored in
reports. No test-driven threshold tuning is performed. If further changes are
selected after viewing these test results, obtain a new independent final test set.
A real deployment needs a matching extractor, external validation and human-review
workflow. See RESULTS.md and docs/DEPLOYMENT.md for details.
