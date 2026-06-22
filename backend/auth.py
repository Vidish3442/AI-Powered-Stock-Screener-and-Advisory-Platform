from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from backend.database import get_db
from backend.security import client_ip, rate_limiter
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
import hashlib
import hmac
import logging
import secrets
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
password_hasher = PasswordHasher()

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET or JWT_SECRET == "your-secret-key" or len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be set to a random value of at least 32 characters")
JWT_ALGORITHM = "HS256"

def hash_password_safe(password: str) -> str:
    """Hash a password with Argon2id."""
    return password_hasher.hash(password)

def verify_password_safe(password: str, stored_hash: str) -> bool:
    """Verify Argon2id hashes and legacy salted SHA-256 hashes."""
    if stored_hash.startswith("$argon2"):
        try:
            return password_hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    try:
        salt, password_hash = stored_hash.split(":", 1)
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return hmac.compare_digest(test_hash, password_hash)
    except (AttributeError, ValueError):
        return False

class Signup(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"email": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if email is None:
            return None
        return email
    except jwt.PyJWTError:
        return None

@router.post("/signup")
def signup(data: Signup, request: Request):
    conn = None
    cur = None
    normalized_email = data.email.lower().strip()

    rate_limiter.check(f"signup:ip:{client_ip(request)}", limit=5, window_seconds=3600)
    
    try:
        if len(data.name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        conn = get_db()
        cur = conn.cursor()
            
        cur.execute("SELECT email FROM users WHERE email = %s", (normalized_email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password_safe(data.password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (data.name.strip(), normalized_email, hashed_password)
        )
        conn.commit()
        token = create_access_token(normalized_email)
        
        return {"status": "user created", "token": token, "email": normalized_email, "name": data.name.strip()}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Signup failed")
        raise HTTPException(status_code=500, detail="Unable to create account")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.post("/login")
def login(data: Login, request: Request):
    conn = None
    cur = None
    normalized_email = data.email.lower().strip()
    ip = client_ip(request)

    rate_limiter.check(f"login:ip:{ip}", limit=20, window_seconds=900)
    rate_limiter.check(f"login:account:{ip}:{normalized_email}", limit=5, window_seconds=900)
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("SELECT name, email, password_hash FROM users WHERE email = %s", (normalized_email,))
        user = cur.fetchone()
        
        if not user or not verify_password_safe(data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")        
        if not user['password_hash'].startswith("$argon2") or password_hasher.check_needs_rehash(user['password_hash']):
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE email = %s",
                (hash_password_safe(data.password), normalized_email),
            )
            conn.commit()

        token = create_access_token(normalized_email)
        return {"status": "login successful", "token": token, "email": user['email'], "name": user['name']}
        
    except HTTPException:
        raise
    except Exception:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail="Unable to complete login")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Authentication dependency that validates JWT token and returns user info.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = verify_token(credentials.credentials)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    conn = None
    cur = None
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("SELECT user_id, name, email FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"]
        }
        
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load authenticated user")
        raise HTTPException(status_code=500, detail="Unable to authenticate user")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
