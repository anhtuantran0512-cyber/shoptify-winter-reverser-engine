# Shoptify Winter '26 Study Vault

Local front-end architecture study archive and interactive reader for public editorial web layouts.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Pipeline](#pipeline)
- [Scope](#scope)

## Overview

This repository captures public front-end assets, layout metrics, motion timelines, and design-system documentation into an offline study archive with a local reader interface.

## Prerequisites

- Python 3.10+
- Pillow (`pip install pillow`)

## Usage

```bash
git clone https://github.com/broamstuck-cybr/shoptify-winter-reverser-engine.git
cd shoptify-winter-reverser-engine

# Serve the captured mirror on its expected route
python3 scripts/serve_mirror.py 4174

# Serve the reading interface
python3 -m http.server 4173
```

Open `http://127.0.0.1:4174/editions/winter2026` for the mirror, or `http://127.0.0.1:4173/site/` for the archive reader.

## Project Structure

```text
.
├── assets/       Captured bundles, stylesheets, fonts, media, and manifest
├── docs/         Architecture teardown, design tokens, motion, and asset ledger
├── mirror/       Local runnable mirror using captured bundles
├── scripts/      Capture, inventory, build, and visual comparison scripts
├── site/         Static archive browser UI
├── snapshot/     DOM inventory and reference screenshots
├── src/          Distilled design tokens and reusable components
└── vendor/       Runtime WASM/transcoder dependencies
```

## Pipeline

```bash
python3 scripts/build_inventory.py
python3 scripts/capture_assets.py snapshot/inventory.json assets
python3 scripts/build_site_data.py
python3 scripts/build_docs.py
```

## Scope

- Educational front-end architecture and motion study only.
- Original third-party imagery, copy, fonts, and bundles remain the property of their respective owners; do not redistribute them as a commercial template.
