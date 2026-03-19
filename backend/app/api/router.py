from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.github import router as github_router
from app.api.graph import router as graph_router
from app.api.health import router as health_router
from app.api.loans import router as loans_router
from app.api.sybil import router as sybil_router
from app.api.trust_score import router as trust_score_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(trust_score_router)
api_router.include_router(sybil_router)
api_router.include_router(graph_router)
api_router.include_router(loans_router)
api_router.include_router(github_router)
