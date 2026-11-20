"""Serve the exported Godot web build with the headers needed by modern browsers."""
import argparse
import functools
import http.server
import mimetypes
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "web"


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".pck": "application/octet-stream",
        ".js": "text/javascript",
        ".html": "text/html",
        ".json": "application/json",
    }

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8060)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--dir", default=str(BUILD))
    args = parser.parse_args()
    directory = Path(args.dir).resolve()
    index = directory / "index.html"
    if not index.exists():
        print(f"Missing {index}; run python tools/build_web.py first.", file=sys.stderr)
        return 1
    mimetypes.add_type("application/wasm", ".wasm")
    handler = functools.partial(Handler, directory=str(directory))
    with socketserver.ThreadingTCPServer((args.host, args.port), handler) as server:
        server.daemon_threads = True
        url = f"http://{args.host}:{args.port}/"
        print(f"Serving {directory} at {url}", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
