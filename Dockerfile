FROM python:3.12-slim

WORKDIR /app

# curl is required by the compose healthcheck (not shipped in the slim image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# The whole application is the pinned upstream package. Install it as its own
# layer so it is cached and only rebuilt when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime state directory: the per-user OAuth token store lives under data/.
RUN mkdir -p data

# No first-party source to copy: the app is the `workspace-mcp` console script.
# No EXPOSE: the service is published by Traefik via docker-compose labels.

# Remote multi-user mode uses the streamable-http transport. Host, port, OAuth
# credentials and the token directory all come from the environment (compose).
CMD ["workspace-mcp", "--transport", "streamable-http"]
