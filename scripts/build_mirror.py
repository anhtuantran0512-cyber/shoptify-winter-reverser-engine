#!/usr/bin/env python3
"""
Build the local mirror: the captured page itself, running from assets/.

Nothing is re-implemented. The SSR document keeps its inline router context and
its module bootstrap; the compiled Tailwind CSS and every JS chunk keep their
code. The only transformation is mechanical: every cdn.shopify.com URL is
pointed at the copy in assets/, and same-origin absolute links are pointed at
something that exists locally.

Output: mirror/
  index.html   rewritten SSR document (scripts preserved)
  js/*.js      module graph, imports + asset URLs rewritten
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mirror"
SSR = ROOT / "snapshot" / "page.ssr.html"

# Asset URLs stay root-relative ("/assets/..."): the page then works on
# localhost, a tunnel or any proxy, with no origin guessing. The bundles call
# `new URL(url)` without a base, which throws on a relative string, so the
# document carries a tiny shim (URL_SHIM) that defaults the base to the
# document - the same thing the browser itself does for every other URL use.
ORIGIN = os.environ.get("MIRROR_ORIGIN", "").rstrip("/")

FOLDER = {
    "js": "js",
    "css": "css",
    "fonts": "fonts",
    "images": "images",
    "rive": "rive",
    "video": "video",
    "textures": "textures",
    "data": "data",
    "misc": "misc",
    "html": "html",
    "3d": "3d",
}

# basename -> asset folder, from what actually sits in assets/
BY_NAME: dict[str, str] = {}
for folder in FOLDER.values():
    d = ROOT / "assets" / folder
    if d.is_dir():
        for f in d.iterdir():
            if f.is_file():
                BY_NAME.setdefault(f.name, folder)

URL_RE = re.compile(
    r'https://(?:cdn\.shopify\.com|editions-winter-2026\.myshopify\.com|dl\.polyhaven\.org)'
    r'/[^\s"\'<>\\]+'
)
# chunk *base* prefix: `"https://cdn.shopify.com/oxygen-v2/…/4753383/" + "assets/x.js"`.
# It carries no filename, so the per-URL rewriter can never map it; Vite's
# preload helper appends `assets/<chunk>.js` at runtime and the request goes to
# the live CDN. Point the base at the origin root: `{ORIGIN}/assets/<chunk>` is
# the same file through the mirror's assets symlink.
BASE_RE = re.compile(
    r"https://cdn\.shopify\.com/oxygen-v2/[0-9]+/[0-9]+/[0-9]+/[0-9]+/"
)
CHUNK_RE = re.compile(
    r"https://cdn\.shopify\.com/oxygen-v2/[0-9/]+/assets/([A-Za-z0-9_().\-]+\.(?:js|css))"
    r"(?:\?[^\s\"'<>\\]*)?"
)

# Injected as the first script in <head>. `new URL(path)` with no base throws on
# a relative path; three call sites in the bundles do exactly that (asset URLs,
# canonical links), which aborts hydration and leaves a blank page. Defaulting
# the base to the document is what the platform does for fetch(), src= and
# href=, so relative URLs become uniform everywhere.
URL_SHIM = """<script>(function(){var N=window.URL;if(!N)return;function U(u,b){return b===undefined?new N(u,document.baseURI):new N(u,b)}U.prototype=N.prototype;U.createObjectURL=function(){return N.createObjectURL.apply(N,arguments)};U.revokeObjectURL=function(){return N.revokeObjectURL.apply(N,arguments)};if(N.canParse)U.canParse=function(u,b){return b===undefined?N.canParse(u,document.baseURI):N.canParse(u,b)};if(N.parse)U.parse=function(u,b){return b===undefined?N.parse(u,document.baseURI):N.parse(u,b)};try{window.URL=U}catch(e){}})();</script>"""

SITE = "https://www.shopify.com"

stats = {"hit": 0, "miss": 0, "missing": set()}


def asset_root() -> str:
    """Prefix for local asset URLs: "" (root-relative) unless pinned."""
    return f"{ORIGIN}/" if ORIGIN else "/"


def local(url: str, prefix: str) -> str | None:
    name = url.split("?")[0].rsplit("/", 1)[-1]
    folder = BY_NAME.get(name)
    if not folder:
        return None
    if not (ROOT / "assets" / folder / name).is_file():
        return None
    # keep the query string: the bundles append `&width=` to image URLs
    suffix = "?" + query if (query := url.partition("?")[2]) else ""
    return f"{asset_root()}assets/{folder}/{name}{suffix}"


def rewrite_assets(text: str, prefix: str) -> str:
    """Point every captured CDN URL at its local copy."""

    def repl(m: re.Match) -> str:
        raw = m.group(0)
        trail = ""
        while raw and raw[-1] in ").,;":
            trail = raw[-1] + trail
            raw = raw[:-1]
        found = local(raw, prefix)
        if found:
            stats["hit"] += 1
            return found + trail
        stats["miss"] += 1
        stats["missing"].add(raw.split("?")[0].rsplit("/", 1)[-1])
        return m.group(0)

    return URL_RE.sub(repl, text)


def chunk(name: str) -> str:
    """Compiled chunk -> the folder the capture put it in."""
    return f"/css/{name}" if name.endswith(".css") else f"/js/{name}"


def rewrite_js(text: str) -> str:
    text = BASE_RE.sub(asset_root(), text)
    text = CHUNK_RE.sub(lambda m: chunk(m.group(1)), text)
    # package CDN bases (Rive wasm, three.js KTX2 transcoder) stay local too
    text = text.replace("https://unpkg.com/", f"{asset_root()}vendor/")
    # three.js GLTFLoader defaults its DRACO decoder to gstatic; the capture has
    # no copy, so vendor/ carries one (npm three examples/jsm/libs/draco)
    text = text.replace(
        "https://www.gstatic.com/draco/versioned/decoders/1.5.6/",
        f"{asset_root()}vendor/draco@1.5.6/",
    )
    text = text.replace("https://cdn.jsdelivr.net/npm/", f"{ORIGIN}/vendor/")
    return rewrite_assets(text, "")


def rewrite_html(html: str) -> str:
    html = BASE_RE.sub(asset_root(), html)
    # everything that pointed at the live site keeps working online, except the
    # anchor links of this page and the local /js + /assets paths
    html = re.sub(
        r'href="/(?!/)(?!/js/)(?!/assets/)(?!https://cdn\.shopify\.com)',
        f'href="{SITE}/',
        html,
    )
    # ...but the site's own asset paths must stay local, not become shopify.com
    html = html.replace(f'href="{SITE}/assets/', 'href="/assets/')
    # canonical + hreflang links must stay absolute: the bundles run `new URL()`
    # on them, which throws on a root-relative path
    if ORIGIN:
        html = html.replace(
            f'href="{SITE}/editions/winter2026', f'href="{ORIGIN}/editions/winter2026'
        )

    # sibling chunks (inline bootstrap imports, stylesheet links)
    html = CHUNK_RE.sub(lambda m: chunk(m.group(1)), html)
    html = rewrite_assets(html, "")
    # the shim must run before any module script evaluates
    for anchor in ("<head>", "<head ", "<HEAD>"):
        if anchor in html:
            if anchor == "<head>":
                html = html.replace(anchor, anchor + URL_SHIM, 1)
            break
    return html


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "js").mkdir(parents=True)

    html = SSR.read_text()
    html = rewrite_html(html)
    (OUT / "index.html").write_text(html)

    for js in (ROOT / "assets" / "js").glob("*.js"):
        (OUT / "js" / js.name).write_text(rewrite_js(js.read_text(errors="ignore")))

    (OUT / "css").mkdir()
    for css in (ROOT / "assets" / "css").glob("*.css"):
        (OUT / "css" / css.name).write_text(
            rewrite_assets(css.read_text(errors="ignore"), "")
        )

    # npm packages the bundles pull at runtime: Rive wasm + KTX2 transcoder
    link = OUT / "vendor"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(ROOT / "vendor")

    # the rewritten page asks for {ORIGIN}/assets/...; expose the capture there
    link = OUT / "assets"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(ROOT / "assets")

    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"mirror -> {OUT}  ({size / 1e6:.1f} MB)")
    print(f"urls   local={stats['hit']} missing={stats['miss']}")
    for name in sorted(stats["missing"]):
        print(f"  missing {name}")


if __name__ == "__main__":
    main()
