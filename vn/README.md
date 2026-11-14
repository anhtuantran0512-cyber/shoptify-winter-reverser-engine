# Vietnamese re-skin layer

The captured page is kept exactly as it is (`assets/`, `mirror/`); this folder
supplies **surface art only**. Nothing here touches geometry, rigs, animation
curves, shaders, timings or copy — the models, the Rive files, the scroll
choreography and the effects all remain the ones from the capture.

## What gets replaced

| Target | Original asset | Replacement | Touches |
|---|---|---|---|
| Hero characters (2 figures, robe, props) | `assets/3d/EW26_Hero_251207v3_*.glb` | `vn/assets/3d/…glb` | texture atlas only |
| Hero portrait heads | same glb, image 1 | `vn/art/hero_faces_vn.png` | texture only |
| Hero backdrop painting | `assets/textures/Hero-bg-hires-optimized.ktx2` | `vn/assets/ktx/…ktx2` | pixels only |
| Sidekick scholar (áo giao lĩnh, khăn đóng) | `assets/3d/EW26_Sidekick_251208_*.glb` | `vn/assets/3d/…glb` | texture atlas only |

## Why this cannot change the effects

The `.glb` files are re-packed by `vn/tools/bake.py`: every buffer view is copied
byte for byte (Draco-compressed meshes, joint weights, animation samplers, node
names, materials) and only the two embedded images are swapped for PNGs, with
the glTF texture reference moved from `KHR_texture_basisu` to core `source`.
Rig, keyframes and shader uniforms are therefore identical to the capture.

## Pipeline

```bash
# 1. pull the embedded textures out of a captured model (KTX2)
python3 vn/tools/extract.py hero assets/3d/EW26_Hero_251207v3_compressed-optimized.glb

# 2. decode them for painting (basis_universal CLI: bin/basisu -unpack -ktx2 in.ktx2)
#    re-encode the painted result: bin/basisu -ktx2 -q 255 -mipmap out.png

# 3. bake the re-skin into vn/assets/ and publish the overlay map
python3 vn/tools/bake.py
python3 vn/tools/overlay.py

# 4. serve; serve_mirror.py resolves /assets/... through vn/assets/overlay.json
python3 scripts/serve_mirror.py 4173
```

Deleting `vn/assets/overlay.json` restores the untouched capture instantly.

## Art direction

Vietnamese, and specifically:
- **people**: Lê-dynasty scholar (khăn đóng, áo giao lĩnh), Việt women with black
  hair in a loose bun, all in the same Renaissance oil technique and lighting
- **garments**: raw ivory silk, indigo, lacquer red, gold brocade, lotus and
  water-ripple motifs
- **landscape**: areca palm and bamboo uprights where cypresses stood, banyan
  and jackfruit crowns where umbrella pines stood, white mai blossom where the
  pale flowering masses were, wet rice terraces in the foreground
- **props**: terracotta jar instead of the glass bottle, lotus-carved wooden
  panel instead of the classical frieze, Đông Sơn spiral and calligraphic brush
  strokes on the skateboard deck
- the single hot-pink accent of the page is preserved throughout
