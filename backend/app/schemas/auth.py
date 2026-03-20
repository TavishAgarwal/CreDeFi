import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """L1: Enforce password complexity requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WalletLoginRequest(BaseModel):
    wallet_address: str = Field(min_length=32, max_length=44)
    signature: str
    message: str = Field(min_length=1)
    nonce: str = Field(min_length=1, description="Server-issued nonce from /auth/wallet-nonce")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NonceResponse(BaseModel):
    nonce: str
    wallet_address: str
