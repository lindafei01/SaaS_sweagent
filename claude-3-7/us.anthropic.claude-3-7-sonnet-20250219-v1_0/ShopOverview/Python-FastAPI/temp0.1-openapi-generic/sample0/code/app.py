
import os
import sqlite3
import csv
import io
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Request, Response, status, Query
from fastapi.security import APIKeyCookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
import jwt
from starlette.middleware.sessions import SessionMiddleware

# Import contextlib for lifespan management
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield
    # Clean up resources at shutdown if needed
    pass

# Initialize FastAPI app with lifespan
app = FastAPI(title="Merchant WebApp API", lifespan=lifespan)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("APP_SECRET", "default_secret_key_for_development")
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get("APP_SECRET", "default_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cookie security
cookie_scheme = APIKeyCookie(name="AUTH_COOKIE")

# Database setup
DB_NAME = "db.sqlite3"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create merchants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create wares table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class MerchantRegister(BaseModel):
    email: EmailStr
    name: str
    password: str

class MerchantLogin(BaseModel):
    email: EmailStr
    password: str

class WareUpload(BaseModel):
    csv: str

# Authentication functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(cookie_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Routes
@app.post("/merchants/register", status_code=201)
async def register_merchant(merchant: MerchantRegister):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM merchants WHERE email = ?", (merchant.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(merchant.password)
    
    # Insert new merchant
    cursor.execute(
        "INSERT INTO merchants (email, name, password) VALUES (?, ?, ?)",
        (merchant.email, merchant.name, hashed_password)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Merchant registered successfully"}

@app.post("/merchants/login")
async def login_merchant(response: Response, merchant: MerchantLogin):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Find merchant by email
    cursor.execute("SELECT id, email, password FROM merchants WHERE email = ?", (merchant.email,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not pwd_context.verify(merchant.password, result[2]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": merchant.email}
    )
    
    # Set cookie
    response.set_cookie(
        key="AUTH_COOKIE",
        value=access_token,
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return {"message": "Login successful"}

@app.post("/merchants/upload-wares")
async def upload_wares(ware_upload: WareUpload, email: str = Depends(verify_token)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get merchant ID
    cursor.execute("SELECT id FROM merchants WHERE email = ?", (email,))
    merchant_result = cursor.fetchone()
    
    if not merchant_result:
        conn.close()
        raise HTTPException(status_code=401, detail="Merchant not found")
    
    merchant_id = merchant_result[0]
    
    # Parse CSV
    try:
        csv_file = io.StringIO(ware_upload.csv)
        csv_reader = csv.reader(csv_file)
        
        # Check header
        header = next(csv_reader)
        expected_header = ["name", "description", "price"]
        
        # Case-insensitive header check
        if len(header) != len(expected_header) or not all(h.lower() == e for h, e in zip(header, expected_header)):
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid CSV format. Expected columns: name, description, price")
        
        # Process rows
        for row in csv_reader:
            if len(row) != 3:
                continue  # Skip invalid rows
                
            name, description, price_str = row
            
            try:
                price = float(price_str)
                if price < 0:
                    continue  # Skip negative prices
            except ValueError:
                continue  # Skip rows with invalid price
                
            cursor.execute(
                "INSERT INTO wares (merchant_id, name, description, price) VALUES (?, ?, ?, ?)",
                (merchant_id, name, description, price)
            )
    
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
    
    conn.commit()
    conn.close()
    
    return {"message": "Wares uploaded successfully"}

@app.get("/wares", response_class=HTMLResponse)
async def get_wares(
    minPrice: Optional[float] = Query(None),
    maxPrice: Optional[float] = Query(None)
):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Build query with optional price filters
    query = """
    SELECT w.name, w.description, w.price, m.email
    FROM wares w
    JOIN merchants m ON w.merchant_id = m.id
    """
    
    params = []
    where_clauses = []
    
    if minPrice is not None:
        where_clauses.append("w.price >= ?")
        params.append(minPrice)
    
    if maxPrice is not None:
        where_clauses.append("w.price <= ?")
        params.append(maxPrice)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    cursor.execute(query, params)
    wares = cursor.fetchall()
    conn.close()
    
    # Generate HTML table
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Wares</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
        </style>
    </head>
    <body>
        <h1>Available Wares</h1>
        <table>
            <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Price</th>
                <th>Merchant</th>
            </tr>
    """
    
    for ware in wares:
        html_content += f"""
            <tr>
                <td>{ware['name']}</td>
                <td>{ware['description']}</td>
                <td>${ware['price']:.2f}</td>
                <td>{ware['email']}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)