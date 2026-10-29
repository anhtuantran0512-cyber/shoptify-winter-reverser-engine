#!/usr/bin/env python3
"""Capture live vs mirror in Camoufox at matching scroll positions, then diff.

    python scripts/visual_compare.py [frames]

Frames go to /tmp/mirror-qa/cf-{live,mirror}-NN.png and a numeric report is
printed per frame.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops

OUT = Path("/tmp/mirror-qa")
CF = "/home/broamstuck/.npm-global/bin/camofox"
LIVE = "https://www.shopify.com/editions/winter2026"
MIRROR = "http://127.0.0.1:4174/editions/winter2026"
FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 6


def cf(*args: str) -> str:
    out = subprocess.run([CF, "--user", "studio", *args], capture_output=True, text=True)
    return out.stdout.strip()


def cf_json(*args: str):
    raw = cf("--format", "json", *args)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def evaljs(tab: str, expr: str):
    res = cf_json("eval", expr, tab)
    return res.get("result") if res.get("ok") else None


def close_all() -> None:
    tabs = cf_json("get-tabs").get("tabs", [])
    for t in tabs:
        cf("close", t["tabId"])


def shoot(tab: str, name: str) -> None:
    cf("screenshot", "--path", str(OUT / name), tab)


def capture(label: str, url: str) -> dict:
    tab = None
    for attempt in range(4):
        tab = cf_json("open", url).get("tabId")
        if tab:
            break
        time.sleep(3)
    if not tab:
        raise SystemExit(f"cannot open {url}")
    time.sleep(14)
    height = evaljs(tab, "document.body.scrollHeight") or 0
    y = 0
    while y < height:
        evaljs(tab, f"window.scrollTo(0,{y})")
        time.sleep(0.12)
        y += 1100
    evaljs(tab, "window.scrollTo(0,0)")
    time.sleep(3)
    height = evaljs(tab, "document.body.scrollHeight") or height
    positions = [round(height * i / (FRAMES - 1)) if i else 0 for i in range(FRAMES)]
    current = 0
    for i, pos in enumerate(positions):
        # approach in small steps so the smooth-scroll driver and the scroll-
        # driven scenes settle the way they do for a real reader
        step = 600 if pos >= current else -600
        y = current
        while (step > 0 and y < pos) or (step < 0 and y > pos):
            y = min(pos, y + step) if step > 0 else max(pos, y + step)
            evaljs(tab, f"window.scrollTo(0,{y})")
            time.sleep(0.05)
        current = pos
        time.sleep(5.0)
        shoot(tab, f"cf-{label}-{i:02d}.png")
    info = {
        "label": label,
        "tab": tab,
        "height": height,
        "positions": positions,
        "sections": evaljs(tab, "document.querySelectorAll('[data-section-id]').length"),
        "canvases": evaljs(tab, "document.querySelectorAll('canvas').length"),
        "viewport": [
            evaljs(tab, "innerWidth"),
            evaljs(tab, "innerHeight"),
        ],
    }
    cf("close", tab)
    time.sleep(2)
    return info


def diff() -> None:
    for i in range(FRAMES):
        a_path = OUT / f"cf-live-{i:02d}.png"
        b_path = OUT / f"cf-mirror-{i:02d}.png"
        if not (a_path.exists() and b_path.exists()):
            continue
        a = Image.open(a_path).convert("RGB")
        b = Image.open(b_path).convert("RGB")
        if a.size != b.size:
            print(f"frame {i}: size {a.size} != {b.size}")
            continue
        d = ImageChops.difference(a, b)
        hist = d.convert("L").histogram()
        total = sum(hist)
        changed = sum(hist[24:]) / total * 100
        mean = sum(v * n for v, n in enumerate(hist)) / total
        print(f"frame {i}: mean={mean:5.2f} changed>24={changed:5.1f}%")
        d.save(OUT / f"diff-{i:02d}.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    close_all()
    report = {}
    for label, url in (("live", LIVE), ("mirror", MIRROR)):
        report[label] = capture(label, url)
        print(label, report[label]["height"], "px", report[label]["sections"], "sections",
              report[label]["canvases"], "canvases")
    (OUT / "camofox-compare.json").write_text(json.dumps(report, indent=2))
    diff()


if __name__ == "__main__":
    main()
