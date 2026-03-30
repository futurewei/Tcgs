from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .topics import router as topics_router
from .capacity import router as capacity_router
from .templates import router as templates_router
from .wiki import router as wiki_router
from .insights import router as insights_router
from .stage_instances import router as stage_instances_router
from .upload import router as upload_router
from .risks import router as risks_router
from .profile import router as profile_router
from .core_ideas import router as core_ideas_router
from .responsibility import router as responsibility_router
from .algo_delivery import router as algo_delivery_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
api_router.include_router(capacity_router, prefix="/capacity", tags=["capacity"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(wiki_router, prefix="/wiki", tags=["wiki"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
api_router.include_router(stage_instances_router, tags=["stage-instances"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(risks_router, tags=["risks"])
api_router.include_router(profile_router, tags=["profile"])
api_router.include_router(core_ideas_router, tags=["core-ideas"])
api_router.include_router(responsibility_router, prefix="/responsibility", tags=["responsibility"])
api_router.include_router(algo_delivery_router, prefix="/algo-deliveries", tags=["algo-deliveries"])
