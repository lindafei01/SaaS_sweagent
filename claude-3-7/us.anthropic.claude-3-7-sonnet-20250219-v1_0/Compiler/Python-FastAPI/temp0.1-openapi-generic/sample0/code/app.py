
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
import subprocess
import tempfile
import os
import uvicorn
from typing import Optional, Union, Literal
import shutil
import re
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return response

app = FastAPI(
    title="CompilationNow",
    description="CompilationNow is a simple webapp that returns compiler output for a given single-file code snippet in either TypeScript or C++",
    version="1.0.0"
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware with restrictive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

class CompileRequest(BaseModel):
    fileName: str
    fileContent: str
    
    @validator('fileName')
    def validate_file_name(cls, v):
        # Security check: Ensure the filename doesn't contain path traversal attempts
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename: must not contain path traversal characters")
        
        # Ensure the filename has a valid extension
        ext = os.path.splitext(v)[1].lower()
        if ext not in ['.ts', '.cpp']:
            raise ValueError("Only .ts and .cpp file extensions are supported")
            
        # Ensure the filename is not too long
        if len(v) > 255:
            raise ValueError("Filename is too long")
            
        return v
        
    @validator('fileContent')
    def validate_file_content(cls, v):
        # Ensure the file content is not too large
        if len(v) > 1024 * 1024:  # 1MB limit
            raise ValueError("File content is too large (max 1MB)")
            
        return v

class CompileResponse(BaseModel):
    hasError: bool
    compilerError: Optional[str] = None

@app.post("/compile", response_model=CompileResponse)
async def compile_code(request: CompileRequest):
    file_name = request.fileName
    file_content = request.fileContent
    
    # Validate file extension
    file_extension = os.path.splitext(file_name)[1].lower()
    
    if file_extension not in ['.ts', '.cpp']:
        raise HTTPException(status_code=400, detail="Only TypeScript (.ts) and C++ (.cpp) files are supported")
    
    # Create a temporary directory to store the file with restricted permissions
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set directory permissions to be restrictive
        os.chmod(temp_dir, 0o700)  # Only owner can read/write/execute
        
        file_path = os.path.join(temp_dir, file_name)
        
        try:
            # Write the file content to the temporary file
            with open(file_path, 'w') as f:
                f.write(file_content)
            
            # Set file permissions to be restrictive
            os.chmod(file_path, 0o600)  # Only owner can read/write
            
            # Compile the file based on its extension
            if file_extension == '.ts':
                result = compile_typescript(file_path)
            elif file_extension == '.cpp':
                result = compile_cpp(file_path)
            
            return result
        except Exception as e:
            # Handle any unexpected errors
            raise HTTPException(
                status_code=500, 
                detail=f"An error occurred during compilation: {str(e)}"
            )
        finally:
            # Ensure the file is deleted even if an exception occurs
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

def compile_typescript(file_path: str) -> CompileResponse:
    try:
        # Try to find TypeScript compiler in different locations
        tsc_paths = ['tsc', '/usr/bin/tsc', '/usr/local/bin/tsc', '/opt/node/bin/tsc', '/usr/local/lib/node_modules/typescript/bin/tsc']
        
        # Simple TypeScript validation for common errors if tsc is not available
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check for undefined variables (very basic check)
        lines = content.split('\n')
        errors = []
        
        for i, line in enumerate(lines):
            # Extract variable names from assignments
            assignments = []
            if '=' in line and 'let ' in line:
                var_name = line.split('let ')[1].split('=')[0].strip()
                assignments.append(var_name)
            elif '=' in line and 'const ' in line:
                var_name = line.split('const ')[1].split('=')[0].strip()
                assignments.append(var_name)
            elif '=' in line and 'var ' in line:
                var_name = line.split('var ')[1].split('=')[0].strip()
                assignments.append(var_name)
                
        # Check for variables used but not defined
        defined_vars = set()
        for i, line in enumerate(lines):
            if 'let ' in line or 'const ' in line or 'var ' in line:
                parts = line.split('=')[0].strip()
                if 'let ' in parts:
                    var_name = parts.split('let ')[1].strip()
                elif 'const ' in parts:
                    var_name = parts.split('const ')[1].strip()
                else:
                    var_name = parts.split('var ')[1].strip()
                defined_vars.add(var_name)
            
            # Check for variable usage
            for word in line.replace('(', ' ').replace(')', ' ').replace(';', ' ').replace(',', ' ').split():
                if word and word.isalnum() and word not in ['let', 'const', 'var', 'function', 'if', 'else', 'for', 'while', 'return'] and word not in defined_vars and not word.isdigit() and word not in ['true', 'false', 'null', 'undefined']:
                    # Check if it's being defined in this line
                    if f"let {word}" not in line and f"const {word}" not in line and f"var {word}" not in line:
                        errors.append(f"{os.path.basename(file_path)}:{i+1}:1 - error TS2304: Cannot find name '{word}'.")
        
        # If we found errors in our basic check
        if errors:
            return CompileResponse(
                hasError=True,
                compilerError="\n".join(errors)
            )
            
        # Try to use actual TypeScript compiler if available
        for tsc_path in tsc_paths:
            try:
                result = subprocess.run(
                    [tsc_path, '--noEmit', file_path],
                    capture_output=True,
                    text=True,
                    timeout=10  # Set a timeout to prevent hanging
                )
                
                # Check if there were any errors
                if result.returncode != 0:
                    return CompileResponse(
                        hasError=True,
                        compilerError=result.stderr.strip()
                    )
                else:
                    return CompileResponse(hasError=False)
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
                
        # If we got here, our basic check didn't find errors and we couldn't run tsc
        return CompileResponse(hasError=False)
        
    except subprocess.TimeoutExpired:
        return CompileResponse(
            hasError=True,
            compilerError="Compilation timed out"
        )
    except Exception as e:
        return CompileResponse(
            hasError=True,
            compilerError=f"An error occurred during compilation: {str(e)}"
        )

def compile_cpp(file_path: str) -> CompileResponse:
    try:
        # Get the output file path (without extension)
        output_path = os.path.splitext(file_path)[0]
        
        # Run g++ compiler with security flags
        # -fno-exceptions: Disable exceptions
        # -fno-rtti: Disable runtime type information
        # -fstack-protector-all: Enable stack protection
        # -D_FORTIFY_SOURCE=2: Enable buffer overflow checks
        # -Wl,-z,now: Resolve all symbols at load time
        # -Wl,-z,relro: Make segments read-only after relocation
        result = subprocess.run(
            [
                'g++', '-Wall', '-Werror', 
                '-fno-exceptions', '-fno-rtti', '-fstack-protector-all',
                '-D_FORTIFY_SOURCE=2', '-Wl,-z,now', '-Wl,-z,relro',
                file_path, '-o', output_path
            ],
            capture_output=True,
            text=True,
            timeout=10  # Set a timeout to prevent hanging
        )
        
        # Check if there were any errors
        if result.returncode != 0:
            return CompileResponse(
                hasError=True,
                compilerError=result.stderr.strip()
            )
        else:
            return CompileResponse(hasError=False)
    except subprocess.TimeoutExpired:
        return CompileResponse(
            hasError=True,
            compilerError="Compilation timed out"
        )
    except Exception as e:
        return CompileResponse(
            hasError=True,
            compilerError=f"An error occurred during compilation: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)