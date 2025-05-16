
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from typing import List, Optional
import tempfile
import os
import subprocess
import shutil
import re
import uuid
import uvicorn

app = FastAPI(
    title="GIF Creator API",
    description="API to create a GIF from a set of images with specified parameters.",
    version="1.0.0"
)

# Validate target size format (e.g., "500x500")
def validate_target_size(target_size: str) -> bool:
    pattern = r'^\d+x\d+$'
    return bool(re.match(pattern, target_size))

# Validate file extension to ensure it's an image
def validate_image_extension(filename: str) -> bool:
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff']
    _, ext = os.path.splitext(filename.lower())
    return ext in valid_extensions

@app.post("/create-gif")
async def create_gif(
    images: List[UploadFile] = File(...),
    targetSize: str = Form(...),
    delay: int = Form(10),
    appendReverted: bool = Form(False)
):
    # Validate inputs
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    if not validate_target_size(targetSize):
        raise HTTPException(status_code=400, detail="Invalid target size format. Use WIDTHxHEIGHT (e.g., 500x500)")
    
    if delay < 1:
        raise HTTPException(status_code=400, detail="Delay must be at least 1 millisecond")
    
    # Create a temporary directory to store uploaded images
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded images to temporary directory
        image_paths = []
        for i, image in enumerate(images):
            if not validate_image_extension(image.filename):
                raise HTTPException(status_code=400, detail=f"File {image.filename} is not a valid image")
            
            # Generate a safe filename with UUID to prevent path traversal attacks
            safe_filename = f"{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"
            file_path = os.path.join(temp_dir, safe_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            image_paths.append(file_path)
        
        if not image_paths:
            raise HTTPException(status_code=400, detail="No valid images provided")
        
        # If appendReverted is True, add the images in reverse order (excluding the last one to avoid duplication)
        if appendReverted and len(image_paths) > 1:
            image_paths.extend(image_paths[-2::-1])
        
        # Create output GIF path
        output_gif = os.path.join(temp_dir, "output.gif")
        
        # Build ImageMagick convert command
        cmd = [
            "convert",
            "-delay", str(delay/10),  # convert from milliseconds to centiseconds for ImageMagick
            "-loop", "0",  # 0 means loop forever
            "-resize", targetSize,
        ]
        cmd.extend(image_paths)
        cmd.append(output_gif)
        
        # Execute the command
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error creating GIF: {e.stderr.decode() if e.stderr else str(e)}"
            )
        
        # Read the output GIF
        with open(output_gif, "rb") as f:
            gif_data = f.read()
        
        # Return the GIF
        return Response(content=gif_data, media_type="image/gif")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)