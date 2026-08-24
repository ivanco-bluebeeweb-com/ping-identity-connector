# Ping Identity Connector — UI Component Plan

Source: `UI_COMPONENT_VOCABULARY.md` + `~/UI_INTERFACE_STANDARD.md`. Only primitives
from the verified vocabulary are used below.

## Standing rules applied (binding for every screen in this plan)
- Every input carries its own visible label (via a `Text(variant="caption")` +
  input pair, never a bare placeholder).
- Placeholders are contextually specific to the exact field (e.g. a real-looking
  environment ID), never generic ("enter value").
- The connect form container is stretched to the full width of the left sidebar;
  its own contents (inputs, selects, buttons) stretch to fill it (`align="stretch"`).
- The sidebar carries NO instructions duplicated from the "How do I get this?"
  modal — the modal is the only place with the credential-setup walkthrough.
- No `Card` (decorated box) anywhere in the left sidebar — plain `Stack` +
  `Divider` only.

## 1. Left sidebar (`slot="left"`)

**Not connected:**
- `Button` "How do I get this?" (ghost, opens `ping_connect_help` modal panel)
- `Form(action="connect_ping")`:
  - Region `Select` (NA/EU/AP/CA) — first field, since it determines the base URL
  - Environment ID `Input` (placeholder: a realistic UUID shape)
  - Worker Client ID `Input`
  - Worker Client Secret `Input` (masked via `ui.Password` if available in SDK,
    else a plain `Input` — checked against verified vocabulary before final code)
  - Submit button "Connect"

**Connected (one or more environments):**
- `Text` environment label, `Divider`
- `Button` list (ghost, full width, left-aligned) opening each center panel:
  Users, Groups, Populations, Applications, Sign-On Policies, Identity Providers,
  Activity Log
- `Divider`
- `Button` "App settings" (secondary, always last)

## 2. Center panels (`slot="center"`, `center_overlay=True`)

- `ping_users` — `DataTable` (name, username, email, status) or `Empty` if none
- `ping_groups` — `DataTable` (name, population, member count)
- `ping_populations` — `DataTable` (name, user count, default flag)
- `ping_applications` — `DataTable` (name, protocol, enabled)
- `ping_policies` — `DataTable` (name, type, default flag)
- `ping_identity_providers` — `DataTable` (name, type, enabled)
- `ping_activity_log` — `DataTable` (actor, action, target, result, timestamp)
- `ping_connect_help` — `Markdown` walkthrough (Worker App creation + roles)
- Every panel above: `Empty(message="Nothing to show here", icon=...)` base state
  when not connected, registered with `center_overlay=True`.

## 3. App settings (`slot="center"`, separate screen)

- `ping_settings` — one row per connected environment: `Text` label + `Button`
  "Disconnect" (destructive). This is the ONLY place disconnect lives.

## 4. Actions map (`ui.Call` targets, no duplication with chat tools)

Every sidebar/center button maps 1:1 to a `@chat.function` name already declared
in `handlers.py` — no UI-only actions invented here that don't exist as callable
tools.
