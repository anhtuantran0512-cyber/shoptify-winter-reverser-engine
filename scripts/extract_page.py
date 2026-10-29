#!/usr/bin/env python3
"""Run a JS extractor inside the live Camofox tab and save the JSON result."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMOFOX = "./.npm-global/bin/camofox"
TAB = sys.argv[1] if len(sys.argv) > 1 else "08c2c8ab-0124-4fa4-a4ec-0e084009a28b"

js = (ROOT / "scripts" / "extract_page.js").read_text()
proc = subprocess.run(
    [CAMOFOX, "--user", "studio", "--format", "json", "eval", js, TAB],
    capture_output=True,
    text=True,
    timeout=180,
)
if proc.returncode != 0:
    print(proc.stderr, file=sys.stderr)
    raise SystemExit(proc.returncode)

payload = json.loads(proc.stdout)
result = payload.get("result", payload)
out = ROOT / "snapshot" / "page-content.json"
out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"wrote {out} ({out.stat().st_size:,} bytes)")
print("sections:", [s["id"] for s in result.get("sections", [])])
