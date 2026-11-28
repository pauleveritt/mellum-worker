from __future__ import annotations

import json
import sys

from detect_installer import detect_installer


def main() -> None:
    package_name = sys.argv[1] if len(sys.argv) > 1 else "detect-installer"
    info = detect_installer(package_name)

    if info is None:
        print(f"Could not detect installer for {package_name}")
        sys.exit(1)

    json.dump(
        {
            "installer": info.installer.value,
            "upgrade_cmd": info.upgrade_cmd,
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
