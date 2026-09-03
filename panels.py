"""Ping Identity Connector panels.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as Okta Connector's /
AWS Connector's panels.py). Every section is a plain ui.Stack, stacked
vertically and left-aligned, no Card border/background/shadow. Disconnect
lives only in "App settings" (panels_settings.py). The one secondary
"App settings" button is always the LAST element at the bottom of the
sidebar.

Per Vlad's standing rule: every input carries its own label (not just a
placeholder), placeholders are contextually specific, the form container is
stretched to the full width of the left sidebar with its contents stretched
to fill it, and the sidebar carries NO instructions that duplicate the
"How do I set this up?" modal.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="Settings", on_click=ui.Call("__panel__ping_settings"),
    )


@ext.panel("ping_sidebar", slot="left", title="Ping Identity")
async def ping_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("How do I get this?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__ping_connect_help")),
            ui.Button("Sign in with PingOne (OIDC / SSO)", variant="primary", size="sm", icon="login"),
            ui.Divider(),
            ui.Text("Or connect via Worker App Credentials", variant="caption"),
            ui.Form(action="connect_ping", submit_label="Connect", children=[
                _field("Environment label", ui.Input(param_name="label", placeholder="Acme Production")),
                _field("Region", ui.Select(param_name="region", options=["NA", "EU", "AP", "CA"], value="NA")),
                _field("Environment ID", ui.Input(param_name="environment_id", placeholder="b1c2d3e4-f5g6-7890-abcd-ef1234567890")),
                _field("Worker Client ID", ui.Input(param_name="client_id", placeholder="Worker Application client ID")),
                _field("Worker Client Secret", ui.Input(param_name="client_secret", placeholder="Worker Application client secret")),
            ]),
            _settings_button(),
        ])
    c = connections[0]
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(c.get("label") or c.get("environment_id", ""), variant="subtitle"),
        ui.Divider(),
        ui.Button("Users", variant="ghost", on_click=ui.Call("__panel__ping_users")),
        ui.Button("Groups", variant="ghost", on_click=ui.Call("__panel__ping_groups")),
        ui.Button("Populations", variant="ghost", on_click=ui.Call("__panel__ping_populations")),
        ui.Button("Applications", variant="ghost", on_click=ui.Call("__panel__ping_applications")),
        ui.Button("Sign-On Policies", variant="ghost", on_click=ui.Call("__panel__ping_policies")),
        ui.Button("Identity Providers", variant="ghost", on_click=ui.Call("__panel__ping_idps")),
        ui.Button("Activity Log", variant="ghost", on_click=ui.Call("__panel__ping_activity")),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("ping_connect_help", slot="center", title="Connect Ping Identity", center_overlay=True)
async def ping_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="How to connect PingOne", level=2),
        ui.Markdown(content=(
            "1. Sign in to the **PingOne Admin Console** for your environment.\n"
            "2. Go to **Applications > Applications > Add Application > Worker**.\n"
            "3. Name it (e.g. \"Imperal Integration\") and save.\n"
            "4. Open the new Worker application's **Roles** tab and grant at least "
            "**Identity Data Admin** (add **Environment Admin** for full policy/app "
            "management).\n"
            "5. Copy the **Client ID** and **Client Secret** from the Worker "
            "application's Configuration tab.\n"
            "6. Copy the **Environment ID** from **Environment > Overview** (top of "
            "the page).\n"
            "7. Note which **region** your environment lives in -- it decides the "
            "PingOne data center your requests go to.\n"
            "8. Paste all four values into the form on the left."
        )),
    ])