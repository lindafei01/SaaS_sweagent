
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
import zipfile
import io
import os
import uvicorn
from typing import List

app = FastAPI(
    title="ZipToTxt",
    description="A simple webapp API for converting zip files into a single text file.",
    version="1.0.11"
)

@app.post("/convert", response_class=PlainTextResponse)
async def convert_zip_to_text(file: UploadFile):
    """
    Convert a zip file into a single text file, concatenating the contents of all text files in the zip.
    """
    # Check if the uploaded file is a zip file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only zip files are supported")
    
    try:
        # Read the uploaded file content
        content = await file.read()
        
        # Create a BytesIO object from the content
        zip_bytes = io.BytesIO(content)
        
        # Open the zip file
        with zipfile.ZipFile(zip_bytes, 'r') as zip_ref:
            # Get all file names in the zip
            file_names = zip_ref.namelist()
            
            # Filter out directories and non-text files
            text_files = []
            for name in file_names:
                # Skip directories and hidden files
                if name.endswith('/') or name.startswith('__MACOSX') or name.startswith('.'):
                    continue
                
                # Try to determine if it's a text file by extension or content
                try:
                    # Common text file extensions
                    text_extensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.c', '.cpp', '.h', '.log']
                    is_text_by_ext = any(name.lower().endswith(ext) for ext in text_extensions)
                    
                    # If not determined by extension, try to decode as text
                    if not is_text_by_ext:
                        # Read a small sample to check if it's text
                        sample = zip_ref.read(name)[:1024]
                        try:
                            sample.decode('utf-8')
                            # If we can decode it as UTF-8, consider it text
                            is_text = True
                        except UnicodeDecodeError:
                            # If we can't decode it as UTF-8, try another common encoding
                            try:
                                sample.decode('latin-1')
                                is_text = True
                            except:
                                is_text = False
                    else:
                        is_text = True
                    
                    if is_text:
                        text_files.append(name)
                except:
                    # If any error occurs, skip this file
                    continue
            
            # Sort files alphabetically for consistent output
            text_files.sort()
            
            # Concatenate the contents of all text files
            all_text = []
            for text_file in text_files:
                try:
                    file_content = zip_ref.read(text_file)
                    # Try to decode with utf-8 first
                    try:
                        decoded_content = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fall back to latin-1 if utf-8 fails
                        decoded_content = file_content.decode('latin-1')
                    
                    # Add file name as header and content
                    all_text.append(f"--- {text_file} ---\n")
                    all_text.append(decoded_content)
                    all_text.append("\n\n")
                except Exception as e:
                    # Skip files that can't be read or decoded
                    continue
            
            # Join all text content
            result = "".join(all_text)
            
            # Return empty string if no text files were found
            if not result:
                return ""
            
            return result
            
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing zip file: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint that provides basic information about the API.
    """
    return {
        "message": "Welcome to ZipToTxt API",
        "description": "Use POST /convert endpoint to convert zip files to text",
        "version": "1.0.11"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)