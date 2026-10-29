#!/usr/bin/env python3
"""
Build a local replay of the captured Editions page.

Takes the server-rendered HTML exactly as Shopify served it, plus the compiled
CSS and JS bundles, and rewrites every cdn.shopify.com URL to the local capture.
The result is not a redesign: it is the page itself, running from assets/.

Output: site/replay/
  index.html                 rewritten SSR document
  tailwind-*.css             compiled Tailwind, url() rewritten
  fonts-*.css                font faces, url() rewritten
  js/*.js                    module graph, imports + asset URLs rewritten
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "replay"
INV = json.loads((ROOT / "snapshot" / "inventory.json").read_text())

FOLDER = {
    "js": "js",
    "css": "css",
    "font": "fonts",
    "image": "images",
    "rive": "rive",
    "video": "video",
    "texture": "textures",
    "data": "data",
    "misc": "misc",
    "html": "html",
}

# basename -> asset type, from the capture inventory
BY_NAME: dict[str, str] = {}
for item in INV:
    name = item["url"].split("?")[0].rsplit("/", 1)[-1]
    BY_NAME.setdefault(name, item["type"])

REPLAY_JS = r"""
// Static replay runtime: hydrate lazy media, autoplay videos, reveal on scroll.
const io = (cb, opts) => new IntersectionObserver(cb, opts || { threshold: 0.15, rootMargin: '0px 0px -10% 0px' });

// 1. lazy media: data-src / data-srcset -> src / srcset
document.querySelectorAll('[data-src]').forEach(el => {
  const u = el.getAttribute('data-src');
  if (u) { el.setAttribute('src', u); el.removeAttribute('data-src'); }
});
document.querySelectorAll('[data-srcset]').forEach(el => {
  const u = el.getAttribute('data-srcset');
  if (u) { el.setAttribute('srcset', u); el.removeAttribute('data-srcset'); }
});
// video elements with data-src (already handled above) + force load
document.querySelectorAll('video').forEach(v => {
  v.muted = true; v.loop = true; v.playsInline = true; v.autoplay = false;
  v.setAttribute('preload', 'metadata');
  try { v.load(); } catch (e) {}
});

// 2. autoplay videos when visible
const vio = io((entries) => {
  entries.forEach(e => {
    const v = e.target;
    if (e.isIntersecting) { v.play().catch(()=>{}); }
    else { v.pause(); }
  });
}, { threshold: 0.25 });
document.querySelectorAll('video').forEach(v => vio.observe(v));

// 3. reveal elements carrying data-reveal (none by default; CSS handles .opacity-0 nav overlays)
// Force-load all images (remove loading=lazy for above-the-fold feel)
document.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = 'eager'; });

// 4. smooth anchor scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const t = document.getElementById(id);
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
});
"""


URL_RE = re.compile(r'https://cdn\.shopify\.com/[^\s"\'<>\\]+')
OXYGEN_RE = re.compile(
    r"https://cdn\.shopify\.com/oxygen-v2/[0-9/]+/assets/([A-Za-z0-9_().\-]+\.(?:js|css))"
    r"(?:\?[^\s\"'<>\\]*)?"
)


def local_for(url: str, prefix: str) -> str | None:
    path = url.split("?")[0]
    name = path.rsplit("/", 1)[-1]
    kind = BY_NAME.get(name)
    if not kind:
        return None
    folder = FOLDER.get(kind)
    if not folder:
        return None
    if not (ROOT / "assets" / folder / name).is_file():
        return None
    return f"{prefix}/assets/{folder}/{name}"


def rewrite(text: str, prefix: str, css_or_js: bool) -> tuple[str, int, int]:
    hits = 0
    misses = 0

    def repl(m: re.Match) -> str:
        nonlocal hits, misses
        raw = m.group(0)
        # url(...) and prose capture the closing paren as part of the match
        trail = ""
        while raw and raw[-1] in ").,;":
            trail = raw[-1] + trail
            raw = raw[:-1]
        local = local_for(raw, prefix)
        if local:
            hits += 1
            return local + trail
        misses += 1
        return m.group(0)

    text = URL_RE.sub(repl, text)
    if css_or_js:
        # inside a stylesheet or module every oxygen chunk sits in the same folder
        text = OXYGEN_RE.sub(lambda m: f"./{m.group(1)}", text)
    return text, hits, misses


def rewrite_js(text: str) -> tuple[str, int, int]:
    """Module imports stay in ./; runtime asset fetches climb to /assets."""
    # same-folder chunk references first (both `from"https://..."` and import())
    swapped = 0
    def chunk(m: re.Match) -> str:
        nonlocal swapped
        swapped += 1
        return f"./{m.group(1)}"
    text = OXYGEN_RE.sub(chunk, text)

    text, hits, misses = rewrite(text, "../../..", css_or_js=False)
    return text, hits + swapped, misses


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "js").mkdir(parents=True)

    # --- HTML ------------------------------------------------------------
    html = (ROOT / "snapshot" / "page.ssr.html").read_text()
    html, h_hits, h_miss = rewrite(html, "../..", css_or_js=True)
    # stylesheet + script tags now point at ./oxygen filenames
    html = re.sub(
        r'(<link[^>]+href=")\./([A-Za-z0-9_().\-]+\.css)(")',
        r"\1./\2\3",
        html,
    )
    (OUT / "index.html").write_text(html)

    # --- CSS -------------------------------------------------------------
    css_stats = []
    for css in (ROOT / "assets" / "css").glob("*.css"):
        text, hits, miss = rewrite(css.read_text(errors="ignore"), "../..", css_or_js=True)
        (OUT / css.name).write_text(text)
        css_stats.append((css.name, hits, miss))

    # --- JS --------------------------------------------------------------
    js_stats = []
    for js in (ROOT / "assets" / "js").glob("*.js"):
        text, hits, miss = rewrite_js(js.read_text(errors="ignore"))
        (OUT / "js" / js.name).write_text(text)
        js_stats.append((js.name, hits, miss))

    # --- strip hydration + analytics: keep the SSR markup only ----------
    html = (OUT / "index.html").read_text()
    # remove all script tags (inline streamed data + bundles + analytics)
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script\b[^>]*/>', '', html)
    # remove GTM iframe
    html = re.sub(r'<iframe[^>]*googletagmanager[^>]*>.*?</iframe>', '', html, flags=re.DOTALL)
    # inject hero fallback image into the empty hero scene container
    html = html.replace(
        '<div class="relative overflow-clip flex justify-end safe-h-150-svh translate-y-[-100%]" data-section-id="hero"></div>',
        '<div class="relative overflow-clip flex justify-end safe-h-150-svh" data-section-id="hero">' +
        '<img src="../../assets/images/herofallback.jpg" alt="Shopify Editions Winter 26" class="absolute inset-0 w-full h-full object-cover" />' +
        '</div>'
    )
    # inject our small runtime before </body>
    html = html.replace('</body>', '<script type="module" src="./replay.js"></script>\n</body>')
    # ensure smooth scroll
    html = html.replace('</head>', '<style>html{scroll-behavior:smooth} [data-reveal]{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease} [data-reveal].is-in{opacity:1;transform:none}</style>\n</head>')
    (OUT / "index.html").write_text(html)

    (OUT / "replay.js").write_text(REPLAY_JS)
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"replay -> {OUT}  ({size/1e6:.1f} MB)")
    print(f"html  resolved={h_hits} left={h_miss}")
    for n, h, m in css_stats:
        print(f"css   {n:28} resolved={h:3} left={m}")
    for n, h, m in js_stats:
        print(f"js    {n:40} resolved={h:3} left={m}")


if __name__ == "__main__":
    main()
