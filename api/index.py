from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import os
import sys
import random

# Add root directory to python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import engine

solver_instance = engine.WordleSolver()

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
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if 'simulate' in path:
            secret = query.get('secret', ['CIGAR'])[0].strip().lower()
            solver_type = query.get('solver', ['exact_dp'])[0].strip().lower()

            try:
                steps = solver_instance.simulate_step_by_step(secret, solver_type)
                comparison = solver_instance.compare_all_solvers(secret)
                res = {
                    'status': 'ok',
                    'secret': secret,
                    'steps': steps,
                    'comparison': comparison
                }
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

        elif 'random' in path:
            word = random.choice(solver_instance.solutions)
            res = {'word': word}

        elif 'compare' in path:
            secret = query.get('secret', ['CIGAR'])[0].strip().lower()
            try:
                comparison = solver_instance.compare_all_solvers(secret)
                res = {'status': 'ok', 'secret': secret, 'comparison': comparison}
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

        elif 'benchmarks' in path:
            res = benchmark_cache or {}

        else:
            res = {'status': 'ok', 'message': 'Wordle Solver API is ready'}

        body = json.dumps(res).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
