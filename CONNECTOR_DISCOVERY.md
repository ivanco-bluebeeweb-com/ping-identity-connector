# Ping Identity Connector — Connector Discovery

**Discovery date:** 2026-08-24
**Release scope:** maximum functionality against the publicly documented PingOne
Platform API (per standing "максимальный функционал" instruction).
**Related task:** BBW Imperal Apps (IAM/Access Management category).

## 1. What Ping Identity actually is

Ping Identity is an enterprise identity company; its cloud IDaaS product is
**PingOne** (SSO, MFA, directory, lifecycle management), exposed through the
**PingOne Platform API** (`https://api.pingone.{region}/v1/environments/{envId}/*`),
with a separate Auth API for token issuance
(`https://auth.pingone.{region}/{envId}/as/token`). Ping also sells PingFederate
(on-prem federation server) — a different product with a different API and auth
model, out of scope for v1.

## 2. Chosen integration surface

**PingOne Platform API v1** (`/v1/environments/{envId}/*`):
- Environments (`/environments`) — list/get (each PingOne "environment" is an
  isolated tenant; a Worker App is scoped to one).
- Populations (`/populations`) — PingOne's grouping of users by policy/directory
  segment (roughly like an OU) — list, get, create.
- Users (`/users`) — full lifecycle: list, get, create, update, enable, disable,
  delete, password reset trigger, list/remove MFA devices.
- Groups (`/groups`) — list, get, create, membership add/remove (distinct from
  Populations — Groups are for access-grouping/app assignment, Populations are
  directory segments).
- Applications (`/applications`) — list, get, create, enable/disable (OIDC/SAML
  app registrations that PingOne authenticates users into).
- Sign-On Policies (`/signOnPolicies`) — list, get (multi-factor/adaptive
  authentication policy chains).
- MFA Policies (`/mfaPolicies` under Populations) — list, get.
- Identity Providers (`/identityProviders`) — external IdPs federated into this
  environment (social/enterprise) — list, get.
- **Activities** (`/activities`) — PingOne's audit/security event log, filterable
  by actor/event type/date, paginated via `_links.next`.

Not in scope for v1 (Tier 2/future): PingOne DaVinci (no-code orchestration),
PingOne Protect (risk signals), PingOne Verify (identity verification),
PingFederate (separate on-prem product, separate API/auth entirely).

## 3. Auth model

**Worker Application, OAuth2 Client Credentials grant** (PingOne's own recommended
machine-to-machine pattern, directly analogous to Okta's OAuth2 Service App):
1. Admin creates a **Worker application** in PingOne Admin Console
   (environment > Applications > Add Application > Worker), assigns it specific
   roles (e.g. Identity Data Admin, Environment Admin) scoped to that environment.
2. Imperal exchanges `client_id`+`client_secret` (HTTP Basic) at
   `https://auth.pingone.{region}/{environmentId}/as/token` with
   `grant_type=client_credentials` for a short-lived bearer access token,
   auto-refreshed on expiry (mirrors the ServiceNow OAuth2 / ServiceNow Basic
   dual-mode client pattern already used across the portfolio).
3. Connect fields: `environment_id` (UUID), `region` (NA / EU / AP / CA — each
   has a distinct API base domain), `client_id`, `client_secret`.

Only `client_id`/`client_secret`/`environment_id`/`region` are persisted —
never the resulting bearer token long-term.

## 4. Terminology / API notes

- Every resource has a stable UUID `id` (standard REST semantics, same as Okta).
- Pagination is HAL-style (`_links.next.href`) rather than Okta's `Link` header
  or ServiceNow's offset/limit — the client follows `_links.next` internally up
  to the requested limit.
- Rate limits are enforced per environment; PingOne returns `429` with a
  `Retry-After` header — client raises a retryable error surfacing that value.
- User states are explicit (`enabled: true/false`, plus `account.status`:
  `OK`, `LOCKED_OUT`, `PASSWORD_EXPIRED` etc.) — surfaced as-is like Okta's
  status enum, not flattened into a single boolean.

## 5. Scope decision (Tier 1 = v1)

**Tier 1 (this release):** see PREPARATION.md §3 (same list, kept in one place
to avoid drift between the two docs).

**Tier 2 (future):** PingOne DaVinci, PingOne Protect, PingOne Verify,
PingFederate on-prem federation server management.

## 6. Security notes

- `client_secret` stored as one encrypted JSON blob per connection, matching
  the Okta/ServiceNow/SAP pattern.
- `delete_user` is a **hard, permanent delete** in PingOne (unlike Okta's
  soft-delete deactivate with a 30-day undo window) — flagged clearly in the
  tool description and gated behind an explicit UI confirm dialog.
- `disable_user` / `remove_user_mfa_device` are destructive-adjacent — clear
  confirmation copy required, no silent defaults.
- Activities log events may contain PII (IP addresses, user agent strings) —
  passed through as-is (PingOne's own data), no extra redaction.
