import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    wallet_address: str | None
    display_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """Lightweight reference used inside nested responses."""
    id: uuid.UUID
    email: EmailStr
    wallet_address: str | None

    model_config = {"from_attributes": True}
