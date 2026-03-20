from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nonce_store import wallet_nonce_store
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
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)

    async def wallet_login(
        self,
        wallet_address: str,
        signature: str,
        message: str = "",
        nonce: str = "",
    ) -> TokenResponse:
        """
        Verify an EIP-191 personal_sign signature and issue a JWT.

        C5: Server-issued nonce is validated and consumed (single-use)
        to prevent replay attacks. The nonce must have been issued via
        GET /auth/wallet-nonce within the last 5 minutes.
        """
        if not message or not signature:
            raise ValueError("Both message and signature are required for wallet login")

        # C5: Validate and consume the server-issued nonce
        if not nonce:
            raise ValueError("Server-issued nonce is required")

        if not wallet_nonce_store.consume(nonce):
            raise ValueError("Invalid or expired nonce — request a new one via /auth/wallet-nonce")

        # Verify the nonce is embedded in the signed message
        if nonce not in message:
            raise ValueError("Nonce mismatch — message does not contain the issued nonce")

        # Recover the address that produced the signature
        try:
            recovered = ContractClient.recover_signer(message, signature)
            if recovered.lower() != wallet_address.lower():
                raise ValueError("Signature mismatch")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Invalid wallet signature: {exc}")

        user = await self._session.scalar(
            select(User).where(User.wallet_address == wallet_address)
        )

        # L2: Check is_active for existing wallet users
        if user and not user.is_active:
            raise ValueError("Account is deactivated")

        if not user:
            # Auto-register wallet-only users
            user = User(wallet_address=wallet_address)
            self._session.add(user)
            await self._session.flush()

        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)
