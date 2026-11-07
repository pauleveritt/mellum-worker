"""A stand-in llama-server: takes its command line, serves /props and /slots from it.

Slots follow -np, each n_ctx is -c / -np rounded up to 256 as llama.cpp does; the build is
FAKE_BUILD_INFO (default b12110-cd959bae9)."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

args = sys.argv[1:]
value = lambda flag, default: args[args.index(flag) + 1] if flag in args else default
port, context, parallel = int(value("--port", "8001")), int(value("-c", "4096")), int(value("-np", "1"))
n_ctx = -(-(context // parallel) // 256) * 256


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = {"/props": {"build_info": os.environ.get("FAKE_BUILD_INFO", "b12110-cd959bae9"),
                           "model_path": value("-m", "")},
                "/slots": [{"id": i, "n_ctx": n_ctx} for i in range(parallel)]}.get(self.path)
        data = json.dumps(body).encode()
        self.send_response(200 if body is not None else 404)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
