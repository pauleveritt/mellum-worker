FROM ghcr.io/astral-sh/uv:0.11.6 AS uv
FROM node:24.22.1-bookworm-slim
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends procps lsof git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN npm install -g @earendil-works/pi-coding-agent@1.4.0
ENV UV_PYTHON_INSTALL_DIR=/opt/python UV_CACHE_DIR=/opt/cache
RUN uv python install 3.14.2
COPY dependencies /opt/dependencies
RUN uv sync --frozen --project /opt/dependencies --python 3.14.2
RUN uv run --project /opt/dependencies --with ruff==0.16.3 --with complexipy==8.3.0 --with pyrefly==1.2.0 python -c 'import json, importlib.metadata as m; print(json.dumps({n:m.version(n) for n in ("ruff","complexipy","pyrefly","pytest")}))' > /opt/tool-versions.json
COPY instrument /opt/instrument
COPY sources.json identity.mjs entry.py relay.mjs start.sh probe.py pytest_probe.py /opt/
RUN chmod -R a+rX /opt && mkdir -p /attempt && chown 1000:1000 /attempt
USER 1000:1000
ENV HOME=/tmp/home UV_CACHE_DIR=/tmp/uv-cache UV_OFFLINE=1 TERM=dumb
ENTRYPOINT ["/bin/sh", "/opt/start.sh"]
