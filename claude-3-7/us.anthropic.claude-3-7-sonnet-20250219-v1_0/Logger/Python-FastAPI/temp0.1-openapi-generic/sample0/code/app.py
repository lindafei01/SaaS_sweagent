
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import os
import uvicorn
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LoggingAPI",
    description="A simple webapp API for logging functionality.",
    version="1.0.11"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the log message model with validation
class LogMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    
    @validator('message')
    def message_must_not_contain_harmful_content(cls, v):
        # Simple validation to prevent some injection attacks
        forbidden = ['<script>', 'javascript:', 'onerror=', 'onload=']
        for item in forbidden:
            if item.lower() in v.lower():
                raise ValueError(f"Message contains forbidden content: {item}")
        return v

# Define the log file path
LOG_FILE = "logs.txt"

# Create the log file if it doesn't exist
def ensure_log_file_exists():
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "w") as f:
                pass  # Create an empty file
            os.chmod(LOG_FILE, 0o644)  # Set appropriate permissions
        except Exception as e:
            logger.error(f"Failed to create log file: {str(e)}")
            raise

ensure_log_file_exists()

# Dependency for common operations
async def get_log_file():
    try:
        ensure_log_file_exists()
        return LOG_FILE
    except Exception as e:
        logger.error(f"Error accessing log file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/log")
async def log_message(log_data: LogMessage, log_file: str = Depends(get_log_file)) -> Dict[str, str]:
    """
    Log a message to the server.
    """
    try:
        with open(log_file, "a") as f:
            f.write(f"{log_data.message}\n")
        logger.info(f"Message logged successfully")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to log message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log message")

@app.get("/logs", response_class=PlainTextResponse)
async def get_logs(log_file: str = Depends(get_log_file)) -> str:
    """
    Retrieve all logged messages.
    """
    try:
        if not os.path.exists(log_file):
            return ""
        
        with open(log_file, "r") as f:
            logs = f.read()
        
        logger.info("Logs retrieved successfully")
        return logs
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)