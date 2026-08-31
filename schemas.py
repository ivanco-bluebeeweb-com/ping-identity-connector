"""Pydantic input contracts and SDL result entities for Ping Identity Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved PingOne environment connection ID. Omit to use the first connected environment.")


class ConnectPingParams(BaseModel):
    label: str = Field("", description="Friendly environment label, e.g. 'Acme Production'.")
    region: str = Field("NA", description="PingOne region: NA, EU, AP, or CA.")
    environment_id: str = Field(..., description="PingOne environment ID (UUID), from Environment > Overview.")
    client_id: str = Field(..., description="Worker Application client ID.")
    client_secret: str = Field(..., description="Worker Application client secret.")


class DisconnectPingParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved PingOne environment connection ID to remove from Imperal.")


class ListUsersParams(ConnectionRefParams):
    q: str = Field("", description="Optional search filter matching username/email prefix.")
    limit: int = Field(50, description="Max users to return (1-200).")


class UserIdParams(ConnectionRefParams):
    user_id: str = Field(..., description="PingOne user ID.")


class CreateUserParams(ConnectionRefParams):
    username: str = Field(..., description="Username (often the email address).")
    email: str = Field(..., description="User's email address.")
    given_name: str = Field("", description="First name.")
    family_name: str = Field("", description="Last name.")
    population_id: str = Field(..., description="Population ID this user belongs to.")
    password: str = Field("", description="Optional initial password (if population's password policy allows admin-set passwords).")


class UpdateUserParams(UserIdParams):
    email: str = Field("", description="New email address, or leave blank to keep unchanged.")
    given_name: str = Field("", description="New first name, or leave blank to keep unchanged.")
    family_name: str = Field("", description="New last name, or leave blank to keep unchanged.")


class ListPopulationsParams(ConnectionRefParams):
    pass


class PopulationIdParams(ConnectionRefParams):
    population_id: str = Field(..., description="PingOne population ID.")


class CreatePopulationParams(ConnectionRefParams):
    name: str = Field(..., description="Population name, e.g. 'Employees'.")
    description: str = Field("", description="Optional description.")


class ListGroupsParams(ConnectionRefParams):
    pass


class GroupIdParams(ConnectionRefParams):
    group_id: str = Field(..., description="PingOne group ID.")


class CreateGroupParams(ConnectionRefParams):
    name: str = Field(..., description="Group name.")
    description: str = Field("", description="Optional description.")


class GroupMemberParams(ConnectionRefParams):
    group_id: str = Field(..., description="PingOne group ID.")
    user_id: str = Field(..., description="PingOne user ID.")


class ListApplicationsParams(ConnectionRefParams):
    pass


class ApplicationIdParams(ConnectionRefParams):
    application_id: str = Field(..., description="PingOne application ID.")


class ListSignOnPoliciesParams(ConnectionRefParams):
    pass


class SignOnPolicyIdParams(ConnectionRefParams):
    policy_id: str = Field(..., description="PingOne sign-on policy ID.")


class ListIdentityProvidersParams(ConnectionRefParams):
    pass


class IdentityProviderIdParams(ConnectionRefParams):
    idp_id: str = Field(..., description="PingOne identity provider ID.")


class ListMfaDevicesParams(UserIdParams):
    pass


class MfaDeviceParams(ConnectionRefParams):
    user_id: str = Field(..., description="PingOne user ID.")
    device_id: str = Field(..., description="PingOne MFA device ID.")


class ListActivitiesParams(ConnectionRefParams):
    since: str = Field("", description="ISO 8601 start time, e.g. '2026-08-01T00:00:00Z'.")
    until: str = Field("", description="ISO 8601 end time.")
    limit: int = Field(50, description="Max events to return (1-200).")
    cursor: str = Field("", description="Pagination cursor from a previous call's next_cursor.")


# ---- SDL entities ----

class PingConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    connection_id: str
    label: str
    environment_id: str
    region: str


class ConnectionList(sdl.Entity):
    id: str = ""
    title: str = ""
    connections: list[PingConnection]


class PingUser(sdl.Entity):
    id: str = ""
    title: str = ""
    user_id: str
    username: str
    email: str
    given_name: str
    family_name: str
    enabled: bool
    population_id: str


class UserList(sdl.Entity):
    id: str = ""
    title: str = ""
    users: list[PingUser]


class PingPopulation(sdl.Entity):
    id: str = ""
    title: str = ""
    population_id: str
    name: str
    description: str
    user_count: int


class PopulationList(sdl.Entity):
    id: str = ""
    title: str = ""
    populations: list[PingPopulation]


class PingGroup(sdl.Entity):
    id: str = ""
    title: str = ""
    group_id: str
    name: str
    description: str


class GroupList(sdl.Entity):
    id: str = ""
    title: str = ""
    groups: list[PingGroup]


class PingApplication(sdl.Entity):
    id: str = ""
    title: str = ""
    application_id: str
    name: str
    protocol: str
    enabled: bool


class ApplicationList(sdl.Entity):
    id: str = ""
    title: str = ""
    applications: list[PingApplication]


class PingSignOnPolicy(sdl.Entity):
    id: str = ""
    title: str = ""
    policy_id: str
    name: str
    is_default: bool


class SignOnPolicyList(sdl.Entity):
    id: str = ""
    title: str = ""
    policies: list[PingSignOnPolicy]


class PingIdentityProvider(sdl.Entity):
    id: str = ""
    title: str = ""
    idp_id: str
    name: str
    provider_type: str
    enabled: bool


class IdentityProviderList(sdl.Entity):
    id: str = ""
    title: str = ""
    identity_providers: list[PingIdentityProvider]


class PingMfaDevice(sdl.Entity):
    id: str = ""
    title: str = ""
    device_id: str
    device_type: str
    status: str
    nickname: str


class MfaDeviceList(sdl.Entity):
    id: str = ""
    title: str = ""
    devices: list[PingMfaDevice]


class ActivityEvent(sdl.Entity):
    id: str = ""
    title: str = ""
    activity_id: str
    actor: str
    action: str
    target: str
    result: str
    recorded_at: str


class ActivityList(sdl.Entity):
    id: str = ""
    title: str = ""
    activities: list[ActivityEvent]
    next_cursor: str


class HealthAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    environment_id: str
    total_users: int
    disabled_users: int
    disabled_applications: int
    failed_logins_24h: int
    notes: str


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    ok: bool
    detail: str
