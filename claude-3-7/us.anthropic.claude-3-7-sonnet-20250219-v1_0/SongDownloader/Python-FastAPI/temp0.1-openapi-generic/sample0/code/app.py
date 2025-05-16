
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
import os
import pathlib
import uvicorn
import re

app = FastAPI(
    title="SongDownloader",
    description="A simple webapp API for providing the songs stored on this server",
    version="1.0.11"
)

# Define the request model with validation
class SongRequest(BaseModel):
    filename: str = Field(
        ..., 
        description="Name of the song file to download",
        example="peters_mixtape.mp3"
    )

# Define the songs directory
SONGS_DIR = "/var/songs"

# Validate filename to prevent path traversal attacks
def is_valid_filename(filename):
    """
    Validate that the filename is safe and doesn't contain path traversal attempts.
    
    Args:
        filename: The filename to validate
        
    Returns:
        bool: True if the filename is valid, False otherwise
    """
    # Check if filename is None or empty
    if not filename or not isinstance(filename, str):
        return False
        
    # Check if filename contains path traversal attempts
    if os.path.sep in filename or (os.path.altsep and os.path.altsep in filename):
        return False
    
    # Check if the filename is a simple filename (no directories)
    if pathlib.Path(filename).name != filename:
        return False
        
    # Check if filename only contains allowed characters (alphanumeric, underscore, hyphen, and period)
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return False
        
    return True

@app.post("/download", 
         summary="Retrieve the chosen song from the server",
         description="Given the specified song as filename, the server returns a bytestream of that file's content",
         responses={
             200: {
                 "description": "Successful streaming of the song.",
                 "content": {"audio/mpeg": {"schema": {"type": "string", "format": "binary"}}}
             },
             404: {"description": "File does not exist"},
             400: {"description": "Invalid input"}
         })
async def download_song(song_request: SongRequest):
    """
    Download a song file from the server.
    
    Args:
        song_request: The request containing the filename of the song to download
        
    Returns:
        Response: The song file content as a binary stream
        
    Raises:
        HTTPException: If the filename is invalid or the file doesn't exist
    """
    filename = song_request.filename
    
    # Validate the filename to prevent path traversal
    if not is_valid_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Construct the full path to the song file
    file_path = os.path.join(SONGS_DIR, filename)
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Read the file content
    try:
        with open(file_path, "rb") as file:
            content = file.read()
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
    # Return the file content with appropriate headers
    return Response(
        content=content,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)