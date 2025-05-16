
import sqlite3
import uuid
from datetime import datetime, date
from typing import List, Optional
import os

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="Click Tracking API",
    description="API for registering and retrieving user clicks.",
    version="1.0.0"
)

# Database setup
DB_NAME = "db.sqlite3"

def get_db():
    """Create a database connection and return it"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with the required table"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create clicks table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clicks (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# Models
class Click(BaseModel):
    id: str = Field(description="The unique identifier for the click.")
    timestamp: str = Field(description="The timestamp of the click.")

# API Endpoints
@app.post("/click", status_code=201)
def register_click(db: sqlite3.Connection = Depends(get_db)):
    """Register a new click in the database"""
    try:
        click_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO clicks (id, timestamp) VALUES (?, ?)",
            (click_id, timestamp)
        )
        db.commit()
        
        return {"message": "Click registered successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to register click: {str(e)}")

@app.get("/clicks", response_model=List[Click])
def get_clicks(
    date: date = Query(..., description="The date to filter clicks"),
    direction: str = Query(
        ..., 
        description="Specify '<', '<=' or '>' etc. to filter clicks before, before or at or after the date.",
        enum=["<", ">", "<=", ">="]
    ),
    db: sqlite3.Connection = Depends(get_db)
):
    """Retrieve clicks based on date filter"""
    try:
        # Validate direction parameter
        if direction not in ["<", ">", "<=", ">="]:
            raise HTTPException(status_code=400, detail="Invalid direction parameter")
        
        # Convert date to string format for comparison
        date_str = date.isoformat()
        
        # Build the query based on the direction
        query = f"SELECT id, timestamp FROM clicks WHERE DATE(timestamp) {direction} ?"
        
        cursor = db.cursor()
        cursor.execute(query, (date_str,))
        
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(status_code=404, detail="No clicks found")
        
        # Convert results to list of Click objects
        clicks = [{"id": row["id"], "timestamp": row["timestamp"]} for row in results]
        
        return clicks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve clicks: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)