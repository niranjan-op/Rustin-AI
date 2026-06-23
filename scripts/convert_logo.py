"""
convert_logo.py
Converts public/.jpeg into all required logo formats and replaces existing logo files.
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SOURCE = PUBLIC / "image.png"

if not SOURCE.exists():
    sys.exit(f"ERROR: Source image not found at {SOURCE}")

print(f"Source image : {SOURCE}  ({SOURCE.stat().st_size // 1024} KB)")

# ── Open and prepare the source image ─────────────────────────────────────────
img = Image.open(SOURCE)
print(f"Mode         : {img.mode}  |  Size: {img.size}")

# Convert to RGBA for full transparency support (needed for ICO)
img_rgba = img.convert("RGBA")

# ── Output targets ─────────────────────────────────────────────────────────────
# (path, format, extra_kwargs)
TARGETS = [
    # Main logo files used by Chainlit
    (PUBLIC / "logo_dark.png",  "PNG",  {}),
    (PUBLIC / "logo_light.png", "PNG",  {}),
    (PUBLIC / "favicon.png",    "PNG",  {}),
    # ICO files — multi-size for best rendering
    (PUBLIC / "logo_dark.ico",  "ICO",  {"sizes": [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]}),
    (PUBLIC / "favicon.ico",    "ICO",  {"sizes": [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]}),
]

for path, fmt, kwargs in TARGETS:
    try:
        if fmt == "PNG":
            img_rgba.save(path, format="PNG", **kwargs)
        elif fmt == "ICO":
            img_rgba.save(path, format="ICO", **kwargs)
        size_kb = path.stat().st_size // 1024
        print(f"  OK  {path.name:<20}  [{fmt}]  {size_kb} KB")
    except Exception as e:
        print(f"  FAIL  {path.name:<20}  ERROR: {e}")

print("\nAll logo files replaced successfully!")
print("Restart the app to see the changes.")
