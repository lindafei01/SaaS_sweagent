
import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Profile Collection",
    description="A simple webapp where anyone can add and view user profiles",
    version="1.0.0"
)

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create profiles table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        profile_page TEXT NOT NULL,
        profile_photo BLOB NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Add a new user profile
@app.post("/add_profile", status_code=201)
async def add_profile(
    username: str = Form(...),
    profile_page: str = Form(...),
    profile_photo: UploadFile = File(...)
):
    # Validate input
    if not username or not profile_page:
        raise HTTPException(status_code=400, detail="Username and profile page are required")
    
    # Check if profile photo is PNG
    if not profile_photo.content_type == "image/png":
        raise HTTPException(status_code=400, detail="Profile photo must be a PNG image")
    
    # Read profile photo content
    photo_content = await profile_photo.read()
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT username FROM profiles WHERE username = ?", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=403, detail="Profile already exists")
        
        # Insert new profile
        cursor.execute(
            "INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)",
            (username, profile_page, photo_content)
        )
        conn.commit()
        
        return {"message": "Profile created successfully"}
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(status_code=400, detail=f"Error creating profile: {str(e)}")
    finally:
        conn.close()

# Get user profile HTML
@app.get("/profile/{username}", response_class=HTMLResponse)
async def get_profile(username: str):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get profile page
    cursor.execute("SELECT profile_page FROM profiles WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return result[0]

# Get user profile photo
@app.get("/profile-photo/{username}")
async def get_profile_photo(username: str):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get profile photo
    cursor.execute("SELECT profile_photo FROM profiles WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Profile photo not found")
    
    # Return PNG image
    return Response(
        content=result[0],
        media_type="image/png"
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)