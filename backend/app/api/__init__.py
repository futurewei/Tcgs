from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .topics import router as topics_router
from .capacity import router as capacity_router
from .templates import router as templates_router
from .wiki import router as wiki_router
from .insights import router as insights_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
api_router.include_router(capacity_router, prefix="/capacity", tags=["capacity"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(wiki_router, prefix="/wiki", tags=["wiki"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
