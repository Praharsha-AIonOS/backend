# backend/auth_router.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime, timedelta
from db import get_db_connection, return_db_connection
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Request/Response Models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str

class TokenVerifyResponse(BaseModel):
    valid: bool
    user: Optional[dict] = None

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to extract and verify user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists in database
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, email FROM users WHERE user_id = %s",
            (int(user_id),)
        )
        user = cursor.fetchone()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user[0],
            "username": user[1],
            "email": user[2]
        }
    finally:
        if conn:
            return_db_connection(conn)

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password length
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING user_id, username, email
        """, (user_data.username, user_data.email, password_hash))
        
        user = cursor.fetchone()
        conn.commit()
        
        # Create access token
        token_jti = str(uuid.uuid4())
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user[0]), "username": user[1], "jti": token_jti},
            expires_delta=access_token_expires
        )
        
        # Store session (optional, for token blacklisting)
        cursor.execute("""
            INSERT INTO sessions (user_id, token_jti, expires_at)
            VALUES (%s, %s, %s)
        """, (
            user[0],
            token_jti,
            datetime.utcnow() + access_token_expires
        ))
        conn.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user[0],
                "username": user[1],
                "email": user[2]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        if conn:
            return_db_connection(conn)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user and return JWT token"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to find user by username or email
        cursor.execute("""
            SELECT user_id, username, email, password_hash
            FROM users
            WHERE username = %s OR email = %s
        """, (credentials.username, credentials.username))
        
        user = cursor.fetchone()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user[3]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        token_jti = str(uuid.uuid4())
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user[0]), "username": user[1], "jti": token_jti},
            expires_delta=access_token_expires
        )
        
        # Store session
        cursor.execute("""
            INSERT INTO sessions (user_id, token_jti, expires_at)
            VALUES (%s, %s, %s)
        """, (
            user[0],
            token_jti,
            datetime.utcnow() + access_token_expires
        ))
        conn.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user[0],
                "username": user[1],
                "email": user[2]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        if conn:
            return_db_connection(conn)

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user by invalidating token (optional implementation)"""
    # In a production system, you might want to blacklist the token
    # For now, we'll just return success - client should remove token
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if a token is valid"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        return {"valid": False, "user": None}
    
    user_id = payload.get("sub")
    if user_id is None:
        return {"valid": False, "user": None}
    
    # Verify user exists
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, email FROM users WHERE user_id = %s",
            (int(user_id),)
        )
        user = cursor.fetchone()
        
        if user is None:
            return {"valid": False, "user": None}
        
        return {
            "valid": True,
            "user": {
                "user_id": user[0],
                "username": user[1],
                "email": user[2]
            }
        }
    finally:
        if conn:
            return_db_connection(conn)

