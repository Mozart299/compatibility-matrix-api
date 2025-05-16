from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, compatibility, assessments, connections, biometrics


api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(compatibility.router, prefix="/compatibility", tags=["compatibility"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(biometrics.router, prefix="/biometrics", tags=["biometrics"])