#!/bin/sh
# A stand-in Pi that records whatever arrives on its stdin. Pi run with -p appends piped stdin to
# its prompt, so a session must never inherit the caller's stdin.
cat > stdin.txt
printf 'def add(a, b):\n    return a + b\n' > add.py
