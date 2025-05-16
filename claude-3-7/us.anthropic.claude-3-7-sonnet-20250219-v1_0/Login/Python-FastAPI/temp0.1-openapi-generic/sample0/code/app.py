
import os
import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from starlette.middleware.cors import CORSMiddleware


# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginResponse(BaseModel):
    token: str
    message: str


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    message: str


# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Get secret key from environment variable or use a default one
SECRET_KEY = os.getenv("APP_SECRET", "default_secret_key_for_development_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI app
app = FastAPI(
    title="LoginAPI",
    description="A simple webapp API for login and registration functionality.",
    version="1.0.11"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "message" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail["message"]}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": str(exc.detail)}
    )


# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()


# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(email: str):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password, name FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "email": user[1], "password": user[2], "name": user[3]}
    return None


def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user


# API Endpoints
@app.post(
    "/login", 
    response_model=LoginResponse, 
    status_code=200, 
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def login(login_data: LoginRequest):
    user = authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid email or password"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"token": access_token, "message": "Login successful"}


@app.post(
    "/register", 
    response_model=MessageResponse, 
    status_code=201, 
    tags=["Authentication"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"}
    }
)
async def register(register_data: RegisterRequest):
    # Check if user already exists
    existing_user = get_user_by_email(register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={"message": "Email already in use or invalid data"}
        )
    
    # Hash the password
    hashed_password = get_password_hash(register_data.password)
    
    # Store user in database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
            (register_data.email, hashed_password, register_data.name)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail={"message": "Email already in use or invalid data"}
        )
    finally:
        conn.close()
    
    return {"message": "Registration successful"}


# Main entry point
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)