
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Secret Storage", description="A secure cloud storage app for string secrets.")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get app secret from environment variable
APP_SECRET = os.getenv("APP_SECRET", "default_secret_key_for_development_only")

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create secrets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        secret TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SecretSet(BaseModel):
    username: str
    secret: str

# Helper functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, APP_SECRET, algorithm="HS256")
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, APP_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return username

# Routes
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT email FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use"
        )
    
    # Check if username already exists
    cursor.execute("SELECT username FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already in use"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Insert new user
    cursor.execute(
        "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
        (user.email, user.username, hashed_password)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Registration successful"}

@app.post("/login")
async def login(user: UserLogin):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Find user by email
    cursor.execute("SELECT email, username, password FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(days=1)
    access_token = create_access_token(
        data={"sub": db_user[1]},  # Use username as subject
        expires_delta=access_token_expires
    )
    
    return {"token": access_token, "message": "Login successful"}

@app.post("/set_secret")
async def set_secret(secret_data: SecretSet, current_user: str = Depends(get_current_user)):
    # Verify that the username in the request matches the authenticated user
    if secret_data.username != current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username does not match authenticated user"
        )
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT username FROM users WHERE username = ?", (secret_data.username,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if secret already exists for this user
    cursor.execute("SELECT id FROM secrets WHERE username = ?", (secret_data.username,))
    existing_secret = cursor.fetchone()
    
    if existing_secret:
        # Update existing secret
        cursor.execute(
            "UPDATE secrets SET secret = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (secret_data.secret, secret_data.username)
        )
    else:
        # Insert new secret
        cursor.execute(
            "INSERT INTO secrets (username, secret) VALUES (?, ?)",
            (secret_data.username, secret_data.secret)
        )
    
    conn.commit()
    conn.close()
    
    return {"message": "Secret has been set successfully"}

@app.get("/get_secret")
async def get_secret(username: str, current_user: str = Depends(get_current_user)):
    # Verify that the username in the request matches the authenticated user
    if username != current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username does not match authenticated user"
        )
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get secret for the user
    cursor.execute("SELECT secret FROM secrets WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found for this user"
        )
    
    return {"secret": result[0]}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)