#!/usr/bin/env python3
"""Generate docs 03 (information architecture) and 05 (asset ledger) from the capture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
content = json.loads((ROOT / "snapshot" / "page-content.json").read_text())


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


# ---------------------------------------------------------------- doc 03
lines = [
    "# 03 — Information architecture",
    "",
    "The page is a single narrative route with twelve chapters. Counts and copy below are",
    "extracted from the live DOM (`snapshot/page-content.json`), not transcribed by hand.",
    "",
    "## Chapter map",
    "",
    "| # | Chapter | Updates | Scroll height | Links | Canvas |",
    "|---|---|---:|---:|---:|---:|",
]
for i, s in enumerate(content["sections"], 1):
    lines.append(
        f"| {i} | **{s['title']}** | {len(s['features'])} | {s['heightPx']:,} px | {s['linkCount']} | {s['canvases']} |"
    )
lines += ["", f"**Total:** {content['totals']['features']} updates, {content['totals']['links']} links, {content['totals']['sections']} chapters.", ""]

for i, s in enumerate(content["sections"], 1):
    lines += [f"## {i}. {s['title']}", "", f"> {s['lead']}", ""]
    if s["groupLabels"]:
        lines += [f"Grouped as: {', '.join(s['groupLabels'])}.", ""]
    lines += ["| # | Update | What it does |", "|---|---|---|"]
    for n, f in enumerate(s["features"], 1):
        desc = f["description"].replace("|", "\\|")
        lines.append(f"| {n} | **{f['title'].replace('|', chr(92) + '|')}** | {desc} |")
    lines.append("")

(ROOT / "docs" / "03-information-architecture.md").write_text("\n".join(lines))
print("03:", len(lines), "lines")

# ---------------------------------------------------------------- doc 05
folders = ["js", "css", "fonts", "rive", "images", "video", "html"]
rows = []
total_files = total_bytes = 0
for f in folders:
    files = [p for p in (ROOT / "assets" / f).glob("*") if p.is_file()]
    b = sum(p.stat().st_size for p in files)
    total_files += len(files)
    total_bytes += b
    rows.append((f, len(files), b))

biggest = sorted(
    ((p.stat().st_size, p.relative_to(ROOT)) for p in (ROOT / "assets").rglob("*") if p.is_file()),
    reverse=True,
)[:15]

fonts = sorted((ROOT / "assets" / "fonts").glob("*.woff2"))
rive = sorted((ROOT / "assets" / "rive").glob("*.riv"))

lines = [
    "# 05 — Asset ledger",
    "",
    "## Totals",
    "",
    "| Folder | Files | Size |",
    "|---|---:|---:|",
]
for f, n, b in rows:
    lines.append(f"| `assets/{f}/` | {n} | {human(b)} |")
lines += [f"| **Total** | **{total_files}** | **{human(total_bytes)}** |", ""]

lines += ["## Largest files", "", "| Size | Path |", "|---:|---|"]
for size, path in biggest:
    lines.append(f"| {human(size)} | `{path}` |")

lines += ["", "## Fonts", "", "| Family | File | Size |", "|---|---|---:|"]
for p in fonts:
    lines.append(f"| {p.name} | `{p.name}` | {human(p.stat().st_size)} |")

lines += ["", "## Rive animations", "", "| File | Size |", "|---|---:|"]
for p in rive:
    lines.append(f"| `{p.name}` | {human(p.stat().st_size)} |")

lines += [
    "",
    "## Provenance",
    "",
    "- Application bundles, CSS and fonts come from `cdn.shopify.com/oxygen-v2/...` — the exact",
    "  hashed URLs the page requested at capture time.",
    "- Images are the same CDN assets re-requested at `width=700` (or the original for SVG).",
    "  Original full-resolution files remain on the CDN; nothing was upscaled.",
    "- Film loops are the original `.mp4` / `.webm` files referenced by the page.",
    "- The page HTML is the server-rendered response, stored at `snapshot/page.ssr.html`.",
    "- `snapshot/inventory.json` is the exact request list; `assets/manifest.json` records",
    "  status, content type, byte size and a truncated SHA-256 for every file.",
    "",
    "## Rules of use",
    "",
    "1. These files are **Shopify Inc. property**. They are here for study, measurement and",
    "   technique extraction — not for redistribution, resale, or production reuse.",
    "2. Do not re-host the imagery or fonts in a public product. Rebuild with licensed assets.",
    "3. The code written in `site/`, `scripts/` and `src/` is original to this vault.",
    "4. If you publish findings, cite the source URL and the capture date, not the files.",
    "",
]
(ROOT / "docs" / "05-asset-ledger.md").write_text("\n".join(lines))
print("05: ok —", total_files, "files,", human(total_bytes))
