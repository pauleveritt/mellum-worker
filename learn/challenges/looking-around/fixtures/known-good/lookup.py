import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"


def _rows(folder):
    for path in sorted(folder.glob("*.csv")):
        with path.open() as f:
            for row in csv.DictReader(f):
                yield row["sensor_id"], int(row["reading"])


def reading(sensor_id):
    for region in DATA.iterdir():
        for sid, value in _rows(region):
            if sid == sensor_id:
                return value
    return None


def region_max(region):
    folder = DATA / region
    if not folder.is_dir():
        return None
    return max(_rows(folder), key=lambda r: r[1])
