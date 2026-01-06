"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import chat, documents, meta

router = APIRouter()

# Include all v1 routers
router.include_router(meta.router)
router.include_router(documents.router)
router.include_router(chat.router)
