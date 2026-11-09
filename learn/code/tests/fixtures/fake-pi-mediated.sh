#!/bin/sh
[ -d tests ] && { echo "tests visible" >&2; exit 9; }
printf '%s\n' "${MELLUM_MEDIATED_TEST-unset}" >> mediated.txt
printf '%s\n' "${MELLUM_MEDIATED_HANDED-unset}" >> handed.txt
# Settle went green, as the real unit records it (F.8: a run advances only on a green settle).
[ -n "${MELLUM_GATE_LOG-}" ] && printf '{"status": "green"}\n' >> "$MELLUM_GATE_LOG"
exit 0
