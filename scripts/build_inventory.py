#!/usr/bin/env python3
"""
shoptify / build_inventory.py
Turn the SSR snapshot into a downloadable inventory.

Policy: only resources the page itself ships to a normal browser. Images are
requested at width=700 so the study vault stays light; originals stay on the CDN.
"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "snapshot" / "page.ssr.html"

text = HTML.read_text(encoding="utf-8", errors="ignore")
raw = re.findall(r"https://cdn\.shopify\.com/[^\s\"'<>\\]+", text)
urls = sorted({u.split("\\")[0].replace("&amp;", "&") for u in raw})

base = lambda u: u.split("?")[0]  # noqa: E731
is_img = lambda u: re.search(r"\.(png|jpe?g|webp|avif|svg|gif)$", base(u), re.I) is not None  # noqa: E731
is_vid = lambda u: re.search(r"\.(mp4|webm)$", base(u), re.I) is not None  # noqa: E731

inventory: list[dict] = []

# --- application code -------------------------------------------------------
for u in urls:
    if "cdn.shopify.com/oxygen-v2/" not in u:
        continue
    if u.endswith(".js"):
        inventory.append({"url": u, "type": "js"})
    elif u.endswith(".css"):
        inventory.append({"url": u, "type": "css"})

# --- fonts (from the font stylesheet) --------------------------------------
for u in urls:
    if re.search(r"\.woff2?$", base(u)):
        inventory.append({"url": u, "type": "font"})

# --- rive animations (all unique) -----------------------------------------
for u in urls:
    if base(u).endswith(".riv"):
        inventory.append({"url": u, "type": "rive", "filename": base(u).rsplit("/", 1)[-1].split("?")[0]})

# --- images: one variant per unique asset, width=700 -----------------------
variants: dict[str, dict[int, str]] = collections.defaultdict(dict)
for u in urls:
    if not is_img(u):
        continue
    m = re.search(r"[?&]width=(\d+)", u)
    variants[base(u)][int(m.group(1)) if m else 0] = u

for b, widths in variants.items():
    if b.endswith(".svg"):
        pick = b
        name = b.rsplit("/", 1)[-1]
    else:
        sep = "&" if "?" in b else "?"
        pick = f"{b}{sep}width=700"
        name = b.rsplit("/", 1)[-1].split("?")[0]
    inventory.append({"url": pick, "type": "image", "filename": name})

# --- video loops -----------------------------------------------------------
for u in urls:
    if is_vid(u):
        inventory.append({"url": base(u), "type": "video", "filename": base(u).rsplit("/", 1)[-1]})

# --- WebGL scene layer: KTX2 textures, Theatre.js timelines, extras --------
for u in urls:
    p = base(u)
    low = p.lower()
    if low.endswith(".ktx2"):
        inventory.append({"url": u, "type": "texture", "filename": p.rsplit("/", 1)[-1]})
    elif low.endswith(".json"):
        inventory.append({"url": u, "type": "data", "filename": p.rsplit("/", 1)[-1]})
    elif low.endswith((".zip", ".txt")):
        inventory.append({"url": u, "type": "misc", "filename": p.rsplit("/", 1)[-1]})
    elif p.endswith(".js") and "/s/files/" in p:
        inventory.append({"url": u, "type": "js", "filename": p.rsplit("/", 1)[-1]})

# --- the page itself -------------------------------------------------------
inventory.append({"url": "https://www.shopify.com/editions/winter2026", "type": "html", "filename": "editions-winter2026.html"})

out = ROOT / "snapshot" / "inventory.json"
out.write_text(json.dumps(inventory, indent=2))
counts = collections.Counter(i["type"] for i in inventory)
print(f"{len(inventory)} resources -> {out}")
print(dict(counts))
