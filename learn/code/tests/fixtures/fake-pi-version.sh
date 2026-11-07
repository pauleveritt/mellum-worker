#!/bin/sh
[ "$1" = "--version" ] && { echo "1.4.0"; exit 0; }
exec "$(dirname "$0")/fake-pi.sh" "$@"
