from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.database import get_db
import hashlib
import secrets
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = "HS256"

def hash_password_safe(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return salt + ":" + password_hash

def verify_password_safe(password: str, stored_hash: str) -> bool:
    try:
        salt, password_hash = stored_hash.split(":", 1)
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == password_hash
    except:
        return False

class Signup(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

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
def signup(data: Signup):
    conn = None
    cur = None
    
    try:
        if len(data.name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        if len(data.password) > 100:
            raise HTTPException(status_code=400, detail="Password is too long")
        
        conn = get_db()
        cur = conn.cursor()
            
        cur.execute("SELECT email FROM users WHERE email = %s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password_safe(data.password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (data.name.strip(), data.email.lower().strip(), hashed_password)
        )
        conn.commit()
        token = create_access_token(data.email.lower().strip())
        
        return {"status": "user created", "token": token, "email": data.email.lower().strip(), "name": data.name.strip()}
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.post("/login")
def login(data: Login):
    conn = None
    cur = None
    
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("SELECT name, email, password_hash FROM users WHERE email = %s", (data.email.lower().strip(),))
        user = cur.fetchone()
        
        if not user or not verify_password_safe(data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")        
        token = create_access_token(data.email.lower().strip())
        return {"status": "login successful", "token": token, "email": user['email'], "name": user['name']}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()