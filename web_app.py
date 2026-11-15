"""
Interactive Wordle Solver Animated Web Dashboard.
Implementation of Bertsimas & Paskov (MIT) - 'An Exact and Interpretable Solution to Wordle'.

Run with:
    python web_app.py
Then open http://localhost:8080 in your browser.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import engine
import tree

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

solver_instance = engine.WordleSolver()
tree_policy = tree.InterpretableTreePolicy()
tree_policy.train_on_salet_g2()

BENCHMARK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'benchmark_results.json')
benchmark_cache = None
if os.path.exists(BENCHMARK_PATH):
    try:
        with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
            benchmark_cache = json.load(f)
    except Exception:
        pass


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet down console logs
        pass

    def send_file(self, filepath, content_type):
        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static frontend assets
        if path == '/' or path == '/index.html':
            root_index = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
            if os.path.exists(root_index):
                self.send_file(root_index, 'text/html; charset=utf-8')
            else:
                self.send_file(os.path.join(FRONTEND_DIR, 'index.html'), 'text/html; charset=utf-8')

        elif path == '/style.css' or path == '/frontend/style.css':
            self.send_file(os.path.join(FRONTEND_DIR, 'style.css'), 'text/css; charset=utf-8')

        elif path == '/app.js' or path == '/frontend/app.js':
            self.send_file(os.path.join(FRONTEND_DIR, 'app.js'), 'application/javascript; charset=utf-8')

        # API Endpoints
        elif path == '/api/simulate':
            secret = query.get('secret', ['VIXEN'])[0].strip().lower()
            solver_type = query.get('solver', ['exact_dp'])[0].strip().lower()

            try:
                steps = solver_instance.simulate_step_by_step(secret, solver_type)
                comparison = solver_instance.compare_all_solvers(secret)
                res = {'status': 'ok', 'secret': secret, 'steps': steps, 'comparison': comparison}
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif path == '/api/compare':
            secret = query.get('secret', ['VIXEN'])[0].strip().lower()
            try:
                comp = solver_instance.compare_all_solvers(secret)
                res = {'status': 'ok', 'secret': secret, 'comparison': comp}
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif path == '/api/tree' or path == '/api/helper':
            raw_history = query.get('history', [''])[0].strip()
            history_list = []
            valid_chars = {'G', 'Y', 'X'}

            if raw_history:
                for entry in raw_history.split(','):
                    if ':' in entry:
                        g, c = entry.split(':', 1)
                        g = g.strip().lower()
                        c = ''.join(ch if ch in valid_chars else 'X' for ch in c.strip().upper())[:5].ljust(5, 'X')
                        if len(g) == 5:
                            history_list.append({'guess': g, 'coloring': c})
            else:
                coloring = query.get('coloring', ['XXXXX'])[0].strip().upper()
                guess = query.get('guess', ['salet'])[0].strip().lower()
                cleaned = ''.join(ch if ch in valid_chars else 'X' for ch in coloring)[:5].ljust(5, 'X')
                if len(guess) == 5:
                    history_list.append({'guess': guess, 'coloring': cleaned})

            try:
                candidates = list(solver_instance.solutions)
                for step in history_list:
                    candidates = engine.filter_candidates(candidates, step['guess'], step['coloring'])

                n = len(candidates)
                recommended = ''
                reason = ''
                status = 'ok'

                if n == 0:
                    status = 'empty'
                    recommended = 'NO MATCH'
                    reason = 'No words match all clues. Please verify the coloring pattern of your guesses.'
                elif n == 1:
                    status = 'solved'
                    recommended = candidates[0].upper()
                    reason = f'100% Certain Solution ({candidates[0].upper()})! Game Solved.'
                elif n == 2:
                    status = 'progress'
                    recommended = candidates[0].upper()
                    reason = f'Two words remain: {candidates[0].upper()} or {candidates[1].upper()} (50% instant win chance).'
                else:
                    if len(history_list) == 1 and history_list[0]['guess'] == 'salet':
                        first_col = history_list[0]['coloring']
                        g2 = solver_instance.salet_g2.get(first_col)
                        if g2:
                            recommended = g2.upper()
                            reason = 'MIT OCT-H Optimal Policy for SALET (Depth 8 Tree)'

                    if not recommended:
                        best_act = None
                        best_ent = -1.0
                        pool = candidates if n <= 5 else (candidates + solver_instance.all_guesses[:300])
                        for g in pool:
                            ent = solver_instance.calculate_entropy(candidates, g)
                            in_state_bonus = 0.001 if g in candidates else 0.0
                            if ent + in_state_bonus > best_ent:
                                best_ent = ent + in_state_bonus
                                best_act = g
                        recommended = (best_act or candidates[0]).upper()
                        reason = f'Optimal Information Discriminator (Entropy = {best_ent:.2f} bits)'

                color_names = {'G': 'Green', 'Y': 'Yellow', 'X': 'Gray'}
                last_col = history_list[-1]['coloring'] if history_list else 'XXXXX'
                path_data = []
                for pos, code in enumerate(last_col, start=1):
                    cname = color_names.get(code, 'Gray')
                    path_data.append({
                        'node_id': pos - 1,
                        'question': f'Tile {pos} is {cname}?',
                        'evaluated_true': True,
                        'tile_position': pos,
                        'tile_color': cname.lower()
                    })
                path_data.append({
                    'node_id': len(last_col),
                    'is_leaf': True,
                    'recommended_guess': recommended.upper()
                })

                res = {
                    'status': status,
                    'turn': len(history_list) + 1,
                    'history': history_list,
                    'recommended_guess': recommended,
                    'reason': reason,
                    'path': path_data,
                    'candidates_count': n,
                    'candidates_sample': [c.upper() for c in candidates[:60]]
                }
            except Exception as e:
                res = {'status': 'error', 'message': str(e)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif path == '/api/random':
            import random
            word = random.choice(solver_instance.solutions)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'word': word}).encode('utf-8'))

        elif path == '/api/benchmarks':
            global benchmark_cache
            if not benchmark_cache and os.path.exists(BENCHMARK_PATH):
                with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
                    benchmark_cache = json.load(f)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(benchmark_cache or {}).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    server = HTTPServer(('127.0.0.1', PORT), RequestHandler)
    print(f'Wordle Solver Animated UI running at http://localhost:{PORT}')
    print('Press Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')


if __name__ == '__main__':
    start_server()
