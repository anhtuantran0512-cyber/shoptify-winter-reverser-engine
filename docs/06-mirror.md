# 06 · The mirror — the page itself, served locally

`mirror/` is not a redesign and not a reimplementation. It is the captured
document plus the captured bundles, running from `assets/`. Nothing in it was
written by hand: the SSR HTML keeps its inline router context and its module
bootstrap, the compiled Tailwind stylesheet is byte-identical apart from URL
rewrites, and every JS chunk keeps its own code.

## Why not a static replay

The scroll experience is not in the markup. The page is a React Router 7 app
compiled for Shopify Oxygen; the sticky full-bleed scenes, the KTX2 textures,
the Theatre.js timelines and the Lenis scroll driver are all client-side. A
markup-only copy renders the layout and none of the motion — `site/replay/`
does exactly that, and that is why it shows still images instead of scenes.

The only way to keep the effects without writing new effects is to let the
original app boot.

## What the boot needed

| Missing | Why | Fix |
|---|---|---|
| `AgenticScene`, `RetailScene`, … (11 chunks) | dynamic imports that only fire when a section scrolls into view | `scripts/capture_chunks.py` walks the import graph until closed |
| 37 `.glb` models + 1 HDRI | requested from `editions-winter-2026.myshopify.com` and `dl.polyhaven.org`, outside the original `cdn.shopify.com` sweep | `scripts/capture_3d.py` |
| `basis_transcoder.js/.wasm` | KTX2 decoding, loaded from jsDelivr at runtime | `vendor/three@…/basis/` |
| `rive.wasm` | Rive runtime wasm, loaded from unpkg | `vendor/@rive-app/webgl2@2.37.2/` |
| `NotoSansJP-*`, `coin-reduced.glb`, `404image.jpg` | referenced by lazily-loaded chunks | captured directly |

Without the scene chunks the page still rendered — one background canvas
instead of three — which is exactly the kind of gap a screenshot at the top of
the page would never reveal.

## The three rewrites

`scripts/build_mirror.py` does three mechanical substitutions and nothing else:

1. **Assets → `http://127.0.0.1:4174/assets/<folder>/<name>`**, absolute on
   purpose. The bundles call `new URL(assetUrl)` with no base object; a
   root-relative path throws `TypeError: Failed to construct 'URL'`.
2. **Query strings preserved.** Image code appends `&width=1800` to a URL it
   already has; dropping `?v=…` produced `…webp&width=1800` and 404s.
3. **Package CDNs → `http://127.0.0.1:4174/vendor/`** for the Rive wasm and the
   KTX2 transcoder.

Internal links keep their real destinations (`https://www.shopify.com/…`) so
navigation still works; the page's own anchors resolve to
`/editions/winter2026#…`.

The origin is baked at build time. Serve on another port with
`MIRROR_ORIGIN=http://127.0.0.1:9000 python scripts/build_mirror.py`.

## Serving

The app matches `location.pathname` against its route table, so the mirror must
answer on `/editions/winter2026`. `python -m http.server` cannot do that without
a redirect that adds a trailing slash, which breaks the route match — hence
`scripts/serve_mirror.py`.

Served at `/` the same document comes back with a 200, and then the router
matches no route and React clears the server markup: an empty page that looks
exactly like a broken build. The server therefore 302s `/`, `/index.html` and any
unknown path to the real route, so no URL gets the blank variant.

```bash
python3 scripts/serve_mirror.py 4174
# http://127.0.0.1:4174/editions/winter2026   (or just http://127.0.0.1:4174)
```

## Verification

Captured in Camoufox, both surfaces in the same browser, walking the page in
600 px steps and waiting for the scroll-driven scenes to settle.

```bash
uv venv .qa && . .qa/bin/activate && uv pip install playwright pillow
python scripts/visual_compare.py 6
```

| | live | mirror |
|---|---|---|
| document height | 48 281 px | 48 281 px |
| `[data-section-id]` | 13 | 13 |
| canvases at y=10 000 | 3 | 3 |
| section offsets | — | identical to the pixel |

Pixel difference per frame (1 268 × 720):

```
frame 0 (top)      0.0 % changed
frame 1 (20 %)     0.0 % changed
frame 2 (40 %)     0.0 % changed
frame 3 (60 %)     1.6 % changed   ← rotating globe, different animation phase
frame 4 (80 %)     2.1 % changed   ← same
frame 5 (bottom)   0.0 % changed
```

Console: no application errors. The only noise is Shopify's own consent and
GTM cookies being rejected — they are third-party on `127.0.0.1`, which is a
browser policy, not a page fault. Video playback matches too: the same number of
videos are playing at the same scroll offsets on both surfaces.

## Limits worth knowing

- Images were captured at `width=700`; the `1700w` srcset entry resolves to the
  same file, so a 4K display will see a softer painting than the original.
- `gtag`, GTM and the consent pipeline still call out to Google. Nothing is
  proxied and nothing is faked; offline they fail silently.
- This is a study copy. Copy, imagery, fonts and bundles remain Shopify Inc.
  property and must not be redeployed.
