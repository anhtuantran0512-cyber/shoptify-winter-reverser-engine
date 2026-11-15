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


def _fit(
    art: Path, size: tuple[int, int], capture: Path | None = None
) -> tuple[bytes, str]:
    """Art -> (encoded bytes, mime) at the captured texture size.

    When the captured atlas carried a cut-out alpha channel and the art is
    opaque, the captured alpha is reused so UV islands keep their exact
    silhouette (masks, holes, feathered edges) and only colour changes.
    """
    from io import BytesIO

    from PIL import Image

    im = Image.open(art).convert("RGBA")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    if capture and capture.exists():
        cap = Image.open(capture)
        if "A" in cap.getbands() and cap.getchannel("A").getextrema()[0] < 250:
            if im.getchannel("A").getextrema()[0] >= 250:  # art is fully opaque
                a = cap.getchannel("A")
                im.putalpha(a if a.size == size else a.resize(size, Image.LANCZOS))
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
    src: Path, dst: Path, replacements: dict[int, Path], capture: Path | None = None
) -> None:
    j, BIN = _buffer(src.read_bytes())
    views = j["bufferViews"]
    payload = {
        i: BIN[v.get("byteOffset", 0) : v.get("byteOffset", 0) + v["byteLength"]]
        for i, v in enumerate(views)
    }
    for idx, (art, size) in replacements.items():
        data, mime = _fit(art, size, capture / f"img{idx}.png" if capture else None)
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
            repack_glb(src, OUT / "3d" / src.name, reps, cap if cap.is_dir() else None)


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
