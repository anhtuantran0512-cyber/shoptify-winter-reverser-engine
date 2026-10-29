# 01 — Teardown

**Source** `https://www.shopify.com/editions/winter2026`
**Captured** 29 Oct 2026, one session, desktop viewport 1280×720
**Method** Camoufox (Camofox MCP) + `performance.getEntriesByType('resource')` + DOM walk + CDN retrieval

---

## 1. What the page is

A launch film disguised as a web page. One route, one scroll, twelve chapters, 199 product updates. The document is 46,000–48,000 px tall depending on viewport; each chapter is a sticky scene with a painted backdrop, a giant category word and a grid of feature cards that resolve as you move through it.

The visual thesis is in the title: **The Renaissance Edition**. Classical painting, modern commerce, one saturated pink shopping bag. The interface itself stays almost monochrome so the art direction can carry the colour.

## 2. Runtime stack

| Layer | What was found | Evidence |
|---|---|---|
| Hosting / framework | Shopify Oxygen + Remix (React Router) | `window.__remixManifest`, `/oxygen-v2/.../assets/` paths |
| CSS | Tailwind CSS 4.2.2, 129.7 KB compiled | first line of `tailwind-G-N6aznT.css` |
| Motion | Rive (27 files) + Lenis smooth scroll + View Transitions | `rive-DN8nxF7J.js`, `lenis` references, `startViewTransition` |
| Media | Responsive image CDN, 77 film loops, canvas scenes | `srcset` at 9 widths, `.mp4` / `.webm` |
| GPU | `detect-gpu` before heavy scenes | `detect-gpu.esm-rYSyepAo.js` |
| Analytics | GTM `GTM-KW6FGBL7`, GA4 | network entries |
| Fonts | NeueMontreal 700, HWCigars 400, ImperialScript 400, Inter Variable | `fonts-latin-CzfLCQn_.css` |

### Bundle map

| File | Size | Role |
|---|---:|---|
| `components-BdJai906.js` | 248 KB | shared component library |
| `(_locale).editions.winter2026-CdSmWtXg.js` | 240 KB | page route: scenes, scroll orchestration, Lenis |
| `rive-DN8nxF7J.js` | 172 KB | Rive runtime + WASM loader |
| `constants-AgmyR9jG.js` | 56 KB | copy/data constants |
| `index-PQP4aay3.js` | 56 KB | shared index chunk |
| `Button-uHjSK4Hu.js` | 36 KB | button variants |
| `root-C6D-dr4m.js` | 12 KB | document shell |
| remaining six chunks | 24 KB | entry, manifest, meta, error logging, consent |

### Routes in the same build

```
/                             ($locale root)
/editions/winter2026          the page studied here
/editions/winter2026/key      feature index
/editions/winter2026/video/:handle
/editions/winter2026/merch    swag store
/editions/winter2026/cart
/test-500
```

This is not a campaign microsite with a static export. It is a Hydrogen storefront: the merch drop and cart are first-class routes in the same Remix manifest.

## 3. Document shape

- 1.47 MB of server-rendered HTML.
- ~398 KB of inline `<script>` — serialized loader data, not hand-written code.
- Zero `<style>` tags: all styling is the compiled Tailwind file.
- 12 `<section id>` blocks inside `#main-content`; heights from 1,916 px (Checkout) to 7,946 px (Sidekick).
- Sections are `pointer-events-none` shells with `pointer-events-auto` islands. This lets the painted background own the cursor while CTAs stay clickable.
- The hero is translated `-100%` above the main flow, so the first paint is a fixed stage rather than a normal header.

## 4. Layout technique

The grid is a 12-column subgrid with a 12–16 px gutter:

```
global-lg:max-w-4/5  →  grid-template-with-gaps
grid-cols-subgrid    →  articles inherit the column tracks
```

Two consequences worth stealing:

1. **Feature cards align to the same rails as the headline.** No independent card grid, no drift.
2. **Container queries (`w-[100cqw]`, `left-[-20cqw]`)** let a chapter shift its own stage without measuring the viewport.

Section labelling uses two type roles only: `headline-1` for the chapter word (up to 220 px), `narrative-1` for the serif deck. Everything else is 12–14 px UI text. That restraint is why 46,000 px never feels loud.

## 5. Performance posture

The initial document is heavy (1.47 MB HTML) but the media is disciplined: images are CDN-resized per breakpoint, film loops are short and muted, Rive files are 20–300 KB each, and `content-visibility` plus `IntersectionObserver` defer off-screen scenes. `detect-gpu` gates the expensive canvas work, so low-tier devices get the static composition instead of a slideshow.

## 6. What to take, what to leave

**Take**
- The chapter model: one idea per 2,000–8,000 px, each with its own art direction.
- Paper/ink palette with a single saturated accent.
- Two-type-role discipline (display + narrative) and hairline rules.
- Subgrid alignment between headline and cards.
- Easing curves that feel like physical settles, not linear fades.

**Leave**
- The paintings, copy, fonts and Rive files as production assets. They are Shopify's.
- The 1.47 MB SSR document. It works for a flagship launch; it is wrong for a dashboard.
- The 46,000 px length unless you have twelve genuinely distinct stories.

## 7. Reproduce the capture

```bash
camofox open "https://www.shopify.com/editions/winter2026"
python3 scripts/extract_page.py <tabId>
python3 scripts/build_inventory.py
python3 scripts/capture_assets.py snapshot/inventory.json assets
python3 scripts/build_site_data.py
```

Output: `snapshot/page-content.json`, `snapshot/inventory.json`, `assets/`, `site/data.js`.
