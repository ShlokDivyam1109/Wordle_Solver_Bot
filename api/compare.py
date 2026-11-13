from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import engine

solver_instance = engine.WordleSolver()


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        secret = query.get('secret', ['CIGAR'])[0].strip().lower()

        try:
            comparison = solver_instance.compare_all_solvers(secret)
            res = {'status': 'ok', 'secret': secret, 'comparison': comparison}
        except Exception as e:
            res = {'status': 'error', 'message': str(e)}

        body = json.dumps(res).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

