#!/usr/bin/env python3
"""
Serve the mirror at the path the original page lives at.

The captured app is a React Router document: on boot it matches
`window.location.pathname` against its route table, so the mirror has to be
reachable at `/editions/winter2026` rather than at a folder name. This server
does exactly that, plus the MIME types the bundles expect.

The build bakes one origin into every asset URL (`MIRROR_ORIGIN`, because the
bundles call `new URL(assetUrl)` without a base and choke on root-relative
paths). That origin is *this* machine, so when the page is opened through a
tunnel or a preview proxy those URLs point at the viewer's own localhost. On
every text response we therefore swap the baked origin for the origin the
request actually arrived on, taken from the Host header.

    python3 scripts/serve_mirror.py [port]
"""
from __future__ import annotations

import mimetypes
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "mirror"
PAGE_PATH = "/editions/winter2026"

# must match the MIRROR_ORIGIN the mirror was built with
BAKED = os.environ.get("MIRROR_ORIGIN", "http://127.0.0.1:4174").rstrip("/")

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("application/octet-stream", ".ktx2")
mimetypes.add_type("application/octet-stream", ".riv")
mimetypes.add_type("application/octet-stream", ".glb")

TEXT_SUFFIXES = (".html", ".js", ".css")

_cache: dict[tuple[str, float, str], bytes] = {}


class MirrorHandler(SimpleHTTPRequestHandler):
    server_version = "mirror"

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
            self._redirect()
            return
        self._alias_chunk()
        if self._serve_rebased():
            return
        return super().do_GET()

    def _alias_chunk(self) -> None:
        """`/assets/<chunk>.js` -> `/js/<chunk>.js` (also `.css` -> `/css/`).

        The bundles build lazy-chunk URLs as `<base> + "assets/<name>"`, and the
        build points <base> at this origin. `assets/` is the capture's own
        folder and holds no compiled chunks, so resolve those names against the
        mirror's js/ and css/ folders instead.
        """
        path = self.path.split("?", 1)[0]
        if not path.startswith("/assets/") or path.count("/") != 2:
            return
        if (ROOT / path.lstrip("/")).is_file():
            return
        name = path.rsplit("/", 1)[-1]
        for folder in ("js", "css"):
            if (ROOT / folder / name).is_file():
                self.path = f"/{folder}/{name}"
                return

    def _redirect(self) -> None:
        # relative: must keep whatever host/proxy prefix the request came from
        self.send_response(302)
        self.send_header("Location", PAGE_PATH)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _public_origin(self) -> str | None:
        """The origin the browser used, whatever the proxy did to Host.

        Reverse proxies in front of this server are not consistent: some pass
        the public vhost through, some pass loopback. If we take a loopback
        Host at face value the rewritten asset URLs point at the *viewer's*
        own machine and nothing loads, so fall back through the evidence the
        request carries: forwarded headers, then Referer, then the platform's
        own hostname.
        """
        host = self.headers.get("Host", "")
        fwd = self.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
        proto = self.headers.get("X-Forwarded-Proto", "").split(",")[0].strip()
        loopback = ("127.0.0.1", "localhost", "0.0.0.0", "[::1]", "")

        def is_local(h: str) -> bool:
            return h.split(":")[0] in ("127.0.0.1", "localhost", "0.0.0.0", "[::1]") or not h

        if fwd and not is_local(fwd):
            return f"{proto or 'https'}://{fwd}"
        if not is_local(host):
            return f"{proto or 'https'}://{host}"
        ref = self.headers.get("Referer", "")
        if ref:
            try:
                from urllib.parse import urlsplit

                parts = urlsplit(ref)
                if parts.hostname and parts.hostname not in ("127.0.0.1", "localhost"):
                    return f"{parts.scheme}://{parts.netloc}"
            except ValueError:
                pass
        sandbox = os.environ.get("E2B_SANDBOX_ID")
        if sandbox and self.server.server_address[1]:
            return f"https://{self.server.server_address[1]}-{sandbox}.e2b.app"
        return None

    def _serve_rebased(self) -> bool:
        """Serve a text file with the baked origin swapped for this request's."""
        path = self.path.split("?", 1)[0]
        if not path.endswith(TEXT_SUFFIXES):
            return False
        if path == "/":
            path = "/index.html"
        file = (ROOT / path.lstrip("/")).resolve()
        try:
            file.relative_to(ROOT.resolve())
        except ValueError:
            return False
        if not file.is_file():
            return False

        mtime = file.stat().st_mtime
        key = (str(file), mtime, self._public_origin() or BAKED)
        body = _cache.get(key)
        if body is None:
            text = file.read_text(errors="ignore")
            origin = self._public_origin()
            if origin and origin != BAKED:
                text = text.replace(BAKED, origin)
            body = text.encode()
            _cache[key] = body

        self.send_response(200)
        ctype = (
            "text/javascript"
            if file.suffix == ".js"
            else (mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        )
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def send_head(self):  # noqa: N802
        # Unknown paths are routes of the same SPA, not missing files: hand
        # them the document and let the router render, instead of a 404 page.
        if not self.path.startswith(("/assets/", "/js/", "/css/", "/vendor/")):
            if not (ROOT / self.path.split("?", 1)[0].lstrip("/")).exists():
                self._redirect()
                return None
        return super().send_head()

    def end_headers(self) -> None:
        # the bundles call fetch() on json/ktx2 across relative paths
        self.send_header("Access-Control-Allow-Origin", "*")
        # if a proxy hands us a loopback Host, the Referer is the only place the
        # real public origin shows up; don't let the browser strip it
        self.send_header("Referrer-Policy", "unsafe-url")
        path = self.path.split("?", 1)[0]
        if path.startswith(("/assets/", "/vendor/", "/js/", "/css/")):
            # 60 MB of glb/ktx2/video: reloads must not refetch it every time
            self.send_header("Cache-Control", "public, max-age=604800")
        else:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    _logged = 0

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))
        # First few document requests tell us how the proxy talks to us: which
        # Host it passes, and whether the real origin rides on Referer /
        # X-Forwarded-*. Logged once so a broken preview can be diagnosed
        # without a browser inspector.
        if type(self).__name__ == "MirrorHandler" and self.path.startswith("/editions/"):
            if MirrorHandler._logged < 3:
                MirrorHandler._logged += 1
                keys = ("Host", "Referer", "X-Forwarded-Host", "X-Forwarded-Proto", "X-Real-IP")
                hdrs = {k: self.headers.get(k) for k in keys if self.headers.get(k)}
                sys.stderr.write(
                    f"  proxy headers {hdrs} -> origin {self._public_origin()}\n"
                )


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4174
    handler = partial(MirrorHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"mirror  http://127.0.0.1:{port}{PAGE_PATH}   (rebasing {BAKED})")
    server.serve_forever()


if __name__ == "__main__":
    main()
