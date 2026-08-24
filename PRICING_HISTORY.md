# Pricing History — Ping Identity Connector

## 2026-08-24 — initial pricing (build → deploy → update_pricing → submit_for_review)

Same pattern as Okta/MuleSoft/Asana this build cycle: pricing set via
`developer.update_pricing` (canonical call, NOT `save_pricing`) BEFORE
`submit_for_review`, per the standing rule ("ты не выставила прайсинги на
функции перед заливом на платформу... это должно быть частью дефолтного
поведения всегда для всех приложений и для всех сессий").

**First call failed with the same silent-mismatch pattern seen on Okta and
MuleSoft** — response reported `model stored as 'free'` and every
`tool_prices` key "not stored" despite no error being raised by the API.
Immediate retry with the identical payload succeeded (returned the full
saved app object with `manifest_json` populated). Confirms this is a
platform-side quirk, not a client mistake — retry once with the identical
payload before assuming failure. Worth a platform bug ticket (see
`APP_PREPARATION_STANDARD.md` for the standing note on this).

**Also hit and fixed during this app's deploy step:** `gh repo create`
defaults to `--private`, but the platform's `deploy_app` clone step has no
stored GitHub credential and can only pull public repos — deploy failed with
"could not read Username for 'https://github.com'" until the repo was made
public via `gh repo edit --visibility public`. Every new app's repo must be
created/kept **public**, matching the working Okta Connector precedent.

**Prices — fixed platform scale {0, 8, 16, 20, 40, 60}, no exceptions, no
markup (Ping Identity is not a Google-backed metered API):**

| Цена | Функции |
|---|---|
| 0 | `connect_ping`, `disconnect_ping`, `list_connections` (настройка доступа, не операция с PingOne API) |
| 8 | `list_users`, `get_user`, `list_populations`, `get_population`, `list_groups`, `get_group`, `list_applications`, `get_application`, `list_sign_on_policies`, `get_sign_on_policy`, `list_identity_providers`, `get_identity_provider`, `list_activities`, `list_user_mfa_devices` (простое чтение состояния) |
| 16 | `create_user`, `update_user`, `enable_user`, `disable_user`, `create_population`, `create_group`, `add_user_to_group`, `remove_user_from_group`, `enable_application`, `disable_application` (стандартное одиночное write-действие) |
| 20 | `delete_user` (необратимое удаление — в отличие от Okta это реальный, а не soft delete), `trigger_password_reset`, `remove_user_mfa_device` (security-критичное действие, влияющее на доступ немедленно) |
| 40 | `audit_environment` (агрегированный value-add отчёт по всему окружению) |
| 60 | — (bulk-операций пока нет в v1) |
