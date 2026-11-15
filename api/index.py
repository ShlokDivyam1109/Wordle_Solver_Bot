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

def generate_tree_trace(coloring: str, recommended_word: str):
    """Pure Python decision path generator for OCT-H tile conditions with zero external dependencies."""
    color_names = {'G': 'Green', 'Y': 'Yellow', 'X': 'Gray'}
    path = []
    for pos, code in enumerate(coloring, start=1):
        color_name = color_names.get(code, 'Gray')
        path.append({
            'node_id': pos - 1,
            'question': f'Tile {pos} is {color_name}?',
            'evaluated_true': True,
            'tile_position': pos,
            'tile_color': color_name.lower()
        })
    path.append({
        'node_id': len(coloring),
        'is_leaf': True,
        'recommended_guess': recommended_word.upper()
    })
    return path

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

        # Detect the requested route from all sources:
        # 1. query parameter (__route__ from vercel rewrite)
        # 2. x-matched-path header (from Vercel proxy)
        # 3. x-forwarded-uri header
        # 4. parsed.path or self.path
        matched_path = self.headers.get('x-matched-path') or self.headers.get('x-forwarded-uri') or ''
        route_query = query.get('__route__', [''])[0]
        full_target = f"{path} {matched_path} {route_query} {self.path}".lower()

        # If query params were passed in matched_path (e.g. ?secret=...&solver=...)
        if 'secret' not in query and '?' in matched_path:
            extra_query = urllib.parse.parse_qs(matched_path.split('?', 1)[1])
            query.update(extra_query)

        # 1. Serve frontend HTML
        if path in ('/', '/index.html') or matched_path in ('/', '/index.html'):
            html_path = os.path.join(ROOT_DIR, 'index.html')
            if not os.path.exists(html_path):
                html_path = os.path.join(ROOT_DIR, 'frontend', 'index.html')
            with open(html_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # 2. Serve CSS
        if path.endswith('.css') or matched_path.endswith('.css'):
            css_path = os.path.join(ROOT_DIR, 'frontend', 'style.css')
            with open(css_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/css; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # 3. Serve JS
        if (path.endswith('.js') or matched_path.endswith('.js')) and not ('api' in path and not path.endswith('.js')):
            js_path = os.path.join(ROOT_DIR, 'frontend', 'app.js')
            with open(js_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # 4. Favicon
        if path == '/favicon.ico' or matched_path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        # 5. API Endpoints
        status_code = 200
        if 'simulate' in full_target:
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
                status_code = 500
                res = {'status': 'error', 'message': str(e)}

        elif 'random' in full_target:
            word = random.choice(solver_instance.solutions)
            res = {'word': word}

        elif 'compare' in full_target:
            secret = query.get('secret', ['CIGAR'])[0].strip().lower()
            try:
                comparison = solver_instance.compare_all_solvers(secret)
                res = {'status': 'ok', 'secret': secret, 'comparison': comparison}
            except Exception as e:
                status_code = 500
                res = {'status': 'error', 'message': str(e)}

        elif 'benchmarks' in full_target:
            res = benchmark_cache or {}

        elif 'tree' in full_target or 'helper' in full_target:
            # Multi-turn history support:
            # Supports comma-separated entries: history=salet:xyxxx,brond:xyxxx
            # Also backwards-compatible with single-turn: guess=salet&coloring=xyxxx
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
                # Progressively filter candidates through all history steps
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
                    # If exactly turn 1 with SALET, use paper's exact optimal G2 table
                    if len(history_list) == 1 and history_list[0]['guess'] == 'salet':
                        first_col = history_list[0]['coloring']
                        g2 = solver_instance.salet_g2.get(first_col)
                        if g2:
                            recommended = g2.upper()
                            reason = 'MIT OCT-H Optimal Policy for SALET (Depth 8 Tree)'

                    # Otherwise, compute optimal discriminator
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

                last_col = history_list[-1]['coloring'] if history_list else 'XXXXX'
                path_data = generate_tree_trace(last_col, recommended)

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
                status_code = 500
                res = {'status': 'error', 'message': str(e)}

        else:
            status_code = 404
            res = {'status': 'error', 'message': f'Not found: {path}'}

        body = json.dumps(res).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
