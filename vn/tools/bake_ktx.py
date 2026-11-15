#!/usr/bin/env python3
"""Re-encode the painted chapter backdrops as real Basis KTX2.

The page loads each chapter plate as `/assets/textures/<name>.ktx2` and hands
it straight to KTX2Loader, so the replacement has to be genuine Basis data at
the captured resolution -- a PNG behind the same name stalls the loader.

Paint into `vn/art/ktx/<name>_vn.png` at (any multiple of) the captured size;
run this to write `vn/assets/ktx/<name>.ktx2`.

    python3 vn/tools/bake_ktx.py          # everything painted so far
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "assets" / "textures"
ART = ROOT / "vn" / "art" / "ktx"
OUT = ROOT / "vn" / "assets" / "ktx"

BASISU = Path("/tmp/basenc/package/bin/basisu")

# one painted plate may stand in for several captured names (the build requests
# a content-hashed copy of the same sky in one place)
ALIASES: dict[str, list[str]] = {
    "Online_bg-brighter_251201v2-optimized":
        ["Online_bg-brighter_251201v2-optimized_5cdbdf82-dff0-40c9-8c76-111f92afc5ee"],
}


def encode(art: Path, capture: Path, dst: Path) -> None:
    # the captured plate is Basis, so take its size from the decoded atlas
    size = Image.open(ROOT / "vn" / "work" / "ktx" / f"{capture.stem}.png").size
    im = Image.open(art).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "in.png"
        im.save(png, "PNG")
        subprocess.run(
            [str(BASISU), "-ktx2", "-q", "255", "-mipmap",
             "-output_file", str(dst), str(png)],
            check=True, capture_output=True,
        )
    print(f"  ktx2 {dst.relative_to(ROOT)}  {dst.stat().st_size / 1e6:.2f} MB"
          f"  ({size[0]}x{size[1]}, from {art.name})")


def main(only: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for art in sorted(ART.glob("*_vn.png")):
        name = art.stem[: -len("_vn")]
        if only and name not in only:
            continue
        capture = CAP / f"{name}.ktx2"
        if not capture.exists():
            print(f"skip {art.name}: no captured {capture.name}")
            continue
        for target in [name, *ALIASES.get(name, [])]:
            encode(art, CAP / f"{name}.ktx2", OUT / f"{target}.ktx2")


if __name__ == "__main__":
    main(sys.argv[1:])
