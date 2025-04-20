# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, compatibility, assessments

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(compatibility.router, prefix="/compatibility", tags=["compatibility"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])