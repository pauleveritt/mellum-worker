#!/bin/sh
# A stand-in worker for the mediated-arm test: it writes a broken add() on the
# first dispatch and a correct one once the corrective prompt (which names the
# failing acceptance checks) arrives, so the gate's re-dispatch loop can be
# driven without a model.
case "$*" in
  *acceptance*) printf 'def add(a, b):\n    return a + b\n' > add.py ;;
  *)            printf 'def add(a, b):\n    return a + b + 1\n' > add.py ;;
esac
