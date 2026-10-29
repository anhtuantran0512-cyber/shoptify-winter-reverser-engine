#!/usr/bin/env python3
"""Capture every JS chunk the bundles reference, including lazy ones.

The first pass only saw chunks the page had already loaded. The chapter scenes
(`AgenticScene-*.js`, `RetailScene-*.js`, ...) are dynamic imports that only
fire when the section scrolls into view, so they were never requested during
the capture. This walks the import graph until nothing is missing.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "assets" / "js"
BASE = "https://cdn.shopify.com/oxygen-v2/47215/49013/102837/4753383/assets/"

REL_RE = re.compile(r'["\']\./([A-Za-z0-9_().\-]+\.js)["\']')
ABS_RE = re.compile(r"oxygen-v2/[0-9/]+/assets/([A-Za-z0-9_().\-]+\.js)")
CSS_ABS_RE = re.compile(r"oxygen-v2/[0-9/]+/assets/([A-Za-z0-9_().\-]+\.css)")


def refs() -> set[str]:
    found: set[str] = set()
    for path in JS.glob("*.js"):
        text = path.read_text(errors="ignore")
        found |= set(REL_RE.findall(text))
        found |= set(ABS_RE.findall(text))
    return found


def fetch(name: str) -> int:
    url = name if name.startswith("http") else BASE + name
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    (JS / name.rsplit("/", 1)[-1]).write_bytes(data)
    return len(data)


def main() -> None:
    round_no = 0
    while True:
        round_no += 1
        have = {p.name for p in JS.glob("*.js")}
        missing = sorted(refs() - have)
        print(f"round {round_no}: {len(missing)} missing")
        if not missing:
            break
        for name in missing:
            try:
                size = fetch(name)
                print(f"  {size / 1024:7.1f} KB  {name}")
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {name}: {exc}")
        if round_no > 8:
            break

    # stylesheets referenced by the bundles (fonts, tailwind)
    css_dir = ROOT / "assets" / "css"
    css_have = {p.name for p in css_dir.glob("*.css")}
    css_refs: set[str] = set()
    for path in JS.glob("*.js"):
        css_refs |= set(CSS_ABS_RE.findall(path.read_text(errors="ignore")))
    for name in sorted(css_refs - css_have):
        url = BASE + name
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                (css_dir / name).write_bytes(r.read())
            print(f"  css {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  css FAIL {name}: {exc}")

    total = sum(p.stat().st_size for p in JS.glob("*.js"))
    print(f"{len(list(JS.glob('*.js')))} chunks, {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
