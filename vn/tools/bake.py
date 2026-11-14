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
}

# sidecar .ktx2 backdrops -> art file (written as .png at the same size)
KTX_SKINS: dict[str, str] = {
    "textures/Hero-bg-hires-optimized.ktx2": "hero_bg_vn.png",
}

# ui images (plain <img>) -> art file
IMG_SKINS: dict[str, str] = {}


def _buffer(glb: bytes) -> tuple[dict, bytes]:
    clen, _ = struct.unpack("<II", glb[12:20])
    j = json.loads(glb[20 : 20 + clen])
    binlen = struct.unpack("<I", glb[20 + clen : 24 + clen])[0]
    return j, glb[28 + clen : 28 + clen + binlen]


def _fit(art: Path, size: tuple[int, int]) -> bytes:
    """Art -> PNG bytes at the captured texture size."""
    from io import BytesIO

    from PIL import Image

    im = Image.open(art).convert("RGBA")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def repack_glb(src: Path, dst: Path, replacements: dict[int, Path]) -> None:
    j, BIN = _buffer(src.read_bytes())
    views = j["bufferViews"]
    payload = {
        i: BIN[v.get("byteOffset", 0) : v.get("byteOffset", 0) + v["byteLength"]]
        for i, v in enumerate(views)
    }
    for idx, (art, size) in replacements.items():
        png = _fit(art, size)
        payload[j["images"][idx]["bufferView"]] = png
        j["images"][idx]["mimeType"] = "image/png"
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
            repack_glb(src, OUT / "3d" / src.name, reps)


def bake_ktx() -> None:
    for rel, art in KTX_SKINS.items():
        p, a = ROOT / "assets" / rel, ART / art
        if a.exists():
            dst = OUT / "ktx" / Path(rel).name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(a.read_bytes())
            print(f"  ktx2 {dst.relative_to(ROOT)} (from {art})")


if __name__ == "__main__":
    names = sys.argv[1:] or list(GLB_SKINS)
    for n in names:
        bake(n)
    if not sys.argv[1:]:
        bake_ktx()
