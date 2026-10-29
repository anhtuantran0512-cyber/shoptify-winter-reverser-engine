#!/usr/bin/env python3
"""Inspect the mirror in Chromium: console, page errors, failed requests."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:4174/editions/winter2026"

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium",
        args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("console", lambda m: print(f"[console.{m.type}] {m.text[:400]}"))
    page.on("pageerror", lambda e: print(f"[pageerror] {e}"))
    page.on("requestfailed", lambda r: print(f"[failed] {r.url[:160]} :: {r.failure}"))
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(12000)
    info = page.evaluate(
        """() => ({
          url: location.href,
          title: document.title,
          body: !!document.body,
          h: document.body ? document.body.scrollHeight : 0,
          sections: document.querySelectorAll('[data-section-id]').length,
          canvases: document.querySelectorAll('canvas').length,
          imgs: document.images.length,
          broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0).length,
          text: document.body ? document.body.innerText.slice(0, 200) : '',
        })"""
    )
    print("INFO", info)
    page.screenshot(path="/tmp/mirror-qa/chromium-hero.png")
    browser.close()
