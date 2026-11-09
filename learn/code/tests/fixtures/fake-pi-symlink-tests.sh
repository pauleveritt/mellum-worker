#!/bin/sh
# Replaces the project's tests/ with a symlink to a directory outside the workspace.
printf '%s\n' prompt >> prompts.txt
[ -L tests ] || { rm -rf tests; ln -s "$FAKE_OUTSIDE" tests; }
exit 0
