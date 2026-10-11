# Explain the project confidently

## 45-second introduction

“NetGuard is an IoT network-flow intrusion-detection research project. I used the
public RT-IoT2022 dataset, removed exact duplicate model-input patterns and conflicting
labels, and compared logistic regression with a random forest. I selected the model
and alert threshold on a validation partition, then evaluated on a held-out test set.
The dashboard scores CSV flows, suggests attack families, and offers feature-sensitivity
diagnostics. Its main limitation is that this is controlled lab traffic, so I would
need session/device/time-separated external validation before production use.”

Adapt this only after you have run the project and understand the implementation.
Disclose AI assistance if your institution asks; do not claim deployment experience.

## Questions you should be ready to answer

**Why remove duplicate inputs before splitting?**
The same model-visible feature vector in train and test can create overly optimistic
results. Hashing only retained features catches exact duplicates even when ports/IDs differ.
It does not solve near duplicates or capture-level correlation.

**Why remove ports and row IDs?**
Row IDs can reveal ordering, and ports can be device/service shortcuts. Removing them
reduces some shortcut opportunities. Protocol and service can still encode lab context;
external validation remains necessary. A port ablation is a useful future experiment.

**Why 60/20/20?**
Training fits model parameters. Validation selects the model and threshold. The test
partition is evaluated after those choices. Preprocessing is fit on training only.
Global deterministic duplicate/conflict cleaning defines the benchmark cohort before
splitting; it is explicitly not an untouched raw traffic distribution.

**Why not focus on accuracy?**
Class imbalance and rare attacks can hide failures. We report precision, recall,
average precision, F2, false-positive rate, the confusion matrix and per-family results.

**Why F2?**
It weights recall more than precision. A validation false-positive-rate constraint
adds a workload consideration. The test FPR is 1.25%, so the ≤1% validation target
does not carry over exactly even to this held-out partition.

**Is the score a probability?**
It is the model's `predict_proba` output, displayed as an uncalibrated score. It is
not a calibrated probability that an incident is real on an arbitrary network.

**What does the explanation do?**
It replaces one of 15 globally important numeric features with its benign training
median and measures the score change. It is not SHAP; feature interactions and
correlation can distort the explanation. No causal claim is made.

**Can it detect unknown attacks?**
This experiment does not establish zero-day detection. It is supervised on known
families. Unknown categories/ranges are data-quality flags, not a zero-day detector.

**What was the weakest result?**
The family classifier fails the one NMAP_FIN_SCAN test example and has weaker UDP-scan
performance. Macro-F1 is lower than weighted-F1. Rare classes need more independent data.

**Why is the raw dataset much bigger than the final cohort?**
Many captured rows share the exact same retained feature vector. Deduplication reduces
123,117 rows to 18,262 usable unique vectors after conflicts are removed. It changes
class prevalence and evaluation weight, so results describe unique patterns rather
than the original flow-volume distribution.

## Study order

1. Read `reports/RESULTS.md` and reproduce the demo.
2. Open `notebooks/01_analysis.ipynb` and follow data audit and evaluation.
3. Read `src/core.py` for inference and validation.
4. Read `src/train.py` for splits, baselines and threshold selection.
5. Run `python -m unittest discover -s tests -v`.
6. Change one documented experiment at a time using validation data. If you make choices
   based on the current test results, create a fresh independent final test set.

## CV entry after you understand the work

**NetGuard — Explainable IoT Intrusion Detection | Python, scikit-learn, Pandas**

- Built a reproducible flow-classification pipeline with deduplication, stratified
  train/validation/test partitions and baseline comparison on UCI RT-IoT2022.
- Developed a local dashboard for batch scoring, attack-family suggestions, feature
  sensitivity and CSV export; documented false positives and rare-class limitations.

Avoid “real-time enterprise IDS,” “zero-day protection,” or “99% production accuracy.”
