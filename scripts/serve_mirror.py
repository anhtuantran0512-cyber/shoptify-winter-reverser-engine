#!/usr/bin/env python3
"""
Serve the mirror at the path the original page lives at.

The captured app is a React Router document: on boot it matches
`window.location.pathname` against its route table, so the mirror has to be
reachable at `/editions/winter2026` rather than at a folder name. This server
does exactly that, plus the MIME types the bundles expect.

    python3 scripts/serve_mirror.py [port]
"""
from __future__ import annotations

import mimetypes
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "mirror"
PAGE_PATH = "/editions/winter2026"

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/octet-stream", ".ktx2")
mimetypes.add_type("application/octet-stream", ".riv")
mimetypes.add_type("application/octet-stream", ".glb")


class MirrorHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == PAGE_PATH or path == PAGE_PATH + "/":
            self.path = "/index.html"
        elif path.startswith(PAGE_PATH + "#"):
            self.path = "/index.html"
        elif path == "/" or path == "/index.html":
            # The bundle dispatches on location.pathname: served at "/" the
            # router matches no route and React clears the SSR markup, which
            # is a blank page. Send the browser to the real route instead.
            self.send_response(302)
            self.send_header("Location", PAGE_PATH)
            self.end_headers()
            return
        return super().do_GET()

    def send_head(self):  # noqa: N802
        # Unknown paths are routes of the same SPA, not missing files: hand
        # them the document and let the router render, instead of a 404 page.
        if not self.path.startswith(("/assets/", "/js/", "/css/", "/vendor/")):
            if not (ROOT / self.path.split("?", 1)[0].lstrip("/")).exists():
                self.send_response(302)
                self.send_header("Location", PAGE_PATH)
                self.end_headers()
                return None
        return super().send_head()

    def end_headers(self) -> None:
        # the bundles call fetch() on json/ktx2 across relative paths
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4174
    handler = partial(MirrorHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"mirror  http://127.0.0.1:{port}{PAGE_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
