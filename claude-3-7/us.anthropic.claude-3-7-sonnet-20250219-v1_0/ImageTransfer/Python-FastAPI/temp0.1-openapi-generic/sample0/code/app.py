
from fastapi import FastAPI, UploadFile, HTTPException, File, Response
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from typing import Dict, Any
import mimetypes
import uvicorn

app = FastAPI(
    title="Image Upload and Share API",
    description="An API for uploading images and generating shareable links.",
    version="1.0.0"
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload an image and get a shareable link.
    
    Args:
        file: The image file to upload
        
    Returns:
        A JSON object containing the ID of the uploaded image
    """
    try:
        # Generate a unique ID for the image
        image_id = str(uuid.uuid4())
        
        # Get the file extension from the filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        
        # Create the file path
        file_path = os.path.join(UPLOAD_DIR, f"{image_id}{file_extension}")
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"id": image_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/images/{image_id}")
async def get_image(image_id: str) -> Response:
    """
    Get an image by its ID.
    
    Args:
        image_id: The ID of the image to retrieve
        
    Returns:
        The image file
    """
    try:
        # Find the file with the given image_id
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(image_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                # Determine the content type based on the file extension
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"
                
                # Read the file
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                # Return the file with the appropriate content type
                return Response(
                    content=file_content,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f"inline; filename={filename}"
                    }
                )
        
        # If no file is found, return a 404 error
        raise HTTPException(status_code=404, detail="Image not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint that provides basic API information.
    """
    return {
        "message": "Image Upload and Share API",
        "version": "1.0.0",
        "endpoints": {
            "/upload": "POST - Upload an image",
            "/images/{imageId}": "GET - View an image"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)