#!/usr/bin/env python3
"""
shoptify / capture_assets.py
Download the publicly-served front-end resources of a page for offline study.

This mirrors what the browser already downloads to render the page (DevTools >
Network). It does NOT bypass auth, paywalls, or access private endpoints.

Usage:
    python3 capture_assets.py inventory.json ../assets

inventory.json: [{"url": "...", "type": "js|css|font|image|html|rive"}, ...]
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
)
EXT_BY_TYPE = {
    "js": ".js",
    "css": ".css",
    "font": ".woff2",
    "image": "",
    "html": ".html",
    "rive": ".riv",
    "json": ".json",
    "texture": ".ktx2",
    "data": ".json",
    "misc": "",
}


def slug(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path) or "index"
    return name


def fetch(url: str, timeout: int = 45) -> tuple[bytes, str, int]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.status


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    inventory = json.loads(Path(sys.argv[1]).read_text())
    out_root = Path(sys.argv[2])
    subdirs = {
        k: out_root / k
        for k in ("js", "css", "fonts", "images", "rive", "html", "video", "textures", "data", "misc")
    }

    manifest = []
    for item in inventory:
        url = item["url"]
        kind = item.get("type", "other")
        folder = {
            "font": subdirs["fonts"],
            "image": subdirs["images"],
            "js": subdirs["js"],
            "css": subdirs["css"],
            "rive": subdirs["rive"],
            "html": subdirs["html"],
            "video": subdirs["video"],
            "texture": subdirs["textures"],
            "data": subdirs["data"],
            "misc": subdirs["misc"],
            "json": subdirs["data"],
        }.get(kind)
        if folder is None:
            continue
        folder.mkdir(parents=True, exist_ok=True)

        filename = item.get("filename") or slug(url)
        if kind == "image" and "." not in filename:
            ct = mimetypes.guess_type(url)[0] or ""
            filename += mimetypes.guess_extension(ct) or ".bin"

        dest = folder / filename
        if dest.exists() and dest.stat().st_size > 0:
            manifest.append(
                {
                    "url": url,
                    "kind": kind,
                    "path": str(dest.relative_to(out_root.parent)),
                    "bytes": dest.stat().st_size,
                    "status": "cached",
                }
            )
            continue

        try:
            t0 = time.time()
            body, ctype, status = fetch(url)
            if not Path(filename).suffix:
                ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ""
                dest = dest.with_suffix(ext)
            dest.write_bytes(body)
            digest = hashlib.sha256(body).hexdigest()[:16]
            manifest.append(
                {
                    "url": url,
                    "kind": kind,
                    "path": str(dest.relative_to(out_root.parent)),
                    "contentType": ctype,
                    "bytes": len(body),
                    "sha256_16": digest,
                    "status": status,
                    "ms": round((time.time() - t0) * 1000),
                }
            )
            print(f"OK  {kind:5} {len(body):>9,}B  {dest.name}")
        except Exception as exc:  # noqa: BLE001
            manifest.append({"url": url, "kind": kind, "status": "error", "error": str(exc)})
            print(f"ERR {kind:5} {url} -> {exc}")

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    ok = sum(1 for m in manifest if m["status"] != "error")
    print(f"\n{ok}/{len(manifest)} captured -> {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
