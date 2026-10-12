"""Local dashboard + bounded JSON API. No external web services required."""
import argparse
import csv
import io
import json
import threading
import webbrowser
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import pandas as pd
from src.core import ROOT, load_bundle, predict, explain

MAX_BODY = 8 * 1024 * 1024
LOCK = threading.Lock()

def read_csv(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Upload a non-empty CSV file.')
    headers = next(csv.reader(io.StringIO(text)), [])
    if len(headers) != len(set(headers)):
        raise ValueError('Duplicate CSV column names are not allowed.')
    try:
        frame = pd.read_csv(io.StringIO(text), nrows=5001)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as exc:
        raise ValueError('Unable to parse CSV. Use the bundled sample format.') from exc
    return frame

class Handler(BaseHTTPRequestHandler):
    bundle = None
    meta = None

    def send(self, status, content, content_type='application/json; charset=utf-8'):
        if not isinstance(content, bytes):
            content = json.dumps(content, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            return self.send(200, (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/health':
            return self.send(200, {'status': 'ok', 'model': self.bundle['selected_model']})
        if path == '/api/meta':
            return self.send(200, self.meta)
        if path == '/api/sample':
            return self.send(200, {'csv': (ROOT / 'data/samples/demo_flows.csv').read_text(),
                                   'description': 'Held-out demonstration: up to 25 examples per family; not production prevalence.'})
        if path == '/sample.csv':
            return self.send(200, (ROOT / 'data/samples/demo_flows.csv').read_bytes(), 'text/csv; charset=utf-8')
        return self.send(404, {'error': 'Not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ['/api/predict', '/api/explain']:
            return self.send(404, {'error': 'Not found'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send(415, {'error': 'Content-Type must be application/json.'})
        origin = self.headers.get('Origin')
        if origin:
            parsed_origin = urlparse(origin)
            if (parsed_origin.scheme not in ('http', 'https')
                    or parsed_origin.netloc.lower() != self.headers.get('Host', '').lower()):
                 return self.send(403, {'error': 'Cross-origin requests are not accepted.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.send(413, {'error': 'Request must be between 1 byte and 8 MB.'})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Expected a JSON object.')
            frame = read_csv(payload.get('csv'))
            with LOCK:
                if path == '/api/predict':
                    result = {'rows': predict(frame, self.bundle, payload.get('threshold')),
                              'threshold': payload.get('threshold', self.bundle['threshold'])}
                else:
                    result = explain(frame, int(payload.get('index', 0)), self.bundle)
            return self.send(200, result)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            return self.send(400, {'error': str(exc)})
        except Exception:
            return self.send(500, {'error': 'Inference failed. Check model and dependency versions.'})

    def log_message(self, format, *args):
        # Uploaded rows are never printed or persisted.
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8501')))
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    Handler.bundle = load_bundle()
    Handler.meta = {name: json.loads((ROOT / f'reports/{file}').read_text()) for name, file in
                    [('metrics', 'metrics.json'), ('audit', 'data_audit.json'), ('schema', 'schema.json')]}
    Handler.meta['importance'] = pd.read_csv(ROOT / 'reports/permutation_importance.csv').head(12).to_dict('records')
    server = ThreadingHTTPServer(('0.0.0.0', args.port), Handler)
    server.daemon_threads = True
    print(f'NetGuard ready: http://127.0.0.1:{args.port}  |  Ctrl+C to stop', flush=True)
    if not args.no_browser:
        webbrowser.open(f'http://127.0.0.1:{args.port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
