#!/usr/bin/env bash
# The Pi pin (scripts/pi-pin.env) and the one check that notices a different
# pi. Sourced by install.sh and run.sh; install.bat reads the .env itself.

# shellcheck source=pi-pin.env
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/pi-pin.env"

# Prints the version a pi binary reports; nothing when it cannot run.
pi_version() { "${1:-pi}" --version 2>/dev/null | tr -d '[:space:]'; }

# Warn when the pi on PATH is not the pinned one. The course is measured on
# PI_VERSION, and an older pi silently loads this repo's extensions under a
# different API. Never blocks: a learner's newer pi still runs the worker.
warn_unpinned_pi() {
    local have
    have="$(pi_version pi)"
    if [[ -z "$have" ]]; then
        echo "[WARN] no pi on PATH; this course pins $PI_VERSION." >&2
    elif [[ "$have" != "$PI_VERSION" ]]; then
        echo "[WARN] pi $have is not the pinned $PI_VERSION; the course is measured on $PI_VERSION." >&2
    else
        return 0
    fi
    echo "       install it: npm install -g --prefix \"\$HOME/.local\" $PI_PACKAGE@$PI_VERSION" >&2
    return 0
}
