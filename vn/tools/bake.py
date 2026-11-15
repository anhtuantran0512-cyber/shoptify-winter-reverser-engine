#!/usr/bin/env python3
"""Bake the Vietnamese re-skin into a drop-in copy of the captured models.

Nothing about behaviour changes: the script only swaps the images embedded in
each .glb (and the standalone .ktx2 backdrops), then writes the result under
vn/assets/. Geometry, Draco payload, skinning, animation samplers, materials,
lights and node names are copied through untouched, and the glTF texture
references are switched from KHR_texture_basisu to core PNG/JPEG.

    python3 vn/tools/bake.py            # all chapters
    python3 vn/tools/bake.py hero       # just one
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "vn" / "assets"
ART = ROOT / "vn" / "art"

# chapter -> {embedded image index: (art file, (width, height) of the original)}
# The art is resampled to the captured texture size so UV islands keep their
# exact place in the atlas.
GLB_SKINS: dict[str, dict[int, tuple[str, tuple[int, int]]]] = {
    "hero": {
        0: ("hero_atlas_vn.png", (2048, 2048)),
        1: ("hero_faces_vn.png", (1024, 512)),
    },
    "sidekick": {0: ("sidekick_vn.png", (2048, 2048))},
    "agentic": {1: ("agentic_props_vn.png", (1024, 1024))},
    "agentic_fg": {0: ("agentic_fg_vn.png", (2048, 1152))},
    "marketing": {0: ("marketing_vn.png", (2048, 2048))},
    "checkout": {0: ("checkout_vn.png", (2048, 2048))},
    "operations": {0: ("operations_vn.png", (2048, 2048))},
    "shopapp": {0: ("shopapp_vn.png", (2048, 2048))},
    "retail": {0: ("retail_vn.png", (2048, 2048))},
    "pos_env": {
        0: ("pos_env_vn.png", (2048, 2048)),
        1: ("pos_env_dome_vn.png", (2048, 2048)),
    },
    "globe": {0: ("globe_vn.png", (1024, 512))},
    "b2b": {
        0: ("b2b_vn.png", (2048, 2048)),
        1: ("b2b_heads_vn.png", (1024, 512)),
    },
    "finance": {
        0: ("finance_tree_vn.png", (1024, 1024)),
        1: ("finance_vn.png", (2048, 2048)),
    },
    "shipping": {0: ("shipping_vn.png", (2048, 2048))},
    "online": {1: ("online_vn.png", (2048, 2048))},
    "developer": {0: ("developer_vn.png", (2048, 2048))},
    # the chapters also load separate *_fg / *_bg models whose atlases are the
    # same artwork, so they reuse the painted files above
    # Operations_fg_* carries the same five-figure composition as the EW26
    # model, so the same painting serves both.
    "operations_fg": {0: ("operations_vn.png", (2048, 2048))},
    # B2B_fg_* is a different layout (two seated figures + heads), painted
    # separately.
    "b2b_fg": {
        0: ("b2b_fg_vn.png", (2048, 2048)),
        2: ("b2b_heads_vn.png", (1024, 512)),
    },
    "online_fg": {2: ("online_vn.png", (2048, 2048))},
    "shipping_fg": {1: ("shipping_vn.png", (2048, 2048))},
    "marketing_fg": {0: ("marketing_vn.png", (2048, 2048))},
    "checkout_fg": {0: ("checkout_vn.png", (2048, 2048))},
    "finance_fg": {
        0: ("finance_tree_vn.png", (512, 512)),
        1: ("finance_vn.png", (2048, 2048)),
    },
    "checkout_bg": {0: ("ktx/Checkout_bg_diffuse-optimized_vn.png", (2048, 1024))},
    "shipping_bg": {0: ("ktx/Shipping_bg_diffuse-optimized_vn.png", (2048, 2048))},
    "marketing": {0: ("marketing_vn.png", (2048, 2048))},
}

# atlases that are a figure painted on blank canvas: take the silhouette from
# the painting instead of the capture, so no canvas texel reaches the edge
# atlases that are figures painted on blank canvas: the silhouette comes from
# the painting (measured canvas colour), never from the capture, or the blank
# canvas leaks through the soft edge as a white halo.
ALPHA_MODE: dict[str, str] = {
    "checkout": "art",
    "operations": "art",
    "operations_fg": "art",
    "b2b_fg": "art",
    "shopapp": "art",
    "finance": "art",
    "finance_fg": "art",
    "shipping": "art",
    "shipping_fg": "art",
    "b2b": "art",
    "checkout_fg": "art",
}
# per (chapter, image index) override
ALPHA_MODE_IDX: dict[tuple[str, int], str] = {
    ("hero", 1): "art",          # portrait heads: painted cut-out
}

# sidecar .ktx2 backdrops are handled by vn/tools/bake_ktx.py (real Basis)
KTX_SKINS: dict[str, str] = {}

# ui images (plain <img>) -> art file
IMG_SKINS: dict[str, str] = {}


def _buffer(glb: bytes) -> tuple[dict, bytes]:
    clen, _ = struct.unpack("<II", glb[12:20])
    j = json.loads(glb[20 : 20 + clen])
    binlen = struct.unpack("<I", glb[20 + clen : 24 + clen])[0]
    return j, glb[28 + clen : 28 + clen + binlen]


def _bleed(rgb, known, radius: int = 24):
    """Replace unknown colour with the nearest known colour (blur/divide).

    A cut-out atlas is sampled with mipmaps, so whatever colour sits in the
    texels just outside the silhouette gets averaged into the edge -- painted
    white canvas there shows up as a bright halo on screen. Growing the
    figure's own colour outward (premultiplied blur divided by a blurred
    coverage mask) removes the halo without touching the alpha channel.
    """
    from PIL import Image, ImageFilter

    k = known.filter(ImageFilter.GaussianBlur(radius))
    kp = k.point(lambda v: max(v, 1))
    premul = Image.composite(rgb, Image.new("RGB", rgb.size, (0, 0, 0)), known)
    del kp
    import numpy as np

    num = np.asarray(premul.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    den = np.asarray(k, dtype=np.float32)[..., None]
    est = num / np.maximum(den, 1.0)
    est = np.clip(est, 0, 255)
    orig = np.asarray(rgb, dtype=np.float32)
    m = np.asarray(known, dtype=bool)[..., None]
    out = np.where(m, orig, est)
    return Image.fromarray(out.astype("uint8"), "RGB")


def _art_alpha(im, capture_alpha):
    """Silhouette from the painting: pixels far from the canvas colour."""
    import numpy as np
    from PIL import Image, ImageFilter

    rgb = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    # The blank canvas is not always pure white: measure the most common very
    # light colour and treat that as the background reference.
    flat = rgb.reshape(-1, 3)
    light = flat[flat.min(axis=1) > 0.80]
    if len(light) < 1000:
        light = flat[flat.min(axis=1) > 0.65]
    canvas = np.median(light, axis=0) if len(light) else np.ones(3)
    dist = np.abs(rgb - canvas).max(axis=2)
    ramp = np.clip((dist - 0.030) / 0.070, 0.0, 1.0)
    a = (ramp * 255).astype("uint8")
    mask = Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.7))
    # multiply by the capture's own (feathered) alpha rather than clipping to
    # a binary threshold: keeps the anti-aliased hair and hem edges smooth
    ca = np.asarray(capture_alpha, dtype=np.float32) / 255.0
    # the capture alpha is exact inside the figure; normalise the soft rim
    ca = np.clip(ca / 0.85, 0.0, 1.0)
    mask = Image.fromarray(
        (np.asarray(mask, dtype=np.float32) * ca).astype("uint8"), "L"
    ).filter(ImageFilter.GaussianBlur(1.2))
    # bleed the subject's colour under the soft edge so mipmaps cannot pull
    # the blank canvas into the silhouette
    solid = mask.point(lambda v: 255 if v >= 250 else 0)
    rgb = _bleed(im.convert("RGB"), solid)
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    return out


def _clean_rim(im):
    """Erode a cut-out's alpha by a pixel and bleed colour underneath it.

    Hand-assembled cut-out art can carry a light rim *inside* the alpha
    channel (the paint's own light edge).  Shrinking by one texel and filling
    the vacated colour from the subject stops mipmaps turning that rim into a
    white halo.
    """
    from PIL import Image, ImageFilter

    import numpy as np

    a = im.getchannel("A")
    solid = a.point(lambda v: 255 if v >= 250 else 0).filter(ImageFilter.MinFilter(5))
    rgb = _bleed(im.convert("RGB"), solid)
    a = a.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(0.8))
    # every texel that is not fully opaque gets the *subject's* colour: paint
    # tips and wisps keep their alpha but stop carrying the blank canvas
    av = np.asarray(a, dtype=np.float32)
    base = np.asarray(rgb, dtype=np.float32)
    orig = np.asarray(im.convert("RGB"), dtype=np.float32)
    keep = (av >= 249.5)[..., None]
    out = Image.fromarray(np.where(keep, orig, base).astype("uint8"), "RGB").convert("RGBA")
    out.putalpha(a)
    return out


def _fit(
    art: Path, size: tuple[int, int], capture: Path | None = None, alpha: str = "capture"
) -> tuple[bytes, str]:
    """Art -> (encoded bytes, mime) at the captured texture size.

    When the captured atlas carried a cut-out alpha channel and the art is
    opaque, the captured alpha is reused so UV islands keep their exact
    silhouette (masks, holes, feathered edges) and only colour changes.
    """
    from io import BytesIO

    from PIL import Image, ImageFilter

    im = Image.open(art).convert("RGBA")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    if im.getchannel("A").getextrema()[0] < 250:
        im = _clean_rim(im)
    if capture and capture.exists():
        cap = Image.open(capture)
        if "A" in cap.getbands() and cap.getchannel("A").getextrema()[0] < 250:
            a = cap.getchannel("A")
            if a.size != size:
                a = a.resize(size, Image.LANCZOS)
            if im.getchannel("A").getextrema()[0] >= 250:  # art is opaque
                if alpha == "art":
                    # The art is a figure painted on blank canvas.  Take the
                    # silhouette from the painting itself (distance from the
                    # canvas colour, the same ramp that cleared the hero's
                    # hair halo) and intersect it with the captured alpha, so
                    # canvas texels never render as a white fringe.
                    im = _art_alpha(im, a)
                else:
                    # Non-figure cut-out (ragged painted panel): keep the
                    # captured shape and colour-bleed the art into it.
                    im = _bleed(im.convert("RGB"), a.point(lambda v: 255 if v >= 250 else 0))
                    im = im.convert("RGBA")
                    im.putalpha(a)
            else:
                im.putalpha(a)
    buf = BytesIO()
    if im.getchannel("A").getextrema()[0] < 255:
        # cut-out atlas: black the fully transparent texels so PNG compresses
        rgb = im.convert("RGB")
        rgb.paste((0, 0, 0), mask=im.getchannel("A").point(lambda v: 255 if v < 3 else 0))
        rgb = rgb.convert("RGBA")
        rgb.putalpha(im.getchannel("A"))
        rgb.save(buf, "PNG", optimize=True)
        return buf.getvalue(), "image/png"
    im.convert("RGB").save(buf, "JPEG", quality=90, optimize=True, progressive=True)
    return buf.getvalue(), "image/jpeg"


def repack_glb(
    src: Path,
    dst: Path,
    replacements: dict[int, Path],
    capture: Path | None = None,
    alpha: str = "capture",
    chapter: str = "",
) -> None:
    j, BIN = _buffer(src.read_bytes())
    views = j["bufferViews"]
    payload = {
        i: BIN[v.get("byteOffset", 0) : v.get("byteOffset", 0) + v["byteLength"]]
        for i, v in enumerate(views)
    }
    for idx, (art, size) in replacements.items():
        data, mime = _fit(
            art,
            size,
            capture / f"img{idx}.png" if capture else None,
            ALPHA_MODE_IDX.get((chapter, idx), alpha),
        )
        payload[j["images"][idx]["bufferView"]] = data
        j["images"][idx]["mimeType"] = mime
        j["images"][idx].pop("extensions", None)

    for t in j.get("textures", []):
        ext = (t.get("extensions") or {}).pop("KHR_texture_basisu", None)
        if ext:
            t["source"] = ext["source"]
        if not t["extensions"]:
            t.pop("extensions", None)

    for key, drop in (("extensionsUsed", True), ("extensionsRequired", True)):
        if key in j:
            j[key] = [e for e in j[key] if e != "KHR_texture_basisu"]
            if not j[key]:
                j.pop(key)

    out = bytearray()
    for i, v in enumerate(views):
        while len(out) % 4:
            out.append(0)
        v["byteOffset"] = len(out)
        v["byteLength"] = len(payload[i])
        out += payload[i]
    while len(out) % 4:
        out.append(0)
    j["buffers"] = [{"byteLength": len(out)}]

    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(
        b"glTF"
        + struct.pack("<II", 2, total)
        + struct.pack("<II", len(js), 0x4E4F534A)
        + js
        + struct.pack("<II", len(out), 0x004E4942)
        + bytes(out)
    )
    print(f"  glb  {dst.relative_to(ROOT)}  {total / 1e6:.2f} MB")


MODEL_FILES = {
    "hero": "EW26_Hero_251207v3_compressed-optimized.glb",
    "sidekick": "EW26_Sidekick_251208_compressed-optimized.glb",
    "agentic": "EW26_Agentic_Props_251209v5_compressed-optimized.glb",
    "agentic_fg": "Agentic_fg_251209_compressed-optimized.glb",
    "book": "Rigged_Book_CS_Animated_V5_compressed-optimized.glb",
    "online": "EW26_Online_251209v3_compressed-optimized.glb",
    "retail": "Retail_mg_251205v2_compressed-optimized.glb",
    "pos_env": "POS_V53_environment_251209v2_compressed-optimized.glb",
    "pos_hub": "POS_v53_Hub_251208v2_compressed-optimized.glb",
    "marketing": "EW26_Marketing_251209v4_compressed-optimized.glb",
    "checkout": "EW26_Checkout_251209_compressed-optimized.glb",
    "operations": "EW26_Operations_251207_compressed-optimized.glb",
    "globe": "Renaissance_Globe_251209v2-optimized.glb",
    "shopapp": "EW26_ShopApp_251208v3_compressed-optimized.glb",
    "b2b": "EW26_B2B_251205v2_compressed-optimized.glb",
    "finance": "EW26_Finance_251208v2_compressed-optimized.glb",
    "shipping": "EW26_Shipping_251204_compressed-optimized.glb",
    "developer": "EW26_Developer_251207v5_compressed-optimized.glb",
    "operations_fg": "Operations_fg_smaller_251127_compressed-optimized.glb",
    "b2b_fg": "B2B_fg_smaller_251127_compressed-optimizedv2.glb",
    "b2b_fg": "B2B_fg_smaller_251127_compressed-optimizedv2.glb",
    "online_fg": "Online_fg_smaller_251127_compressed-optimized.glb",
    "shipping_fg": "Shipping_fg_smaller_251127_compressed-optimized.glb",
    "marketing_fg": "Marketing_fg_smaller_251127_compressed-optimized.glb",
    "checkout_fg": "Checkout_fg_smaller_251127_compressed-optimized.glb",
    "checkout_bg": "Checkout_bg_diffuse-optimized.glb",
    "shipping_bg": "Shipping_bg_diffuse-optimized.glb",
    "finance_fg": "finance_fg_smaller_251127_compressed-optimized.glb",
}


def bake(name: str) -> None:
    print(f"[{name}]")
    if name in GLB_SKINS:
        src = ROOT / "assets" / "3d" / MODEL_FILES[name]
        reps = {
            i: (ART / f, size)
            for i, (f, size) in GLB_SKINS[name].items()
            if (ART / f).exists()
        }
        if reps:
            cap = ROOT / "vn" / "work" / name
            repack_glb(
                src, OUT / "3d" / src.name, reps,
                cap if cap.is_dir() else None, ALPHA_MODE.get(name, "capture"), name,
            )


BASISU = Path("/tmp/basenc/package/bin/basisu")


def bake_ktx() -> None:
    """Encode the backdrop art as real Basis KTX2.

    The page hands this file to KTX2Loader, so it has to be an actual
    supercompressed texture: a PNG behind a .ktx2 name stalls the preloader on
    a black screen instead of failing loudly.
    """
    import subprocess
    import tempfile

    for rel, art in KTX_SKINS.items():
        a = ART / art
        if not a.exists():
            continue
        dst = OUT / "ktx" / Path(rel).name
        dst.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "in.png"
            png.write_bytes(a.read_bytes())
            subprocess.run(
                [
                    str(BASISU), "-ktx2", "-q", "255", "-mipmap",
                    "-output_file", str(dst), str(png),
                ],
                check=True,
                capture_output=True,
            )
        print(f"  ktx2 {dst.relative_to(ROOT)} ({dst.stat().st_size} B, from {art})")


if __name__ == "__main__":
    names = sys.argv[1:] or list(GLB_SKINS)
    for n in names:
        bake(n)
    if not sys.argv[1:]:
        bake_ktx()
