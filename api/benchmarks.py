from http.server import BaseHTTPRequestHandler
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

BENCHMARK_PATH = os.path.join(ROOT_DIR, 'data', 'benchmark_results.json')
benchmark_cache = None
if os.path.exists(BENCHMARK_PATH):
    try:
        with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
            benchmark_cache = json.load(f)
    except Exception:
        pass


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        body = json.dumps(benchmark_cache or {}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

