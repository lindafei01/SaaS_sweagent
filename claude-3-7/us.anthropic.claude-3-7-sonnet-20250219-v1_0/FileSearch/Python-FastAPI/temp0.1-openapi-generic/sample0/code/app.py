
import os
import re
import time
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(
    title="FileSearch",
    description="An API for checking if a file with given content or name exists on the server",
    version="1.0.11"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Add TrustedHost middleware
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # Restrict in production
)

# Simple rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
        
    async def __call__(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old requests
        self.requests = {ip: times for ip, times in self.requests.items() 
                        if times[-1] > current_time - 60}
        
        # Check if client has exceeded rate limit
        if client_ip in self.requests:
            times = self.requests[client_ip]
            if len(times) >= self.requests_per_minute:
                oldest_time = times[0]
                if current_time - oldest_time < 60:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                times.pop(0)
            times.append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return True

rate_limiter = RateLimiter()

# Define the request model
class SearchRequest(BaseModel):
    search_content: Optional[str] = Field(default=None, description="Content to search for in files")
    search_filename: Optional[str] = Field(default=None, description="Filename prefix to match")
    search_dir: Optional[str] = Field(default=None, description="Relative directory path within /data")

# Define the response model
class SearchResponse(BaseModel):
    files: List[str]

# Base data directory
DATA_DIR = "/data"

@app.post("/search", response_model=SearchResponse)
async def search_files(request: SearchRequest, _: bool = Depends(rate_limiter)):
    """
    Retrieve a list of files from the server that contain the specified content or match the filename.
    
    The server stores files in the /data directory. This endpoint will return a list of complete paths 
    to files in data that contain the specified content or start. It is possible to specify a relative 
    path in search_dir.
    """
    # Validate input
    if not request.search_content and not request.search_filename:
        raise HTTPException(status_code=400, detail="Either search_content or search_filename must be provided")
    
    # Determine the search directory
    search_dir = DATA_DIR
    if request.search_dir:
        # Sanitize the search_dir to prevent directory traversal attacks
        search_dir_path = request.search_dir.lstrip('/')
        search_dir = os.path.normpath(os.path.join(DATA_DIR, search_dir_path))
        
        # Ensure the search directory is within the DATA_DIR
        if not search_dir.startswith(DATA_DIR):
            raise HTTPException(status_code=400, detail="Invalid search directory")
    
    # Check if the search directory exists
    if not os.path.exists(search_dir) or not os.path.isdir(search_dir):
        return SearchResponse(files=[])
    
    matching_files = []
    
    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(search_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if filename matches
            if request.search_filename and file.startswith(request.search_filename):
                matching_files.append(file_path)
                continue
            
            # Check if content matches
            if request.search_content:
                try:
                    # Try to read as text first
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if request.search_content in content:
                                matching_files.append(file_path)
                                continue
                    except UnicodeDecodeError:
                        # If text reading fails, try binary search
                        with open(file_path, 'rb') as f:
                            binary_content = f.read()
                            if request.search_content.encode('utf-8') in binary_content:
                                matching_files.append(file_path)
                except Exception as e:
                    # Skip files that can't be read
                    pass
    
    return SearchResponse(files=matching_files)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)