#!/bin/sh
# Records the environment a session runs with (LC.39 native sessions).
printf 'HOME=%s\nUV_CACHE_DIR=%s\nFROM_DRIVER=%s\n' "${HOME-}" "${UV_CACHE_DIR-}" "${FROM_DRIVER-}" > env.txt
