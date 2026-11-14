#!/usr/bin/env python3
"""Pull the embedded images out of a captured .glb as KTX2 files.

    python3 vn/tools/extract.py romans assets/3d/EW26_Sidekick_251208_compressed-optimized.glb
"""
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
name, glb = sys.argv[1], Path(sys.argv[2])
b = glb.read_bytes()
clen, _ = struct.unpack('<II', b[12:20])
j = json.loads(b[20:20 + clen])
binlen = struct.unpack('<I', b[20 + clen:24 + clen])[0]
BIN = b[28 + clen:28 + clen + binlen]
out = ROOT / "vn" / "work" / name
out.mkdir(parents=True, exist_ok=True)
for i, im in enumerate(j.get('images', [])):
    bv = j['bufferViews'][im['bufferView']]
    o = bv.get('byteOffset', 0)
    f = out / f"img{i}.ktx2"
    f.write_bytes(BIN[o:o + bv['byteLength']])
    print(f, im.get('name'), im.get('mimeType'), bv['byteLength'])
