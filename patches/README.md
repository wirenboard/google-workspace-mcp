# patches/

Build-time vendor patches applied to the pip-installed `workspace-mcp` package
inside the Docker image (see the `Dockerfile`). These are NOT upstream forks —
each is a minimal, self-verifying edit that fails the build if the upstream code moved.

## disable_cimd.py
Disables FastMCP CIMD so Claude Code falls back to DCR. Claude Code 2.1.x is
CIMD-first and sends `client_id=https://claude.ai/oauth/claude-code-client-metadata`;
this server cannot fetch that document through Cloudflare (302 to datacenter IPs),
so CIMD auth fails with a 400 "unregistered client". DCR works, but the client only
uses it when the server does not advertise CIMD. The patch injects
`enable_cimd=<WORKSPACE_MCP_ENABLE_CIMD>` (default false) into the `GoogleProvider(...)`
call in `core/server.py`.

Runtime toggle: `WORKSPACE_MCP_ENABLE_CIMD=true` re-enables CIMD.

### Updating on a workspace-mcp / fastmcp version bump
The patch anchors on the `allowed_client_redirect_uris=allowed_client_redirect_uris,`
kwarg line of the `GoogleProvider(...)` call. If a new workspace-mcp release changes
that call, `disable_cimd.py` exits non-zero and the CI build fails — update the anchor
and re-verify that FastMCP still gates the CIMD metadata flag on `enable_cimd`.

`fastmcp` is pinned in `requirements.txt` because the injected kwarg depends on the
`GoogleProvider(enable_cimd=...)` signature; when bumping either pin, re-check that
signature still exists. The patch also fails the build if upstream starts setting
`enable_cimd=` itself (so we adopt their toggle instead of double-patching).
