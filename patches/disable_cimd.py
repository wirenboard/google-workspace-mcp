#!/usr/bin/env python3
"""Build-time vendor patch for the pip-installed workspace-mcp package.

Disables FastMCP's CIMD (Client ID Metadata Document) support so Claude Code
falls back to Dynamic Client Registration (DCR). Claude Code 2.1.x is CIMD-first
and sends client_id=https://claude.ai/oauth/claude-code-client-metadata; this
server cannot fetch that document through Cloudflare (302 to datacenter IPs), so
CIMD auth fails with a 400 "unregistered client". DCR works here, but the client
only uses it when the server does NOT advertise CIMD. Upstream FastMCP gates the
`client_id_metadata_document_supported` metadata flag on its CIMD manager, which
exists only when GoogleProvider(enable_cimd=True); so this patch injects
`enable_cimd=<env>` into the GoogleProvider(...) call in core/server.py.

Runtime toggle: WORKSPACE_MCP_ENABLE_CIMD (default false = CIMD disabled).

Self-verifying: if a workspace-mcp version bump moves the call site, the anchor
no longer matches and the build FAILS loudly instead of shipping an unpatched image.
"""
import os
import sys
import sysconfig

TARGET = os.path.join(sysconfig.get_paths()["purelib"], "core", "server.py")
KWARG = "allowed_client_redirect_uris=allowed_client_redirect_uris,"
MARKER = "WB vendor patch: disable CIMD"  # unique sentinel from our injected comment


def main() -> None:
    with open(TARGET, encoding="utf-8") as f:
        lines = f.readlines()
    text = "".join(lines)

    if MARKER in text:
        print(f"[patch-cimd] already patched: {TARGET}")
        return

    # Fail loudly (do NOT silently skip) if upstream introduced its own enable_cimd
    # handling: we must then re-evaluate this patch instead of shipping unpatched.
    if "enable_cimd=" in text:
        sys.exit(
            f"[patch-cimd] FAILED: {TARGET} already sets 'enable_cimd=' without our "
            f"marker. workspace-mcp added its own CIMD toggle - review this patch."
        )

    hits = [i for i, line in enumerate(lines) if line.strip() == KWARG]
    if len(hits) != 1:
        sys.exit(
            f"[patch-cimd] FAILED: expected exactly one '{KWARG}' line in "
            f"{TARGET}, found {len(hits)}. workspace-mcp changed - update this patch."
        )

    i = hits[0]
    indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
    injection = (
        f"{indent}# WB vendor patch: disable CIMD so Claude Code uses DCR (its claude.ai\n"
        f"{indent}# CIMD URL is unfetchable through Cloudflare). Toggle: WORKSPACE_MCP_ENABLE_CIMD.\n"
        f'{indent}enable_cimd=(os.getenv("WORKSPACE_MCP_ENABLE_CIMD", "false").strip().lower() in ("1", "true", "yes", "on")),\n'
    )
    lines.insert(i + 1, injection)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[patch-cimd] patched {TARGET}: CIMD disabled by default (env WORKSPACE_MCP_ENABLE_CIMD)")


if __name__ == "__main__":
    main()
