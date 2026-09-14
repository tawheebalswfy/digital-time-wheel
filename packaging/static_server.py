from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SPAHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = Path(self.translate_path(self.path.split('?', 1)[0]))
        if not path.exists() or path.is_dir():
            self.path = '/index.html'
        return super().do_GET()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5173)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), lambda *x, **y: SPAHandler(*x, directory=args.directory, **y))
    server.serve_forever()
