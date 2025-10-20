from fastapi import APIRouter
from app.api.v1.endpoints import health, qa, standards, imports, reviews, prompts, audit, metrics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"]) 
api_router.include_router(qa.router)
api_router.include_router(standards.router)
api_router.include_router(imports.router)
api_router.include_router(reviews.router)
api_router.include_router(prompts.router)
api_router.include_router(audit.router)
api_router.include_router(metrics.router)
