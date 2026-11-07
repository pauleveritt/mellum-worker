# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Small PNG copies of the lesson illustrations for the /lesson tutor in Pi: Kitty-protocol
terminals draw PNG only. Writes learn/assets/illustrations/terminal/<name>.png at 640 px wide.

    uv run scripts/terminal-pictures.py
"""
from pathlib import Path

from PIL import Image

SRC = Path(__file__).resolve().parents[1] / "learn" / "assets" / "illustrations"
OUT = SRC / "terminal"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    made = 0
    for webp in sorted(SRC.glob("*.webp")):
        png = OUT / f"{webp.stem}.png"
        if png.exists() and png.stat().st_mtime >= webp.stat().st_mtime:
            continue
        with Image.open(webp) as im:
            im = im.convert("RGB")
            im.thumbnail((640, 320))
            # Flat vector art: a 256-colour palette keeps each copy small.
            im.quantize(256).save(png, optimize=True)
        made += 1
    print(f"wrote {made} picture(s) to {OUT}")


if __name__ == "__main__":
    main()
