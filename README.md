# google-workspace-mcp (deploy)

Deployment for the [`workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp)
server (Gmail / Calendar / Docs / Sheets / Slides / Drive) as a **remote,
multi-user** MCP server in **OAuth 2.1** mode for a single Google Workspace
organization.

One Google OAuth "Internal" app serves everyone: each user connects the remote
MCP once, authorises with their corporate Google account, and the server stores
their personal refresh token under the `data/` volume. Users only click
"Authorize"; the app credentials (`client_id`/`client_secret`) identify the app,
not the user.

The whole application is the pinned upstream `workspace-mcp` package baked into
an image; there is no first-party code here. Upgrade by bumping the `==` pin in
`requirements.txt`.

## Prerequisites

### 1. Google Cloud — Internal OAuth app (once)
- Create a project in **your Workspace organization** (so `User type: Internal`
  is available — this removes the CASA/verification and 100-user limits).
- Enable the APIs you need (Drive, Docs, Sheets, Gmail, Calendar, …).
- OAuth consent screen → **User type: Internal**; add the required scopes
  (prefer the narrowest, e.g. `drive.file` over full `drive` when it suffices).
- Create an OAuth client → **Web application**. Add the Authorized redirect URI:
  `https://<WORKSPACE_DOMAIN>/oauth2callback`
- Copy the client id/secret into `.env`.
- Optional: an admin can mark this OAuth client **Trusted** in the Admin Console
  (Security → API controls → App access control) so users skip the consent screen.

### 2. Host — Traefik + DNS (see the org's Traefik guide)
- DNS A-record `<WORKSPACE_DOMAIN>` → the host's public IP.
- Router/NAT: forward **both 80 and 443** (80 is needed for the ACME HTTP-01
  challenge and the http→https redirect).
- Traefik stack must have the `letsEncrypt` resolver and a global http→https
  redirect. Without it, plain http returns 404 and the cert will not issue.
- A shared external Docker network `docker_main_net` must exist (Traefik lives on
  it). `make net` creates it if missing, and `make up` calls it automatically.

## Configure & run
```bash
make env          # create .env from .env.example
# edit .env:
#   GOOGLE_OAUTH_CLIENT_ID=...apps.googleusercontent.com
#   GOOGLE_OAUTH_CLIENT_SECRET=...
#   WORKSPACE_DOMAIN=mcp.example.com
make config       # validate compose + .env substitution
make up           # start (image pulled from ghcr.io, published via Traefik)
make logs         # follow logs
```

`make help` lists all targets (`env`, `config`, `build`, `pull`, `net`, `up`,
`down`, `restart`, `logs`).

## How users connect
Add the remote MCP connector URL in the client (e.g. Claude):
```
https://<WORKSPACE_DOMAIN>/mcp
```
On first use the user is redirected to the Google consent screen (their
corporate account) and then works against their own Drive/Gmail/etc. If the
OAuth client is marked Trusted, no consent screen appears.

## Environment variables
| Variable | Where | Meaning |
|----------|-------|---------|
| `GOOGLE_OAUTH_CLIENT_ID` | `.env` | OAuth client id of the Internal app |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `.env` | OAuth client secret |
| `WORKSPACE_DOMAIN` | `.env` | Public host; drives `WORKSPACE_EXTERNAL_URL` and the Traefik router |
| `MCP_ENABLE_OAUTH21` | compose | `true` — multi-user OAuth 2.1 mode |
| `WORKSPACE_MCP_HOST` / `WORKSPACE_MCP_PORT` | compose | bind `0.0.0.0:8000` |
| `WORKSPACE_MCP_CREDENTIALS_DIR` | compose | per-user token dir under `/app/data` |
| `IMAGE` | `.env` (optional) | Full ghcr.io image path; must equal your GitHub repo path |

## Upgrading the server
Bump the pin in `requirements.txt` (e.g. `workspace-mcp==1.22.0` → newer), push
to `main`; CI smoke-tests, builds and pushes `:latest`, and watchtower redeploys.

## Claude Code & CIMD

Claude Code 2.1.x is CIMD-first: if the server advertised
`client_id_metadata_document_supported`, Claude would send
`client_id=https://claude.ai/oauth/claude-code-client-metadata`, which this server
cannot fetch through Cloudflare (302 to datacenter IPs) → 400 "unregistered client".
So the image applies a build-time patch (`patches/disable_cimd.py`) that disables
CIMD; Claude Code then uses Dynamic Client Registration (DCR), which works here.

- Toggle with `WORKSPACE_MCP_ENABLE_CIMD` (default `false` = CIMD off).
- A `workspace-mcp` version bump may require updating the patch — the build fails
  loudly if the upstream call site changed (see `patches/README.md`).

## Security notes
- The `data/` volume holds every user's Google **refresh token** — a
  high-value target. Restrict host access, back it up carefully, and consider
  disk encryption. For a hardened remote setup, upstream also supports a GCS
  credential backend (`WORKSPACE_MCP_CREDENTIAL_STORE_BACKEND=gcs`).
- Grant the OAuth app the minimum scopes required.
- Never commit `.env`; the committed files contain only placeholders.
- The container runs as root (matching the Traefik/compose convention). For extra
  isolation you may add a non-root `USER` to the `Dockerfile` (keep `/app/data`
  writable) and set `WORKSPACE_MCP_ALLOWED_CLIENT_REDIRECT_URIS` to restrict which
  OAuth client redirect URIs the server accepts.

## Conventions
Follows the org's «Как создавать проект» guide, adapted for a third-party app:
state in `data/`, config from ENV/`.env`, prebuilt ghcr.io image behind Traefik
with watchtower, CI gating the build. See `AGENTS.md`.
