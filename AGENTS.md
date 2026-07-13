# Agent Instructions — google-workspace-mcp (deploy)

Deployment/ops repo for the third-party `workspace-mcp` server
(taylorwilsdon/google_workspace_mcp), run as a REMOTE multi-user server in
OAuth 2.1 mode for one Google Workspace organization.

There is NO first-party application code here: the whole app is the pinned
`workspace-mcp` PyPI package baked into our image. That is why this repo has no
`src/`, `settings.py`, `tests/` or `templates/` — the usual project skeleton is
adapted to a deploy wrapper.

## Structure
- `requirements.txt` — the single pinned dependency (`workspace-mcp==...`); bump to upgrade.
- `Dockerfile` — slim image that installs the pinned package and runs it in streamable-http mode.
- `docker-compose.yml` — deploy template: ghcr.io image, data volume, Traefik + watchtower labels.
- `.env.example` / `.env` — deploy secrets & domain (`.env` is gitignored).
- `data/` — runtime state: per-user OAuth token store (gitignored, docker volume).
- `.github/workflows/` — CI: smoke-test the pinned package → build → push to ghcr.io.
- `Makefile` — all routine docker-compose actions (`make help`).

## Deploy (short)
```bash
make env          # create .env from the template
# edit .env: GOOGLE_OAUTH_CLIENT_ID / SECRET / WORKSPACE_DOMAIN
make config       # validate compose + .env substitution
make up           # start behind Traefik
make logs         # follow logs
```
Full procedure (Google Cloud Internal OAuth app, Traefik prerequisites, how
users connect) is in `README.md`.

## Conventions
- All mutable state (per-user tokens) lives under `data/`, mounted as a volume.
- All config/secrets come from ENV / `.env` — never hardcoded, never committed.
  The committed compose and `.env.example` contain only placeholders.
- Deploy a prebuilt ghcr.io image via docker-compose behind Traefik; watchtower
  auto-updates. Do not build on prod.
- Upgrade the server by bumping the `==` pin in `requirements.txt` (CI rebuilds).
- Code comments are in English. Routine actions go through `make` targets.
- No `EXPOSE` in the Dockerfile — Traefik publishes the service via compose labels.
- The compose `IMAGE` must match the GitHub repo path (CI pushes
  ghcr.io/<owner>/<repo>); override it in `.env` if the repo is named differently.
  The service needs the shared external network `docker_main_net` (`make net`).
