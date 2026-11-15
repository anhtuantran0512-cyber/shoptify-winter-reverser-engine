#!/usr/bin/env python3
"""Extract + decode every embedded texture of the captured chapter models.

Writes vn/work/<chapter>/img<i>.png ready to paint.  The basisu CLI ships the
transcoder, so this is the only tool needed for the round trip.
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASISU = Path("/tmp/basenc/package/bin/basisu")
GLB = ROOT / "assets" / "3d"
WORK = ROOT / "vn" / "work"

CHAPTERS = {
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
    # foreground/bg models the chapters also load (different files from the
    # *_fg / *_bg texture plates above)
    "checkout_bg": "Checkout_bg_diffuse-optimized.glb",
    "checkout_fg": "Checkout_fg_smaller_251127_compressed-optimized.glb",
    "developer_bg": "Developer_bg_diffuse-optimized.glb",
    "finance_bg": "Finance_bg_diffuse-optimized.glb",
    "marketing_fg": "Marketing_fg_smaller_251127_compressed-optimized.glb",
    "online_fg": "Online_fg_smaller_251127_compressed-optimized.glb",
    "operations_bg": "Operations_bg_diffuse-optimized.glb",
    "operations_fg": "Operations_fg_smaller_251127_compressed-optimized.glb",
    "shipping_bg": "Shipping_bg_diffuse-optimized.glb",
    "shipping_fg": "Shipping_fg_smaller_251127_compressed-optimized.glb",
    "shopapp_bg": "ShopApp_bg_diffuse-optimized.glb",
    "finance_fg": "finance_fg_smaller_251127_compressed-optimized.glb",
    "b2b_fg": "B2B_fg_smaller_251127_compressed-optimizedv2.glb",
    "key": "key.glb",
}


def images_of(glb: Path):
    b = glb.read_bytes()
    clen, _ = struct.unpack("<II", b[12:20])
    j = json.loads(b[20:20 + clen])
    binlen = struct.unpack("<I", b[20 + clen:24 + clen])[0]
    return j, b[28 + clen:28 + clen + binlen]


def main(only: list[str]) -> None:
    todo = {k: v for k, v in CHAPTERS.items() if not only or k in only}
    for name, fname in todo.items():
        p = GLB / fname
        if not p.exists():
            print(f"skip {name}: {fname} missing")
            continue
        j, BIN = images_of(p)
        out = WORK / name
        out.mkdir(parents=True, exist_ok=True)
        for i, im in enumerate(j.get("images", [])):
            bv = j["bufferViews"][im["bufferView"]]
            o = bv.get("byteOffset", 0)
            ktx = out / f"img{i}.ktx2"
            ktx.write_bytes(BIN[o:o + bv["byteLength"]])
            subprocess.run(
                [str(BASISU), "-unpack", "-ktx2", str(ktx)],
                cwd=out, capture_output=True, check=False,
            )
            cands = sorted(out.glob(f"img{i}_unpacked_rgba_*"))
            if not cands:
                cands = sorted(out.glob(f"img{i}_unpacked_rgb_*"))
            if cands:
                target = out / f"img{i}.png"
                target.write_bytes(cands[0].read_bytes())
                for c in out.glob(f"img{i}_unpacked_*"):
                    c.unlink()
                ktx.unlink(missing_ok=True)
                from PIL import Image

                w, h = Image.open(target).size
                print(f"{name:12s} img{i}  {w}x{h}  {im.get('name','')}")
            else:
                print(f"{name:12s} img{i}  DECODE FAILED")


if __name__ == "__main__":
    main(sys.argv[1:])
