from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "CreDeFi"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/credefi"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Blockchain
    RPC_URL: str = "http://127.0.0.1:8545"
    CHAIN_PRIVATE_KEY: str = ""  # deployer/backend signer — set via .env
    LOAN_CONTRACT_ADDRESS: str = ""
    VAULT_CONTRACT_ADDRESS: str = ""
    NFT_CONTRACT_ADDRESS: str = ""
    RATE_MODEL_ADDRESS: str = ""
    USDC_ADDRESS: str = ""
    WETH_ADDRESS: str = ""

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""


settings = Settings()
