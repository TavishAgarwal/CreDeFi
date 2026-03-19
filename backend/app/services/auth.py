from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, data: RegisterRequest) -> User:
        existing = await self._session.scalar(
            select(User).where(User.email == data.email)
        )
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._session.scalar(
            select(User).where(User.email == data.email)
        )
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)

    async def wallet_login(self, wallet_address: str, signature: str) -> TokenResponse:
        """Placeholder — verify wallet signature and issue token."""
        # TODO: implement actual signature verification (e.g. via eth_account or solana)
        user = await self._session.scalar(
            select(User).where(User.wallet_address == wallet_address)
        )
        if not user:
            raise ValueError("Wallet not linked to any account")

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)
