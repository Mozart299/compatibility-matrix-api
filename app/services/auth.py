# app/services/auth.py
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, TokenPayload

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for handling authentication operations"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify that a plain password matches hashed password"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a password hash"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        """Generate a new access token"""
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        
        return jwt.encode(
            payload, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Generate a new refresh token"""
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        
        return jwt.encode(
            payload, 
            settings.JWT_REFRESH_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def decode_token(token: str, verify_exp: bool = True) -> Optional[TokenPayload]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": verify_exp}
            )
            token_data = TokenPayload(**payload)
            return token_data
        except JWTError:
            return None
            
    @staticmethod
    def decode_refresh_token(token: str) -> Optional[TokenPayload]:
        """Decode and validate a refresh token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_REFRESH_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            if payload.get("type") != "refresh":
                return None
            return token_data
        except JWTError:
            return None

    @staticmethod
    def get_user_by_email(db: Session, email: EmailStr) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def authenticate_user(db: Session, email: EmailStr, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user