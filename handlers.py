"""Chat functions for Ping Identity Connector (PingOne Platform API)."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import ping_client as pc
from app import chat
from schemas import (
    ActivityEvent, ActivityList, ApplicationIdParams, ApplicationList,
    ConnectPingParams, ConnectionList, ConnectionRefParams, CreateGroupParams,
    CreatePopulationParams, CreateUserParams, DeleteResult,
    DisconnectPingParams, GroupIdParams, GroupList, GroupMemberParams,
    HealthAudit, IdentityProviderIdParams, IdentityProviderList,
    ListActivitiesParams, ListApplicationsParams, ListGroupsParams,
    ListIdentityProvidersParams, ListMfaDevicesParams, ListPopulationsParams,
    ListSignOnPoliciesParams, ListUsersParams, MfaDeviceList, NoParams,
    PingApplication, PingConnection, PingGroup, PingIdentityProvider,
    PingMfaDevice, PingPopulation, PingSignOnPolicy, PingUser,
    MfaDeviceParams, PopulationIdParams, PopulationList,
    SignOnPolicyIdParams, SignOnPolicyList, UpdateUserParams, UserIdParams,
    UserList,
)

_SECRET_NAME = "ping_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> PingConnection:
    return PingConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or c.get("environment_id", ""),
        environment_id=c.get("environment_id", ""),
        region=c.get("region", "NA"),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise pc.PingError("No PingOne environment connected yet. Call connect_ping first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise pc.PingError(f"No saved PingOne connection with id '{connection_id}'.")
    return connections[0]


def _client_for(c: dict) -> pc.PingClient:
    return pc.PingClient(
        environment_id=c.get("environment_id", ""),
        client_id=c.get("client_id", ""),
        client_secret=c.get("client_secret", ""),
        region=c.get("region", "NA"),
    )


@chat.function("connect_ping", "Connect a PingOne environment via a Worker Application (client credentials), after verifying connectivity.", action_type="write", chain_callable=True, data_model=PingConnection, event="ping-identity-connector.connect_ping", effects=["ping.provider.connected"])
async def connect_ping(ctx, params: ConnectPingParams) -> ActionResult:
    """Connect a PingOne environment via a Worker Application (client credentials), after verifying connectivity."""
    record = {
        "environment_id": params.environment_id,
        "client_id": params.client_id,
        "client_secret": params.client_secret,
        "region": (params.region or "NA").upper(),
    }
    client = _client_for(record)
    try:
        await client.verify_connection()
    except pc.PingError as exc:
        return ActionResult.error(str(exc), code="PING_CONNECT_FAILED", retryable=exc.retryable)

    record.update({"id": str(uuid.uuid4()), "label": params.label or params.environment_id})
    connections = await _load_connections(ctx)
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(data=_connection_entity(record), summary="PingOne environment connected.")


@chat.function("disconnect_ping", "Disconnect a PingOne environment: deletes only the saved credentials. Nothing in PingOne itself is changed.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.disconnect_ping", effects=["ping.provider.disconnected"])
async def disconnect_ping(ctx, params: DisconnectPingParams) -> ActionResult:
    """Disconnect a PingOne environment: deletes only the saved credentials. Nothing in PingOne itself is changed."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No saved PingOne connection with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data=DeleteResult(ok=True, detail="PingOne environment disconnected."))


@chat.function("list_connections", "List the connected PingOne environments.", action_type="read", chain_callable=True, data_model=ConnectionList, event="ping-identity-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List the connected PingOne environments."""
    connections = await _load_connections(ctx)
    return ActionResult.success(data=ConnectionList(connections=[_connection_entity(c) for c in connections]))


def _user_entity(u: dict) -> PingUser:
    name = u.get("name", {}) or {}
    return PingUser(
        user_id=u.get("id", ""),
        username=u.get("username", ""),
        email=u.get("email", ""),
        given_name=name.get("given", ""),
        family_name=name.get("family", ""),
        enabled=bool(u.get("enabled", True)),
        population_id=(u.get("population", {}) or {}).get("id", ""),
    )


@chat.function("list_users", "List users in the connected PingOne environment, optionally filtered by a search string.", action_type="read", chain_callable=True, data_model=UserList, event="ping-identity-connector.list_users")
async def list_users(ctx, params: ListUsersParams) -> ActionResult:
    """List users in the connected PingOne environment, optionally filtered by a search string."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    q: dict = {"limit": max(1, min(params.limit, 200))}
    if params.q:
        q["filter"] = f'username sw "{params.q}"'
    try:
        data, _ = await client.request("GET", "/users", params=q)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("users", [])
    return ActionResult.success(data=UserList(users=[_user_entity(u) for u in items]))


@chat.function("get_user", "Read one PingOne user in full.", action_type="read", chain_callable=True, data_model=PingUser, event="ping-identity-connector.get_user")
async def get_user(ctx, params: UserIdParams) -> ActionResult:
    """Read one PingOne user in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/users/{params.user_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_user_entity(data or {}))


@chat.function("create_user", "Create a new PingOne user in a population.", action_type="write", chain_callable=True, data_model=PingUser, event="ping-identity-connector.create_user", effects=["ping.user.created"])
async def create_user(ctx, params: CreateUserParams) -> ActionResult:
    """Create a new PingOne user in a population."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {
        "username": params.username,
        "email": params.email,
        "name": {"given": params.given_name, "family": params.family_name},
        "population": {"id": params.population_id},
    }
    if params.password:
        body["password"] = {"value": params.password}
    try:
        data, _ = await client.request("POST", "/users", json_body=body)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_user_entity(data or {}))


@chat.function("update_user", "Update selected fields of an existing PingOne user. Only given fields change.", action_type="write", chain_callable=True, data_model=PingUser, event="ping-identity-connector.update_user", effects=["ping.user.updated"])
async def update_user(ctx, params: UpdateUserParams) -> ActionResult:
    """Update selected fields of an existing PingOne user. Only given fields change."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body: dict = {}
    if params.email:
        body["email"] = params.email
    if params.given_name or params.family_name:
        body["name"] = {"given": params.given_name, "family": params.family_name}
    try:
        data, _ = await client.request("PATCH", f"/users/{params.user_id}", json_body=body)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_user_entity(data or {}))


@chat.function("enable_user", "Enable a disabled PingOne user, restoring their sign-in access.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.enable_user", effects=["ping.user.enabled"])
async def enable_user(ctx, params: UserIdParams) -> ActionResult:
    """Enable a disabled PingOne user, restoring their sign-in access."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("PATCH", f"/users/{params.user_id}", json_body={"enabled": True})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="User enabled."))


@chat.function("disable_user", "Disable a PingOne user, blocking their sign-in.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.disable_user", effects=["ping.user.disabled"])
async def disable_user(ctx, params: UserIdParams) -> ActionResult:
    """Disable a PingOne user, blocking their sign-in."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("PATCH", f"/users/{params.user_id}", json_body={"enabled": False})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="User disabled."))


@chat.function("delete_user", "Permanently delete a PingOne user. Cannot be undone -- unlike Okta's deactivate, PingOne performs a real, irreversible delete.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.delete_user", effects=["ping.user.deleted"])
async def delete_user(ctx, params: UserIdParams) -> ActionResult:
    """Permanently delete a PingOne user. Cannot be undone -- unlike Okta's deactivate, PingOne performs a real, irreversible delete."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("DELETE", f"/users/{params.user_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="User permanently deleted."))


@chat.function("trigger_password_reset", "Trigger PingOne's own password-reset flow for a user (sends them a reset email/notification).", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.trigger_password_reset", effects=["ping.user.password_reset_triggered"])
async def trigger_password_reset(ctx, params: UserIdParams) -> ActionResult:
    """Trigger PingOne's own password-reset flow for a user (sends them a reset email/notification)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("POST", f"/users/{params.user_id}/password", json_body={"recovery": {}})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="Password reset triggered."))


def _mfa_entity(d: dict) -> PingMfaDevice:
    return PingMfaDevice(
        device_id=d.get("id", ""),
        device_type=d.get("type", ""),
        status=d.get("status", ""),
        nickname=d.get("nickname", ""),
    )


@chat.function("list_user_mfa_devices", "List MFA devices enrolled for a PingOne user.", action_type="read", chain_callable=True, data_model=MfaDeviceList, event="ping-identity-connector.list_user_mfa_devices")
async def list_user_mfa_devices(ctx, params: ListMfaDevicesParams) -> ActionResult:
    """List MFA devices enrolled for a PingOne user."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/users/{params.user_id}/devices")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("devices", [])
    return ActionResult.success(data=MfaDeviceList(devices=[_mfa_entity(d) for d in items]))


@chat.function("remove_user_mfa_device", "Remove one enrolled MFA device from a PingOne user -- use when a user has lost their device.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.remove_user_mfa_device", effects=["ping.user.mfa_device_removed"])
async def remove_user_mfa_device(ctx, params: MfaDeviceParams) -> ActionResult:
    """Remove one enrolled MFA device from a PingOne user -- use when a user has lost their device."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("DELETE", f"/users/{params.user_id}/devices/{params.device_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="MFA device removed; user must re-enroll."))


def _population_entity(p: dict) -> PingPopulation:
    return PingPopulation(
        population_id=p.get("id", ""),
        name=p.get("name", ""),
        description=p.get("description", ""),
        user_count=int((p.get("userCount") or 0)),
    )


@chat.function("list_populations", "List Populations (directory segments users belong to) in the connected PingOne environment.", action_type="read", chain_callable=True, data_model=PopulationList, event="ping-identity-connector.list_populations")
async def list_populations(ctx, params: ListPopulationsParams) -> ActionResult:
    """List Populations (directory segments users belong to) in the connected PingOne environment."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/populations")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("populations", [])
    return ActionResult.success(data=PopulationList(populations=[_population_entity(p) for p in items]))


@chat.function("get_population", "Read one PingOne population in full.", action_type="read", chain_callable=True, data_model=PingPopulation, event="ping-identity-connector.get_population")
async def get_population(ctx, params: PopulationIdParams) -> ActionResult:
    """Read one PingOne population in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/populations/{params.population_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_population_entity(data or {}))


@chat.function("create_population", "Create a new PingOne population.", action_type="write", chain_callable=True, data_model=PingPopulation, event="ping-identity-connector.create_population", effects=["ping.population.created"])
async def create_population(ctx, params: CreatePopulationParams) -> ActionResult:
    """Create a new PingOne population."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {"name": params.name, "description": params.description}
    try:
        data, _ = await client.request("POST", "/populations", json_body=body)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_population_entity(data or {}))


def _group_entity(g: dict) -> PingGroup:
    return PingGroup(
        group_id=g.get("id", ""),
        name=g.get("name", ""),
        description=g.get("description", ""),
    )


@chat.function("list_groups", "List Groups (access-grouping for app assignment) in the connected PingOne environment.", action_type="read", chain_callable=True, data_model=GroupList, event="ping-identity-connector.list_groups")
async def list_groups(ctx, params: ListGroupsParams) -> ActionResult:
    """List Groups (access-grouping for app assignment) in the connected PingOne environment."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/groups")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("groups", [])
    return ActionResult.success(data=GroupList(groups=[_group_entity(g) for g in items]))


@chat.function("get_group", "Read one PingOne group in full.", action_type="read", chain_callable=True, data_model=PingGroup, event="ping-identity-connector.get_group")
async def get_group(ctx, params: GroupIdParams) -> ActionResult:
    """Read one PingOne group in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/groups/{params.group_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_group_entity(data or {}))


@chat.function("create_group", "Create a new PingOne group.", action_type="write", chain_callable=True, data_model=PingGroup, event="ping-identity-connector.create_group", effects=["ping.group.created"])
async def create_group(ctx, params: CreateGroupParams) -> ActionResult:
    """Create a new PingOne group."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {"name": params.name, "description": params.description}
    try:
        data, _ = await client.request("POST", "/groups", json_body=body)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_group_entity(data or {}))


@chat.function("add_user_to_group", "Add a user to a PingOne group.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.add_user_to_group", effects=["ping.group.member_added"])
async def add_user_to_group(ctx, params: GroupMemberParams) -> ActionResult:
    """Add a user to a PingOne group."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("POST", f"/groups/{params.group_id}/memberships", json_body={"user": {"id": params.user_id}})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="User added to group."))


@chat.function("remove_user_from_group", "Remove a user from a PingOne group.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.remove_user_from_group", effects=["ping.group.member_removed"])
async def remove_user_from_group(ctx, params: GroupMemberParams) -> ActionResult:
    """Remove a user from a PingOne group."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("DELETE", f"/groups/{params.group_id}/memberships/{params.user_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="User removed from group."))


def _app_entity(a: dict) -> PingApplication:
    return PingApplication(
        application_id=a.get("id", ""),
        name=a.get("name", ""),
        protocol=a.get("protocol", ""),
        enabled=bool(a.get("enabled", True)),
    )


@chat.function("list_applications", "List applications (OIDC/SAML) registered in the connected PingOne environment.", action_type="read", chain_callable=True, data_model=ApplicationList, event="ping-identity-connector.list_applications")
async def list_applications(ctx, params: ListApplicationsParams) -> ActionResult:
    """List applications (OIDC/SAML) registered in the connected PingOne environment."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/applications")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("applications", [])
    return ActionResult.success(data=ApplicationList(applications=[_app_entity(a) for a in items]))


@chat.function("get_application", "Read one PingOne application in full.", action_type="read", chain_callable=True, data_model=PingApplication, event="ping-identity-connector.get_application")
async def get_application(ctx, params: ApplicationIdParams) -> ActionResult:
    """Read one PingOne application in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/applications/{params.application_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_app_entity(data or {}))


@chat.function("enable_application", "Enable a PingOne application.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.enable_application", effects=["ping.application.enabled"])
async def enable_application(ctx, params: ApplicationIdParams) -> ActionResult:
    """Enable a PingOne application."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("PATCH", f"/applications/{params.application_id}", json_body={"enabled": True})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="Application enabled."))


@chat.function("disable_application", "Disable a PingOne application.", action_type="write", chain_callable=True, data_model=DeleteResult, event="ping-identity-connector.disable_application", effects=["ping.application.disabled"])
async def disable_application(ctx, params: ApplicationIdParams) -> ActionResult:
    """Disable a PingOne application."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        await client.request("PATCH", f"/applications/{params.application_id}", json_body={"enabled": False})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(ok=True, detail="Application disabled."))


def _policy_entity(p: dict) -> PingSignOnPolicy:
    return PingSignOnPolicy(
        policy_id=p.get("id", ""),
        name=p.get("name", ""),
        is_default=bool(p.get("default", False)),
    )


@chat.function("list_sign_on_policies", "List Sign-On Policies (MFA/adaptive authentication chains) configured in the connected PingOne environment.", action_type="read", chain_callable=True, data_model=SignOnPolicyList, event="ping-identity-connector.list_sign_on_policies")
async def list_sign_on_policies(ctx, params: ListSignOnPoliciesParams) -> ActionResult:
    """List Sign-On Policies (MFA/adaptive authentication chains) configured in the connected PingOne environment."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/signOnPolicies")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("signOnPolicies", [])
    return ActionResult.success(data=SignOnPolicyList(policies=[_policy_entity(p) for p in items]))


@chat.function("get_sign_on_policy", "Read one PingOne sign-on policy in full.", action_type="read", chain_callable=True, data_model=PingSignOnPolicy, event="ping-identity-connector.get_sign_on_policy")
async def get_sign_on_policy(ctx, params: SignOnPolicyIdParams) -> ActionResult:
    """Read one PingOne sign-on policy in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/signOnPolicies/{params.policy_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_policy_entity(data or {}))


def _idp_entity(i: dict) -> PingIdentityProvider:
    return PingIdentityProvider(
        idp_id=i.get("id", ""),
        name=i.get("name", ""),
        provider_type=i.get("type", ""),
        enabled=bool(i.get("enabled", True)),
    )


@chat.function("list_identity_providers", "List external Identity Providers federated into the connected PingOne environment.", action_type="read", chain_callable=True, data_model=IdentityProviderList, event="ping-identity-connector.list_identity_providers")
async def list_identity_providers(ctx, params: ListIdentityProvidersParams) -> ActionResult:
    """List external Identity Providers federated into the connected PingOne environment."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/identityProviders")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("identityProviders", [])
    return ActionResult.success(data=IdentityProviderList(identity_providers=[_idp_entity(i) for i in items]))


@chat.function("get_identity_provider", "Read one PingOne identity provider in full.", action_type="read", chain_callable=True, data_model=PingIdentityProvider, event="ping-identity-connector.get_identity_provider")
async def get_identity_provider(ctx, params: IdentityProviderIdParams) -> ActionResult:
    """Read one PingOne identity provider in full."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/identityProviders/{params.idp_id}")
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_idp_entity(data or {}))


def _activity_entity(a: dict) -> ActivityEvent:
    actors = a.get("actors", {}) or {}
    resources = a.get("resources", []) or []
    target = resources[0].get("name", "") if resources else ""
    return ActivityEvent(
        activity_id=a.get("id", ""),
        actor=(actors.get("user", {}) or {}).get("name", "") or (actors.get("client", {}) or {}).get("name", ""),
        action=a.get("action", ""),
        target=target,
        result=(a.get("result", {}) or {}).get("status", ""),
        recorded_at=a.get("recordedAt", ""),
    )


@chat.function("list_activities", "List Activity (audit) log events for the connected PingOne environment -- logins, admin actions, MFA events.", action_type="read", chain_callable=True, data_model=ActivityList, event="ping-identity-connector.list_activities")
async def list_activities(ctx, params: ListActivitiesParams) -> ActionResult:
    """List Activity (audit) log events for the connected PingOne environment -- logins, admin actions, MFA events."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    q: dict = {"limit": max(1, min(params.limit, 200))}
    if params.filter:
        q["filter"] = params.filter
    if params.cursor:
        q["cursor"] = params.cursor
    try:
        data, _ = await client.request("GET", "/activities", params=q)
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("_embedded", {}).get("activities", [])
    next_cursor = ((data or {}).get("_links", {}) or {}).get("next", {}).get("href", "")
    return ActionResult.success(data=ActivityList(activities=[_activity_entity(a) for a in items], next_cursor=next_cursor))


@chat.function("audit_environment", "Build one aggregated health report for the connected PingOne environment: total/disabled users, disabled applications, and recent failed logins.", action_type="read", chain_callable=True, data_model=HealthAudit, event="ping-identity-connector.audit_environment")
async def audit_environment(ctx, params: ConnectionRefParams) -> ActionResult:
    """Build one aggregated health report for the connected PingOne environment: total/disabled users, disabled applications, and recent failed logins."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        users, _ = await client.request("GET", "/users", params={"limit": 200})
        apps, _ = await client.request("GET", "/applications", params={"limit": 200})
        failed, _ = await client.request("GET", "/activities", params={"filter": 'action eq "AUTHENTICATION" and result.status eq "FAILED"', "limit": 50})
    except pc.PingError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    user_items = (users or {}).get("_embedded", {}).get("users", [])
    app_items = (apps or {}).get("_embedded", {}).get("applications", [])
    failed_items = (failed or {}).get("_embedded", {}).get("activities", [])
    disabled_users = sum(1 for u in user_items if not u.get("enabled", True))
    disabled_apps = sum(1 for a in app_items if not a.get("enabled", True))
    return ActionResult.success(data=HealthAudit(
        environment_id=c.get("environment_id", ""),
        total_users=len(user_items),
        disabled_users=disabled_users,
        disabled_applications=disabled_apps,
        failed_logins_24h=len(failed_items),
        notes=(
            f"{len(user_items)} users ({disabled_users} disabled), "
            f"{len(app_items)} applications ({disabled_apps} disabled), "
            f"{len(failed_items)} failed logins recently."
        ),
    ))
