
import os
import subprocess
import tempfile
import uuid
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
import uvicorn

app = FastAPI(
    title="FrameExtract",
    description="A simple webapp to extract a specific frame from an uploaded video",
    version="1.0.0"
)

@app.post("/extract")
async def extract_frame(
    videoFileName: Annotated[str, Form()],
    frameNumber: Annotated[int, Form()],
    video: Annotated[UploadFile, File()]
):
    """
    Extract a specific frame from an uploaded video.
    
    Args:
        videoFileName: Name of the video file
        frameNumber: The frame number (in seconds) to extract
        video: The uploaded video file
    
    Returns:
        The extracted frame as a PNG image
    """
    # Create a unique temporary directory to store files
    temp_dir = tempfile.mkdtemp()
    video_path = ""
    output_path = ""
    
    try:
        # Generate a unique filename to prevent path traversal attacks
        safe_filename = f"{uuid.uuid4()}.mp4"
        video_path = os.path.join(temp_dir, safe_filename)
        
        # Save the uploaded video to the temporary file
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        # Generate output image path
        output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")
        
        # Use ffmpeg to extract the frame
        # -y: Overwrite output files without asking
        # -ss: Seek to position (in seconds)
        # -i: Input file
        # -vframes 1: Extract only one frame
        # -q:v 2: Quality level (lower is better)
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(frameNumber),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        
        # Run the ffmpeg command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Check if the frame was successfully extracted
        if process.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(
                status_code=404,
                detail={"error": f"Frame at second {frameNumber} could not be found."}
            )
        
        # Read the extracted frame
        with open(output_path, "rb") as f:
            image_data = f.read()
        
        # Return the image with the appropriate content type
        return Response(content=image_data, media_type="image/png")
    
    finally:
        # Clean up temporary files
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        try:
            os.rmdir(temp_dir)
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)