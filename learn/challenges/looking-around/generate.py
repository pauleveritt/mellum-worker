"""Writes base/data/ for the looking-around challenge: 8 regions, 25 sites each, one CSV per site
with 60 sensors (12,000 in all), so no single look shows the data and the task needs looking
around: listing folders, reading files, searching. Readings are unique within a region, so each
region has one highest sensor. Deterministic: run it again and every file is identical."""

import random
import shutil
from pathlib import Path

REGIONS = ["north", "south", "east", "west", "central", "coast", "valley", "ridge"]
rng = random.Random(4711)
data = Path(__file__).parent / "base" / "data"
shutil.rmtree(data, ignore_errors=True)
ids = [f"S-{n:05d}" for n in range(1, 12001)]
rng.shuffle(ids)
for r, region in enumerate(REGIONS):
    readings = rng.sample(range(100, 10000), 1500)
    for s in range(25):
        rows = ["sensor_id,reading"]
        for k in range(60):
            i = r * 1500 + s * 60 + k
            rows.append(f"{ids[i]},{readings[s * 60 + k]}")
        site = data / region / f"site-{s + 1:02d}.csv"
        site.parent.mkdir(parents=True, exist_ok=True)
        site.write_text("\n".join(rows) + "\n")
print(f"wrote {data} (8 regions, 200 sites, 12,000 sensors)")
