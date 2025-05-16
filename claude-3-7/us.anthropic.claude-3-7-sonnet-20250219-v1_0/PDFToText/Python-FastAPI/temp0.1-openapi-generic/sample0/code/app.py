
import os
import subprocess
import tempfile
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
import uvicorn

app = FastAPI(
    title="PDF to Text Converter API",
    description="A simple API to convert PDF files to Text format.",
    version="1.0.0"
)

@app.post("/convert", response_class=PlainTextResponse)
async def convert_pdf_to_text(file: Annotated[UploadFile, File(description="The PDF file to be converted.")]):
    """
    Convert a PDF file to Text format.
    
    Args:
        file: The PDF file to be converted.
        
    Returns:
        The extracted text content from the PDF.
        
    Raises:
        HTTPException: If the file is not provided, not a PDF, or if conversion fails.
    """
    # Check if file was provided
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check if the file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            # Write the uploaded file content to the temporary file
            content = await file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
        
        # Create a temporary file for the output text
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_txt:
            temp_txt_path = temp_txt.name
        
        # Run pdftotext to convert PDF to text
        process = subprocess.run(
            ["pdftotext", "-layout", temp_pdf_path, temp_txt_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if the conversion was successful
        if process.returncode != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"PDF conversion failed: {process.stderr}"
            )
        
        # Read the converted text
        with open(temp_txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Clean up temporary files
        os.unlink(temp_pdf_path)
        os.unlink(temp_txt_path)
        
        # Return the text content
        return text_content
    
    except Exception as e:
        # Clean up temporary files if they exist
        for path in [temp_pdf_path, temp_txt_path]:
            if 'path' in locals() and os.path.exists(path):
                os.unlink(path)
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during conversion: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint that provides API information."""
    return {
        "message": "PDF to Text Converter API",
        "version": "1.0.0",
        "usage": "POST /convert with a PDF file to convert it to text"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)