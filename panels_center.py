"""Ping Identity Connector -- center panels for Users/Groups/Populations/Applications/Policies/IdPs/Activity."""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _table_or_empty(rows, columns, empty_message, empty_icon):
    if not rows:
        return ui.Empty(message=empty_message, icon=empty_icon)
    return ui.DataTable(rows=rows, columns=columns)


@ext.panel("ping_users", slot="center", title="Users", center_overlay=True)
async def ping_users(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Users")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/users", params={"limit": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load users: {exc}")
    items = (data or {}).get("_embedded", {}).get("users", [])
    rows = []
    for u in items:
        name = u.get("name", {}) or {}
        rows.append({
            "name": (name.get("given", "") + " " + name.get("family", "")).strip(),
            "username": u.get("username", ""),
            "email": u.get("email", ""),
            "enabled": "Yes" if u.get("enabled", True) else "No",
        })
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="username", label="Username"),
        ui.DataColumn(key="email", label="Email"),
        ui.DataColumn(key="enabled", label="Enabled"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Users", level=2),
        _table_or_empty(rows, columns, "No users found", "Users"),
    ])


@ext.panel("ping_groups", slot="center", title="Groups", center_overlay=True)
async def ping_groups(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="UsersRound")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/groups")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load groups: {exc}")
    items = (data or {}).get("_embedded", {}).get("groups", [])
    rows = [{"name": g.get("name", ""), "description": g.get("description", "")} for g in items]
    columns = [ui.DataColumn(key="name", label="Name"), ui.DataColumn(key="description", label="Description")]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Groups", level=2),
        _table_or_empty(rows, columns, "No groups found", "UsersRound"),
    ])


@ext.panel("ping_populations", slot="center", title="Populations", center_overlay=True)
async def ping_populations(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Layers")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/populations")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load populations: {exc}")
    items = (data or {}).get("_embedded", {}).get("populations", [])
    rows = [{"name": p.get("name", ""), "userCount": str(p.get("userCount", 0)), "description": p.get("description", "")} for p in items]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="userCount", label="Users"),
        ui.DataColumn(key="description", label="Description"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Populations", level=2),
        _table_or_empty(rows, columns, "No populations found", "Layers"),
    ])


@ext.panel("ping_applications", slot="center", title="Applications", center_overlay=True)
async def ping_applications(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="AppWindow")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/applications")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load applications: {exc}")
    items = (data or {}).get("_embedded", {}).get("applications", [])
    rows = [{"name": a.get("name", ""), "type": a.get("type", ""), "enabled": "Yes" if a.get("enabled", True) else "No"} for a in items]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="type", label="Type"),
        ui.DataColumn(key="enabled", label="Enabled"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Applications", level=2),
        _table_or_empty(rows, columns, "No applications found", "AppWindow"),
    ])


@ext.panel("ping_policies", slot="center", title="Sign-On Policies", center_overlay=True)
async def ping_policies(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/signOnPolicies")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load sign-on policies: {exc}")
    items = (data or {}).get("_embedded", {}).get("signOnPolicies", [])
    rows = [{"name": p.get("name", ""), "default": "Yes" if p.get("default") else "No"} for p in items]
    columns = [ui.DataColumn(key="name", label="Name"), ui.DataColumn(key="default", label="Default")]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Sign-On Policies", level=2),
        _table_or_empty(rows, columns, "No sign-on policies found", "ShieldCheck"),
    ])


@ext.panel("ping_idps", slot="center", title="Identity Providers", center_overlay=True)
async def ping_idps(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Share2")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/identityProviders")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load identity providers: {exc}")
    items = (data or {}).get("_embedded", {}).get("identityProviders", [])
    rows = [{"name": i.get("name", ""), "type": i.get("type", ""), "enabled": "Yes" if i.get("enabled", True) else "No"} for i in items]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="type", label="Type"),
        ui.DataColumn(key="enabled", label="Enabled"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Identity Providers", level=2),
        _table_or_empty(rows, columns, "No identity providers found", "Share2"),
    ])


@ext.panel("ping_activity", slot="center", title="Activity Log", center_overlay=True)
async def ping_activity(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ScrollText")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/activities", params={"limit": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load activity log: {exc}")
    items = (data or {}).get("_embedded", {}).get("activities", [])
    rows = [{
        "recordedAt": a.get("recordedAt", ""),
        "actor": (a.get("actors", {}) or {}).get("user", {}).get("name", "") if isinstance(a.get("actors"), dict) else "",
        "action": a.get("action", ""),
        "result": (a.get("result", {}) or {}).get("status", ""),
    } for a in items]
    columns = [
        ui.DataColumn(key="recordedAt", label="Time"),
        ui.DataColumn(key="actor", label="Actor"),
        ui.DataColumn(key="action", label="Action"),
        ui.DataColumn(key="result", label="Result"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Activity Log", level=2),
        _table_or_empty(rows, columns, "No recent activity", "ScrollText"),
    ])
