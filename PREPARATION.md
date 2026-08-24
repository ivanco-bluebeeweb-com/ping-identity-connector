# Ping Identity Connector — Preparation

**Version:** 0.1.0 (planning)
**Date:** 2026-08-24
**Related task:** BBW Imperal Apps (IAM/Access Management category — Ping Identity)
**Scope decision:** maximum feasible capability against the publicly documented
PingOne Platform API (per standing "максимальный функционал" instruction).

## 1. App passport

**Name:** Ping Identity Connector
**One-line purpose:** Connect your own PingOne environment to manage Users,
Groups, Populations, Applications, Sign-On/MFA Policies and Identity Providers,
plus review the Activity (audit) log for security visibility.

**What it is not:**
- Not PingFederate (the separate on-prem federation server product) — this
  connector targets PingOne, Ping's cloud IDaaS platform, which is where new
  Ping deployments and Gartner Leader recognition concentrate.
- Not PingOne DaVinci (no-code orchestration builder) — separate product surface,
  Tier 2/future.
- Not PingOne Protect (risk/fraud signals) — Tier 2/future, a distinct add-on SKU.

## 2. Human problem

> An IT admin or security engineer running PingOne needs to provision/deprovision
> users, manage group and population membership, configure which sign-on policy
> protects an application, or investigate a suspicious authentication event —
> without opening the PingOne Admin Console for every routine task.

### Personas
| Persona | Trigger | Value |
|---|---|---|
| IT admin | New hire needs an account + population/group | create_user + add_user_to_group in one flow |
| Security engineer | Investigating a suspicious login | list_activities filtered by user/event type |
| Helpdesk agent | User locked out / needs MFA reset | list_user_mfa_devices, remove/reset a device |
| PingOne org admin | Wants an environment health snapshot | audit_environment — locked users, disabled apps, recent failed logins |
| App owner | Onboarding a new application to SSO | create_application, assign sign-on policy |

## 3. Scope tiers

**Tier 1 (this release):**
- connect_pingone (Worker App client_id + client_secret + environment_id + region),
  disconnect_pingone, list_connections
- Environments: list_environments, get_environment
- Populations: list_populations, get_population, create_population
- Users: list_users, get_user, create_user, update_user, enable_user, disable_user,
  delete_user, set_user_password (send reset), list_user_mfa_devices, remove_user_mfa_device
- Groups: list_groups, get_group, create_group, add_user_to_group,
  remove_user_from_group, list_group_members
- Applications: list_applications, get_application, create_application,
  enable_application, disable_application
- Sign-On/MFA Policies: list_sign_on_policies, get_sign_on_policy,
  list_mfa_policies, get_mfa_policy
- Identity Providers: list_identity_providers, get_identity_provider
- Activity log: list_activities (audit/security events, filtered by date/actor/event)
- Value-add: audit_environment (disabled users, locked users, disabled apps,
  recent failed-login spike from Activities)

**Tier 2 (future):** PingOne DaVinci flows, PingOne Protect risk policies,
PingOne Verify (identity verification), PingFederate on-prem federation server
management (separate product, separate auth model).

## 4. Auth model detail

PingOne Worker Application (machine-to-machine OAuth2 client credentials):
1. Admin creates a **Worker application** in PingOne Admin Console
   (Applications > Add Application > Worker), which yields a `client_id` +
   `client_secret` scoped to specific roles (e.g. Identity Data Admin,
   Environment Admin) on one environment.
2. Imperal exchanges client_id+client_secret at the environment's Auth API
   token endpoint (`https://auth.pingone.{region}/{environmentId}/as/token`)
   for a short-lived access token (client_credentials grant), auto-refreshed.
3. Every request also needs the **environment_id** (UUID) and **region**
   (NA/EU/AP/CA — PingOne is a multi-region SaaS, each region has its own API
   base domain) as first-class connect fields, same pattern as ServiceNow's
   instance_host / Okta's org_domain.

Only the client_id/client_secret/environment_id/region are stored — never the
resulting bearer access token long-term (cached in-memory with expiry).

## 5. Safety notes (see APP_SAFETY_CHECKLIST.md)

- `delete_user` is a hard, permanent delete in PingOne (no native 30-day undo
  like Okta's deactivate) — tool description must say so explicitly, and the
  panel must require a confirm dialog before calling it.
- `disable_user` / `remove_user_mfa_device` are destructive-adjacent (block
  sign-in / force re-enrollment) — clear confirmation copy required.
- Activity log events may contain PII (IP addresses, user agent strings) —
  passed through as-is (PingOne's own data), no extra redaction.
