"""Archive a phase's raw run files (trace, stdout, diff) as one deterministic tarball.

Raw files are never committed. Each phase directory gets `<phase>.tar.gz`
holding them at their original relative paths, attached to a `research-*`
release. Same inputs give the same bytes, so the SHA-256 in
`evals/PROVENANCE.md` can be checked after a rebuild.

    uv run python -m ladder.archive_raw --out DIR --tag TAG PHASE_DIR...
"""

import argparse
import gzip
import hashlib
import tarfile
from pathlib import Path

RAW_NAMES = ("trace.jsonl", "stdout.txt", "diff.patch")
RELEASE_URL = "https://github.com/andrevanzuydam/mellum-worker/releases/download"


def _normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o644
    return info


def archive_phase(phase_dir: Path, out_dir: Path) -> Path | None:
    """Write `<phase>.tar.gz` into out_dir; None (and no file) when no raw files exist."""
    phase_dir = Path(phase_dir)
    files = sorted(
        p for p in phase_dir.rglob("*") if p.is_file() and p.name in RAW_NAMES
    )
    if not files:
        return None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{phase_dir.name}.tar.gz"
    with out.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tar:
                for path in files:
                    arcname = f"{phase_dir.name}/{path.relative_to(phase_dir).as_posix()}"
                    tar.add(path, arcname=arcname, filter=_normalize)
    return out


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("phase_dirs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for phase_dir in args.phase_dirs:
        tarball = archive_phase(phase_dir, args.out)
        if tarball is not None:
            print(f"{phase_dir.resolve().name} {sha256(tarball)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
