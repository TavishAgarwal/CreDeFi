from fastapi import APIRouter

from app.services.blockchain import blockchain_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/chain")
async def chain_status():
    """Return blockchain connection status for debugging and verification."""
    return blockchain_client.get_chain_status()
