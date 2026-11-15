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
| Agentic library scene (seated scholar) | `assets/3d/Agentic_fg_251209_*.glb` | `vn/assets/3d/…glb` | texture only |
| Agentic flying props | `assets/3d/EW26_Agentic_Props_251209v5_*.glb` | `vn/assets/3d/…glb` | texture only |
| Retail shop wall (13 decks, frieze) | `assets/3d/Retail_mg_251205v2_*.glb` | `vn/assets/3d/…glb` | texture only |
| POS hall (Huế điện arcade + dome) | `assets/3d/POS_V53_environment_251209v2_*.glb` | `vn/assets/3d/…glb` | texture only |
| Marketing landscape | `assets/3d/EW26_Marketing_251209v4_*.glb` | `vn/assets/3d/…glb` | texture only |
| Checkout customer | `assets/3d/EW26_Checkout_251209_*.glb` | `vn/assets/3d/…glb` | texture only |
| Operations (five figures at a table) | `assets/3d/EW26_Operations_251207_*.glb` | `vn/assets/3d/…glb` | texture only |
| Renaissance globe (Vietnamese map) | `assets/3d/Renaissance_Globe_251209v2-*.glb` | `vn/assets/3d/…glb` | texture only |
| Shop app rider (woman on horse) | `assets/3d/EW26_ShopApp_251208v3_*.glb` | `vn/assets/3d/…glb` | texture only |

## Why this cannot change the effects

The `.glb` files are re-packed by `vn/tools/bake.py`: every buffer view is copied
byte for byte (Draco-compressed meshes, joint weights, animation samplers, node
names, materials) and only the two embedded images are swapped for PNGs, with
the glTF texture reference moved from `KHR_texture_basisu` to core `source`.
Rig, keyframes and shader uniforms are therefore identical to the capture.

## Pipeline

```bash
# 1. decode every embedded texture of every chapter model into vn/work/<chapter>/
python3 vn/tools/decode_all.py            # or: decode_all.py retail pos_env ...

#    paint into vn/art/<chapter>_vn.png (any size; it is resampled to the
#    captured atlas size so UV islands keep their place).  Cut-out atlases keep
#    the captured alpha channel -- the baker re-applies it automatically.

# 2. bake: swap image payloads inside the GLBs, JPEG where the atlas is opaque
python3 vn/tools/bake.py                  # or: bake.py operations shopapp

# 3. chapter backdrops (full-screen plates) -> real Basis KTX2
python3 vn/tools/bake_ktx.py

# 4. publish the overlay map and serve
python3 vn/tools/overlay.py
python3 scripts/serve_mirror.py 4173
```

`vn/work/` holds ~840 MB of decoded atlases and is git-ignored; it is rebuilt
by step 1.

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

## Chapter map

| Chapter | Texture | Motif |
|---|---|---|
| Hero | 2 atlases | Lê scholar garments, Việt heads, calligraphy deck |
| Sidekick | 1 atlas | indigo áo giao lĩnh, lotus-carved panel, terracotta jar |
| Agentic | props + library scene | dó paper books, lattice window, woman scholar |
| Retail | shop wall | Đông Sơn drum, nón lá, Hạ Long, phượng hoàng decks; elephant frieze |
| POS env | hall + dome | Huế điện red lacquer columns, lotus coffers, hạc oculus |
| Marketing | landscape | Ninh Bình karst, rice paddies, nón lá on the river |
| Checkout | customer | áo tứ tân + sage yếm + pink khăn vấn, chữ Nôm parchment |
| Operations | five figures | Lê court dress in the same five poses |
| Globe | equirect map | Vietnamese antique chart, dragon boats, hạc |
| Shop app | rider | áo tứ thân rider, indigo saddle blanket, silk khăn vấn cap |
