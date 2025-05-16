
import os
import tempfile
import subprocess
import shutil
from typing import List
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(
    title="PDF Concatenation Service",
    description="A service that concatenates multiple PDF files into a single PDF.",
    version="1.0.0"
)

@app.post("/concatenate", summary="Concatenate multiple PDF files")
async def concatenate_pdfs(files: List[UploadFile] = File(...)):
    """
    Accepts multiple PDF files and returns a single concatenated PDF.
    
    - **files**: An array of PDF files to concatenate.
    
    Returns:
        A single concatenated PDF file.
    """
    # Validate input
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
    
    # Create a directory for temporary files if it doesn't exist
    os.makedirs("temp_pdfs", exist_ok=True)
    
    # Generate unique IDs for this request
    request_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        # Save uploaded files to temporary directory
        for i, file in enumerate(files):
            # Generate a secure filename
            temp_filename = f"temp_pdfs/input_{request_id}_{i}.pdf"
            
            # Save the file
            content = await file.read()
            with open(temp_filename, "wb") as f:
                f.write(content)
            
            temp_files.append(temp_filename)
        
        # Create output file path
        output_path = f"temp_pdfs/output_{request_id}.pdf"
        
        try:
            # Use pdfunite to concatenate the files
            cmd = ["pdfunite"] + temp_files + [output_path]
            process = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Check if the output file was created
            if not os.path.exists(output_path):
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to concatenate PDF files"
                )
            
            # Return the concatenated file
            return FileResponse(
                path=output_path,
                media_type="application/pdf",
                filename="concatenated.pdf",
                background=lambda: cleanup_files([output_path] + temp_files)
            )
            
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing the files: {e.stderr}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing the files: {str(e)}"
            )
    except Exception as e:
        # Clean up any files that were created
        cleanup_files(temp_files)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the files: {str(e)}"
        )

def cleanup_files(file_paths):
    """Clean up temporary files after they are no longer needed."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore errors during cleanup

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)