#!/usr/bin/env python3
"""Build site/data.js + compressed chapter media for the shoptify vault."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MEDIA = SITE / "media"
SNAP = ROOT / "snapshot"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# notes that are not derivable from the DOM
CHAPTER_NOTES = {
    "sidekick": "The opener doubles as the product thesis: an AI operator that acts inside the admin. 19 updates across four movements - insight, delegation, design, simplification.",
    "agentic": "Two updates, one idea: storefronts that live inside AI chat. The shortest chapter, treated as a manifesto page.",
    "online": "The largest product story after Developer. Rollouts (A/B testing), SimGym (agentic shopper simulation) and a long tail of merchandising upgrades.",
    "retail": "Hardware as narrative. POS Hub, connected scanners, subscriptions and in-store operational depth.",
    "marketing": "Product Network is the headline: cross-merchant product placement inside Shopify surfaces.",
    "checkout": "Conversion mechanics: Shop Pay, per-market customization, local payment expansion.",
    "operations": "Inventory modelling, mobile quick sale, analytics visualisation and admin security.",
    "shop-app": "Shop as a consumer surface: dynamic storefronts, deals feed, shoppable video, Minis.",
    "b2b": "Wholesale goes global: Collective, ACH, per-fulfillment payments and retailer discovery.",
    "finance": "Capital, Balance and Credit converge into an embedded fintech suite.",
    "shipping": "Carrier breadth, packaging defaults and returns workflow.",
    "developer": "The technical centrepiece: 54 updates, MCP tooling, commerce agents and the new build stack.",
}

FEATURE_GROUPS = {
    "sidekick": ["Insights, proactively delivered", "Complexity, delegated", "Designs, refined", "Tedious tasks, simplified"],
}


def dominant_color(path: Path) -> str:
    """Pick a vivid, recurring colour from the frame (not the muddy average)."""
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((120, 120))
        q = img.quantize(colors=16, method=Image.Quantize.MEDIANCUT).convert("RGB")
        counts = {}
        for px in q.get_flattened_data():
            r, g, b = px
            mx, mn = max(px), min(px)
            if mx < 60 or mx > 245:
                continue
            sat = (mx - mn) / mx if mx else 0
            if sat < 0.28:
                continue
            counts[px] = counts.get(px, 0) + 1
        if not counts:
            return "#8c8c83"
        # weight by frequency and saturation
        def score(item):
            px, n = item
            mx, mn = max(px), min(px)
            return n * ((mx - mn) / mx)

        px = max(counts.items(), key=score)[0]
        return "#%02x%02x%02x" % px
    except Exception:
        return "#8c8c83"


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def main() -> None:
    content = json.loads((SNAP / "page-content.json").read_text())
    MEDIA.mkdir(parents=True, exist_ok=True)

    # --- compress chapter shots -------------------------------------------
    # only 00-hero.png and NN-<chapter>.png are reference frames; QA/vault shots
    # live in the same folder but must not enter the chapter gallery.
    shots = sorted(
        p for p in (SNAP / "screenshots").glob("*.png") if re.match(r"^\d{2}-[a-z0-9-]+\.png$", p.name)
    )
    media_index = {}
    for shot in shots:
        out = MEDIA / (shot.stem + ".webp")
        if not out.exists():
            with Image.open(shot) as im:
                im = im.convert("RGB")
                im.thumbnail((1400, 1400))
                im.save(out, "WEBP", quality=80, method=5)
        media_index[shot.stem] = f"media/{out.name}"

    # --- filesystem inventory ---------------------------------------------
    kinds = {"js": "js", "css": "css", "fonts": "fonts", "rive": "rive", "images": "images", "video": "video", "html": "html"}
    assets = {}
    for key, folder in kinds.items():
        files = [p for p in (ROOT / "assets" / folder).glob("*") if p.is_file()]
        assets[key] = {
            "count": len(files),
            "bytes": sum(p.stat().st_size for p in files),
            "samples": sorted(p.name for p in files)[:12],
            "files": sorted(p.name for p in files) if key in ("images", "rive", "video", "fonts") else [],
        }

    bundles = []
    for p in sorted((ROOT / "assets" / "js").glob("*.js")):
        bundles.append({"name": p.name, "bytes": p.stat().st_size})
    bundles.sort(key=lambda b: -b["bytes"])

    routes = []
    manifest = ROOT / "assets" / "js" / "manifest-2c6320c2.js"
    if manifest.exists():
        raw = manifest.read_text()
        m = re.search(r"window\.__remixManifest=(\{.*\});?\s*$", raw, re.S)
        if m:
            parsed = json.loads(m.group(1))
            routes = [
                {"id": k, "path": v.get("path", ""), "hasLoader": v.get("hasLoader", False)}
                for k, v in parsed.get("routes", {}).items()
            ]

    # --- chapters ----------------------------------------------------------
    chapters = []
    for i, sec in enumerate(content["sections"]):
        stem = f"{i + 1:02d}-{sec['id']}"
        shot = SNAP / "screenshots" / f"{stem}.png"
        chapters.append(
            {
                "index": i + 1,
                "roman": ROMAN[i],
                "id": sec["id"],
                "title": sec["title"],
                "lead": sec["lead"],
                "features": sec["features"],
                "featureCount": len(sec["features"]),
                "groups": FEATURE_GROUPS.get(sec["id"], sec["groupLabels"]),
                "note": CHAPTER_NOTES.get(sec["id"], ""),
                "heightPx": sec["heightPx"],
                "canvases": sec["canvases"],
                "images": sec["images"],
                "links": sec["links"],
                "accent": dominant_color(shot) if shot.exists() else "#8c8c83",
                "shot": media_index.get(stem, ""),
            }
        )

    total_assets = sum(v["bytes"] for v in assets.values())
    total_files = sum(v["count"] for v in assets.values())

    data = {
        "meta": {
            "name": "shoptify",
            "title": "Shoptify",
            "subtitle": "Winter '26 Editions - study vault",
            "source": content["url"],
            "capturedAt": content["capturedAt"],
            "description": content["meta"]["description"],
            "legal": (
                "Reference study. Page copy, imagery, fonts and bundles remain the property of Shopify Inc. "
                "Captured from publicly served front-end resources for internal learning; not for redistribution or production reuse."
            ),
        },
        "stats": {
            "files": total_files,
            "bytes": total_assets,
            "size": human(total_assets),
            "features": content["totals"]["features"],
            "chapters": len(chapters),
            "pageHeight": content["totals"]["pageHeight"],
            "links": content["totals"]["links"],
        },
        "assets": assets,
        "bundles": bundles,
        "routes": routes,
        "chapters": chapters,
        "hero": media_index.get("00-hero", ""),
        "shotList": [{"stem": k, "path": v} for k, v in media_index.items()],
        "tokens": {
            "colors": [
                {"name": "Paper", "hex": "#F7F7EE", "use": "Primary light surface, body text on dark"},
                {"name": "Ink", "hex": "#292919", "use": "Dark surface, secondary text"},
                {"name": "Black", "hex": "#000000", "use": "Stage background, headlines"},
                {"name": "Rule", "hex": "#DCDCD0", "use": "Hairlines, dividers on paper"},
                {"name": "Muted", "hex": "#909083", "use": "Meta labels, captions"},
                {"name": "Deep muted", "hex": "#5C5C4E", "use": "Secondary copy"},
                {"name": "Violet", "hex": "#5433EB", "use": "Rare interactive accent"},
                {"name": "Violet light", "hex": "#8051FF", "use": "Hover / glow"},
            ],
            "type": [
                {"name": "NeueMontreal Bold", "class": "headline-1", "size": "72px -> clamp(120px, 10.96vw, 220px)", "lh": "0.9", "ls": "-0.03em", "font": "NeueMontreal, Helvetica, Arial", "sample": "Renaissance"},
                {"name": "NeueMontreal Bold", "class": "headline-2", "size": "64px", "lh": "0.9", "ls": "-0.03em", "font": "NeueMontreal", "sample": "Commerce, reimagined"},
                {"name": "NeueMontreal Bold", "class": "headline-4", "size": "32px", "lh": "0.95", "ls": "-0.03em", "font": "NeueMontreal", "sample": "Agentic storefronts"},
                {"name": "HWCigars Regular", "class": "narrative-1", "size": "28px -> clamp(32px, 1.75vw + 18.5px, 48px)", "lh": "0.96", "ls": "-0.05em", "font": "HWCigars, Georgia, serif", "sample": "A new world of commerce."},
                {"name": "HWCigars Regular", "class": "narrative-2", "size": "24px", "lh": "0.97", "ls": "-0.05em", "font": "HWCigars", "sample": "150+ product updates."},
                {"name": "ImperialScript", "class": "script", "size": "display", "lh": "1", "ls": "0", "font": "ImperialScript, cursive", "sample": "The Renaissance Edition"},
                {"name": "Inter Variable", "class": "ui", "size": "14px", "lh": "1", "ls": "-0.01em", "font": "Inter-Variable, Helvetica", "sample": "Start for free"},
            ],
            "layout": [
                {"k": "Grid gap", "v": "12px mobile -> clamp(12px, 1vw, 16px) desktop"},
                {"k": "Subgrid", "v": "grid-cols-subgrid 2 / 12 columns inside sections"},
                {"k": "Section height", "v": "1,916px - 7,946px (deliberate scroll scenes)"},
                {"k": "Radius", "v": "0.125rem - 0.75rem (xs -> xl); pills for header CTA"},
                {"k": "Breakpoints", "v": "430, 770, 940, 1024, 1080, 1280, 1680, 1712 px"},
            ],
            "motion": [
                {"name": "lines-draw", "curve": "cubic-bezier(0.34, 0.22, 0.47, 0.84)", "dur": "3s", "use": "Hero line illustration draw-in"},
                {"name": "lines-complete", "curve": "cubic-bezier(0.72, 0.16, 0.19, 0.96)", "dur": "1s", "use": "Line completion snap"},
                {"name": "scroll-state", "curve": "cubic-bezier(0.41, 0.19, 0.13, 0.95)", "dur": "0.6s", "use": "Scroll-linked state transitions"},
                {"name": "slide", "curve": "cubic-bezier(0.72, 0.16, 0.19, 0.96)", "dur": "0.6s", "use": "Slide / scene entrance"},
                {"name": "fade-out", "curve": "cubic-bezier(0.25, 0.46, 0.45, 0.94)", "dur": "0.52s", "use": "Cross-fade between scenes"},
                {"name": "hover", "curve": "ease-out", "dur": "0.3s", "use": "Links, cards, CTA"},
            ],
            "stack": [
                {"name": "Shopify Oxygen", "detail": "Hosting + edge runtime for the Hydrogen storefront"},
                {"name": "Remix / React Router", "detail": "window.__remixManifest, 9 routes incl. cart, merch, video/:handle"},
                {"name": "Tailwind CSS 4.2.2", "detail": "129.7 KB compiled CSS, @layer properties + utilities, oklch palette"},
                {"name": "Rive", "detail": "27 .riv files, WASM runtime chunk 172 KB"},
                {"name": "Lenis", "detail": "Smooth scroll orchestration in the page bundle"},
                {"name": "detect-gpu", "detail": "GPU tiering before heavy canvas / WebGL scenes"},
                {"name": "View Transitions + IntersectionObserver", "detail": "Scene hand-off and lazy media activation"},
                {"name": "Google Tag Manager", "detail": "GTM-KW6FGBL7 + GA4 measurement"},
            ],
        },
        "resources": {
            "fonts": [
                {"family": "NeueMontreal", "weight": 700, "file": "3ee238256136fcfdfca35decbd44d0d4.woff2"},
                {"family": "HWCigars", "weight": 400, "file": "49a57a6e59f6a50f0627418abeb58fec.woff2"},
                {"family": "ImperialScript", "weight": 400, "file": "389d4f8566b3b9cbe083b682c7fabf06.woff2"},
                {"family": "Inter Variable", "weight": 400, "file": "5949cd393a8375a896fd0a9b74307666.woff2"},
            ],
            "css": ["tailwind-G-N6aznT.css", "fonts-latin-CzfLCQn_.css"],
        },
        "docs": [
            {"name": "Teardown", "path": "docs/01-teardown.md"},
            {"name": "Design system", "path": "docs/02-design-system.md"},
            {"name": "Information architecture", "path": "docs/03-information-architecture.md"},
            {"name": "Motion & media", "path": "docs/04-motion-and-media.md"},
            {"name": "Asset ledger", "path": "docs/05-asset-ledger.md"},
        ],
    }

    (SITE / "data.js").write_text("window.SHOPTIFY = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"data.js: {(SITE / 'data.js').stat().st_size:,} bytes")
    print(f"media: {len(media_index)} webp")
    print(f"stats: {data['stats']}")
    print("accents:", {c['id']: c['accent'] for c in chapters})


if __name__ == "__main__":
    main()
