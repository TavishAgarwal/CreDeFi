from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.contracts.client import ContractClient


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

    async def wallet_login(self, wallet_address: str, signature: str, message: str = "") -> TokenResponse:
        """
        Verify an EIP-191 personal_sign signature and issue a JWT.

        The frontend signs a standard login message containing the wallet
        address and a nonce.  We recover the signer address from the
        signature and verify it matches the claimed wallet_address.
        """
        # Recover the address that produced the signature
        if message and signature:
            try:
                recovered = ContractClient.recover_signer(message, signature)
                if recovered.lower() != wallet_address.lower():
                    raise ValueError(
                        f"Signature mismatch: recovered {recovered}, expected {wallet_address}"
                    )
            except Exception as exc:
                raise ValueError(f"Invalid wallet signature: {exc}")
        else:
            raise ValueError("Both message and signature are required for wallet login")

        user = await self._session.scalar(
            select(User).where(User.wallet_address == wallet_address)
        )
        if not user:
            # Auto-register wallet-only users
            user = User(wallet_address=wallet_address)
            self._session.add(user)
            await self._session.flush()

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)
