#!/usr/bin/env python3
"""
Find CDN assets referenced only from the downloaded CSS and JS (icons, font
fallbacks, scene textures, emoji plates) and add them to the inventory.

The HTML scan in build_inventory.py cannot see these, which is why a first pass
looks complete while the replay is missing pieces.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "snapshot" / "inventory.json"

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".gif")
FONT_EXT = (".woff2", ".woff", ".ttf", ".otf")


def kind_for(path: str) -> str | None:
    low = path.lower()
    if low.endswith(".js"):
        return "js"
    if low.endswith(".css"):
        return "css"
    if low.endswith(FONT_EXT):
        return "font"
    if low.endswith(IMAGE_EXT):
        return "image"
    if low.endswith(".riv"):
        return "rive"
    if low.endswith(".ktx2"):
        return "texture"
    if low.endswith(".json"):
        return "data"
    if low.endswith((".mp4", ".webm")):
        return "video"
    if low.endswith((".txt", ".zip")):
        return "misc"
    return None


def main() -> None:
    inv = json.loads(INV.read_text())
    have = {i["url"].split("?")[0] for i in inv}

    found: set[str] = set()
    for folder in ("css", "js"):
        for f in (ROOT / "assets" / folder).glob("*"):
            if f.suffix not in (".css", ".js"):
                continue
            text = f.read_text(errors="ignore")
            for u in re.findall(r"https://cdn\.shopify\.com/[^\s\"'\\ )]+", text):
                u = u.rstrip("',;")
                if "/oxygen-v2/" in u:
                    continue
                found.add(u.split("?")[0])

    added = 0
    for url in sorted(found):
        if url in have:
            continue
        kind = kind_for(url)
        if not kind:
            continue
        inv.append({"url": url, "type": kind, "filename": url.rsplit("/", 1)[-1]})
        have.add(url)
        added += 1

    INV.write_text(json.dumps(inv, indent=2))
    print(f"added {added} css/js-only assets; inventory now {len(inv)}")


if __name__ == "__main__":
    main()
