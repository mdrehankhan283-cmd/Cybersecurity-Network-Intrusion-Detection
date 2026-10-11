# Verification record

- Training, baseline comparison and test evaluation ran on the bundled UCI data.
- Twelve unittest checks passed; see test_verification.txt.
- Local HTTP prediction returned 158 sample results; feature explanation returned 15 diagnostics.
- Invalid schema, threshold, duplicate headers, empty input, cross-origin requests and incorrect content type were rejected.
- Dashboard DOM integration ran against the actual local Python API using jsdom: loading, pagination, explanation, model-evidence tabs, threshold application/reset, filtering, export handler and bad-upload state cleanup passed with no JavaScript errors.
- CLI inference completed on the bundled 158-row sample.
- All 8 analysis notebook code cells executed successfully; outputs are embedded.
- Python sources compile; dashboard JavaScript passes Node syntax checking.
- Evaluation chart was rendered and visually inspected.

Browser pixel/layout inspection was not completed because a Chromium binary could not be downloaded in this environment. DOM tests are not a substitute for browser visual testing. The Windows launcher was inspected but not executed on Windows; inference and API tests ran on Linux with Python 3.12.14.

The optional raw-data download fallback was exercised during source acquisition. Training uses the included source archive and checks its SHA-256 against source.json. Runtime package versions are recorded in environment.json and requirements.txt.
