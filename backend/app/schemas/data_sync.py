from pydantic import BaseModel


class SyncRequest(BaseModel):
    providers: list[str] | None = None  # None = sync all


class SyncProviderResult(BaseModel):
    provider: str
    error: str


class SyncResponse(BaseModel):
    synced_providers: list[str]
    failed_providers: list[SyncProviderResult]
    features: dict[str, float]
    trust_score: float | None = None
    risk_tier: str | None = None
    loan_limit: float | None = None


class GitHubConnectRequest(BaseModel):
    code: str


class GitHubConnectResponse(BaseModel):
    username: str
    is_verified: bool
