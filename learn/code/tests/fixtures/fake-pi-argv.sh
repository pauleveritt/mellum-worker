#!/bin/sh
[ -d tests ] && { echo "tests visible" >&2; exit 9; }
printf "%s\n" "$@" > argv.txt
