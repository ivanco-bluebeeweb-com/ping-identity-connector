"""Ping Identity Connector extension declaration.

PingOne is Ping Identity's cloud IDaaS platform: SSO, MFA, directory and
lifecycle management, exposed through the PingOne Platform API
(api.pingone.{region}/v1/environments/{envId}/*).
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "ping-identity-connector",
    version="0.1.0",
    display_name="Ping Identity",
    description=(
        "Connect your own PingOne environment (Worker Application) to manage "
        "Users, Groups, Populations, Applications, Sign-On Policies and "
        "Identity Providers, plus review the Activity log for security "
        "visibility."
    ),
    icon="icon.svg",
    capabilities=["ping:read", "ping:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="ping_identity",
    description=(
        "Ping Identity Connector — manage Users, Groups, Populations, "
        "Applications, Sign-On Policies, Identity Providers, and the "
        "Activity log for a PingOne environment."
    ),
)

ext.secret(
    "ping_connections",
    "JSON list of connected PingOne environments and encrypted Worker App credentials. Managed only through connect_ping and disconnect_ping.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one PingOne environment connection is saved."""
    import json

    raw = await ctx.secrets.get("ping_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    return {
        "healthy": True,
        "connected": len(connections) > 0,
        "connection_count": len(connections),
    }
