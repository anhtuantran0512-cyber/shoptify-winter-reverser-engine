# 04 — Motion & media

The page treats scrolling as a timeline. Rive handles authored micro-scenes, video handles product demos, canvas handles one custom scene, and Lenis normalises the input so all three share the same clock.

---

## 1. Motion stack

| Layer | Implementation | Observation |
|---|---|---|
| Smooth scroll | Lenis | 26 references in the page bundle; drives scene progress |
| Scene detection | `IntersectionObserver` | 11 uses; activates media only when a chapter is near |
| Transitions | View Transitions API | 16 references across shared components |
| Authored animation | Rive (`.riv`) | 27 files, WASM runtime, 172 KB chunk |
| Procedural | Canvas 2D | one canvas in the Online chapter |
| Film | `<video>` loops | 77 unique files, muted, short |
| CSS | keyframes + custom properties | line drawing, stagger, orbit, emoji rise |

`detect-gpu` is loaded before the heavy scenes. On a low-tier GPU the site keeps the composition and drops the expensive rendering rather than shipping a broken experience.

## 2. Rive inventory

27 files, all under `assets/rive/`. Names map to product demos:

```
apps_1_12_16.riv            apps_2_12_9_v2.riv         apps_3_12_9_v2.riv
apps_4_12_9.riv             apps_5_12_9_v2.riv         chatgpt_12_10_v5.riv
dev_dash_12_8.riv           flow_12_9.riv              pulse_12_10.riv
rollouts_12_9_v2.riv        sim_gym_12_9.riv           themes_12_9_v9.riv
u113/u132/u151/u15/u16      u172/u200/u2/u50/u5         u6/u7/u8/u82/u95
```

Pattern: product-named files for hero scenes, `u###` files for secondary UI vignettes. Each is small enough to stream on demand; none is inlined.

**To play them back**, use the Rive runtime (`@rive-app/canvas` or `@rive-app/webgl`) and point `src` at the local file. The site itself lazy-loads the runtime only when a Rive canvas enters the viewport.

## 3. Film loops

77 unique `.mp4` / `.webm` files, mostly 0.2–1.1 MB, used as product demos inside feature cards. They are:

- muted and looped,
- poster-backed (`preview_images/*.thumbnail.jpg`),
- not autoplayed until the card is active,
- duplicated in two codecs where browser support matters.

Total download if you mirror all of them: roughly 45–60 MB, which is why the vault keeps them as a separate, lazily listed folder.

## 4. Easing system

```
--lines-duration: 3s;          --lines-easing: cubic-bezier(.34,.22,.47,.84);
--lines-complete-duration: 1s; --lines-complete-easing: cubic-bezier(.72,.16,.19,.96);
--scroll-state-duration: .6s;  --scroll-state-easing: cubic-bezier(.41,.19,.13,.95);
--slide-duration: .6s;         --slide-easing: cubic-bezier(.72,.16,.19,.96);
--fade-out-duration: .52s;     --fade-out-easing: cubic-bezier(.25,.46,.45,.94);
--hover-interaction-duration: .3s;
```

The long 3s draw-in is the signature. Everything else is 0.5–0.6s and exits faster than it enters, which keeps the scroll from feeling laggy.

## 5. Scene choreography (per chapter)

1. Chapter word fades up from the stage (`media-entrance`).
2. Painting settles with a slow scale; headline mask reveals.
3. Feature cards stagger in at 75 ms intervals (`--stagger-fade-in-delay`).
4. Media activates only when the card is in the middle band of the viewport.
5. On exit, the scene cross-fades in 0.52 s and the next chapter's stage mounts.

The `pointer-events-none` section shell with `pointer-events-auto` islands means the artwork can sit behind the cursor without blocking links — a small detail that makes the scroll feel like film rather than a document.

## 6. Rebuilding the motion without copying it

- Use one long authorial animation per chapter, not per card.
- Keep interaction feedback at 0.2–0.3 s; keep scene transitions at 0.5–0.7 s.
- Gate heavy work behind `IntersectionObserver` + a capability check.
- Respect `prefers-reduced-motion`: replace scene transitions with cuts, keep content visible.
- Poster-first for every video; never autoplay sound.
- Prefer CSS/WAAPI for layout motion; reserve Rive/Lottie for illustration that genuinely needs a timeline.
