from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from pydantic import BaseModel, EmailStr, Field
from argon2 import PasswordHasher
from app.database import get_db_connection
from argon2.exceptions import HashingError
from datetime import datetime, timedelta, timezone
from app.database import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError

import jwt
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHashError,
)

router=APIRouter(prefix="/auth", tags=["Authentication"])
password_hasher=PasswordHasher()


class RegisterRequest(BaseModel):
    email:EmailStr
    password:str= Field(min_length=8, max_length=128)


@router.post("/register", status_code=201)
def register_user(request: RegisterRequest):
    password_hash=password_hasher.hash(request.password)

    query=text("""
    INSERT INTO users(email, password_hash)
    VALUES (:email, :password_hash)
    ON CONFLICT (email) DO NOTHING
    RETURNING id, email, is_active, created_at

""")
    try:
        with get_db_connection() as connection:
            result = connection.execute(
                query,{
                    "email": str(request.email).lower(),
                    "password_hash": password_hash                
                }
            )
            user = result.mappings().one_or_none()
            if user is None:
                raise HTTPException(
                    status_code=409,
                    detail="Email is already registered"
                )
            return dict(user)
    except HTTPException:
        raise 
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to register user"
        )
        

class LoginRequest(BaseModel):
    email:EmailStr
    password:str=Field(min_length=1, max_length=128)

@router.post("/login")
def login_user(request: LoginRequest):
    query = text("""
        SELECT id, email, password_hash, is_active
        FROM users
        WHERE email = :email
    """)

    try:
        with get_db_connection() as connection:
            result = connection.execute(
                query,
                {"email": str(request.email).lower()}
            )
            user = result.mappings().one_or_none()

    except Exception as e:
        print(f"Login database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to process login"
        )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    try:
        password_hasher.verify(
            user["password_hash"],
            request.password
        )
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user["id"]),
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }



# oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")
# def get_current_user(token: str = Depends(oauth2_scheme)):


bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    credentials_error=HTTPException(
        status_code=401,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},        
    )
    try:
        payload=jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp"]}            
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise credentials_error 
    query=text("""
    SELECT *
    FROM users 
    WHERE id = :user_id
    """)
    try:
        with get_db_connection() as connection:
            result=connection.execute(
                query,
                {"user_id": user_id}                
            )
            user=result.mappings().one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to verify user"            
        )  
    if user is None or not user["is_active"]:
        raise credentials_error
    return dict(user)     

@router.get("/me")
def get_me(current_user:dict=Depends(get_current_user)):
    return current_user



#              eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzkyNzc1ODk1LCJleHAiOjE3OTI3Nzc2OTV9.p3kCu90DKGuw5MLnHJIkJEXZT3h0GhfJMlvwXZ28jbA
         