# From research prototype to operational evaluation

## What works now

- A localhost dashboard and JSON endpoints score completed flow-feature records.
- The bundled test sample, CLI, feature contract, model artifacts and benchmark work offline after installation.
- No live packet capture, packet blocking, SIEM connection, authentication service or cloud hosting is included.

## Endpoint contract

`GET /api/health`: readiness. `GET /api/meta`: fixed metrics, audit, schema and importance.
`GET /api/sample`: held-out sample CSV. `GET /sample.csv`: downloadable sample.

`POST /api/predict` with JSON `{ "csv": "<CSV text>", "threshold": 0.532 }` returns rows.
Omit threshold to use the exact saved validation threshold. `POST /api/explain` takes
`{ "csv": "<CSV text>", "index": 0 }` for a zero-based flow index. The UI displays one-based IDs.

```python
import json
from urllib.request import Request, urlopen
from pathlib import Path
payload = json.dumps({'csv': Path('data/samples/demo_flows.csv').read_text()}).encode()
request = Request('http://127.0.0.1:8501/api/predict', data=payload,
                  headers={'Content-Type': 'application/json'})
result = json.load(urlopen(request))
print(result['rows'][0])
```

Maximum 5,000 rows / 8 MB JSON body. Duplicate headers, missing features, empty
categories, nonnumeric values, NaN, infinity and negative numeric values are rejected.
Unknown nonempty categories are accepted through one-hot `handle_unknown='ignore'`
and flagged. Extras such as labels and ports are ignored, not used as evidence.

## Feature extraction is a deployment gate

RT-IoT2022 was extracted using Zeek plus a Flowmeter plugin. Merely renaming columns
from CICFlowMeter, NFStream or standard Zeek logs is not a validated conversion.
Numeric units, timeout policy, forward/backward direction, flag counts and rate
definitions must match. The export has no validated live adapter here.
Do not infer rates from a tiny subset of fields or fill missing features with zeros.

Before a pilot:

1. Reproduce original feature definitions and units; compare known captures against an approved extraction reference.
2. Collect authorized, representative benign and labeled attack traffic on the target network.
3. Hold out entire devices, sessions, sites and later time periods. Keep those groups out of model and threshold selection.
4. Assess alert volume, rare-family recall and precision under realistic low attack prevalence.
5. Calibrate scores on separate data if probabilities are required; choose thresholds using analyst capacity and threat costs.
6. Operate in shadow mode with human review, record outcomes, monitor drift and define rollback criteria.

Changing attack prevalence changes alert precision, even at the same TPR/FPR.
For example, assuming 99.45% TPR and 1.25% FPR transferred unchanged (unproven), at
0.1% attack prevalence the implied precision would be only about 7.4%. A strong lab
score alone therefore does not justify automatic blocking.

The bundled server binds to localhost and is intended for local use. It is not an
internet-facing application server. A multi-user deployment would need authentication,
TLS, request timeouts/rate limits, model/version controls, privacy review and operational
logging appropriate to that deployment. Never accept arbitrary uploaded joblib files;
serialized Python models must be trusted.
