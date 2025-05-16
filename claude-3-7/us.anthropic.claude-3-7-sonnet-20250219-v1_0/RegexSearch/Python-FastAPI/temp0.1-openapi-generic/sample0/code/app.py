
import os
import re
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import pathlib

# Define response models
class FileSearchResponse(BaseModel):
    files: List[str]

class ErrorResponse(BaseModel):
    error: str

# Create FastAPI app
app = FastAPI(
    title="File Search API",
    description="API for searching files based on matching a given regex against their content.",
    version="1.0.0"
)

# Define the files root directory
FILES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")

@app.get("/search", 
         response_model=FileSearchResponse,
         responses={
             400: {"model": ErrorResponse},
             500: {"model": ErrorResponse}
         })
async def search_files(
    regex: str = Query(..., description="The regex pattern to match partially against file contents"),
    directory: Optional[str] = Query(None, description="The directory path to search files in, relative to the files root directory"),
    recursive: bool = Query(False, description="Whether to search recursively in subdirectories")
):
    try:
        # Validate and compile regex
        try:
            pattern = re.compile(regex)
        except re.error:
            raise HTTPException(status_code=400, detail={"error": "Invalid regex pattern"})
        
        # Determine the search directory
        search_dir = FILES_ROOT
        if directory:
            # Sanitize directory path to prevent directory traversal attacks
            # Convert to Path object and resolve to absolute path
            dir_path = pathlib.Path(FILES_ROOT) / directory
            
            # Ensure the path is within FILES_ROOT
            try:
                # Resolve to absolute path
                abs_dir_path = dir_path.resolve()
                abs_files_root = pathlib.Path(FILES_ROOT).resolve()
                
                # Check if the path is within FILES_ROOT
                if not str(abs_dir_path).startswith(str(abs_files_root)):
                    raise HTTPException(status_code=400, detail={"error": "Directory traversal not allowed"})
                
                search_dir = str(abs_dir_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail={"error": f"Invalid directory path: {str(e)}"})
            
            # Check if directory exists
            if not os.path.isdir(search_dir):
                raise HTTPException(status_code=400, detail={"error": f"Directory '{directory}' does not exist"})
        
        # Search for files matching the regex
        matching_files = []
        
        try:
            # Determine how to walk the directory
            if recursive:
                for root, _, files in os.walk(search_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if _check_file_content(file_path, pattern):
                            # Get path relative to search_dir
                            rel_path = os.path.relpath(file_path, search_dir)
                            matching_files.append(rel_path)
            else:
                # Non-recursive search
                for item in os.listdir(search_dir):
                    item_path = os.path.join(search_dir, item)
                    if os.path.isfile(item_path) and _check_file_content(item_path, pattern):
                        matching_files.append(item)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": f"Error searching files: {str(e)}"})
        
        return {"files": matching_files}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Internal server error: {str(e)}"})

def _check_file_content(file_path: str, pattern: re.Pattern) -> bool:
    """
    Check if the file content matches the given regex pattern.
    
    Args:
        file_path: Path to the file
        pattern: Compiled regex pattern
        
    Returns:
        True if the file content matches the pattern, False otherwise
    """
    try:
        # Skip directories and non-text files
        if not os.path.isfile(file_path):
            return False
            
        # Try to read the file as text
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
            return bool(pattern.search(content))
    except Exception:
        # If there's any error reading the file, skip it
        return False

if __name__ == "__main__":
    # Create files directory if it doesn't exist
    os.makedirs(FILES_ROOT, exist_ok=True)
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)