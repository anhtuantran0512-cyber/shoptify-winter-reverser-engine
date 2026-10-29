#!/usr/bin/env python3
"""Capture the 3D scene payload the bundles fetch.

The WebGL scenes load .glb models from the storefront CDN and one HDRI from
polyhaven. The first inventory only watched cdn.shopify.com, so these were
missing. This grabs every URL the bundles reference on those hosts.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "assets" / "js"
OUT_3D = ROOT / "assets" / "3d"
OUT_ENV = ROOT / "assets" / "textures"

HOSTS = ("editions-winter-2026.myshopify.com", "dl.polyhaven.org")
URL_RE = re.compile(r"https://(?:" + "|".join(re.escape(h) for h in HOSTS) + r")/[^\s\"'<>\\]+")


def targets() -> list[str]:
    found: set[str] = set()
    for js in JS.glob("*.js"):
        found.update(URL_RE.findall(js.read_text(errors="ignore")))
    for html in (ROOT / "snapshot" / "page.ssr.html",):
        found.update(URL_RE.findall(html.read_text(errors="ignore")))
    return sorted(u.rstrip(").,;") for u in found)


def dest(url: str) -> Path:
    name = url.split("?")[0].rsplit("/", 1)[-1]
    if name.endswith((".hdr", ".ktx2")):
        return OUT_ENV / name
    if name.endswith((".mp4", ".m3u8")):
        return ROOT / "assets" / "video" / name
    return OUT_3D / name


def main() -> None:
    OUT_3D.mkdir(parents=True, exist_ok=True)
    urls = targets()
    print(f"{len(urls)} files")
    total = 0
    for url in urls:
        path = dest(url)
        if path.is_file() and path.stat().st_size:
            total += path.stat().st_size
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL {path.name}: {exc}")
            continue
        path.write_bytes(data)
        total += len(data)
        print(f"  {len(data) / 1e6:6.1f} MB  {path.name}")
    print(f"total {total / 1e6:.1f} MB in {OUT_3D.name}/ + {OUT_ENV.name}/")


if __name__ == "__main__":
    main()
