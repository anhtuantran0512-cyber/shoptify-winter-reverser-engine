#!/usr/bin/env python3
"""Point the mirror at the Vietnamese re-skin without editing the capture.

The page asks for /assets/3d/<model>.glb and /assets/textures/<file>.ktx2. We
serve the same paths, but resolve them to vn/assets/* when a re-skinned copy
exists. The capture under assets/ stays untouched, so the overlay can be
switched off by deleting one JSON file.

    python3 vn/tools/overlay.py            # write vn/assets/overlay.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VEND = ROOT / "vn" / "assets"
OUT = VEND / "overlay.json"


def main() -> None:
    mapping: dict[str, str] = {}
    for f in (VEND / "3d").glob("*.glb"):
        mapping[f"/assets/3d/{f.name}"] = f"/vn/assets/3d/{f.name}"
    for f in (VEND / "img").glob("*"):
        mapping[f"/assets/images/{f.name}"] = f"/vn/assets/img/{f.name}"
    for f in (VEND / "ktx").glob("*"):
        # the page asks for the .ktx2; a PNG serves the same role for the shader
        stem = f.stem
        mapping[f"/assets/textures/{stem}.ktx2"] = f"/vn/assets/ktx/{f.name}"
    OUT.write_text(json.dumps(mapping, indent=1, sort_keys=True) + "\n")
    print(f"{OUT.relative_to(ROOT)}  {len(mapping)} overrides")
    for k, v in sorted(mapping.items()):
        print(f"  {k} -> {v}")


if __name__ == "__main__":
    main()
