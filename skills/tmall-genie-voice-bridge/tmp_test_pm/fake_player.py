from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length else b''
        try:
            payload = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            payload = {'_raw': body.decode('utf-8', errors='replace')}
        response = {
            'ok': True,
            'path': self.path,
            'payload': payload,
            'headers': dict(self.headers),
        }
        data = json.dumps(response, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 57901), Handler).serve_forever()
