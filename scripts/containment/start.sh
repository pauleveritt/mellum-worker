#!/bin/sh
set -eu
mkdir -p /tmp/home
cp -a /opt/cache /tmp/uv-cache
touch /tmp/runtime-ready
exec "$@"
