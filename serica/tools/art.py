"""Serica art pipeline: raw generations -> sized WebP.

usage: python3 serica/tools/art.py
Chapters 10–12 currently use graded derivatives of nearby paintings while their
own artwork is pending; the file names are already wired in js/content.js.
"""
from PIL import Image, ImageOps, ImageEnhance
import glob, os

RAW = "serica/img/raw"
OUT = "serica/img/art"
os.makedirs(OUT, exist_ok=True)


def save(im, name, width=1600, q=82):
    h = round(width * im.height / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    path = os.path.join(OUT, name)
    im.save(path, "WEBP", quality=q, method=6)
    print(f"{name:22} {im.size} {os.path.getsize(path)//1024}KB")


def duotone(im, dark, light):
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.12)
    return ImageOps.colorize(g, dark, light)


for p in sorted(glob.glob(f"{RAW}/*.jpg")):
    name = os.path.basename(p).replace(".jpg", ".webp")
    save(Image.open(p).convert("RGB"), name)

# --- stand-ins (regenerated when the image budget allows) -------------------
retail = Image.open(f"{RAW}/04-retail.jpg").convert("RGB")
save(ImageOps.mirror(retail), "10-finance.webp")

checkout = Image.open(f"{RAW}/06-checkout.jpg").convert("RGB")
dawn = ImageEnhance.Color(ImageOps.mirror(checkout)).enhance(0.92)
dawn = ImageEnhance.Brightness(dawn).enhance(1.04)
save(dawn, "11-shipping.webp")

b2b = Image.open(f"{RAW}/09-b2b.jpg").convert("RGB")
sketch = duotone(b2b, "#3a2a1c", "#efe6d2")
save(ImageEnhance.Sharpness(sketch).enhance(1.3), "12-developer.webp")
