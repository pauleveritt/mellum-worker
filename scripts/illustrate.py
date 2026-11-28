# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow==11.3.0"]
# ///
"""Generate the Lessons illustrations from learn/assets/illustrations/prompts.toml.

Each entry is the shared style plus its own subject and seed, sent to an image
service with the lab server's API (POST {prompt, width, height, seed,
negative_prompt} -> {"image": base64 PNG}). Images are written as WebP beside
the prompts file. Missing images only, unless --force names them.

    uv run scripts/illustrate.py                 # every missing image
    uv run scripts/illustrate.py --force tier-easy baseline
    ILLUSTRATE_URL=http://host:port/api/generate uv run scripts/illustrate.py
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import tomllib
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "learn" / "assets" / "illustrations"
DEFAULT_URL = "http://192.168.88.99:11436/api/generate"


def load() -> tuple[dict, dict[str, dict]]:
    data = tomllib.loads((FOLDER / "prompts.toml").read_text(encoding="utf-8"))
    shared = {k: v for k, v in data.items() if not isinstance(v, dict)}
    return shared, {k: v for k, v in data.items() if isinstance(v, dict)}


def request(shared: dict, entry: dict) -> dict:
    # An entry may override the shared style or negative prompt, e.g. to allow
    # one short word in a speech bubble where the shared style forbids text.
    return {
        "prompt": f"{entry['subject']}, {entry.get('style', shared['style'])}",
        "negative_prompt": entry.get("negative", shared.get("negative")),
        "width": entry.get("width", shared["width"]),
        "height": entry.get("height", shared["height"]),
        "seed": entry["seed"],
    }


def generate(url: str, body: dict, timeout: float = 600) -> bytes:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return base64.b64decode(json.load(response)["image"])


def save(png: bytes, path: Path, width: int) -> None:
    image = Image.open(io.BytesIO(png)).convert("RGB")
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    image.save(path, "WEBP", quality=82, method=6)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", nargs="*", default=None, metavar="NAME",
                        help="regenerate these images (all of them when no name is given)")
    parser.add_argument("--url", default=os.environ.get("ILLUSTRATE_URL", DEFAULT_URL))
    args = parser.parse_args(argv)
    shared, entries = load()
    forced = set(entries) if args.force == [] else set(args.force or ())
    unknown = forced - set(entries)
    if unknown:
        parser.error(f"no prompt for {', '.join(sorted(unknown))}")
    todo = [n for n in entries if n in forced or not (FOLDER / f"{n}.webp").exists()]
    for i, name in enumerate(todo, 1):
        started = time.monotonic()
        print(f"[{i}/{len(todo)}] {name} …", end=" ", flush=True)
        png = generate(args.url, request(shared, entries[name]))
        save(png, FOLDER / f"{name}.webp", shared["width"])
        print(f"{time.monotonic() - started:.0f} s", flush=True)
    print("nothing to do" if not todo else f"wrote {len(todo)} image(s) to {FOLDER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
