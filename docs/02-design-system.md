# 02 — Design system

Everything below was read from the compiled stylesheet and the live computed styles. Hex values are exact; class names are the site's own.

---

## 1. Colour

| Token | Value | Role |
|---|---|---|
| Paper | `#F7F7EE` | light surface, body text on dark |
| Ink | `#292919` | dark surface, secondary text |
| Black | `#000000` | stage background |
| Rule | `#DCDCD0` | hairlines on paper |
| Muted | `#909083` | meta, captions |
| Deep muted | `#5C5C4E` | secondary copy |
| Violet | `#5433EB` | rare interactive accent |
| Violet light | `#8051FF` | hover / glow |
| Edition pink | `#EA1360` | sampled from the hero's shopping bag; used here as the vault accent |

The site's own CSS is almost entirely neutral: `text-light` is `#f7f7ee`, `text-dark` is `#292919`, `bg-light` / `bg-dark` mirror them. Colour enters through the paintings, not the components. That is the core move: **neutral interface, chromatic art direction**.

Tailwind's palette is present but barely used — `oklch()` definitions for gray, blue, green, yellow and red survive in the compiled file, mostly for form and consent UI.

## 2. Type

| Class | Family | Size | Line-height | Tracking |
|---|---|---|---:|---:|
| `headline-1` | NeueMontreal 700 | `clamp(120px, 10.96vw + 35.8px, 220px)` | 0.9 | −0.03em |
| `headline-2` | NeueMontreal 700 | 64px | 0.9 | −0.03em |
| `headline-3` | NeueMontreal 700 | 54px | 0.9 | −0.02em |
| `headline-4` | NeueMontreal 700 | 32px | 0.95 | −0.03em |
| `narrative-1` | HWCigars 400 | `clamp(32px, 1.75vw + 18.5px, 48px)` | 0.96 | −0.05em |
| `narrative-2` | HWCigars 400 | 24px | 0.97 | −0.05em |
| `narrative-3` | HWCigars 400 | 20px | 0.97 | −0.04em |
| UI / CTA | Inter Variable | 14px | 1.0 | −0.01em |

Three families, strictly graded: **NeueMontreal** for structural words, **HWCigars** for the editorial voice, **Inter** for controls. **ImperialScript** appears as a decorative signature, not as a text face.

Details that matter:
- `text-box: trim-both cap alphabetic` on display classes — removes the font's internal leading so headlines sit optically flush to rules.
- `text-wrap: pretty` on every display/narrative class.
- Negative tracking scales with size (−0.02 to −0.05em), never a fixed value.
- Line-height below 1 on all display type; the page relies on tight leading for its poster feel.

## 3. Space and grid

| Property | Value |
|---|---|
| Base spacing unit | `0.25rem` |
| Grid gutter | `12px`, `clamp(12px, 1vw, 16px)` on desktop |
| Section grid | 2 columns mobile, 12-column subgrid on `global-lg` |
| Content width | `max-w-4/5` of the stage, left-shifted by `-20cqw` |
| Radius scale | `0.125 / 0.25 / 0.375 / 0.5 / 0.75rem`; pills for header CTA |
| Breakpoints observed | 430, 770, 940, 1024, 1080, 1280, 1680, 1712 px |

Sections never centre a narrow column. They set a stage and align content to its right or left edge, which is why the page reads as a sequence of rooms rather than a stack of blog posts.

## 4. Components observed

- **Fixed header** — wordmark, `Editions` menu, search, `Shopify.com`, pill CTA. Backdrop is transparent over art.
- **Chapter rail** — left edge, Roman numerals I–XII, current chapter in pink. Doubles as navigation and progress.
- **Chapter opener** — oversized word (220 px ceiling), serif deck below, painting behind.
- **Feature grid** — `article` blocks on subgrid columns; title 20–32 px, body 12–14 px, optional text CTA and media.
- **CTAs** — text links with underline/arrow inside content; one white pill in the header.
- **Video affordances** — poster image with a small play control; never autoplay with sound.
- **Consent / commerce UI** — the only place the neutral palette relaxes into standard form controls.

## 5. Motion language

| Token | Curve | Duration | Use |
|---|---|---|---|
| `--lines-easing` | `cubic-bezier(.34,.22,.47,.84)` | 3s | line illustration draw-in |
| `--lines-complete-easing` | `cubic-bezier(.72,.16,.19,.96)` | 1s | completion snap |
| `--scroll-state-easing` | `cubic-bezier(.41,.19,.13,.95)` | 0.6s | scroll-driven scene states |
| `--slide-easing` | `cubic-bezier(.72,.16,.19,.96)` | 0.6s | scene entrance |
| `--fade-out-easing` | `cubic-bezier(.25,.46,.45,.94)` | 0.52s | cross-fade |
| hover | `ease-out` | 0.3s | links, cards |

Named keyframes in the stylesheet: `line-fade`, `load-lines`, `media-entrance`, `stagger-fade-in`, `nav-item-in`, `orbit-path`, `emoji-rise`, `opacityPulse`, `timeline-start`. They are narrative devices — draw, settle, reveal — not decorative loops.

Reduced motion is respected via `@media (prefers-reduced-motion)`, and scene state is driven by `IntersectionObserver` rather than scroll position alone.

## 6. Accessibility notes

- Sections use real `h2` per chapter and `h3/h4` per feature; the DOM outlines cleanly even when visually layered.
- Skip link is the first focusable element.
- CTAs are anchors with visible text; icon-only controls carry `aria-label`.
- Contrast: `#F7F7EE` on `#292919` ≈ 12.6:1; `#909083` on paper is ~3.1:1 and used only for meta text at 10–11 px — a deliberate but borderline choice worth improving in a rebuild.
- Focus rings exist but are custom; don't remove them when adapting.

## 7. Rebuild checklist

1. Set paper `#F7F7EE`, ink `#292919`, one accent. Resist a second accent.
2. Load a geometric grotesque for headlines and a serif for decks. Two roles, no third.
3. Align every card to the headline's column tracks.
4. Use 1 px rules instead of shadows; use space instead of cards where possible.
5. Animate only entrance, state change and scene hand-off. Keep one long draw-in per chapter.
6. Provide empty, loading, error and populated states — the source page hides its loading state behind art, which is elegant but not reusable.
