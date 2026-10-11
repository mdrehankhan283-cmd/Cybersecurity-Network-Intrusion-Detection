# NetGuard
### Explainable IoT Network Intrusion Detection

A complete, runnable Data Science project for investigating suspicious network-flow
patterns: real-device benchmark data, reproducible training, honest held-out evaluation,
and a local dashboard with CSV scoring and feature-sensitivity diagnostics.

**Python 3.12 · scikit-learn · Pandas · Random Forest · Local HTML dashboard**

![Held-out evaluation and feature importance](reports/figures/evaluation.png)

## Run in minutes

**Windows:** extract this project, install Python 3.12, then double-click
`START_WINDOWS.bat`. Keep the command window open. Click **Load real-data demo**.
Hindi instructions: [START_HERE.md](START_HERE.md).

**macOS / Linux:** with Python 3.12 available, run `bash start.sh`.

Manual setup:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8501 if the browser does not open automatically.
Pretrained artifacts and held-out sample CSVs are included; no training or API key
is needed to try the app. Internet is needed for the first dependency installation.
Only load the bundled/trusted model artifact: joblib is a Python serialization format.

## What is included

- Binary attack detector selected against logistic-regression and majority baselines.
- Separate candidate attack-family classifier, with rare-class weaknesses reported.
- Validation-selected review threshold, confusion matrix and per-family recall.
- CSV upload, strict feature validation, range/category quality flags and results export.
- Per-flow sensitivity analysis and validation permutation importance.
- A documented raw source archive, trained models, executed analysis notebook and tests.
- Hindi setup instructions, interview guide, model card and deployment-gap documentation.

This is **offline flow scoring** on real-device lab data. It is not a connected live
IDS, packet sniffer, automatic blocker or production-certified security product.

## Actual held-out results

| Metric | Random forest |
|---|---:|
| Test patterns | 3,653 |
| Attack recall | 99.45% |
| Attack precision | 97.67% |
| False-positive rate | 1.25% |
| Detected / missed attacks | 1255 / 7 |
| False alerts / benign patterns | 30 / 2391 |

These are cleaned, within-dataset benchmark results, not production guarantees.
The 1% validation FPR target becomes 1.25% on test. Exact-feature deduplication reduces
123,117 raw records to 18,262 usable unique patterns and substantially changes class
prevalence. NMAP_FIN_SCAN has only one test example; its family label is misclassified.
See the full [results report](reports/RESULTS.md) and [model card](docs/MODEL_CARD.md).

## Method

1. Verify UCI source archive and inspect actual CSV labels.
2. Remove source/destination ports, row ID and target from features.
3. Remove conflicting-label groups and deduplicate exact model-input vectors.
4. Split 60/20/20 by attack family, seed 42; assert no feature-hash overlap.
5. Fit preprocessing and models only on train. Select threshold/model on validation.
6. Evaluate once on test and retain predictions, audit trail and uncertainty estimates.
7. Serve inference locally through the same feature-validation and model pipeline.

Data is from a real IoT testbed with controlled attacks. Near duplicates and shared
capture conditions may remain; no trustworthy time/session/device split is available.
Protocol/service features may still encode lab shortcuts. External validation is required.

## Project map

| Path | Purpose |
|---|---|
| `app.py`, `web/index.html` | Local HTTP app and responsive dashboard |
| `predict.py` | Batch CLI inference |
| `src/core.py` | Feature validation, scoring, sensitivity |
| `src/train.py`, `src/download.py` | Reproducible training and verified download |
| `models/netguard.joblib` | Trusted pretrained detector and family model |
| `data/samples/` | Held-out demonstration CSV and separate true labels |
| `data/raw/rt-iot2022.zip` | Original attributed dataset archive in the download package |
| `notebooks/01_analysis.ipynb` | Executed data audit, EDA and evaluation walkthrough |
| `reports/` | Metrics, hashes, splits, predictions, plots and experiment report |
| `docs/` | Model card, field deployment notes and interview guide |
| `tests/` | Inference, leakage and report consistency checks |

## CLI and reproduction

```bash
python predict.py data/samples/demo_flows.csv --output predictions.csv
python -m unittest discover -s tests -v
# Training/plots/notebook dependencies are optional for ordinary inference:
python -m pip install -r requirements-dev.txt
python -m src.train
jupyter lab notebooks/01_analysis.ipynb
```

Training overwrites the generated reports and model. The raw archive is already
bundled in this ZIP; `src.download` fetches it from UCI if absent. Checksums protect
against silently changed data. Runtime versions are pinned; exact binary artifact
bytes may still differ across platforms, so compare metrics and split manifests.

## Input contract

Use the exact 81 features in `reports/schema.json`. Up to 5,000 rows per request.
`data/samples/demo_flows.csv` is the template. Label, ID and port columns are ignored.
Generic PCAP, Zeek conn.log and CICFlowMeter files are not drop-in compatible.
The project does not include a validated live feature extractor. No fabricated
features or zero-filled schema conversion is used. See [deployment notes](docs/DEPLOYMENT.md).

## GitHub and presentation

Suggested repository: `netguard-intrusion-detection`. Put this folder's contents at
repository root so this README renders. Do not upload `.venv`, caches or the expanded
raw CSV. The raw ZIP is ignored by Git; the download script retrieves it for retraining.
Include the model, sample files and reports to make the demonstration easy to run.
GitHub Pages cannot execute this Python model; there is no public hosted demo in this package.

Start with [interview preparation](docs/INTERVIEW_GUIDE.md). Understand the code and
limitations before describing the project as your work. A methodologically clear
benchmark is more useful than an unsupported “99% production accuracy” claim.

## Verification

Training, 12 unit checks, local API/CLI inference, 8 notebook cells and dashboard DOM
flows were exercised. See [verification record](reports/VERIFICATION.md) for exact
coverage and the unperformed browser-layout / Windows-runtime checks.

## Attribution and licenses

Dataset: S., B. & Nagapadma, R. (2023), **RT-IoT2022**, UCI Machine Learning Repository.
[DOI 10.24432/C5P338](https://doi.org/10.24432/C5P338). Dataset and derived samples:
**CC BY 4.0**. Original code: **MIT**. See [DATA_LICENSE.md](DATA_LICENSE.md) and [LICENSE](LICENSE).
