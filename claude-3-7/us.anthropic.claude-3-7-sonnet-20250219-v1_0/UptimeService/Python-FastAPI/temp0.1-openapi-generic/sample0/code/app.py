
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Service Monitoring API",
    description="API for monitoring the status of services.",
    version="1.0.0"
)

# Database setup
DB_NAME = "db.sqlite3"

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create services table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id TEXT NOT NULL,
        token TEXT NOT NULL,
        last_notification TIMESTAMP NOT NULL,
        UNIQUE(service_id, token)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models for request/response validation
class HeartbeatRequest(BaseModel):
    serviceId: str
    token: str

class ServiceResponse(BaseModel):
    serviceId: str
    lastNotification: str

class ServicesRequest(BaseModel):
    token: str

# API endpoints
@app.post("/heartbeat")
async def register_heartbeat(request: HeartbeatRequest):
    """Register a heartbeat for a service."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current timestamp
        current_time = datetime.utcnow().isoformat()
        
        # Check if service exists with this token
        cursor.execute(
            "SELECT * FROM services WHERE service_id = ? AND token = ?",
            (request.serviceId, request.token)
        )
        service = cursor.fetchone()
        
        if service:
            # Update existing service
            cursor.execute(
                "UPDATE services SET last_notification = ? WHERE service_id = ? AND token = ?",
                (current_time, request.serviceId, request.token)
            )
        else:
            # Insert new service
            cursor.execute(
                "INSERT INTO services (service_id, token, last_notification) VALUES (?, ?, ?)",
                (request.serviceId, request.token, current_time)
            )
        
        conn.commit()
        conn.close()
        
        return {"message": "Heartbeat registered successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/services", response_model=List[ServiceResponse])
async def get_services(request: ServicesRequest):
    """Get overview of registered services."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all services registered with the given token
        cursor.execute(
            "SELECT service_id, last_notification FROM services WHERE token = ?",
            (request.token,)
        )
        
        services = cursor.fetchall()
        conn.close()
        
        # Format response
        response = [
            {"serviceId": service["service_id"], "lastNotification": service["last_notification"]}
            for service in services
        ]
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)